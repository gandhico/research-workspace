"""v4 figure: (a,b) error ratio to pid heatmaps, both platforms; (c) idgc_v4 gain multipliers vs model targets on X2."""
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
OUT = HERE.parents[1] / "results" / "quat_v4_2026-09-12"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360", "hard45b", "hardstep_b", "hard45c", "hardstep_c")
MLABEL = ("Roll", "Full3", "Hard45", "Hardstep", "Yaw360", "Hard45b", "Hardstep_b", "Hard45c", "Hardstep_c")
CONTROLLERS = ("pid_res", "dual_v2", "pid_body", "pid_res_body", "idgc_v4", "dual_idgc_v4")
CLABEL = {"pid_res": "PID + residual (ACC)", "dual_v2": "dual v2 (gated)", "pid_body": "body-axis PID",
          "pid_res_body": "body-axis PID + residual", "idgc_v4": "ID gain-corrected PID", "dual_idgc_v4": "ID gain-corrected + residual"}
CMAP = LinearSegmentedColormap.from_list("div", ["#2166ac", "#92c5de", "#eeeeee", "#f4a582", "#b2182b"])
AXIS_COLORS = ("#1b6ca8", "#d1495b", "#3c8d2f")

rows = list(csv.DictReader((OUT / "summary_v4.csv").open(encoding="utf-8")))
idx = {(r["platform"], r["mission"], r["controller"]): r for r in rows}
fig = plt.figure(figsize=(15, 8.6), constrained_layout=True)
gs = fig.add_gridspec(2, 2, height_ratios=(1.0, 0.8))
for k, (platform, title) in enumerate((("x2", "(a) Skydio X2"), ("cf2-rotor", "(b) Crazyflie 2 (1.5x rotors)"))):
    ax = fig.add_subplot(gs[0, k])
    M = np.array([[math.log2(float(idx[(platform, m, c)]["ratio_vs_pid"])) for m in MISSIONS] for c in CONTROLLERS])
    im = ax.imshow(np.clip(M, -2, 2), cmap=CMAP, vmin=-2, vmax=2, aspect="auto")
    for i, c in enumerate(CONTROLLERS):
        for j, m in enumerate(MISSIONS):
            r = idx[(platform, m, c)]
            crash = float(r["z_min_m"]) < 0.05
            ax.text(j, i, f"{float(r['ratio_vs_pid']):.2f}" + ("\nCRASH" if crash else ""), ha="center", va="center",
                    fontsize=7.2, color="white" if abs(M[i, j]) > 1.2 else "#222222")
    ax.axhline(1.5, color="#333333", lw=1.2)
    ax.set_xticks(range(len(MISSIONS)))
    ax.set_xticklabels(MLABEL, fontsize=7.5, rotation=30)
    ax.set_yticks(range(len(CONTROLLERS)))
    ax.set_yticklabels([CLABEL[c] for c in CONTROLLERS], fontsize=8)
    ax.set_title(title + ": mean q-error / PID (apa)", fontsize=10)
cb = fig.colorbar(im, ax=fig.axes[:2], shrink=0.85, pad=0.01)
cb.set_ticks([-2, -1, 0, 1, 2])
cb.set_ticklabels(["0.25x", "0.5x", "1x", "2x", ">=4x"])

targets = (1 / 1.6564388, 1 / 1.43510296, 1 / 0.41983376)
for k, mission in enumerate(("hard45", "hardstep")):
    ax = fig.add_subplot(gs[1, k])
    with (OUT / "x2" / mission / "idgc_v4" / "trace.csv").open(encoding="utf-8") as f:
        tr = list(csv.DictReader(f))
    t = np.array([float(r["t"]) for r in tr])
    for a, name, col, tg in zip("xyz", ("roll", "pitch", "yaw"), AXIS_COLORS, targets):
        ax.plot(t, [float(r[f"mp_{a}"]) for r in tr], color=col, lw=2, label=f"m {name}")
        ax.axhline(tg, color=col, lw=1, ls="--")
    ax.axvline(3.0, color="#888888", lw=1, ls=":")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("gain multiplier m")
    ax.set_title(f"(c{k + 1}) X2 {mission}: identified gain correction (dashed = model J/j_tune)", fontsize=10)
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="center right")
fig.suptitle("P5 v4: body-axis PID and identification-based gain correction (45 s, attitude-priority allocation)",
             fontsize=11)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"v4_figure.{ext}", dpi=170)
print("wrote", OUT / "v4_figure.png")
