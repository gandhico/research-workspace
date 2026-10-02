"""Summary figure for the v0 campaign: error ratio vs PID per mission, both platforms.

Reads results/quat_dual_v0_2026-09-12/summary.csv (written by sweep_v0.py).
One axis (ratio vs PID, log scale), fixed categorical order, Okabe-Ito colours
plus hatching so series identity never relies on colour alone.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "results" / "quat_dual_v0_2026-09-12"
SERIES = (("pid_res", "PID + CMG residual", "#0072B2", ""),
          ("st_pid", "CMG self-tuned PID", "#E69F00", "//"),
          ("dual", "Dual (self-tuning + residual)", "#009E73", ".."))
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
LABEL = {"x2": "Skydio X2", "cf2-rotor": "Crazyflie 2 (1.5x rotors)"}

TOP = 1.6
rows = list(csv.DictReader((OUT / "summary.csv").open(encoding="utf-8")))
fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharey=True, constrained_layout=True)
width = 0.26
for ax, platform in zip(axes, ("x2", "cf2-rotor")):
    pr = {r["mission"]: r for r in rows if r["platform"] == platform}
    x = np.arange(len(MISSIONS))
    for k, (key, name, color, hatch) in enumerate(SERIES):
        vals = [float(pr[m][f"{key}_ratio"]) for m in MISSIONS]
        shown = [min(v, TOP) for v in vals]
        bars = ax.bar(x + (k - 1) * width, shown, width * 0.92, color=color, hatch=hatch,
                      edgecolor="white", linewidth=0.6, label=name)
        for b, v in zip(bars, vals):
            if v <= TOP:
                ax.text(b.get_x() + b.get_width() / 2, v * 1.03, f"{v:.2f}", ha="center",
                        va="bottom", fontsize=6.5, color="#333333")
    for j, m in enumerate(MISSIONS):
        clipped = [(name, float(pr[m][f"{key}_ratio"]), float(pr[m][f"{key}_sat"]))
                   for key, name, _, _ in SERIES if float(pr[m][f"{key}_ratio"]) > TOP]
        if clipped:
            txt = "diverged (bars clipped):\n" + "\n".join(
                f"{n.split(' (')[0]}: x{r:.1f} PID, rotor sat {s:.2f}" for n, r, s in clipped)
            ax.annotate(txt, xy=(j + 0.13, TOP), xytext=(j - 1.55, 1.18), fontsize=7, color="#222222",
                        ha="left", va="center",
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", lw=0.6),
                        arrowprops=dict(arrowstyle="->", color="#555555", lw=0.8))
    ax.axhline(1.0, color="#555555", lw=1.0, ls="--")
    ax.set_yscale("log")
    ax.set_ylim(0.2, TOP)
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks([0.25, 0.5, 0.75, 1.0, 1.5])
    ax.set_yticklabels(["0.25", "0.5", "0.75", "1 (PID)", "1.5"])
    ax.set_xticks(x)
    ax.set_xticklabels(["Roll", "Full3", "Hard45", "Hardstep", "Yaw360"])
    ax.set_title(LABEL[platform], fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_ylabel("mean q-error / PID  (lower is better)")
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=3,
           fontsize=8.5, frameon=False)
fig.suptitle("P5 v0: quaternion tracking, 45 s, PID base k_i = 0.05 k_q (log scale)", fontsize=11)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"v0_ratio_vs_pid.{ext}", dpi=200)
print("wrote", OUT / "v0_ratio_vs_pid.png")
