"""Extend the verified eprop_anneal reproduction to all 5 standard missions
(roll, full3, hard45, hardstep, yaw360) on both X2 and CF2.

Three combinations have a frozen prior number to verify against (hard45-CF2,
hardstep-CF2, hard45-Skydio, from learned_gate_{results,hardstep,skydio}.json).
The other seven (roll x2, full3 x2, yaw360 x2, hardstep-Skydio) have NO prior
frozen result anywhere on this machine -- they are reported as newly generated,
not verified reproductions. This script prints which is which; do not conflate
the two in any writeup.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(r"C:\Research\papers\P3_Gate_Residual\learned\code")  # fully local, no D: dependency
BENCH = REPO / "experiments" / "controller_benchmarks"
sys.path.insert(0, str(BENCH))

import mujoco  # noqa: E402
from learned_gate_experiment import build_world, reset_world, LearnedGate, W_PAIR  # noqa: E402
from benchmark_metrics import summarize_controller_run  # noqa: E402
import mujoco_classical_vs_neural_stn as B  # noqa: E402

OUT = Path(__file__).resolve().parent / "traces_5missions"
OUT.mkdir(parents=True, exist_ok=True)

QUADS = ["bitcraze_crazyflie_2", "skydio_x2"]
MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
SIM_TIME, DT, Z_REF = 45.0, 0.0005, 1.0
LR, K_ERR, K_RATE, LEAK = 8e-4, 8.0, 0.0, 0.0

# Frozen ground-truth scores (score, qerr_mean) where they exist, for verification.
FROZEN = {
    ("bitcraze_crazyflie_2", "hard45", "classical"): 0.287391,
    ("bitcraze_crazyflie_2", "hard45", "online_pes"): 0.038258,
    ("bitcraze_crazyflie_2", "hard45", "eprop_anneal"): 0.038215,
    ("bitcraze_crazyflie_2", "hardstep", "classical"): 0.690470,
    ("bitcraze_crazyflie_2", "hardstep", "online_pes"): 1.787807,
    ("bitcraze_crazyflie_2", "hardstep", "eprop_anneal"): 2.104360,
    ("skydio_x2", "hard45", "classical"): 0.299286,
    ("skydio_x2", "hard45", "online_pes"): 0.129264,
    ("skydio_x2", "hard45", "eprop_anneal"): 0.134809,
}


def run_traced(w, gate, mission, sim_time, dt, z_ref, classical_only=False):
    reset_world(w, z_ref)
    if gate is not None:
        gate.neuron.reset()
    rows = []
    while w.data.time < sim_time:
        t = float(w.data.time)
        w.data.xfrc_applied[:] = 0.0
        pos = np.array(w.data.qpos[w.qpos_adr:w.qpos_adr + 3], dtype=float)
        vel = np.array(w.data.qvel[w.qvel_adr:w.qvel_adr + 3], dtype=float)
        q_mj = B.q_normalize(np.array(w.data.qpos[w.qpos_adr + 3:w.qpos_adr + 7], dtype=float))
        omega = np.array(w.data.qvel[w.qvel_adr + 3:w.qvel_adr + 6], dtype=float)
        q_meas = B.mujoco_quat_to_paper_quat(q_mj)
        q_ref = B.reference_quat(t, mission, sim_time)
        eul_ref = B.reference_euler(t, mission, sim_time)
        q_err = B.q_mul(q_ref, B.q_conj(q_meas))
        if q_err[0] < 0.0:
            q_err = -q_err
        axis_error = q_err[1:4]

        if classical_only or gate is None:
            tau_body = np.clip(-w.kq * axis_error - w.kw * omega, -w.tau_limit, w.tau_limit)
            neuron_v_mean = neuron_r_mean = activity_mean = 0.0
        else:
            tau_body = gate.step(t, axis_error, omega, dt)
            neuron_v_mean = float(np.mean(gate.neuron.v))
            neuron_r_mean = float(np.mean(gate.neuron.r)) if hasattr(gate.neuron, "r") else 0.0
            activity_mean = float(np.mean(np.clip(getattr(gate.neuron, "r", gate.neuron.v), 0.0, 1.0)))
        tau_body = np.clip(tau_body, -w.tau_limit, w.tau_limit)

        r_wb = w.data.xmat[w.body_id].reshape(3, 3)
        body_z_world = r_wb[:, 2]
        tilt_cos = max(0.35, body_z_world[2])
        collective = w.total_mass * (w.gravity + 6.0 * (z_ref - pos[2]) + 4.0 * (0.0 - vel[2])) / tilt_cos
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
            "event_count_step": 0.0, "activity_mean": activity_mean, "activity_max": 0.0,
            "neuron_v_mean": neuron_v_mean, "neuron_r_mean": neuron_r_mean,
        })
    summ = summarize_controller_run(rows, w.tau_limit)
    if gate is not None and gate.n_steps > 0:
        summ["gate_activity_mean"] = gate.activity_sum / gate.n_steps
        summ["gate_residual_mean"] = gate.residual_sum / gate.n_steps
    return rows, summ


def save_csv(rows, path):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    all_summaries = {}
    for quad in QUADS:
        w = build_world(quad, DT)
        gkw = dict(dt=DT, sim_time=SIM_TIME, neuron_name="hyperlif")
        for mission in MISSIONS:
            print(f"\n=== {quad} / {mission} ===", flush=True)
            qdir = OUT / quad / mission
            qdir.mkdir(parents=True, exist_ok=True)

            rows_c, summ_c = run_traced(w, None, mission, SIM_TIME, DT, Z_REF, classical_only=True)
            save_csv(rows_c, qdir / "classical.csv")

            g_pes = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(), learn=True,
                                 lr=LR, k_err=K_ERR, k_rate=K_RATE, leak=LEAK)
            rows_pes, summ_pes = run_traced(w, g_pes, mission, SIM_TIME, DT, Z_REF)
            save_csv(rows_pes, qdir / "online_pes.csv")

            g_ep = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(), learn=True,
                                lr=LR * 2.0, k_err=K_ERR, k_rate=K_RATE, leak=LEAK,
                                elig=True, anneal=True)
            rows_ep, summ_ep = run_traced(w, g_ep, mission, SIM_TIME, DT, Z_REF)
            save_csv(rows_ep, qdir / "eprop_anneal.csv")

            for name, summ in [("classical", summ_c), ("online_pes", summ_pes), ("eprop_anneal", summ_ep)]:
                frozen = FROZEN.get((quad, mission, name))
                tag = "NEW (no prior frozen result)" if frozen is None else (
                    "VERIFIED match" if abs(summ["score"] - frozen) < 1e-5 else
                    f"MISMATCH vs frozen {frozen:.6f}")
                print(f"  {name:14s} score={summ['score']:.6f}  [{tag}]", flush=True)

            all_summaries[f"{quad}/{mission}"] = {
                "classical": summ_c, "online_pes": summ_pes, "eprop_anneal": summ_ep}

    (OUT / "all_summaries.json").write_text(json.dumps(all_summaries, indent=2))
    print(f"\nwrote {OUT / 'all_summaries.json'}")
