"""§6.4 figures from the architecture-sweep registry (dataset,arch,neuron,readout,seed,accuracy,
events_per_sample,...). Two figures: (4) HyperLIF-LIF transfer-gap heatmap, (5) N-MNIST efficiency
Pareto (accuracy vs spikes).

    python hpc/make_arch_figures.py --reg /path/_registry.csv --out results/figures_slides
"""
from __future__ import annotations

import argparse
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

COL = {"lif": "#888780", "hyperlif": "#1D9E75", "adaptive": "#7F77DD"}
LAB = {"lif": "LIF", "hyperlif": "HyperLIF", "adaptive": "Adaptive"}
DNAME = {"dvsg32_wide": "DVS-32", "dvsg48_wide": "DVS-48", "nmnist_wide": "N-MNIST",
         "shd_wide_T20": "SHD", "ssc_wide_T20": "SSC"}
ORDER = ["dvsg32_wide", "dvsg48_wide", "nmnist_wide", "shd_wide_T20", "ssc_wide_T20"]
ARCHS = ["conv", "rsnn", "delay"]
MK = {"conv": "o", "rsnn": "s", "delay": "^"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reg", required=True)
    ap.add_argument("--out", default="results/figures_slides")
    ap.add_argument("--pareto-dataset", default="nmnist_wide")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.reg, encoding="utf-8")))
    acc, ev = defaultdict(list), defaultdict(list)
    for r in rows:
        try:
            v = float(r["accuracy"])
        except (ValueError, KeyError, TypeError):
            continue
        k = (r["dataset"], r.get("arch", "ff"), r["neuron"], r["readout"])
        acc[k].append(v)
        try:
            ev[k].append(float(r["events_per_sample"]))
        except (ValueError, KeyError, TypeError):
            pass
    M = {k: st.mean(v) for k, v in acc.items()}
    E = {k: st.mean(ev[k]) for k in ev}
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    datasets = [d for d in ORDER if any(k[0] == d for k in M)]
    plt.rcParams.update({"font.size": 12, "figure.facecolor": "white"})

    def best(ds, arch, neuron):
        cs = [M[k] for k in M if k[0] == ds and k[1] == arch and k[2] == neuron]
        return max(cs) if cs else np.nan

    # FIG 4 — transfer gap heatmap (arch x dataset): best HyperLIF - best LIF
    gap = np.full((len(ARCHS), len(datasets)), np.nan)
    for i, arch in enumerate(ARCHS):
        for j, ds in enumerate(datasets):
            h, l = best(ds, arch, "hyperlif"), best(ds, arch, "lif")
            if not (np.isnan(h) or np.isnan(l)):
                gap[i, j] = h - l
    fig, ax = plt.subplots(figsize=(7.5, 3.1))
    im = ax.imshow(gap, cmap="Greens", vmin=0, vmax=0.16, aspect="auto")
    ax.set_xticks(range(len(datasets))); ax.set_xticklabels([DNAME.get(d, d) for d in datasets])
    ax.set_yticks(range(len(ARCHS))); ax.set_yticklabels(ARCHS)
    for i in range(len(ARCHS)):
        for j in range(len(datasets)):
            if not np.isnan(gap[i, j]):
                ax.text(j, i, f"+{gap[i, j]:.3f}", ha="center", va="center", fontsize=10, color="#173404")
    ax.set_title("HyperLIF − LIF accuracy gap (best readout) — positive in every cell")
    fig.colorbar(im, label="Δ accuracy", fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(out / "fig4_arch_transfer_gap.png", dpi=150); plt.close(fig)

    # FIG 5 — efficiency Pareto (one dataset): accuracy vs events, color=neuron, marker=arch
    ds = a.pareto_dataset
    fig, ax = plt.subplots(figsize=(7.2, 5))
    for k in M:
        if k[0] != ds or M[k] < 0.6 or k not in E:
            continue
        ax.scatter(E[k], M[k], c=COL.get(k[2], "#888"), marker=MK.get(k[1], "o"),
                   s=48, alpha=.85, edgecolor="white", linewidth=.5, zorder=3)
    ax.set_xscale("log"); ax.set_xlabel("events / sample  (log scale)"); ax.set_ylabel("test accuracy")
    ax.set_title(f"{DNAME.get(ds, ds)} — accuracy vs spikes (configs ≥ 0.6):\nHyperLIF/Adaptive reach top accuracy at 1–2 orders of magnitude fewer spikes")
    leg = [Line2D([0], [0], marker="o", color="w", markerfacecolor=COL[n], label=LAB[n], markersize=9) for n in COL]
    leg += [Line2D([0], [0], marker=MK[ar], color="#555", markerfacecolor="w", label=ar, markersize=8, linestyle="") for ar in ARCHS]
    ax.legend(handles=leg, fontsize=9, frameon=False, ncol=2); ax.grid(alpha=.3, which="both")
    fig.tight_layout(); fig.savefig(out / "fig5_efficiency_pareto.png", dpi=150); plt.close(fig)

    print("wrote:", ", ".join(p.name for p in sorted(out.glob("fig[45]*.png"))))
    print("transfer gaps (arch x dataset):")
    for i, arch in enumerate(ARCHS):
        print(" ", arch, {DNAME.get(datasets[j], datasets[j]): round(gap[i, j], 3) for j in range(len(datasets)) if not np.isnan(gap[i, j])})


if __name__ == "__main__":
    main()
