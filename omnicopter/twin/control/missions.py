"""Progressive Omnicopter missions with geometric PD and reference feedforward.

All rotations are about explicitly named WORLD axes. Every command is allocated
through the eight site actuators in the final, hardware-verified rotor frames.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from queue import SimpleQueue
import time

import mujoco
import numpy as np
from hover import XML, attitude_error, kick, make_sim, reset, rotation

HERE = Path(__file__).resolve().parent
AXES = np.eye(3)
BASE = np.array([0., 0., 1.])
STAGES = {
    0: "Hover and quaternion representation",
    1: "Independent translations",
    2: "Small independent attitude changes",
    3: "Large reorientation and hold",
    4: "Complete rotations, both directions",
    5: "Spatial paths and independent orientation",
    6: "Disturbance recovery during missions",
    7: "Yaw-rate envelope exploration",
}


@dataclass(frozen=True)
class Mission:
    name: str
    stage: int
    kind: str
    axis: int = 2
    amplitude: float = 0.0  # metres for translation, degrees for attitude
    move_s: float = 6.0
    hold_s: float = 2.0
    settle_s: float = 8.0
    kick_s: float | None = None
    radius_m: float = .2

    @property
    def duration(self):
        return 2.0 + (2 * self.move_s + self.hold_s if self.kind in ("translate", "attitude")
                      else self.move_s) + self.settle_s


MISSIONS = [
    Mission("hover", 0, "hover", move_s=4),
    Mission("quaternion_sign", 0, "sign", move_s=4),
    *[Mission(f"translate_{a}", 1, "translate", axis=i, amplitude=.20 if i == 2 else .25)
      for i, a in enumerate("xyz")],
    *[Mission(f"attitude_{a}_15", 2, "attitude", axis=i, amplitude=15, move_s=4)
      for i, a in enumerate("xyz")],
    Mission("attitude_x_45", 3, "attitude", axis=0, amplitude=45, move_s=8),
    Mission("attitude_y_45", 3, "attitude", axis=1, amplitude=45, move_s=8),
    Mission("attitude_y_90", 3, "attitude", axis=1, amplitude=90, move_s=12),
    Mission("attitude_x_180", 3, "attitude", axis=0, amplitude=180, move_s=20, hold_s=4),
    Mission("yaw_360", 4, "spin", axis=2, amplitude=360, move_s=36),
    Mission("yaw_minus_360", 4, "spin", axis=2, amplitude=-360, move_s=36),
    Mission("spin_x_360", 4, "spin", axis=0, amplitude=360, move_s=48),
    Mission("spin_y_360", 4, "spin", axis=1, amplitude=360, move_s=48),
    Mission("circle", 5, "circle", move_s=32),
    Mission("figure_eight", 5, "figure8", move_s=48),
    Mission("helix", 5, "helix", move_s=40, radius_m=.15),
    Mission("circle_yaw_360", 5, "circle_spin", amplitude=360, move_s=48),
    Mission("hover_push", 6, "hover", move_s=10, kick_s=4),
    Mission("circle_yaw_push", 6, "circle_spin", amplitude=360, move_s=48, kick_s=22),
    Mission("yaw_360_24s", 7, "spin", amplitude=360, move_s=24),
    Mission("yaw_360_12s", 7, "spin", amplitude=360, move_s=12),
    Mission("yaw_360_6s", 7, "spin", amplitude=360, move_s=6),
]


def smooth(s):
    s = float(np.clip(s, 0, 1))
    return s**3 * (10 - 15*s + 6*s*s)


def smooth_kinematics(t, start, duration):
    """Quintic progress and its first two time derivatives."""
    u = (t - start) / duration
    if u <= 0:
        return 0., 0., 0.
    if u >= 1:
        return 1., 0., 0.
    s = u**3 * (10 - 15*u + 6*u*u)
    sd = 30 * u*u * (1-u)**2 / duration
    sdd = 60 * u * (1-u) * (1-2*u) / duration**2
    return s, sd, sdd


def axis_quaternion(axis, angle):
    return np.r_[np.cos(angle / 2), AXES[axis] * np.sin(angle / 2)]


def reference_kinematics(mission, t, q0):
    """Return origin pose and analytic world-frame reference kinematics."""
    p, v, a = BASE.copy(), np.zeros(3), np.zeros(3)
    q = q0.copy()
    s, sd, sdd = smooth_kinematics(t, 2., mission.move_s)
    angle = angle_rate = angle_accel = 0.0
    if mission.kind in ("translate", "attitude"):
        if t > 2 + mission.move_s + mission.hold_s:
            sr, srd, srdd = smooth_kinematics(
                t, 2 + mission.move_s + mission.hold_s, mission.move_s)
            s, sd, sdd = 1-sr, -srd, -srdd
        if mission.kind == "translate":
            p[mission.axis] += mission.amplitude * s
            v[mission.axis] += mission.amplitude * sd
            a[mission.axis] += mission.amplitude * sdd
        else:
            angle = np.deg2rad(mission.amplitude) * s
            angle_rate = np.deg2rad(mission.amplitude) * sd
            angle_accel = np.deg2rad(mission.amplitude) * sdd
    elif mission.kind == "sign":
        q *= -1 if t >= 4 else 1
    elif mission.kind in ("spin", "circle_spin"):
        angle = np.deg2rad(mission.amplitude) * s
        angle_rate = np.deg2rad(mission.amplitude) * sd
        angle_accel = np.deg2rad(mission.amplitude) * sdd
    if mission.kind in ("circle", "circle_spin", "helix", "figure8"):
        phase = 2 * np.pi * s
        phase_rate = 2 * np.pi * sd
        phase_accel = 2 * np.pi * sdd
        if mission.kind == "figure8":
            p += [mission.radius_m * np.sin(phase), .15 * np.sin(2*phase), 0]
            v += [mission.radius_m * np.cos(phase) * phase_rate,
                  .30 * np.cos(2*phase) * phase_rate, 0]
            a += [mission.radius_m * (-np.sin(phase) * phase_rate**2
                                      + np.cos(phase) * phase_accel),
                  .30 * (-2*np.sin(2*phase) * phase_rate**2
                         + np.cos(2*phase) * phase_accel), 0]
        else:
            p += [mission.radius_m * (np.cos(phase) - 1), mission.radius_m * np.sin(phase),
                  .30 * s if mission.kind == "helix" else 0]
            v += [-mission.radius_m * np.sin(phase) * phase_rate,
                  mission.radius_m * np.cos(phase) * phase_rate,
                  .30 * sd if mission.kind == "helix" else 0]
            a += [-mission.radius_m * (np.cos(phase) * phase_rate**2
                                       + np.sin(phase) * phase_accel),
                  mission.radius_m * (-np.sin(phase) * phase_rate**2
                                      + np.cos(phase) * phase_accel),
                  .30 * sdd if mission.kind == "helix" else 0]
    if angle != 0:
        # Premultiplication: world-axis rotation, not body-axis Euler angles.
        mujoco.mju_mulQuat(q, axis_quaternion(mission.axis, angle), q0)
    omega_world = AXES[mission.axis] * angle_rate
    alpha_world = AXES[mission.axis] * angle_accel
    return p, v, a, q, omega_world, alpha_world, float(np.rad2deg(angle))


def reference(mission, t, q0):
    """Backward-compatible pose-only view of :func:`reference_kinematics`."""
    p, _, _, q, _, _, angle = reference_kinematics(mission, t, q0)
    return p, q, angle


def apply_reference(controller, p, v, a, q, omega_world, alpha_world):
    """Move an origin reference to the controller's centre-of-mass reference."""
    r = rotation(q)
    offset = r @ controller.com
    controller.target_origin = p.copy()
    controller.target_q = q.copy()
    controller.target_com = p + offset
    controller.target_velocity_com = v + np.cross(omega_world, offset)
    controller.target_acceleration_com = (a + np.cross(alpha_world, offset)
                                          + np.cross(omega_world, np.cross(omega_world, offset)))
    controller.target_omega = r.T @ omega_world
    controller.target_alpha = r.T @ alpha_world


