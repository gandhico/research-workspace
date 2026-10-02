"""Stage S0 acceptance tests for vec_race.py (PyTorch process; no MuJoCo import).

1. One-decision prediction: from each recorded MuJoCo state, apply the recorded action for one 20-ms decision and
   compare with MuJoCo's next state (the sim-to-sim model error that matters for learning).
2. Open-loop replay of the whole 12-s action sequence from the recorded start (expected to drift: unstable plant).
3. Gate passes along the recorded trajectory under teacher forcing.
4. CMG batch parity against rl_cmg_2026_09_30/cmg_cells.py.
5. Throughput with 1,024 drones and 32 CMG cells each.
Writes results/s0_validation.json.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rl_cmg_2026_09_30"))
from vec_race import OBS_DIM, CMGBatch, VecRace, quat_to_R  # noqa: E402
from cmg_cells import CMGPopulation, policy_preset  # noqa: E402

torch.set_num_threads(8)
F64 = torch.float64


def rot_err_deg(Ra, Rb):
    c = ((Ra.transpose(-1, -2) @ Rb).diagonal(dim1=-2, dim2=-1).sum(-1) - 1) / 2
    return torch.rad2deg(torch.arccos(c.clamp(-1, 1)))


def main():
    rec = dict(np.load(HERE / "results" / "x2_reference_flight.npz"))
    K = len(rec["action"])
    T = lambda x: torch.as_tensor(x, dtype=F64)
    p, v, R, w, a = T(rec["p"]), T(rec["v"]), T(rec["R"]), T(rec["w"]), T(rec["action"])
    gates = torch.as_tensor(rec["gates"])
    next_gate = torch.cat([torch.zeros(1, dtype=torch.long), gates[:-1]]) % 7
    out = {}

    # 1. one-decision prediction, all decisions in one batch
    sim = VecRace(K, dtype=F64)
    sim.set_state(p[:K], v[:K], R[:K], w[:K], next_gate)
    sim.steps.zero_()
    sim.step(a)
    ep = (sim.p - p[1:]).norm(dim=1)
    ev = (sim.v - v[1:]).norm(dim=1)
    eR = rot_err_deg(quat_to_R(sim.q), R[1:])
    ew = (sim.w - w[1:]).norm(dim=1)
    out["one_decision"] = dict(pos_mm_mean=float(1e3 * ep.mean()), pos_mm_max=float(1e3 * ep.max()),
                               vel_mm_s_mean=float(1e3 * ev.mean()), vel_mm_s_max=float(1e3 * ev.max()),
                               att_deg_mean=float(eR.mean()), att_deg_max=float(eR.max()),
                               rate_rad_s_mean=float(ew.mean()), rate_rad_s_max=float(ew.max()))

    # 2. open-loop replay
    sim = VecRace(1, dtype=F64, episode_s=1e9)
    sim.set_state(p[:1], v[:1], R[:1], w[:1], next_gate[:1])
    drift = []
    for k in range(K):
        sim.step(a[k:k + 1])
        drift.append(float((sim.p[0] - p[k + 1]).norm()))
    drift = np.asarray(drift)
    out["open_loop_position_drift_m"] = {f"{s:.0f}s": float(drift[min(int(s / 0.02), K) - 1]) for s in (0.5, 1, 2, 4, 8, 12)}

    # 3. gate passes, teacher-forced (state reset to MuJoCo at every decision)
    sim = VecRace(1, dtype=F64, episode_s=1e9)
    passes = 0
    for k in range(K):
        sim.set_state(p[k:k + 1], v[k:k + 1], R[k:k + 1], w[k:k + 1], next_gate[k:k + 1])
        _, _, info = sim.step(a[k:k + 1])
        passes += int(info["passed"][0])
    out["gate_passes_teacher_forced"] = dict(vec_sim=passes, mujoco=int(gates[-1]))

    # 4. CMG parity (graded and reset_spike), 1,200 substeps of random currents
    rng = np.random.default_rng(3)
    cur = rng.uniform(0.05, 2.2, size=(1200, 32))
    par = {}
    for mode in CMGBatch.MODES:
        ref = CMGPopulation(32, mode, policy_preset(mode))
        bat = CMGBatch(1, 32, mode, F64)
        worst = 0.0
        for jj in cur:
            f_ref = ref.step(jj, 0.0005)
            bat.step(T(jj)[None], 0.0005)
            worst = max(worst, float(np.max(np.abs(f_ref - bat.features()[0].numpy()))),
                        float(np.max(np.abs(ref.v - bat.v[0].numpy()))))
        par[mode] = worst
    out["cmg_parity_max_abs_diff"] = par

    # 5. throughput: 1,024 drones, 32 graded CMG cells each, policy-sized MLP forward
    n = 1024
    sim = VecRace(n)
    cmg = CMGBatch(n, 32, "graded", torch.float32)
    enc = torch.randn(32, OBS_DIM) / math.sqrt(OBS_DIM)
    net = torch.nn.Sequential(torch.nn.Linear(OBS_DIM + 32, 128), torch.nn.Tanh(), torch.nn.Linear(128, 128), torch.nn.Tanh(),
                              torch.nn.Linear(128, 4))
    t0 = time.perf_counter()
    for _ in range(20):
        obs = sim.observe()
        j = (0.85 + 0.95 * torch.tanh(obs @ enc.T)).clamp(0.05, 2.2)
        for _ in range(40):
            cmg.step(j, 0.0005)
        with torch.no_grad():
            act = torch.tanh(net(torch.cat([obs, cmg.features()], 1)))
        _, done, _ = sim.step(act)
        sim.reset(done); cmg.reset(done)
    out["throughput_decisions_per_s_1024_drones_with_cmg"] = round(n * 20 / (time.perf_counter() - t0))
    (HERE / "results" / "s0_validation.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
