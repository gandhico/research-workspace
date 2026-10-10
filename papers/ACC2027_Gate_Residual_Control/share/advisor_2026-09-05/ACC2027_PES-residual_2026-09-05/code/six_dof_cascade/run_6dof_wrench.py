"""Option B: fully-actuated 6-DOF CMG-PES on X2 -- direct (Fx,Fy,Fz,tau_x,tau_y,tau_z)
wrench via MuJoCo xfrc_applied, bypassing the rotor mixer entirely.

Idealized rigid-body testbed (X2 mass/inertia), NOT a real-quadrotor claim --
built to cleanly observe the CMG-PES architecture's own behavior across all
6 channels before Option A (realistic underactuated position->attitude
cascade). Reuses canonical CMGResidualAugmentor(channels=6) and quat_error,
euler_to_quat -- not reimplemented.

Torque channels are handled in BODY frame throughout (matching the existing
quaternion-PD/omega convention) and rotated to world frame only at the final
xfrc_applied write, using the same R@vector pattern drone.py already uses
for disturbance injection. Force channels are world-frame throughout,
since position/velocity error are naturally world-frame for a free body.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np

from gra_control.gate import CMGResidualAugmentor
from gra_control.math3d import euler_to_quat, quat_angle, quat_conj, quat_error, quat_mul
from gra_control.platforms.drone import SPECS, _free_joint, torque_limits

MASS_FORCE_LIMIT_SCALE = 0.6  # additional-force bound, as a fraction of hover thrust (mass*g)


def position_reference(t: float, mission: str, duration: float) -> np.ndarray:
    """[x, y, z] reference, meters."""
    if mission == "hover3d":
        return np.array([0.0, 0.0, 1.0])
    if mission == "waypoint_step":
        wps = [[0.0, 0.0, 1.0], [0.6, 0.0, 1.0], [0.6, 0.6, 1.3], [0.0, 0.6, 0.7], [0.0, 0.0, 1.0]]
        phase = int(t//9.0) % len(wps)
        return np.array(wps[phase])
    if mission == "circle_xy":
        w = 2*np.pi*0.1
        return np.array([0.5*np.cos(w*t), 0.5*np.sin(w*t), 1.0])
    if mission == "full6_stress":
        return np.array([
            0.45*np.sin(0.6*t)*np.cos(0.35*t),
            0.45*np.sin(0.6*t)*np.sin(0.35*t),
            1.0+0.25*np.sin(0.5*t),
        ])
    raise ValueError(f"unknown mission {mission}")


def attitude_reference(t: float, mission: str, duration: float) -> np.ndarray:
    """Reference quaternion. hover3d/waypoint_step/circle_xy hold level;
    full6_stress reuses the hard45 Euler profile (aggressive, matching the
    existing attitude benchmark) so translation AND attitude are both hard
    at once."""
    if mission == "full6_stress":
        phi = 0.55*np.sin(0.75*t)+0.20*np.sin(2.10*t+0.40)
        theta = 0.45*np.sin(0.95*t+np.pi/3)+0.18*np.sin(1.75*t)
        psi = 0.0
        return euler_to_quat(phi, theta, psi)
    return np.array([1.0, 0.0, 0.0, 0.0])


def run(mission: str, duration: float, dt: float, controller: str, beta: float,
        learning_rate: float, k_error_pos: float, k_rate_pos: float,
        k_error_att: float, k_rate_att: float, seed: int, output: Path) -> dict:
    spec = SPECS["x2"]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))

    wn = np.array([4.0, 4.0, 3.5])
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    tau_limits = torque_limits("x2", inertia, model, "model")
    # z needs headroom ABOVE mass*gravity (the feedforward alone needs 100% of
    # that just to hover); x/y have no such floor since there's no gravity to
    # counteract laterally. Clipping z below mass*gravity (an earlier bug here)
    # meant the feedforward term itself got clipped and the drone just fell.
    force_limits = np.array([
        MASS_FORCE_LIMIT_SCALE*mass*gravity,
        MASS_FORCE_LIMIT_SCALE*mass*gravity,
        1.8*mass*gravity,
    ])
    limits6 = np.concatenate([force_limits, tau_limits])

    kp_pos = mass*np.array([9.0, 9.0, 12.0])
    kd_pos = mass*np.array([4.5, 4.5, 6.0])

    augmentor = None
    if controller != "classical":
        adaptive = controller in {"adaptive-residual", "online-pes-adaptive"}
        mode = "online_pes" if "online-pes" in controller else "residual"
        augmentor = CMGResidualAugmentor(6, limits6, mode, adaptive, beta, learning_rate=learning_rate)

    data.qpos[qa:qa+3] = position_reference(0.0, mission, duration)
    data.qpos[qa+3:qa+7] = quat_conj(attitude_reference(0.0, mission, duration))
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)

    rows: list[dict] = []
    while data.time < duration:
        t = float(data.time)
        p = np.asarray(data.qpos[qa:qa+3], dtype=float)
        v = np.asarray(data.qvel[va:va+3], dtype=float)
        q_meas = quat_conj(np.asarray(data.qpos[qa+3:qa+7], dtype=float))
        omega = np.asarray(data.qvel[va+3:va+6], dtype=float)
        R = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)

        p_ref = position_reference(t, mission, duration)
        qref = attitude_reference(t, mission, duration)
        qe, eq = quat_error(qref, q_meas)

        F0 = np.clip(mass*gravity*np.array([0, 0, 1])-kp_pos*(p-p_ref)-kd_pos*v, -force_limits, force_limits)
        tau0 = np.clip(-kq*eq-kw*omega, -tau_limits, tau_limits)
        wrench0 = np.concatenate([F0, tau0])

        if augmentor is None:
            wrench, residual_norm, gate_mean = wrench0, 0.0, 0.0
        else:
            target = np.clip(np.concatenate([
                -k_error_pos*(p-p_ref)/max(1e-9, np.linalg.norm(force_limits))-k_rate_pos*v,
                -k_error_att*eq-k_rate_att*omega,
            ]), -1.0, 1.0)
            is_online = "online-pes" in controller
            out = augmentor.step(wrench0, dt, target if is_online else None)
            wrench = out.command
            residual_norm = float(np.linalg.norm(out.residual))
            gate_mean = float(np.mean(out.gate))

        data.xfrc_applied[:] = 0.0
        data.xfrc_applied[body_id, 0:3] = wrench[0:3]
        data.xfrc_applied[body_id, 3:6] = R@wrench[3:6]
        data.ctrl[:] = 0.0
        mujoco.mj_step(model, data)

        rows.append({
            "t": t, "pos_err": float(np.linalg.norm(p-p_ref)), "qerr": quat_angle(qe),
            "x": p[0], "y": p[1], "z": p[2], "x_ref": p_ref[0], "y_ref": p_ref[1], "z_ref": p_ref[2],
            "Fx": wrench[0], "Fy": wrench[1], "Fz": wrench[2],
            "tau_x": wrench[3], "tau_y": wrench[4], "tau_z": wrench[5],
            "residual_norm": residual_norm, "gate_mean": gate_mean,
        })

    output.mkdir(parents=True, exist_ok=True)
    with (output/"trace.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    pos_err = np.array([r["pos_err"] for r in rows])
    qerr = np.array([r["qerr"] for r in rows])
    summary = {
        "platform": "x2-6dof-wrench", "controller": controller, "mission": mission,
        "duration": duration, "dt": dt, "pos_err_mean_m": float(pos_err.mean()),
        "pos_err_max_m": float(pos_err.max()), "qerr_mean_rad": float(qerr.mean()),
        "qerr_max_rad": float(qerr.max()),
    }
    import json
    (output/"summary.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mission", required=True, choices=["hover3d", "waypoint_step", "circle_xy", "full6_stress"])
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--controller", default="classical",
                    choices=["classical", "fixed-residual", "adaptive-residual", "online-pes-adaptive"])
    p.add_argument("--beta", type=float, default=0.5)
    p.add_argument("--learning-rate", type=float, default=0.0008)
    p.add_argument("--k-error-pos", type=float, default=8.0)
    p.add_argument("--k-rate-pos", type=float, default=0.0)
    p.add_argument("--k-error-att", type=float, default=8.0)
    p.add_argument("--k-rate-att", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    s = run(a.mission, a.duration, a.dt, a.controller, a.beta, a.learning_rate,
            a.k_error_pos, a.k_rate_pos, a.k_error_att, a.k_rate_att, a.seed, a.output)
    print(f"pos_err_mean={s['pos_err_mean_m']:.4f}m  qerr_mean={np.rad2deg(s['qerr_mean_rad']):.3f}deg")