def preflight(mission, controller):
    """Check path smoothness/coverage and quasistatic thrust feasibility.

    This is a hover-wrench check along the requested attitudes, not proof of
    dynamic feasibility. Dynamic saturation is measured in the actual run.
    """
    q0 = controller.target_q.copy()
    worst_residual, peak, travel, previous = 0., 0., 0., None
    for t in np.linspace(0, mission.duration, 401):
        p, q, angle = reference(mission, t, q0)
        if abs(np.linalg.norm(q) - 1) > 1e-10:
            raise ValueError("Reference quaternion is not normalized")
        if previous is not None:
            dq = attitude_error(previous, q)
            travel += np.linalg.norm(dq)
        previous = q.copy()
        wrench = np.r_[rotation(q).T @ (-controller.mass * controller.gravity), np.zeros(3)]
        u = controller.allocator.solve(wrench)
        worst_residual = max(worst_residual, float(np.linalg.norm(controller.matrix @ u - wrench)))
        peak = max(peak, float(np.max(np.abs(u))))
    if mission.kind in ("spin", "circle_spin") and abs(np.rad2deg(travel) - abs(mission.amplitude)) > 1e-6:
        raise ValueError("Reference did not traverse the full requested rotation")
    return {"samples": 401, "quasistatic_wrench_residual": worst_residual,
            "quasistatic_peak_thrust_N": peak, "reference_rotation_travel_deg": float(np.rad2deg(travel)),
            "passed": worst_residual < 1e-6}


