"""Verify the implemented gate against the manuscript's equation (gate), from logged traces.

  (a) mask_i = 0   <=>   |u0_i| >= l_i  and  s_i * u0_i < 0        (equivalence, both directions)
  (b) |u - u0|_i <= beta * l_i                                      (Proposition 1 (iii) survives the gate)
  (c) command == clip(u0 + gated residual, -l, l)                   (the gate acts before the outer clip)
  (d) the ungated arm never blocks (mask == 1)
Uses the decimated trace.csv (every 10th step, 5 ms).  The runner also records, for every step of every run,
max |native augmentor command - reconstructed command| in summary.json (expected exactly 0).
"""
import json
import sys
from pathlib import Path

import numpy as np

import figlib as F

HERE = Path(__file__).resolve().parent
RES = HERE / "results" / "confirmatory" / "nominal"
ok = True
for plat, beta in (("x2", 0.5), ("cf2-rotor", 0.5)):
    for mission in ("hardstep", "full3"):
        df, summ = F.load(RES / plat / mission / "cmg_pes_gated" / "load_1" / "seed_001")
        lim = np.array(summ["actuation"]["torque_limits_Nm"])
        u0 = df[[f"tau0_{a}" for a in "xyz"]].to_numpy()
        raw = df[[f"raw_residual_{a}" for a in "xyz"]].to_numpy()
        mask = df[[f"output_gate_mask_{a}" for a in "xyz"]].to_numpy()
        gated = df[[f"gated_residual_{a}" for a in "xyz"]].to_numpy()
        cmd = df[[f"tau_command_{a}" for a in "xyz"]].to_numpy()
        blocked = mask == 0.0
        predicted = (np.abs(u0) >= lim - 1e-12) & (raw * u0 < 0.0)
        a_ok = np.array_equal(blocked, predicted)
        b = np.max(np.abs(cmd - u0) / lim)
        c = np.max(np.abs(cmd - np.clip(u0 + gated, -lim, lim)))
        native = summ["cmg_pes"]["max_native_vs_reconstructed_command_error_Nm"]
        ok &= a_ok and b <= beta + 1e-9 and c < 1e-12 and native == 0.0
        print(f"{plat:9s}{mission:9s} (a) equivalence {a_ok}  (b) max|u-u0|/l = {b:.4f} <= {beta}  "
              f"(c) clip residual {c:.1e}  native-vs-reconstructed {native}  blocked samples {int(blocked.sum())}")
for plat in ("x2", "cf2-rotor"):
    df, _ = F.load(RES / plat / "hardstep" / "cmg_pes_table" / "nominal" / "seed_001")
    d_ok = bool(np.all(df[[f"output_gate_mask_{a}" for a in "xyz"]].to_numpy() == 1.0))
    ok &= d_ok
    print(f"{plat:9s}ungated arm never blocks: {d_ok}")
print("\nGATE VERIFIED" if ok else "\nGATE CHECK FAILED")
sys.exit(0 if ok else 1)
