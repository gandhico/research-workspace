"""Slide-ready PNGs from the HPC registry (a results .zip or a _registry.csv).

    python hpc/make_slide_figures.py --reg results/hyperlif_hpc_results_559182.zip --out results/figures_slides
"""
from __future__ import annotations

import argparse
import csv
import io
import statistics as st
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COL = {"lif": "#888780", "hyperlif": "#1D9E75", "adaptive": "#7F77DD"}
LAB = {"lif": "LIF", "hyperlif": "HyperLIF", "adaptive": "Adaptive HyperLIF"}
DNAME = {"dvsg32_wide": "DVS-Gesture 32", "dvsg48_wide": "DVS-Gesture 48",
         "nmnist_wide": "N-MNIST", "shd_wide_T20": "SHD", "ssc_wide_T20": "SSC"}
ORDER = ["shd_wide_T20", "ssc_wide_T20", "nmnist_wide", "dvsg32_wide", "dvsg48_wide"]
NEUR = ["lif", "hyperlif", "adaptive"]
READ = ["membrane", "spike_count", "gate", "hybrid_gr", "hybrid_vr", "hybrid_vr_conductance"]
RSHORT = {"membrane": "mem(V)", "spike_count": "spikes", "gate": "gate(r)",
          "hybrid_gr": "[r,G]", "hybrid_vr": "[V,r]", "hybrid_vr_conductance": "[V,r,G]"}


def load_rows(p):
    p = Path(p)
    if p.suffix == ".zip":
        z = zipfile.ZipFile(p)
        cands = [n for n in z.namelist() if n.endswith(".csv")]
        name = next((n for n in cands if n.endswith("_registry.csv")), cands[0] if cands else None)
        if not name:
            raise SystemExit("no .csv in zip: " + str(z.namelist()[:12]))
        print("registry:", name)
        return list(csv.DictReader(io.TextIOWrapper(z.open(name), encoding="utf-8")))
    return list(csv.DictReader(open(p, encoding="utf-8")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reg", required=True)
    ap.add_argument("--out", default="results/figures_slides")
    a = ap.parse_args()
    rows = load_rows(a.reg)
    acc, ev = defaultdict(list), defaultdict(list)
    for r in rows:
        try:
            v = float(r["accuracy"])
        except (ValueError, KeyError, TypeError):
            continue
        k = (r["dataset"], r["neuron"], r["readout"])
        acc[k].append(v)
        try:
            ev[k].append(float(r["events_per_sample"]))
        except (ValueError, KeyError, TypeError):
            pass
    ds = [d for d in ORDER if any(k[0] == d for k in acc)] + sorted({k[0] for k in acc} - set(ORDER))
    print(f"datasets: {ds} | runs: {len(rows)}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    def M(k): return st.mean(acc[k]) if acc.get(k) else np.nan
    def S(k): return st.pstdev(acc[k]) if len(acc.get(k, [])) > 1 else 0.0
    def E(k): return st.mean(ev[k]) if ev.get(k) else np.nan

    plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "figure.facecolor": "white"})

    # FIG 1 — best accuracy per neuron, per dataset (the headline)
    fig, ax = plt.subplots(figsize=(max(7, 1.7 * len(ds)), 4.7))
    w, x = 0.26, np.arange(len(ds))
    for i, n in enumerate(NEUR):
        best, err = [], []
        for d in ds:
            ks = [(d, n, r) for r in READ if (d, n, r) in acc]
            bk = max(ks, key=M) if ks else None
            best.append(M(bk) if bk else np.nan); err.append(S(bk) if bk else 0)
        ax.bar(x + (i - 1) * w, best, w, yerr=err, capsize=3, label=LAB[n], color=COL[n])
    ax.set_xticks(x); ax.set_xticklabels([DNAME.get(d, d) for d in ds])
    ax.set_ylabel("test accuracy (best readout, 5 seeds)"); ax.set_ylim(0, 1.0)
    ax.set_title(r"HyperLIF $\geq$ Adaptive $>$ LIF across datasets")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(out / "fig1_best_per_neuron.png", dpi=150); plt.close(fig)

    # FIG 2 — structural blindness: readout sweep LIF vs HyperLIF
    d2 = "dvsg32_wide" if "dvsg32_wide" in ds else ds[0]
    nC = 11 if "dvsg" in d2 else (20 if d2 == "shd_wide_T20" else (35 if d2 == "ssc_wide_T20" else 10))
    fig, ax = plt.subplots(figsize=(8.6, 4.7))
    x, w = np.arange(len(READ)), 0.38
    for i, n in enumerate(["lif", "hyperlif"]):
        ax.bar(x + (i - 0.5) * w, [M((d2, n, r)) for r in READ], w,
               yerr=[S((d2, n, r)) for r in READ], capsize=3, label=LAB[n], color=COL[n])
    ax.axhline(1 / nC, ls="--", color="#999", lw=1.2, label=f"chance (1/{nC})")
    ax.set_xticks(x); ax.set_xticklabels([RSHORT[r] for r in READ])
    ax.set_ylabel("test accuracy"); ax.set_ylim(0, 0.9)
    ax.set_title(f"LIF collapses to chance on gate readouts — HyperLIF does not  ({DNAME.get(d2, d2)})")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(out / "fig2_structural_blindness.png", dpi=150); plt.close(fig)

    # FIG 3 — efficiency: accuracy vs spikes, colored by neuron
    fig, ax = plt.subplots(figsize=(7, 5))
    for n in NEUR:
        xs = [E((d2, n, r)) for r in READ if (d2, n, r) in acc]
        ys = [M((d2, n, r)) for r in READ if (d2, n, r) in acc]
        ax.scatter(xs, ys, s=85, color=COL[n], edgecolor="white", label=LAB[n], alpha=.9, zorder=3)
    ax.set_xlabel("events / sample (spikes)"); ax.set_ylabel("test accuracy")
    ax.set_title(f"Accuracy vs spike count — Adaptive is sparser  ({DNAME.get(d2, d2)})")
    ax.legend(frameon=False); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out / "fig3_efficiency_pareto.png", dpi=150); plt.close(fig)

    print("wrote:", ", ".join(p.name for p in sorted(out.glob("*.png"))))


if __name__ == "__main__":
    main()
