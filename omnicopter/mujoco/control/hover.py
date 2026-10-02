"""Six-DoF Omnicopter tracking: geometric PD/feedforward + bounded allocation.

Uses only data.ctrl to control the original eight thrust actuators. No PX4/hardware I/O.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from queue import SimpleQueue
import time

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
XML = HERE.parent / "Omnidrone/mujoco model=omnidrone.xml"


def rotation(q):
    matrix = np.empty(9)
    mujoco.mju_quat2Mat(matrix, np.asarray(q, dtype=float))
    return matrix.reshape(3, 3)


def attitude_error(q, target):
    """Shortest rotation vector from current to target, in current body axes."""
    conjugate = q.copy()
    conjugate[1:] *= -1
    delta = np.empty(4)
    mujoco.mju_mulQuat(delta, conjugate, target)
    if delta[0] < 0:
        delta *= -1
    length = np.linalg.norm(delta[1:])
    return 2 * delta[1:] if length < 1e-10 else (
        2 * np.arctan2(length, delta[0]) / length * delta[1:])


class BoundedAllocator:
    """Small active-set bounded least-squares solver, with explicit KKT check.

    Minimize ||W(Bu-w)||^2 with lower <= u <= upper. A feasible unconstrained
    solution uses the minimum-norm pseudoinverse. Under saturation, constrained
    least squares redistributes demand instead of merely clipping a mixer.
    """
    def __init__(self, matrix, lower, upper, length):
        self.weight = np.r_[np.ones(3), np.full(3, 1 / length)]
        self.a = self.weight[:, None] * matrix
        self.pinv = np.linalg.pinv(self.a)
        self.lower, self.upper = lower.copy(), upper.copy()

    def solve(self, wrench):
        y = self.weight * wrench
        raw = self.pinv @ y
        if np.all(raw >= self.lower) and np.all(raw <= self.upper):
            return raw
        u = np.clip(raw, self.lower, self.upper)
        active = np.where(raw < self.lower, -1, np.where(raw > self.upper, 1, 0))
        for _ in range(100):
            free = active == 0
            candidate = u.copy()
            candidate[free] = np.linalg.lstsq(
                self.a[:, free], y - self.a[:, ~free] @ u[~free], rcond=None)[0]
            direction = candidate - u
            alpha, blocker, side = 1.0, None, 0
            for i in np.flatnonzero(free):
                if candidate[i] < self.lower[i] - 1e-10:
                    step = (self.lower[i] - u[i]) / direction[i]
                    if step < alpha:
                        alpha, blocker, side = max(0.0, step), i, -1
                elif candidate[i] > self.upper[i] + 1e-10:
                    step = (self.upper[i] - u[i]) / direction[i]
                    if step < alpha:
                        alpha, blocker, side = max(0.0, step), i, 1
            u = np.clip(u + alpha * direction, self.lower, self.upper)
            if blocker is not None:
                active[blocker] = side
                continue
            gradient = self.a.T @ (self.a @ u - y)
            violation = np.where(active == -1, -gradient,
                                 np.where(active == 1, gradient, 0.0))
            if np.max(violation) <= 1e-8:
                return u
            active[np.argmax(violation)] = 0
        raise RuntimeError("Bounded allocator did not converge")


class HoverController:
    def __init__(self, model, data, height=1.0):
        if (model.nq, model.nv, model.nu, model.nbody) != (7, 6, 8, 2):
            raise ValueError("This controller supports the original single-body, eight-input Omnicopter")
        self.model = model
        self.bid = model.body("drone").id
        self.mass = float(model.body_mass[self.bid])
        self.com = model.body_ipos[self.bid].copy()
        inertial_rotation = rotation(model.body_iquat[self.bid])
        self.inertia = inertial_rotation @ np.diag(model.body_inertia[self.bid]) @ inertial_rotation.T
        self.gravity = model.opt.gravity.copy()
        self.target_q = model.qpos0[3:7].copy()
        self.target_origin = np.array([0.0, 0.0, height])
        self.target_com = self.target_origin + rotation(self.target_q) @ self.com
        self.target_velocity_com = np.zeros(3)
        self.target_acceleration_com = np.zeros(3)
        self.target_omega = np.zeros(3)
        self.target_alpha = np.zeros(3)
        self.kp_position, self.kd_position = 4.0, 3.6
        self.kp_attitude, self.kd_attitude = 16.0, 7.2
        mujoco.mj_forward(model, data)
        body_rotation = data.xmat[self.bid].reshape(3, 3)
        columns = []
        arm_lengths = []
        for aid in range(model.nu):
            if (model.actuator_trntype[aid] != mujoco.mjtTrn.mjTRN_SITE
                    or model.actuator_gaintype[aid] != mujoco.mjtGain.mjGAIN_FIXED
                    or model.actuator_gainprm[aid, 0] != 1
                    or model.actuator_biastype[aid] != mujoco.mjtBias.mjBIAS_NONE
                    or model.actuator_dyntype[aid] != mujoco.mjtDyn.mjDYN_NONE
                    or not model.actuator_ctrllimited[aid]):
                raise ValueError("Expected bounded, unit-gain, memoryless site thrust actuators")
            sid = int(model.actuator_trnid[aid, 0])
            if model.site_bodyid[sid] != self.bid or model.actuator_trnid[aid, 1] != -1:
                raise ValueError("Expected sites on the drone body without refsite")
            site_rotation = data.site_xmat[sid].reshape(3, 3)
            force = site_rotation @ model.actuator_gear[aid, :3]
            arm = data.site_xpos[sid] - data.xipos[self.bid]
            torque = np.cross(arm, force) + site_rotation @ model.actuator_gear[aid, 3:]
            columns.append(np.r_[body_rotation.T @ force, body_rotation.T @ torque])
            arm_lengths.append(np.linalg.norm(arm))
        self.matrix = np.column_stack(columns)
        if np.linalg.matrix_rank(self.matrix) != 6:
            raise ValueError("Hover requires a rank-six wrench matrix")
        self.allocator = BoundedAllocator(self.matrix, model.actuator_ctrlrange[:, 0],
                                          model.actuator_ctrlrange[:, 1], np.mean(arm_lengths))

    def desired_wrench(self, data):
        """Return the unconstrained PD/feedforward body wrench and state metrics.

        Translational reference quantities are expressed in world axes at the
        centre of mass. Angular reference quantities are expressed in body axes.
        Call after ``mj_forward`` so the kinematic arrays match ``qpos``.
        """
        r = data.xmat[self.bid].reshape(3, 3)
        omega = data.qvel[3:6].copy()  # free-joint angular velocity is body-local
        velocity_com = data.qvel[:3] + r @ np.cross(omega, self.com)
        error_p = self.target_com - data.xipos[self.bid]
        error_r = attitude_error(data.qpos[3:7], self.target_q)
        force_world = self.mass * (self.target_acceleration_com
                                   + self.kp_position * error_p
                                   + self.kd_position * (self.target_velocity_com - velocity_com)
                                   - self.gravity)
        torque_body = self.inertia @ (self.target_alpha
                                      + self.kp_attitude * error_r
                                      + self.kd_attitude * (self.target_omega - omega))
        torque_body += np.cross(omega, self.inertia @ omega)
        wrench = np.r_[r.T @ force_world, torque_body]
        return wrench, {
            "position_error_m": float(np.linalg.norm(data.qpos[:3] - self.target_origin)),
            "attitude_error_deg": float(np.rad2deg(np.linalg.norm(error_r))),
            "speed_com_m_s": float(np.linalg.norm(velocity_com)),
            "rate_rad_s": float(np.linalg.norm(omega)),
        }

    def allocate(self, wrench):
        """Map a requested body wrench to the eight verified rotor axes."""
        wrench = np.asarray(wrench, dtype=float)
        controls = self.allocator.solve(wrench)
        residual = self.matrix @ controls - wrench
        return controls, {
            "force_residual_N": float(np.linalg.norm(residual[:3])),
            "torque_residual_Nm": float(np.linalg.norm(residual[3:])),
            "saturated": bool(np.any(np.isclose(controls, self.allocator.lower, atol=1e-7))
                              or np.any(np.isclose(controls, self.allocator.upper, atol=1e-7))),
        }

    def command(self, data):
        """Compute and allocate the classical geometric PD/feedforward command."""
        wrench, metrics = self.desired_wrench(data)
        controls, allocation_metrics = self.allocate(wrench)
        metrics.update(allocation_metrics)
        metrics["baseline_wrench"] = wrench.tolist()
        metrics["commanded_wrench"] = wrench.tolist()
        return controls, metrics


def make_sim(height=1.0):
    model = mujoco.MjModel.from_xml_path(str(XML))
    data = mujoco.MjData(model)
    controller = HoverController(model, data, height)
    return model, data, controller


def reset(model, data, controller, displaced=True):
    mujoco.mj_resetData(model, data)
    data.qpos[:3] = controller.target_origin
    data.qpos[3:7] = controller.target_q
    if displaced:
        data.qpos[:3] += [0.10, -0.08, -0.15]
        mujoco.mju_quatIntegrate(data.qpos[3:7], np.deg2rad([6., -4., 3.]), 1.0)
    mujoco.mj_forward(model, data)


def kick(data):
    """Repeatable simulated velocity impulse; not a controller force bypass."""
    data.qvel[:3] += [0.30, -0.20, 0.15]
    data.qvel[3:6] += [0.35, -0.25, 0.20]


def snapshot(data, controls, metrics):
    return {"time_s": float(data.time), **metrics,
            **dict(zip(["x_m", "y_m", "z_m"], data.qpos[:3].tolist())),
            **{f"thrust_{i+1}_N": float(v) for i, v in enumerate(controls)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--duration", type=float, help="Simulation seconds; default 15 headless, unlimited viewer")
    parser.add_argument("--start-at-target", action="store_true", help="Skip the small initial displacement")
    parser.add_argument("--output", type=Path, help="Run directory (default timestamped control/output folder)")
    args = parser.parse_args()
    duration = args.duration if args.duration is not None else (15.0 if args.headless else float("inf"))
    if duration <= 0 or np.isnan(duration):
        parser.error("duration must be positive")
    output = args.output or HERE / "output" / datetime.now().strftime("hover_%Y%m%d_%H%M%S_%f")
    output.mkdir(parents=True, exist_ok=False)
    model, data, controller = make_sim()
    reset(model, data, controller, not args.start_at_target)
    metadata = {
        "model_xml": str(XML), "xml_sha256": hashlib.sha256(XML.read_bytes()).hexdigest(),
        "mesh_sha256": hashlib.sha256((XML.parent / "assets/Omnidrone.stl").read_bytes()).hexdigest(),
        "mujoco_version": mujoco.__version__, "dt_s": model.opt.timestep,
        "target_origin_m": controller.target_origin.tolist(), "target_q_wxyz": controller.target_q.tolist(),
        "mass_kg": controller.mass, "inertia_body_kg_m2": controller.inertia.tolist(),
        "gains": {k: getattr(controller, k) for k in ("kp_position", "kd_position", "kp_attitude", "kd_attitude")},
        "wrench_matrix": controller.matrix.tolist(), "control_bounds_N": model.actuator_ctrlrange.tolist(),
        "initial_qpos": data.qpos.tolist(), "feedback": "MuJoCo ground truth; simulation only",
    }
    (output / "config.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    events = SimpleQueue()
    viewer = None
    if not args.headless:
        import mujoco.viewer as mjviewer
        viewer = mjviewer.launch_passive(model, data, key_callback=events.put)
        with viewer.lock():
            viewer.cam.lookat[:] = controller.target_origin
            viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = 1.7, 135, -20
            model.vis.scale.framelength = 0.06 / model.stat.meansize
            model.vis.scale.framewidth = 0.002 / model.stat.meansize
        print("HOVER: Space pause/resume | Enter disturbance | Backspace reset | close window to finish", flush=True)
        print("Target: (0, 0, 1) m, original XML attitude. Control sliders are overwritten by feedback.", flush=True)
    print(f"Logs: {output}", flush=True)
    paused, step, next_render, next_status, episode = False, 0, 0.0, 0.0, 0
    last_metrics, max_control, contacts, count = {}, 0.0, 0, 0
    deadline = time.perf_counter()
    try:
        with (output / "trace.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = None
            while data.time < duration and (viewer is None or viewer.is_running()):
                while not events.empty():
                    key = events.get()
                    if key == 32:
                        paused = not paused
                        deadline = time.perf_counter()
                    elif key == 257:
                        kick(data)
                        print("Applied simulated velocity impulse", flush=True)
                    elif key == 259:
                        reset(model, data, controller, not args.start_at_target)
                        episode += 1
                        deadline = time.perf_counter()
                        next_render, next_status = 0.0, 0.0
                if viewer and paused:
                    mujoco.mj_forward(model, data)
                    viewer.sync()
                    time.sleep(0.01)
                    continue
                mujoco.mj_forward(model, data)
                controls, last_metrics = controller.command(data)
                if not np.all(np.isfinite(controls)) or not np.all(np.isfinite(data.qpos)):
                    raise RuntimeError("Non-finite simulation state/control")
                data.ctrl[:] = controls
                max_control = max(max_control, float(np.max(np.abs(controls))))
                contacts += int(data.ncon > 0)
                count += 1
                if step % 5 == 0:  # 100 Hz logs at the model's 500 Hz control rate
                    row = {"episode": episode, **snapshot(data, controls, last_metrics)}
                    if writer is None:
                        writer = csv.DictWriter(stream, fieldnames=row.keys())
                        writer.writeheader()
                    writer.writerow(row)
                mujoco.mj_step(model, data)
                step += 1
                if viewer:
                    if data.time >= next_render:
                        viewer.sync()
                        next_render = data.time + 1 / 60
                    if data.time >= next_status:
                        print(f"t={data.time:6.1f}s | position error={last_metrics['position_error_m']:.4f}m | attitude error={last_metrics['attitude_error_deg']:.3f}deg", flush=True)
                        next_status = data.time + 2.0
                    deadline += model.opt.timestep
                    remaining = deadline - time.perf_counter()
                    if remaining > 0:
                        time.sleep(remaining)
                    elif remaining < -0.1:
                        deadline = time.perf_counter()
    finally:
        if viewer:
            viewer.close()
        summary = {"sim_time_s": data.time, "episodes": episode + 1, "control_steps": count,
                   "peak_abs_control_N": max_control, "steps_with_contacts": contacts,
                   "last_sample": last_metrics}
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
