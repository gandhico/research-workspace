"""Nengo-native version of run_6dof_cascade.py's Option-A realistic cascade.

Identical plant, mixer, position PD, thrust_vector_to_attitude decomposition,
quaternion-PD inner loop, and the q_des-convention fix -- all imported, not
reimplemented -- with only the CMG-PES augmentor itself swapped for its
Nengo-native equivalent (nengo_cmg.NengoCMGPESAugmentor, verified to match
the frozen NumPy CMGResidualAugmentor to ~1e-7 relative error, see
verify_6dof_nengo_equivalence.py) or a Nengo neuron-family augmentor
(nengo_neuron_family_6dof.NengoNeuronFamilyAugmentorND) for LIF/ALIF/
Izhikevich/LIFRate validation against the same 6-channel cascade.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"nengo_nef_replication_2026-08-29"))
from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402
from nengo_neuron_family_6dof import NengoNeuronFamilyAugmentorND  # noqa: E402

from gra_control.math3d import quat_angle, quat_conj, quat_error  # noqa: E402
from gra_control.platforms.drone import SPECS, _free_joint, _mixer, torque_limits  # noqa: E402

from run_6dof_wrench import position_reference, MASS_FORCE_LIMIT_SCALE  # noqa: E402
from run_6dof_cascade import rotmat_to_quat, thrust_vector_to_attitude  # noqa: E402

MIN_THRUST_FRACTION = 0.05


def build_augmentor(engine: str, limits6: np.ndarray, dt: float, beta: float, learning_rate: float,
                     feature_scale: float = 1.0, native_current_scale: float = 1.0):
    if engine == "cmg":
        return NengoCMGPESAugmentor(6, limits6, dt, beta=beta, learning_rate=learning_rate)
    return NengoNeuronFamilyAugmentorND(engine, 6, limits6, dt, beta=beta, mode="pes", learning_rate=learning_rate,
                                         feature_scale=feature_scale, native_current_scale=native_current_scale)


def run(mission: str, duration: float, dt: float, engine: str, beta: float,
        learning_rate: float, k_error_pos: float, k_error_att: float,
        output: Path, platform: str = "x2",
        wn_att: np.ndarray | None = None, wn_pos: np.ndarray | None = None,
        feature_scale: float = 1.0, native_current_scale: float = 1.0) -> dict:
    spec = SPECS[platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    act_ids, _, B_inv, ctrl_range = _mixer(model)

    wn = np.array([4.0, 4.0, 3.5]) if wn_att is None else np.asarray(wn_att, dtype=float)
    kq = 2.0*inertia*wn*wn
    kw = 2.0*0.95*wn*inertia
    tau_limits = torque_limits(platform, inertia, model, "model")
    force_limits = np.array([MASS_FORCE_LIMIT_SCALE*mass*gravity]*2+[1.8*mass*gravity])
    limits6 = np.concatenate([force_limits, tau_limits])
    wn_pos = np.array([1.0, 1.0, 1.2]) if wn_pos is None else np.asarray(wn_pos, dtype=float)
    kp_pos = mass*wn_pos*wn_pos
    kd_pos = mass*2.0*0.75*wn_pos
    min_thrust = MIN_THRUST_FRACTION*mass*gravity

    augmentor = build_augmentor(engine, limits6, dt, beta, learning_rate, feature_scale, native_current_scale)

    data.qpos[qa:qa+3] = position_reference(0.0, mission, duration)
    data.qpos[qa+3:qa+7] = quat_conj(np.array([1.0, 0.0, 0.0, 0.0]))
    data.qvel[:] = 0.0
    mujoco.mj_forward(model, data)

    rows: list[dict] = []
    q_des_prev = np.array([1.0, 0.0, 0.0, 0.0])
    tau0_prev = np.zeros(3)
    eq_prev = np.zeros(3)
    while data.time < duration:
        t = float(data.time)
        p = np.asarray(data.qpos[qa:qa+3], dtype=float)
        v = np.asarray(data.qvel[va:va+3], dtype=float)
        q_meas = quat_conj(np.asarray(data.qpos[qa+3:qa+7], dtype=float))
        omega = np.asarray(data.qvel[va+3:va+6], dtype=float)

        p_ref = position_reference(t, mission, duration)
        F0 = np.clip(mass*gravity*np.array([0, 0, 1])-kp_pos*(p-p_ref)-kd_pos*v, -force_limits, force_limits)

        pos_target = np.clip(-k_error_pos*(p-p_ref)/max(1e-9, np.linalg.norm(force_limits))-0.0*v, -1.0, 1.0)
        att_target = np.clip(-k_error_att*eq_prev-0.0*omega, -1.0, 1.0)
        target6 = np.concatenate([pos_target, att_target])
        wrench0_for_gate = np.concatenate([F0, tau0_prev])
        out = augmentor.step(wrench0_for_gate, target6)
        F_cmd = out.command[0:3]
        tau_att_residual = out.residual[3:6]
        residual_norm = float(np.linalg.norm(out.residual))
        activity_mean = float(np.mean(out.activity))

        yaw_des = 0.0
        q_des, thrust_mag = thrust_vector_to_attitude(F_cmd, yaw_des, min_thrust)
        q_des = quat_conj(q_des)  # same convention fix as run_6dof_cascade.py
        _, dq_vec = quat_error(q_des, q_des_prev)
        omega_des = 2.0*dq_vec/dt
        q_des_prev = q_des
        qe, eq = quat_error(q_des, q_meas)
        tau0 = np.clip(-kq*eq-kw*(omega-omega_des), -tau_limits, tau_limits)
        tau = np.clip(tau0+tau_att_residual, -tau_limits, tau_limits)
        tau0_prev = tau0
        eq_prev = eq

        motors = B_inv@np.r_[thrust_mag, tau]
        motors = np.clip(motors, ctrl_range[:, 0], ctrl_range[:, 1])
        data.ctrl[:] = 0.0
        data.ctrl[act_ids] = motors
        data.xfrc_applied[:] = 0.0
        mujoco.mj_step(model, data)

        rows.append({
            "t": t, "pos_err": float(np.linalg.norm(p-p_ref)), "qerr": quat_angle(qe),
            "x": p[0], "y": p[1], "z": p[2], "x_ref": p_ref[0], "y_ref": p_ref[1], "z_ref": p_ref[2],
            "thrust": thrust_mag, "tau_x": tau[0], "tau_y": tau[1], "tau_z": tau[2],
            "residual_norm": residual_norm, "activity_mean": activity_mean,
        })

    augmentor.close()
    output.mkdir(parents=True, exist_ok=True)
    with (output/"trace.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    pos_err = np.array([r["pos_err"] for r in rows])
    qerr = np.array([r["qerr"] for r in rows])
    summary = {
        "platform": f"{platform}-6dof-cascade-nengo", "engine": engine, "mission": mission,
        "duration": duration, "dt": dt, "pos_err_mean_m": float(pos_err.mean()),
        "pos_err_max_m": float(pos_err.max()), "qerr_mean_rad": float(qerr.mean()),
        "qerr_max_rad": float(qerr.max()),
    }
    (output/"summary.json").write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mission", required=True, choices=["hover3d", "waypoint_step", "circle_xy", "full6_stress"])
    p.add_argument("--duration", type=float, default=15.0)
    p.add_argument("--dt", type=float, default=0.0005)
    p.add_argument("--engine", required=True, choices=["cmg", "lif", "alif", "izhikevich", "lifrate"])
    p.add_argument("--beta", type=float, default=0.5)
    p.add_argument("--learning-rate", type=float, default=0.0008)
    p.add_argument("--k-error-pos", type=float, default=8.0)
    p.add_argument("--k-error-att", type=float, default=8.0)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--platform", default="x2", choices=["x2", "cf2-rotor"])
    p.add_argument("--wn-att", type=float, nargs=3, default=None)
    p.add_argument("--wn-pos", type=float, nargs=3, default=None)
    p.add_argument("--feature-scale", type=float, default=1.0)
    p.add_argument("--native-current-scale", type=float, default=1.0)
    a = p.parse_args()
    s = run(a.mission, a.duration, a.dt, a.engine, a.beta, a.learning_rate,
            a.k_error_pos, a.k_error_att, a.output, a.platform, a.wn_att, a.wn_pos,
            a.feature_scale, a.native_current_scale)
    print(f"pos_err_mean={s['pos_err_mean_m']:.4f}m  qerr_mean={np.rad2deg(s['qerr_mean_rad']):.3f}deg")
