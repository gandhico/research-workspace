"""Bandwidth-tuned PD+ff on the attitude missions, noise-free and noisy.

PD+ff in the Table V missions used the PD's wn = [4, 4, 3.5] untouched, while
the model-based families get a bandwidth sweep. For a fair comparison PD+ff
gets the same sweep. It is run as backstepping with --no-model-ff, which is
PD+ff algebraically (checked: 1.1e-14 relative on X2 Roll), and accepts
--bw-scale.

Two tunings:
  noise-free  the Table V setting. In a deterministic, noise-free sim more
              gain keeps helping until something saturates, so the optimum
              can sit far above anything a real system would use.
  realistic   the paper's Table VI "realistic" measurement noise (0.020 rad,
              0.050 rad/s, seed 7). Amplified noise gives a genuine interior
              optimum; this is the setting a practitioner would pick.

Sanity: noise-free bw 1 must reproduce the earlier PD+ff numbers to ~1e-12.
Selection: best single bw per platform by mission-mean error.

Run:  python compile_pdff_bw.py
"""
from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
B = HERE / "results" / "baselines_2026-09-10"
TREES = {"noise-free": B / "tune" / "pdff", "realistic": B / "tune" / "pdff_noise"}
FF = HERE / "results" / "pid_baseline_2026-09-10" / "rate_ff_summary.csv"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
GRID = ("0.75", "1", "1.5", "2", "3", "4", "6", "8")


def lab(p, m):
    return f"{p}_{m}_classical".replace("-", "_")


def q(path):
    return json.loads(path.read_text())["qerr_mean_rad"] if path.is_file() else float("nan")


ref = {(r["platform"], r["mission"]): r for r in csv.DictReader(FF.open())}
best = {}
for tag, R in TREES.items():
    for p in ("x2", "cf2-rotor"):
        print(f"\n[{tag}] {p}: PD+ff mean error [rad] by bandwidth scale")
        print(f"{'bw':>6s}" + "".join(f"{m:>10s}" for m in MISSIONS) + f"{'mean':>10s}{'sat max':>9s}")
        scores = {}
        for g in GRID:
            cells = [R / f"bw{g}" / lab(p, m) / "summary.json" for m in MISSIONS]
            if not all(c.is_file() for c in cells):
                continue
            v = [q(c) for c in cells]
            sat = max(json.loads(c.read_text())["saturation_fraction"] for c in cells)
            scores[g] = st.mean(v)
            print(f"{g:>6s}" + "".join(f"{x:10.5f}" for x in v) + f"{scores[g]:10.5f}{sat:9.4f}")
        if tag == "noise-free" and (R / "bw1").is_dir():
            worst = max(abs(q(R / "bw1" / lab(p, m) / "summary.json")
                            / float(ref[(p, m)]["PD_ff"]) - 1.0) for m in MISSIONS)
            print(f"  sanity bw=1 vs earlier PD+ff: max rel diff {worst:.1e}")
        if scores:
            g = min(scores, key=scores.get)
            done = [x for x in GRID if x in scores]
            best[f"{tag}|{p}"] = g
            print(f"  -> tuned bw {g}" + ("   WARNING: grid edge"
                                          if g in (done[0], done[-1]) else "   (interior)"))
(B / "pdff_tuned_bw.json").write_text(json.dumps(best, indent=2))
