"""Is thrust starvation (requested collective > realized) the common mechanism of the CF2 noisy-Hardstep divergence?"""
import sys
from pathlib import Path

import numpy as np

import figlib as F

R = Path(__file__).resolve().parent / "results" / "confirmatory" / "noise" / "cf2-rotor" / "hardstep"
print(f"{'level':10s}{'seed':>5s} | {'arm':14s}{'mean err [deg]':>15s}{'starved share':>15s}{'rotor-sat share':>17s}{'first starvation [s]':>22s}")
for lvl in ("noise_moderate", "noise_realistic"):
    for seed in range(1, 11):
        for arm, tag in (("pdff_rho3", lvl), ("cmg_pes_gated", lvl + "__load_1")):
            d = R / arm / tag / f"seed_{seed:03d}"
            if not (d / "trace.csv").exists():
                continue
            df, s = F.load(d)
            starved = (df.collective_requested_N - df.collective_realized_N).to_numpy() > 1e-3
            first = df.t.to_numpy()[np.argmax(starved)] if starved.any() else float("nan")
            print(f"{lvl[6:]:10s}{seed:5d} | {arm:14s}{np.degrees(s['metrics']['qerr_true_mean_rad']):15.2f}"
                  f"{starved.mean():15.3f}{df.rotor_saturated_any.mean():17.3f}{first:22.2f}")
sys.exit(0)
