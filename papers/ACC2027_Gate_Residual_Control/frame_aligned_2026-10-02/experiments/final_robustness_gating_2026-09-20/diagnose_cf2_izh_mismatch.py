"""Where do the archived runner and the new runner first differ on CF2 (Izhikevich, beta 0.2, Hard45)?"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
A = pd.read_csv(HERE / "results_validation_izh" / "archived_cf2_hard45_beta0.2" / "trace.csv")
N = pd.read_csv(HERE / "results_validation_izh" / "validation_izh" / "izh_vs_archived" / "cf2-rotor" / "hard45" / "izh_pes_ungated" / "nominal" / "seed_001" / "trace.csv")
print(len(A), len(N), "rows")
pairs = {"qerr": ("qerr", "qerr_true_rad"), "tau0_x": ("tau0_x", "tau0_x"), "tau0_y": ("tau0_y", "tau0_y"), "tau0_z": ("tau0_z", "tau0_z"),
         "residual_x": ("residual_x", "realized_residual_x"), "voltage_0": ("voltage_0", "voltage_0"), "activity_0": ("activity_0", "activity_0"),
         "omega_x": ("omega_x", "omega_true_x"), "z": ("z", "z")}
for name, (a, n) in pairs.items():
    d = np.abs(A[a].to_numpy() - N[n].to_numpy())
    idx = np.flatnonzero(d > 1e-13)
    print(f"{name:11s} max diff {d.max():.3e}   first sample differing: " + (f"row {idx[0]} (t = {A.t[idx[0]]:.3f} s)" if idx.size else "never"))
first = min(np.flatnonzero(np.abs(A[a].to_numpy() - N[n].to_numpy()) > 1e-13)[0] for a, n in pairs.values()
            if (np.abs(A[a].to_numpy() - N[n].to_numpy()) > 1e-13).any())
lo = max(first - 2, 0)
print("\naround the first difference (archived | new):")
for k in range(lo, lo + 6):
    print(f"t={A.t[k]:.3f}  qerr {A.qerr[k]:.12f} | {N.qerr_true_rad[k]:.12f}   tau0_x {A.tau0_x[k]:.12e} | {N.tau0_x[k]:.12e}   "
          f"res_x {A.residual_x[k]:.9f} | {N.realized_residual_x[k]:.9f}   sat {int(A.saturated[k])} | {int(N.rotor_saturated_any[k])}")
print("\nsaturation share  archived:", round(float(A.saturated.mean()), 4), " new:", round(float(N.rotor_saturated_any.mean()), 4))
