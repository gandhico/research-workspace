"""Closed-loop MuJoCo hard45/CF2 run using the Nengo-native eprop_anneal
augmentor, to check whether the brief transient numerical discrepancy found
in isolated testing (verify_nengo_eprop_equivalence.py) has any practical
effect on the aggregate score once embedded in a real 45s mission -- the
real test of whether it's usable, not just the isolated worst-case number.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(r"C:\Research\papers\P3_Gate_Residual\learned\code")
BENCH = REPO / "experiments" / "controller_benchmarks"
sys.path.insert(0, str(BENCH))

import mujoco  # noqa: E402
from learned_gate_experiment import build_world, reset_world  # noqa: E402
from benchmark_metrics import summarize_controller_run  # noqa: E402
import mujoco_classical_vs_neural_stn as B  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nengo_eprop_anneal import NengoEpropAnnealAugmentor  # noqa: E402

QUAD, MISSION, SIM_TIME, DT, Z_REF = "bitcraze_crazyflie_2", "hard45", 45.0, 0.0005, 1.0
LR, K_ERR, K_RATE = 8e-4 * 2.0, 8.0, 0.0

if __name__ == "__main__":
    w = build_world(QUAD, DT)
    reset_world(w, Z_REF)
    aug = NengoEpropAnnealAugmentor(3, w.tau_limit, DT, SIM_TIME, LR, K_ERR, K_RATE, blend=0.5)

    rows = []
    while w.data.time < SIM_TIME:
        t = float(w.data.time)
        w.data.xfrc_applied[:] = 0.0
        pos = np.array(w.data.qpos[w.qpos_adr:w.qpos_adr + 3], dtype=float)
        vel = np.array(w.data.qvel[w.qvel_adr:w.qvel_adr + 3], dtype=float)
        q_mj = B.q_normalize(np.array(w.data.qpos[w.qpos_adr + 3:w.qpos_adr + 7], dtype=float))
        omega = np.array(w.data.qvel[w.qvel_adr + 3:w.qvel_adr + 6], dtype=float)
        q_meas = B.mujoco_quat_to_paper_quat(q_mj)
        q_ref = B.reference_quat(t, MISSION, SIM_TIME)
        eul_ref = B.reference_euler(t, MISSION, SIM_TIME)
        q_err = B.q_mul(q_ref, B.q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err
        axis_error = q_err[1:4]

        tau_pd = np.clip(-w.kq * axis_error - w.kw * omega, -w.tau_limit, w.tau_limit)
        out = aug.step(t, axis_error, tau_pd, omega)
        tau_body = np.clip(out.command, -w.tau_limit, w.tau_limit)

        r_wb = w.data.xmat[w.body_id].reshape(3, 3)
        body_z_world = r_wb[:, 2]
        tilt_cos = max(0.35, body_z_world[2])
        collective = w.total_mass * (w.gravity + 6.0 * (Z_REF - pos[2]) + 4.0 * (0.0 - vel[2])) / tilt_cos
        collective = np.clip(collective, 0.0, 2.5 * w.total_mass * max(w.gravity, 1.0))
        force_world = collective * body_z_world
        a_xy = -1.5 * pos[:2] - 2.2 * vel[:2]
        force_world[:2] += w.total_mass * B.clip_norm(a_xy, 3.0)
        w.data.xfrc_applied[w.body_id, 0:3] = force_world
        w.data.xfrc_applied[w.body_id, 3:6] = r_wb @ tau_body
        mujoco.mj_step(w.model, w.data)

        eul_meas = B.quat_to_euler(q_meas)
        eul_err = B.wrap_to_pi(eul_meas - eul_ref)
        rows.append({
            "t": t, "phi_err": eul_err[0], "theta_err": eul_err[1], "psi_err": eul_err[2],
            "qerr_angle": B.quat_angle_error(q_err), "z": pos[2],
            "tau_x": tau_body[0], "tau_y": tau_body[1], "tau_z": tau_body[2],
            "event_count_step": 0.0, "activity_mean": float(np.mean(out.activity)), "activity_max": 0.0,
        })

    summ = summarize_controller_run(rows, w.tau_limit)
    aug.close()
    print(f"Nengo eprop_anneal, hard45/CF2: score={summ['score']:.6f}  qerr_mean={summ['qerr_mean']:.6f}")
    print(f"NumPy  eprop_anneal (frozen):   score=0.038215  qerr_mean=0.035445")
    print(f"difference: {abs(summ['score']-0.038215):.6e}")
