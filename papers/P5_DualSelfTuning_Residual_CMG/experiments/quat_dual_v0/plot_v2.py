"""v2 heatmap: selected controllers x 7 missions, both platforms, crashes marked.

Same diverging log2 scale as v1 (blue better than PID, red worse); CRASH = ground contact.
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
OUT = HERE.parents[1] / "results" / "quat_v2_2026-09-12"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360", "hard45b", "hardstep_b")
MLABEL = ("Roll", "Full3", "Hard45", "Hardstep", "Yaw360", "Hard45b\n(held-out)", "Hardstep_b\n(held-out)")
CONTROLLERS = ("pid_res", "st_pid", "dual", "stn_b_ks", "dual_stn_b_ks", "st_pid_v2", "dual_v2", "stn_ks_v2",
               "dual_stn_ks_v2")
CLABEL = {"pid_res": "PID + residual (ACC 2027)", "st_pid": "target tuner v0", "dual": "dual v0",
          "stn_b_ks": "STN bounded, known sign (v1)", "dual_stn_b_ks": "dual STN known sign (v1)",
          "st_pid_v2": "target tuner v2 (gated)", "dual_v2": "dual v2 (gated)", "stn_ks_v2": "STN known sign v2 (gated)",
          "dual_stn_ks_v2": "dual STN known sign v2 (gated)"}
CMAP = LinearSegmentedColormap.from_list("div", ["#2166ac", "#92c5de", "#eeeeee", "#f4a582", "#b2182b"])

rows = list(csv.DictReader((OUT / "summary_v2.csv").open(encoding="utf-8")))
idx = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
fig, axes = plt.subplots(1, 2, figsize=(14, 5.0), constrained_layout=True)
for ax, platform, title in zip(axes, ("x2", "cf2-rotor"), ("Skydio X2", "Crazyflie 2 (1.5x rotors, T/W 1.98)")):
    M = np.zeros((len(CONTROLLERS), len(MISSIONS)))
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            M[i, j] = math.log2(float(idx[(platform, m, c)]["ratio_vs_pid"]))
    im = ax.imshow(np.clip(M, -2, 2), cmap=CMAP, vmin=-2, vmax=2, aspect="auto")
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            r = idx[(platform, m, c)]
            zmin = float(r["z_min_m"])
            crash = zmin < 0.05                                    # post hoc: sustained ground contact
            low = 0.05 <= zmin <= 0.2                              # pre-declared flag; X2 PID itself is here
            txt = f"{float(r['ratio_vs_pid']):.2f}" + ("\nCRASH" if crash else ("\nlow z" if low else ""))
            ax.text(j, i, txt, ha="center", va="center", fontsize=7.5,
                    color="white" if abs(M[i, j]) > 1.2 else "#222222", fontweight="bold" if crash else "normal")
    ax.axvline(4.5, color="#333333", lw=1.2)
    ax.axhline(4.5, color="#333333", lw=1.2, ls="--")
    ax.set_xticks(range(len(MISSIONS)))
    ax.set_xticklabels(MLABEL, fontsize=8)
    ax.set_yticks(range(len(CONTROLLERS)))
    ax.set_yticklabels([CLABEL[c] for c in CONTROLLERS], fontsize=8)
    ax.set_title(title, fontsize=10)
cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.01)
cb.set_ticks([-2, -1, 0, 1, 2])
cb.set_ticklabels(["0.25x", "0.5x", "1x PID", "2x", ">=4x"])
cb.set_label("mean q-error relative to PID")
fig.suptitle("P5 v2: authority- and validity-gated self-tuning (below dashed line) vs v0/v1 (45 s)\n"
             "CRASH = sustained ground contact (z_min < 0.05 m, post hoc); low z = 0.05-0.2 m, same band as X2 PID "
             "(0.08-0.12 m, 1 ms rotor graze)", fontsize=10)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"v2_heatmap.{ext}", dpi=180)
print("wrote", OUT / "v2_heatmap.png")
