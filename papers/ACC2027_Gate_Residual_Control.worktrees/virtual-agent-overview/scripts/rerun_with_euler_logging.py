"""Reproduce a gra_control.platforms.drone.run_drone simulation with extra
per-axis Euler (roll/pitch/yaw) logging of the actual attitude AND the
reference attitude, for true output-vs-reference plotting.

This does NOT reimplement any control logic -- it imports and calls the
exact same canonical pieces run_drone itself uses (CMGResidualAugmentor,
quat_error, reference_quat, the same MuJoCo model/physics step, the same
kq/kw/limits/mixer setup). The only difference from run_drone is that this
script also converts q_meas and qref to Euler degrees each step and writes
them as extra trace.csv columns. Physics, control decisions, and RNG seed
are identical to run_drone for the same arguments -- this is a logging
wrapper, not an independent reimplementation.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import mujoco
import numpy as np

from gra_control.gate import CMGResidualAugmentor
from gra_control.math3d import euler_to_quat, quat_angle, quat_conj, quat_error, quat_mul, reference_quat
from gra_control.platforms.drone import SPECS, _controller, _free_joint, _mixer, _name_id, torque_limits


def quat_to_euler_zyx(q: np.ndarray) -> tuple[float, float, float]:
    """Inverse of gra_control.math3d.euler_to_quat(phi, theta, psi) -- standard
    321 (roll-pitch-yaw) extraction, for logging/plotting only."""
    w, x, y, z = q
    roll = np.arctan2(2*(w*x+y*z), 1-2*(x*x+y*y))
    pitch = np.arcsin(np.clip(2*(w*y-z*x), -1.0, 1.0))
    yaw = np.arctan2(2*(w*z+x*y), 1-2*(y*y+z*z))
    return float(roll), float(pitch), float(yaw)


def run(
    platform_name: str, controller_name: str, mission: str, duration: float, dt: float,
    beta: float, torque_policy: str, learning_rate: float, k_error: float, k_rate: float,
    actuator_scale: float, seed: int, output: Path,
) -> None:
    spec = SPECS[platform_name]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    limits = torque_limits(platform_name, inertia, model, torque_policy)
    wn = np.array([4.0, 4.0, 3.5])
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    augmentor = _controller(controller_name, limits, beta, learning_rate)

    data.qpos[qa:qa+3] = [0.0, 0.0, 1.0]
    data.qpos[qa+3:qa+7] = quat_conj(euler_to_quat(0.0, 0.0, 0.0))
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)

    if spec.interface == "rotor4":
        act_ids, _, B_inv, ctrl_range = _mixer(model)
        ctrl_range[:, 1] *= actuator_scale
        model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]
    else:
        names = ["body_thrust", "x_moment", "y_moment", "z_moment"]
        act_ids = np.array([_name_id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, n) for n in names])
        ctrl_range = model.actuator_ctrlrange[act_ids].copy()
        gears = np.abs(np.array([
            model.actuator_gear[act_ids[1], 3], model.actuator_gear[act_ids[2], 4],
            model.actuator_gear[act_ids[3], 5],
        ]))

    rows: list[dict] = []
    while data.time < duration:
        t = float(data.time)
        q_meas = quat_conj(np.asarray(data.qpos[qa+3:qa+7], dtype=float))
        omega = np.asarray(data.qvel[va+3:va+6], dtype=float).copy()
        qref = reference_quat(t, mission, duration)
        qe, eq = quat_error(qref, q_meas)
        tau0 = np.clip(-kq*eq-kw*omega, -limits, limits)
        if augmentor is None:
            tau, residual, gate_mean = tau0, np.zeros(3), 0.0
            neuron_v = neuron_r = None
        else:
            target = np.clip(-k_error*eq-k_rate*omega, -1.0, 1.0)
            is_online = controller_name in {"online-pes", "online-pes-fixed", "online-pes-adaptive"}
            out = augmentor.step(tau0, dt, target if is_online else None)
            tau, residual, gate_mean = out.command, out.residual, float(np.mean(out.gate))
            # CoupledMembraneGateBank internal state, post-step: v = membrane
            # potential, r = gate state (0-1). Size 2*channels -- first half is
            # the positive-current branch per axis, second half the negative
            # branch (gate.py CMGResidualAugmentor.step: current = concat[bias+
            # gain*max(normalized,0), bias+gain*max(-normalized,0)]).
            neuron_v = augmentor.units.v.copy()
            neuron_r = augmentor.units.r.copy()

        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
        z, vz = float(data.qpos[qa+2]), float(data.qvel[va+2])
        tilt = max(float(R[2, 2]), 0.35)
        collective = mass*(gravity+6.0*(1.0-z)-4.0*vz)/tilt
        collective = float(np.clip(collective, 0.0, 2.5*mass*max(gravity, 1.0)))

        data.ctrl[:] = 0.0
        data.xfrc_applied[:] = 0.0
        if spec.interface == "rotor4":
            motors = B_inv@np.r_[collective, tau]
            motors = np.clip(motors, ctrl_range[:, 0], ctrl_range[:, 1])
            data.ctrl[act_ids] = motors
        else:
            cmd = np.r_[collective, -tau/np.maximum(gears, 1e-15)]
            cmd = np.clip(cmd, ctrl_range[:, 0], ctrl_range[:, 1])
            data.ctrl[act_ids] = cmd

        mujoco.mj_step(model, data)

        roll, pitch, yaw = quat_to_euler_zyx(q_meas)
        roll_r, pitch_r, yaw_r = quat_to_euler_zyx(qref)
        row = {
            "t": t, "qerr": quat_angle(qe),
            "roll_deg": np.rad2deg(roll), "pitch_deg": np.rad2deg(pitch), "yaw_deg": np.rad2deg(yaw),
            "roll_ref_deg": np.rad2deg(roll_r), "pitch_ref_deg": np.rad2deg(pitch_r), "yaw_ref_deg": np.rad2deg(yaw_r),
            "tau_x": tau[0], "tau_y": tau[1], "tau_z": tau[2],
            "residual_norm": float(np.linalg.norm(residual)), "gate_mean": gate_mean,
            "z": z, "z_ref": 1.0,
        }
        if neuron_v is not None:
            for i, (vv, rr) in enumerate(zip(neuron_v, neuron_r)):
                row[f"neuron_v_{i}"] = vv
                row[f"neuron_r_{i}"] = rr
        rows.append(row)

    output.mkdir(parents=True, exist_ok=True)
    csv_path = output/"trace.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    qerr = np.array([r["qerr"] for r in rows])
    summary = {
        "platform": platform_name, "controller": controller_name, "mission": mission,
        "duration": duration, "dt": dt, "beta": beta, "learning_rate": learning_rate,
        "k_error": k_error, "k_rate": k_rate, "actuator_scale": actuator_scale,
        "qerr_mean_rad": float(qerr.mean()), "qerr_max_rad": float(qerr.max()),
        "trace": str(csv_path),
    }
    (output/"summary.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {csv_path}  qerr_mean_deg={np.rad2deg(qerr.mean()):.3f}  "
          f"qerr_max_deg={np.rad2deg(qerr.max()):.3f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", required=True, choices=list(SPECS.keys()))
    p.add_argument("--controller", required=True)
    p.add_argument("--mission", default="hard45")
    p.add_argument("--duration", type=float, default=45.0)
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--beta", type=float, default=0.5)
    p.add_argument("--torque-policy", default="model")
    p.add_argument("--learning-rate", type=float, default=0.0008)
    p.add_argument("--k-error", type=float, default=8.0)
    p.add_argument("--k-rate", type=float, default=0.0)
    p.add_argument("--actuator-scale", type=float, default=1.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    run(a.platform, a.controller, a.mission, a.duration, a.dt, a.beta, a.torque_policy,
        a.learning_rate, a.k_error, a.k_rate, a.actuator_scale, a.seed, a.out)
