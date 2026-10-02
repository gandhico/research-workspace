"""Parity of the batched exact-ACC CMG cells (CMGBatch mode 'acc') with the ACC controller's own bank
(ACC2027_Gate_Residual_Control/src/gra_control/gate.py, CoupledMembraneGateBank, adaptive conductance), driven by
ACC-style paired currents I = 0.75 + 1.25 max(+/-u, 0). Writes results/cmg_acc_parity.json."""
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r"C:\Research\papers\ACC2027_Gate_Residual_Control\src")
from gra_control.gate import CMGConfig, CoupledMembraneGateBank  # noqa: E402
from vec_race import CMGBatch  # noqa: E402

rng = np.random.default_rng(7)
u = np.clip(np.cumsum(rng.normal(0, 0.05, size=(4000, 16)), 0), -1, 1)      # slowly varying normalized requests
cur = np.concatenate([0.75 + 1.25 * np.maximum(u, 0), 0.75 + 1.25 * np.maximum(-u, 0)], 1)
ref = CoupledMembraneGateBank(32, True, CMGConfig())
bat = CMGBatch(1, 32, "acc", torch.float64)
wv = wr = wa = 0.0
for j in cur:
    r = ref.step(j, 0.0005)
    bat.step(torch.as_tensor(j)[None], 0.0005)
    wv = max(wv, float(np.abs(ref.v - bat.v[0].numpy()).max()))
    wr = max(wr, float(np.abs(r - bat.r[0].numpy()).max()))
    wa = max(wa, float(np.abs(np.clip(1e5 * r, 0, 1) - bat.features()[0].numpy()).max()))
a = bat.features()[0].numpy()
out = dict(max_abs_voltage=wv, max_abs_gate=wr, max_abs_activity=wa,
           final_activity_saturated_fraction=float((a > 0.99).mean()), final_activity_mean=float(a.mean()))
(HERE / "results" / "cmg_acc_parity.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
