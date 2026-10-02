"""v3 heatmap: 9 controllers x 9 missions, both platforms, attitude-priority allocation, crashes marked.

Diverging log2 scale (blue better than PID under the same allocation, red worse).
Vertical lines separate original | v1 held-out | v3 new held-out missions.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "results" / "quat_v3_2026-09-12"
ALLOC = json.loads((OUT / "alloc_screen" / "selected.json").read_text(encoding="utf-8"))["allocation"]
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360", "hard45b", "hardstep_b", "hard45c", "hardstep_c")
MLABEL = ("Roll", "Full3", "Hard45", "Hardstep", "Yaw360", "Hard45b", "Hardstep_b", "Hard45c\n(new)", "Hardstep_c\n(new)")
CONTROLLERS = ("pid_res", "st_pid", "dual", "st_pid_v2", "dual_v2", "stn_ks_v2", "stn_dx_v3", "dual_stn_dx_v3")
CLABEL = {"pid_res": "PID + residual", "st_pid": "target tuner (ungated)", "dual": "dual (ungated)",
          "st_pid_v2": "target tuner v2 (gated)", "dual_v2": "dual v2 (gated)", "stn_ks_v2": "STN known sign (gated)",
          "stn_dx_v3": "STN dither-identified", "dual_stn_dx_v3": "dual STN dither-identified"}
CMAP = LinearSegmentedColormap.from_list("div", ["#2166ac", "#92c5de", "#eeeeee", "#f4a582", "#b2182b"])

rows = list(csv.DictReader((OUT / "summary_v3.csv").open(encoding="utf-8")))
idx = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
fig, axes = plt.subplots(1, 2, figsize=(15, 4.9), constrained_layout=True)
for ax, platform, title in zip(axes, ("x2", "cf2-rotor"), ("Skydio X2", "Crazyflie 2 (1.5x rotors, T/W 1.98)")):
    M = np.zeros((len(CONTROLLERS), len(MISSIONS)))
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            M[i, j] = math.log2(float(idx[(platform, m, c)]["ratio_vs_pid"]))
    im = ax.imshow(np.clip(M, -2, 2), cmap=CMAP, vmin=-2, vmax=2, aspect="auto")
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            r = idx[(platform, m, c)]
            crash = float(r["z_min_m"]) < 0.05
            txt = f"{float(r['ratio_vs_pid']):.2f}" + ("\nCRASH" if crash else "")
            ax.text(j, i, txt, ha="center", va="center", fontsize=7.2,
                    color="white" if abs(M[i, j]) > 1.2 else "#222222", fontweight="bold" if crash else "normal")
    for x in (4.5, 6.5):
        ax.axvline(x, color="#333333", lw=1.2)
    ax.set_xticks(range(len(MISSIONS)))
    ax.set_xticklabels(MLABEL, fontsize=7.5)
    ax.set_yticks(range(len(CONTROLLERS)))
    ax.set_yticklabels([CLABEL[c] for c in CONTROLLERS], fontsize=8)
    ax.set_title(title, fontsize=10)
cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.01)
cb.set_ticks([-2, -1, 0, 1, 2])
cb.set_ticklabels(["0.25x", "0.5x", "1x PID", "2x", ">=4x"])
cb.set_label(f"mean q-error relative to PID ({ALLOC} allocation)")
fig.suptitle(f"P5 v3: attitude-priority allocation ({ALLOC}) and dither-identified self-tuning (45 s); "
             "CRASH = z_min < 0.05 m", fontsize=11)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"v3_heatmap.{ext}", dpi=180)
print("wrote", OUT / "v3_heatmap.png")
