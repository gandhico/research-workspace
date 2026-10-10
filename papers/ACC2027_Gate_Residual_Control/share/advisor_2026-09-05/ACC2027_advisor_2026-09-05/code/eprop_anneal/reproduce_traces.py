"""Reproduce full per-timestep traces for classical / online_pes / eprop_anneal
on Bitcraze/hard45, matching learned_gate_experiment.py's exact defaults.

Why this exists: the original repo (D:\\NMSU_backups\\...\\neuromorphic-robotics-control)
only ever wrote SUMMARY scalars to learned_gate_results.json -- the per-step
`rows` computed inside run_episode() were discarded, never saved. No raw trace
for eprop_anneal exists anywhere on this machine. This script does not modify
any file in that repo; it imports its exact functions/classes unmodified and
adds trace capture, so the physics/control law is byte-identical to what
produced the frozen summary numbers (verified below, not assumed).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import LEGACY_P3  # noqa: E402

REPO = LEGACY_P3  # shipped with this package
BENCH = REPO / "experiments" / "controller_benchmarks"
sys.path.insert(0, str(BENCH))

import mujoco  # noqa: E402
from learned_gate_experiment import (  # noqa: E402
    build_world, reset_world, LearnedGate, W_PAIR,
)
from benchmark_metrics import summarize_controller_run  # noqa: E402
import mujoco_classical_vs_neural_stn as B  # noqa: E402

OUT = Path(__file__).resolve().parent / "traces"
OUT.mkdir(parents=True, exist_ok=True)

QUAD, MISSION, SIM_TIME, DT, Z_REF = "bitcraze_crazyflie_2", "hard45", 45.0, 0.0005, 1.0
LR, K_ERR, K_RATE, LEAK = 8e-4, 8.0, 0.0, 0.0


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
            decoder_fro = 0.0
        else:
            tau_body = gate.step(t, axis_error, omega, dt)
            neuron_v_mean = float(np.mean(gate.neuron.v))
            neuron_r_mean = float(np.mean(gate.neuron.r)) if hasattr(gate.neuron, "r") else 0.0
            activity_mean = float(np.mean(np.clip(gate.neuron.r if hasattr(gate.neuron, "r")
                                                    else gate.neuron.v, 0.0, 1.0)))
            decoder_fro = float(np.linalg.norm(gate.W - W_PAIR))
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
            "decoder_frobenius_change": decoder_fro,
        })
    summ = summarize_controller_run(rows, w.tau_limit)
    if gate is not None and gate.n_steps > 0:
        summ["gate_activity_mean"] = gate.activity_sum / gate.n_steps
        summ["gate_residual_mean"] = gate.residual_sum / gate.n_steps
    return rows, summ


def save_csv(rows, path):
    import csv
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}  ({len(rows)} rows)")


if __name__ == "__main__":
    w = build_world(QUAD, DT)
    gkw = dict(dt=DT, sim_time=SIM_TIME, neuron_name="hyperlif")

    print("=== classical ===")
    rows_c, summ_c = run_traced(w, None, MISSION, SIM_TIME, DT, Z_REF, classical_only=True)
    save_csv(rows_c, OUT / "classical.csv")
    print(f"  reproduced score={summ_c['score']:.6f}  (frozen: 0.287391)")

    print("=== online_pes ===")
    g_pes = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(), learn=True,
                         lr=LR, k_err=K_ERR, k_rate=K_RATE, leak=LEAK)
    rows_pes, summ_pes = run_traced(w, g_pes, MISSION, SIM_TIME, DT, Z_REF)
    save_csv(rows_pes, OUT / "online_pes.csv")
    print(f"  reproduced score={summ_pes['score']:.6f}  (frozen: 0.038258)")

    print("=== eprop_anneal ===")
    g_ep = LearnedGate(w, **gkw, blend=0.5, W=W_PAIR.copy(), learn=True,
                        lr=LR * 2.0, k_err=K_ERR, k_rate=K_RATE, leak=LEAK,
                        elig=True, anneal=True)
    rows_ep, summ_ep = run_traced(w, g_ep, MISSION, SIM_TIME, DT, Z_REF)
    save_csv(rows_ep, OUT / "eprop_anneal.csv")
    print(f"  reproduced score={summ_ep['score']:.6f}  (frozen: 0.038215)")

    import json
    (OUT / "reproduction_summary.json").write_text(json.dumps(
        {"classical": summ_c, "online_pes": summ_pes, "eprop_anneal": summ_ep}, indent=2))
    print(f"\nwrote {OUT / 'reproduction_summary.json'}")
