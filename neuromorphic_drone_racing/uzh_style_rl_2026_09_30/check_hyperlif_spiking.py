"""Coherence of the RL spiking line with the established Nengo HyperLIF (P2_HyperLIF_Nengo).

1. Step-by-step parity with P2's own HyperLIFNeuron(method="stable") (the update its Nengo neuron uses).
2. Firing-rate curve vs P2's recorded results/csv/03_current_sweep.csv (dt = 1e-4, 0.6 s, J = 0..3).
3. The same curve at the RL neural step dt = 5e-4 (does the coarser step keep P2's behaviour?).
Writes results/hyperlif_coherence.json.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
P2 = Path(r"C:\Research\papers\P2_HyperLIF_Nengo")
sys.path.insert(0, str(P2))
from src.neurons.hyperlif import HyperLIFNeuron, HyperLIFParams  # noqa: E402
from vec_race import HyperLIFBatch  # noqa: E402

torch.set_num_threads(2)
out = {}

# 1. parity with P2's stable update, random currents across all three regimes
rng = np.random.default_rng(5)
cur = rng.uniform(0.0, 3.0, size=(4000, 16))
refs = [HyperLIFNeuron(HyperLIFParams(event_threshold=1.0)) for _ in range(16)]
bat = HyperLIFBatch(1, 16, torch.float64)
worst_v = worst_r = 0.0
ev_ref = np.zeros(16)
for row in cur:
    for k, n in enumerate(refs):
        s = n.step(float(row[k]), 1e-4, method="stable")
        ev_ref[k] += s["events"] > 0
    bat.step(torch.as_tensor(row)[None], 1e-4)
    worst_v = max(worst_v, max(abs(refs[k].voltage - float(bat.v[0, k])) for k in range(16)))
    worst_r = max(worst_r, max(abs(refs[k].reset_gate - float(bat.r[0, k])) for k in range(16)))
out["parity_with_P2_step"] = dict(max_abs_voltage=worst_v, max_abs_gate=worst_r,
                                  spike_counts_equal=bool(np.array_equal(ev_ref, bat.events[0].numpy())))

# 2./3. firing-rate curve
p2 = {round(float(r["input_current"]), 1): float(r["event_rate_hz"])
      for r in csv.DictReader((P2 / "results/csv/03_current_sweep.csv").open()) if r["model"] == "HyperLIF"}
J = torch.as_tensor(np.round(np.arange(0.0, 3.0001, 0.1), 4), dtype=torch.float64)   # P2's exact current grid
for name, dt in (("dt_1e-4", 1e-4), ("dt_5e-4", 5e-4)):
    b = HyperLIFBatch(1, len(J), torch.float64)
    settle = 0.15                                   # P2's experiments/03_current_sweep.py steady-state window
    n_settle = round(settle / dt)
    for k in range(round(0.6 / dt)):
        if k == n_settle:
            ev0 = b.events[0].clone()
        b.step(J[None], dt)
    rate = ((b.events[0] - ev0) / (0.6 - settle)).numpy()
    out[f"rate_curve_{name}"] = {f"{j:.1f}": dict(this=round(float(r), 1), P2=round(p2.get(round(float(j), 1), float("nan")), 1))
                                 for j, r in zip(J.numpy(), rate)}
(HERE / "results" / "hyperlif_coherence.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out["parity_with_P2_step"], indent=1))
for name in ("dt_1e-4", "dt_5e-4"):
    c = out[f"rate_curve_{name}"]
    print(name, " ".join(f"J{j}:{v['this']}/{v['P2']}" for j, v in c.items() if 1.3 <= float(j) <= 2.6))
