"""Where does the gated residual's Hardstep deficit come from?  Error vs time since each step onset.

Steps occur at t = 1, 3, 5, ... (2 s dwell).  For each bin of time-since-onset we average the true
error over all 22 complete steps, for PD+ff and the gated residual, and report the contribution of
each bin to the difference in the 45-s mean.  Also reports how much of the saturated time the gate acts in.
"""
import sys
from pathlib import Path

import numpy as np

import figlib as F

HERE = Path(__file__).resolve().parent
RES = HERE / "results" / "confirmatory" / "nominal"
EDGES = np.array([0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0])


def load(plat, arm):
    tag = "load_1" if arm == "cmg_pes_gated" else "nominal"
    df, _ = F.load(RES / plat / "hardstep" / arm / tag / "seed_001")
    return df


for plat in ("x2", "cf2-rotor"):
    b, g = load(plat, "pdff_rho3"), load(plat, "cmg_pes_gated")
    t = b.t.to_numpy()
    eb, eg = np.degrees(b.qerr_true_rad.to_numpy()), np.degrees(g.qerr_true_rad.to_numpy())
    since = (t - 1.0) % 2.0
    live = t >= 1.0
    total = len(t)
    print(f"\n{plat}: mean error PD+ff {np.degrees(b.qerr_true_rad.mean()):.3f} deg, gated {np.degrees(g.qerr_true_rad.mean()):.3f} deg, "
          f"difference {np.degrees(g.qerr_true_rad.mean() - b.qerr_true_rad.mean()):+.3f} deg")
    print(f"  {'bin [s after step]':20s}{'PD+ff':>9s}{'gated':>9s}{'diff':>9s}{'share of total diff':>22s}")
    diffs = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        m = live & (since >= lo) & (since < hi)
        mb, mg = eb[m].mean(), eg[m].mean()
        contrib = (eg[m].sum() - eb[m].sum()) / total
        diffs.append(contrib)
        print(f"  {lo:4.2f}-{hi:4.2f}{'':11s}{mb:9.3f}{mg:9.3f}{mg - mb:+9.3f}")
    pre = ~live
    diffs.append((eg[pre].sum() - eb[pre].sum()) / total)
    tot = sum(diffs)
    print(f"  contribution to the 45-s mean difference [deg], by bin: " + "  ".join(f"{d:+.3f}" for d in diffs))
    print(f"  sum {tot:+.3f} deg")
    # how much of the time the baseline axis is at its box, and how often the gate acts inside those samples
    loaded = b[[f"baseline_loaded_{a}" for a in "xyz"]].to_numpy().astype(bool)
    blocked = g[[f"output_gate_mask_{a}" for a in "xyz"]].to_numpy() == 0.0
    print("  baseline axis at its torque box, share of time [x y z]:", np.round(loaded.mean(0), 3))
    print("  in the GATED run: blocked share of samples per axis  [x y z]:", np.round(blocked.mean(0), 3))
sys.exit(0)
