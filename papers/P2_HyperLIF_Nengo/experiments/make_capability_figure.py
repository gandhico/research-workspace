"""Paper 3 capability figure: (A) task error per Nengo app, LIF vs calibrated HyperLIF vs Adaptive;
(B) the PES rate-matched curve (error vs firing rate, with the honest ceiling vs LIF). Reads exp 13/15
CSVs, writes paper/figures/fig_nengo_capability.{png,pdf}."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def load(name):
    with open(ROOT / "results" / "csv" / name) as f:
        return list(csv.DictReader(f))


# ---- panel A: capability matrix (exp 13) ----
rows = load("13_hyperlif_nengo_capability_matrix.csv")
apps = ["comm_channel", "function_square", "transform_2d", "integrator", "oscillator",
        "working_memory", "pes_learning"]
labels = ["comm", "function", "transform", "integrator", "oscillator", "memory", "PES"]
neurons = ["LIF", "HyperLIF_T023", "Adaptive_T033"]
colors = {"LIF": "#888780", "HyperLIF_T023": "#185FA5", "Adaptive_T033": "#1baf7a"}
err = {n: [] for n in neurons}
for app in apps:
    for n in neurons:
        v = next(r for r in rows if r["app"] == app and r["neuron"] == n)
        err[n].append(float(v["error"]))

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11, 4.2))
x = range(len(apps)); w = 0.27
for i, n in enumerate(neurons):
    axA.bar([xi + (i - 1) * w for xi in x], err[n], width=w,
            color=colors[n], label=n.replace("_T023", " (calib.)").replace("_T033", " (calib.)"))
axA.set_xticks(list(x)); axA.set_xticklabels(labels, rotation=25, ha="right")
axA.set_ylabel("task error (lower is better)")
axA.set_title("(a) capability coverage — every app runs; HyperLIF weak only on PES")
axA.legend(frameon=False, fontsize=9)
axA.spines[["top", "right"]].set_visible(False)

# ---- panel B: PES rate-matched curve (exp 15) ----
pes = load("15_pes_rate_matched.csv")
lif = next(r for r in pes if r["neuron"] == "LIF")
hl = [r for r in pes if r["neuron"] != "LIF"]
pts = sorted((float(r["firing_hz"]), float(r["pes_late_rmse"])) for r in hl)
rates = [p[0] for p in pts]; late = [p[1] for p in pts]
axB.plot(rates, late, "o-", color="#185FA5", label="HyperLIF (rate swept)")
axB.axhline(float(lif["pes_late_rmse"]), ls="--", color="#888780",
            label=f"LIF ({float(lif['firing_hz']):.0f} Hz)")
best = min(range(len(late)), key=lambda i: late[i])
axB.annotate("sweet spot\n~40 Hz", (rates[best], late[best]),
             textcoords="offset points", xytext=(8, 14), fontsize=9,
             arrowprops=dict(arrowstyle="->", color="#185FA5"))
axB.set_xlabel("HyperLIF firing rate (Hz)"); axB.set_ylabel("PES late error (RMSE)")
axB.set_title("(b) the efficiency ↔ learning-speed trade")
axB.legend(frameon=False, fontsize=9)
axB.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
for ext in ("png", "pdf"):
    fig.savefig(FIG / f"fig_nengo_capability.{ext}", dpi=150, bbox_inches="tight")
print(f"wrote {FIG / 'fig_nengo_capability.png'} (+ pdf)")
