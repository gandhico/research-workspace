"""v1 heatmap: error ratio vs PID for every controller x mission (original + held-out), both platforms.

Diverging colour scale on log2(ratio): blue = better than PID, grey = equal, red = worse.
Cells carry their numeric ratio so identity never relies on colour; diverged cells read DIV.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "results" / "quat_v1_2026-09-12"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360", "hard45b", "hardstep_b")
MLABEL = ("Roll", "Full3", "Hard45", "Hardstep", "Yaw360", "Hard45b\n(held-out)", "Hardstep_b\n(held-out)")
CONTROLLERS = ("pid_res", "st_pid", "st_pid_f", "stn", "stn_b", "stn_b_ks", "dual", "dual_f", "dual_stn_b",
               "dual_stn_b_ks")
CLABEL = {"pid_res": "PID + residual (ACC 2027)", "st_pid": "target tuner v0", "st_pid_f": "target tuner + sat. freeze",
          "stn": "STN-PID-PES (faithful, CMG)", "stn_b": "STN bounded", "stn_b_ks": "STN bounded, known sign*",
          "dual": "dual v0", "dual_f": "dual + sat. freeze", "dual_stn_b": "dual STN bounded",
          "dual_stn_b_ks": "dual STN bounded, known sign*"}
CMAP = LinearSegmentedColormap.from_list("div", ["#2166ac", "#92c5de", "#eeeeee", "#f4a582", "#b2182b"])

rows = list(csv.DictReader((OUT / "summary_v1.csv").open(encoding="utf-8")))
idx = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), constrained_layout=True)
for ax, platform, title in zip(axes, ("x2", "cf2-rotor"), ("Skydio X2", "Crazyflie 2 (1.5x rotors)")):
    M = np.zeros((len(CONTROLLERS), len(MISSIONS)))
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            M[i, j] = math.log2(float(idx[(platform, m, c)]["ratio_vs_pid"]))
    im = ax.imshow(np.clip(M, -2, 2), cmap=CMAP, vmin=-2, vmax=2, aspect="auto")
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            r = idx[(platform, m, c)]
            txt = "DIV" if r["diverged"] == "True" else f"{float(r['ratio_vs_pid']):.2f}"
            if r["diverged"] != "True" and float(r["saturation_fraction"]) > 0.5:
                txt += "\nsat"
            ax.text(j, i, txt, ha="center", va="center", fontsize=7.5,
                    color="white" if abs(M[i, j]) > 1.2 else "#222222")
    ax.axvline(4.5, color="#333333", lw=1.2)
    ax.set_xticks(range(len(MISSIONS)))
    ax.set_xticklabels(MLABEL, fontsize=8)
    ax.set_yticks(range(len(CONTROLLERS)))
    ax.set_yticklabels([CLABEL[c] for c in CONTROLLERS], fontsize=8)
    ax.set_title(title, fontsize=10)
cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.01)
cb.set_ticks([-2, -1, 0, 1, 2])
cb.set_ticklabels(["0.25x", "0.5x", "1x PID", "2x", ">=4x"])
cb.set_label("mean q-error relative to PID")
fig.suptitle("P5 v1: self-tuning, residual and dual CMG controllers (45 s; * = post-smoke ablation)", fontsize=11)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"v1_heatmap.{ext}", dpi=180)
print("wrote", OUT / "v1_heatmap.png")
