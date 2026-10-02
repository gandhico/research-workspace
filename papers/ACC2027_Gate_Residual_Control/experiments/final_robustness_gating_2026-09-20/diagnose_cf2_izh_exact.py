"""Bit-level comparison of the two CF2 Izhikevich traces: which quantity first differs, and when?"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
A = pd.read_csv(HERE / "results_validation_izh" / "archived_cf2_hard45_beta0.2" / "trace.csv")
N = pd.read_csv(HERE / "results_validation_izh" / "validation_izh" / "izh_vs_archived" / "cf2-rotor" / "hard45" / "izh_pes_ungated" / "nominal" / "seed_001" / "trace.csv")
common = {"qerr": "qerr_true_rad", "tau0_x": "tau0_x", "tau0_y": "tau0_y", "tau0_z": "tau0_z", "omega_x": "omega_true_x",
          "omega_y": "omega_true_y", "omega_z": "omega_true_z", "z": "z", "residual_x": "realized_residual_x",
          "residual_y": "realized_residual_y", "residual_z": "realized_residual_z", "target_x": "target_x", "pes_error_x": "pes_error_x",
          "current_0": "current_0", "activity_0": "activity_0", "activity_3": "activity_3", "gate_0": "gate_0", "decoder_w_0": "decoder_w_0",
          "decoder_w_7": "decoder_w_7"}
rows = []
for a, n in common.items():
    x, y = A[a].to_numpy(), N[n].to_numpy()
    idx = np.flatnonzero(x != y)
    rows.append((a, int(idx[0]) if idx.size else -1, float(A.t[idx[0]]) if idx.size else float("nan"), int(idx.size)))
print(f"{'column':14s}{'first exact diff (row)':>24s}{'t [s]':>10s}{'# rows differing':>20s}")
for r in sorted(rows, key=lambda r: (r[1] < 0, r[1])):
    print(f"{r[0]:14s}{r[1]:24d}{r[2]:10.3f}{r[3]:20d}")
print("\nactivity spikes near the first divergence: archived vs new, units 0-5 at rows 8735..8742 (t step 5 ms):")
for k in range(8736, 8743):
    print(k, f"{A.t[k]:.3f}", [round(float(A[f'activity_{u}'][k]), 6) for u in range(6)], "|", [round(float(N[f'activity_{u}'][k]), 6) for u in range(6)])