GATES = {
    "peak_position_error_m": .12, "peak_attitude_error_deg": 15.,
    "tail_position_error_m": .01, "tail_attitude_error_deg": .5,
    "saturation_fraction": .02, "max_abs_input_N": 10.00000001,
    "rotation_endpoint_error_deg": 5., "rotation_progress_peak_error_deg": 20.,
}
ABORT = {"minimum_body_origin_z_m": .40, "maximum_distance_from_start_m": 2.,
         "attitude_error_deg": 100., "contact": True, "nonfinite": True}


def run(mission, output, view=False, controller_mode="pd", beta=.05,
        learning_rate=8e-4, leak=1e-6):
    model, data, controller = make_sim()
    reset(model, data, controller, False)
    runtime = None
    if controller_mode == "cmg-pes":
        from residual import PESWrenchAugmentor
        runtime = PESWrenchAugmentor(controller, beta, learning_rate, leak)
    elif controller_mode == "nengo-pd":
        from nengo_controllers import NengoPDController
        runtime = NengoPDController(controller, model.opt.timestep)
    elif controller_mode == "nengo-cmg-pes":
        from nengo_controllers import NengoCMGPESController
        runtime = NengoCMGPESController(
            controller, model.opt.timestep, beta, learning_rate, leak)
    q0 = controller.target_q.copy()
    plan = preflight(mission, controller)
    if not plan["passed"]:
        return {"name": mission.name, "stage": mission.stage, "status": "preflight_failed", "preflight": plan}
    events = SimpleQueue()
    viewer = None
    if view:
        import mujoco.viewer as mjviewer
        viewer = mjviewer.launch_passive(model, data, key_callback=events.put)
        with viewer.lock():
            viewer.cam.lookat[:] = BASE
            viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 2.2, 135, -20
        print("Space: pause/resume | close window: stop. Mission runs once; thrust sliders are controlled.", flush=True)
    steps = int(round(mission.duration / model.opt.timestep))
    previous_q = data.qpos[3:7].copy()
    progress = 0.
    paused = False
    aborted = None
    counters = {"peak_position_error_m": 0., "peak_attitude_error_deg": 0.,
                "tail_position_error_m": 0., "tail_attitude_error_deg": 0.,
                "max_abs_input_N": 0., "saturated_steps": 0, "steps_with_contacts": 0,
                "peak_force_residual_N": 0., "peak_torque_residual_Nm": 0.,
                "peak_pes_residual_norm": 0.,
                "rotation_progress_peak_error_deg": 0., "sum_position_error_sq": 0.,
                "sum_attitude_error_sq": 0., "tail_samples": 0}
    dt = model.opt.timestep
    deadline, next_frame = time.perf_counter(), 0.
    last_angle, count = 0., 0
    output.mkdir(parents=True, exist_ok=False)
    run_config = {"mission": asdict(mission), "duration_s": mission.duration,
                  "controller": controller_mode, "gates": GATES, "abort": ABORT,
                  "preflight": plan}
    if controller_mode == "cmg-pes":
        from residual import controller_metadata
        run_config["cmg_pes"] = controller_metadata(runtime)
    elif runtime is not None:
        run_config["nengo"] = runtime.metadata()
    (output / "mission.json").write_text(json.dumps(run_config, indent=2), encoding="utf-8")
    try:
        with (output / "trace.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = None
            for step in range(steps + 1):
                if viewer:
                    while True:
                        while not events.empty():
                            if events.get() == 32:
                                paused = not paused
                                deadline = time.perf_counter()
                        if not viewer.is_running():
                            aborted = "viewer_closed"
                            break
                        if not paused:
                            break
                        viewer.sync()
                        time.sleep(.01)
                    if aborted:
                        break
                if mission.kick_s is not None and step == round(mission.kick_s / dt):
                    kick(data)
                mujoco.mj_forward(model, data)
                if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)):
                    aborted = "nonfinite_state"
                    break
                p, v, a, q, omega_world, alpha_world, last_angle = reference_kinematics(
                    mission, data.time, q0)
                apply_reference(controller, p, v, a, q, omega_world, alpha_world)
                controls, metrics = (controller.command(data) if runtime is None
                                     else runtime.command(data, dt))
                data.ctrl[:] = controls
                increment_world = rotation(previous_q) @ attitude_error(previous_q, data.qpos[3:7])
                progress += np.rad2deg(float(increment_world @ AXES[mission.axis]))
                previous_q = data.qpos[3:7].copy()
                count += 1
                for key in ["position", "attitude"]:
                    unit = "m" if key == "position" else "deg"
                    value = metrics[f"{key}_error_{unit}"]
                    counters[f"peak_{key}_error_{unit}"] = max(counters[f"peak_{key}_error_{unit}"], value)
                    counters[f"sum_{key}_error_sq"] += value**2
                    if data.time >= mission.duration - 2 - 1e-8:
                        counters[f"tail_{key}_error_{unit}"] = max(counters[f"tail_{key}_error_{unit}"], value)
                counters["tail_samples"] += int(data.time >= mission.duration - 2 - 1e-8)
                counters["max_abs_input_N"] = max(counters["max_abs_input_N"], float(np.max(np.abs(controls))))
                counters["saturated_steps"] += int(metrics["saturated"])
                counters["steps_with_contacts"] += int(data.ncon > 0)
                counters["peak_force_residual_N"] = max(counters["peak_force_residual_N"], metrics["force_residual_N"])
                counters["peak_torque_residual_Nm"] = max(counters["peak_torque_residual_Nm"], metrics["torque_residual_Nm"])
                counters["peak_pes_residual_norm"] = max(
                    counters["peak_pes_residual_norm"], metrics.get("pes_residual_norm", 0.))
                counters["rotation_progress_peak_error_deg"] = max(counters["rotation_progress_peak_error_deg"], abs(progress - last_angle))
                if step % 5 == 0 or step == steps:
                    scalar_metrics = {key: value for key, value in metrics.items()
                                      if np.ndim(value) == 0}
                    row = {"time_s": data.time, **scalar_metrics, "reference_rotation_deg": last_angle,
                           "actual_rotation_progress_deg": progress}
                    for vector_name in ("baseline_wrench", "commanded_wrench",
                                        "pes_residual_wrench", "pes_learning_target"):
                        if vector_name in metrics:
                            labels = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")
                            row.update({f"{vector_name}_{label}": float(value)
                                        for label, value in zip(labels, metrics[vector_name])})
                    for i, axis in enumerate("xyz"):
                        row[f"{axis}_m"] = data.qpos[i]
                        row[f"ref_{axis}_m"] = p[i]
                    for i, axis in enumerate("wxyz"):
                        row[f"q_{axis}"] = data.qpos[i+3]
                        row[f"ref_q_{axis}"] = q[i]
                    for i, axis in enumerate("xyz"):
                        row[f"v{axis}_m_s"] = data.qvel[i]
                        row[f"w{axis}_rad_s"] = data.qvel[i+3]
                    if model.nsensordata >= 9:
                        for start, prefix, units in ((0, "imu_accel", "m_s2"),
                                                     (3, "imu_gyro", "rad_s"),
                                                     (6, "imu_vel", "m_s")):
                            row.update({f"{prefix}_{axis}_{units}": float(data.sensordata[start+i])
                                        for i, axis in enumerate("xyz")})
                    row.update({f"thrust_{i+1}_N": u for i, u in enumerate(controls)})
                    if writer is None:
                        writer = csv.DictWriter(stream, fieldnames=row.keys())
                        writer.writeheader()
                    writer.writerow(row)
                if data.ncon:
                    aborted = "contact"
                elif data.qpos[2] < ABORT["minimum_body_origin_z_m"]:
                    aborted = "height_envelope"
                elif np.linalg.norm(data.qpos[:3] - BASE) > ABORT["maximum_distance_from_start_m"]:
                    aborted = "position_envelope"
                elif metrics["attitude_error_deg"] > ABORT["attitude_error_deg"]:
                    aborted = "attitude_envelope"
                elif not np.all(np.isfinite(controls)):
                    aborted = "nonfinite_control"
                if aborted or step == steps:
                    break
                mujoco.mj_step(model, data)
                if viewer:
                    if data.time >= next_frame:
                        with viewer.lock():
                            viewer.user_scn.ngeom = 1
                            mujoco.mjv_initGeom(viewer.user_scn.geoms[0], mujoco.mjtGeom.mjGEOM_SPHERE,
                                np.array([.025, .025, .025]), p, np.eye(3).flatten(), np.array([0., 1., 1., .65]))
                        viewer.sync()
                        next_frame = data.time + 1/60
                    deadline += dt
                    remaining = deadline - time.perf_counter()
                    if remaining > 0:
                        time.sleep(remaining)
                    elif remaining < -.1:
                        deadline = time.perf_counter()
    finally:
        if runtime is not None and hasattr(runtime, "close"):
            runtime.close()
        if viewer:
            viewer.close()
    if count == 0:
        return {"name": mission.name, "stage": mission.stage, "status": "aborted", "reason": aborted}
    counters["saturation_fraction"] = counters["saturated_steps"] / count
    counters["position_RMSE_m"] = np.sqrt(counters.pop("sum_position_error_sq") / count)
    counters["attitude_RMSE_deg"] = np.sqrt(counters.pop("sum_attitude_error_sq") / count)
    is_spin = mission.kind in ("spin", "circle_spin")
    counters["actual_rotation_progress_deg"] = progress if is_spin else None
    counters["rotation_endpoint_error_deg"] = abs(progress - mission.amplitude) if is_spin else None
    if not is_spin:
        counters["rotation_progress_peak_error_deg"] = None
    failed = [key for key, limit in GATES.items() if counters[key] is not None and counters[key] > limit]
    if counters["tail_samples"] == 0:
        failed.append("missing_final_hold")
    result = {"name": mission.name, "stage": mission.stage, "status": "aborted" if aborted else ("fail" if failed else "pass"),
              "abort_reason": aborted, "failed_gates": failed, "completed_time_s": data.time,
              "planned_duration_s": mission.duration, "samples": count, **counters}
    (output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--mission", choices=[m.name for m in MISSIONS])
    parser.add_argument("--view", action="store_true", help="View a single mission in real time")
    parser.add_argument("--max-stage", type=int, choices=range(8), default=7)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--controller", choices=("pd", "cmg-pes", "nengo-pd", "nengo-cmg-pes"),
        default="pd")
    parser.add_argument("--beta", type=float, default=.05,
                        help="CMG residual fraction (cmg-pes only)")
    parser.add_argument("--learning-rate", type=float, default=8e-4,
                        help="Online PES decoder learning rate (cmg-pes only)")
    parser.add_argument("--leak", type=float, default=1e-6,
                        help="Online PES decoder leak (cmg-pes only)")
    args = parser.parse_args()
    if args.list:
        for m in MISSIONS:
            print(f"{m.stage}: {m.name:24s} {m.duration:5.1f}s | {STAGES[m.stage]}")
        return
    if args.view and not args.mission:
        parser.error("--view requires --mission NAME")
    output = args.output or HERE / "output" / datetime.now().strftime("campaign_%Y%m%d_%H%M%S_%f")
    output.mkdir(parents=True, exist_ok=False)
    selected = [m for m in MISSIONS if m.name == args.mission] if args.mission else [m for m in MISSIONS if m.stage <= args.max_stage]
    if args.beta < 0 or args.beta > 1 or args.learning_rate < 0 or args.leak < 0:
        parser.error("beta must be in [0,1], and learning-rate/leak must be nonnegative")
    manifest = {"mujoco_version": mujoco.__version__, "dt_s": .002,
                "controller": args.controller,
                "baseline": "Geometric PD plus analytic velocity/acceleration feedforward; bounded 6x8 allocation",
                "cmg_pes_parameters": ({"beta": args.beta, "learning_rate": args.learning_rate,
                                        "leak": args.leak} if "cmg-pes" in args.controller else None),
                "gains": {"kp_position": 4., "kd_position": 3.6, "kp_attitude": 16., "kd_attitude": 7.2},
                "rotation_convention": "Fixed world axes; q_ref = q_world_axis(angle) * q_XML_initial",
                "model_xml_sha256": hashlib.sha256(XML.read_bytes()).hexdigest(),
                "mesh_sha256": hashlib.sha256((XML.parent / "assets/Omnidrone.stl").read_bytes()).hexdigest(),
                "hover_py_sha256": hashlib.sha256((HERE / "hover.py").read_bytes()).hexdigest(),
                "missions_py_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "nengo_controllers_py_sha256": (hashlib.sha256(
                    (HERE / "nengo_controllers.py").read_bytes()).hexdigest()
                    if args.controller.startswith("nengo-") else None),
                "gates": GATES, "abort": ABORT, "selected_missions": [asdict(m) for m in selected]}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    results = []
    halted = False
    for m in selected:
        if halted:
            results.append({"name": m.name, "stage": m.stage, "status": "skipped", "reason": "prior mission did not pass"})
            continue
        print(f"START stage {m.stage}: {m.name} ({m.duration:.0f}s simulated)", flush=True)
        result = run(m, output / m.name, args.view, args.controller,
                     args.beta, args.learning_rate, args.leak)
        results.append(result)
        print(f"{result['status'].upper()}: {m.name} | peak position={result.get('peak_position_error_m', 0):.4f}m | peak attitude={result.get('peak_attitude_error_deg', 0):.2f}deg | gates={result.get('failed_gates', [])}", flush=True)
        halted = result["status"] != "pass"
        (output / "campaign.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (output / "campaign.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"RESULTS: {output}", flush=True)
    if halted:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
