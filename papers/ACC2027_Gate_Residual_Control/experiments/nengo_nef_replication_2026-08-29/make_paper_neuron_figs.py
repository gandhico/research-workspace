"""Regenerate the neuron-family figures at their true printed size.

The originals were authored at figsize=(18, 12) and then placed in a 3.5 in
IEEE column, a 5.1x reduction that turns 7 pt cell labels into about 1.4 pt.
No LaTeX option fixes that: a figure has to be drawn at the size it will be
printed, so the fonts survive at 1:1.

Two variants per platform, both vector PDF:

  *_mechanism_col.pdf    88 mm  single column, the two panels the text
                         actually argues from (improvement, residual effort)
  *_mechanism_wide.pdf   181 mm two columns (figure*), all four panels

Four heatmaps plus four colorbars cannot be legible in one 88 mm column at
any font size, so the column variant drops to two panels rather than
pretending otherwise.

Run:  python make_paper_neuron_figs.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE / "results" / "neuron_family_compiled" / "neuron_family_results.json"
OUT = HERE / "results" / "neuron_family_compiled" / "paper_figs"

FAMILY_ORDER = ("cmg-fixed", "cmg-pes", "lif-fixed", "lif-pes", "alif-fixed",
                "alif-pes", "izhikevich-fixed", "izhikevich-pes",
                "lifrate-fixed", "lifrate-pes")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")

# IEEE two-column: 88 mm column, 181 mm text width.
COL_IN = 88.0 / 25.4
WIDE_IN = 181.0 / 25.4

SPECS = {
    "improvement_pct": ("mean $q$-error improvement", "improvement [%]",
                        "RdYlGn", -60, 60, "+.0f"),
    "residual_utilization_rms": ("normalized residual effort",
                                 "RMS residual / limit", "magma", 0, None, ".2f"),
    "activity_occupancy_fraction": ("neural feature occupancy",
                                    r"fraction $|a|>10^{-9}$", "Blues", 0, 1, ".2f"),
    "decoder_drift_fro": ("decoder movement", r"$\|W_T-W_0\|_F$",
                          "cividis", 0, None, ".2f"),
}


def matrix(records, platform, metric):
    m = np.full((len(FAMILY_ORDER), len(MISSIONS)), np.nan)
    for r in records:
        if r["platform"] == platform and metric in r:
            m[FAMILY_ORDER.index(r["family_mode"]),
              MISSIONS.index(r["mission"])] = r[metric]
    return m


def heatmap(ax, m, title, cbar_label, cmap, vmin, vmax, fmt, *, fs):
    im = ax.imshow(m, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    lut = plt.get_cmap(cmap)
    ax.set_xticks(range(len(MISSIONS)))
    ax.set_xticklabels(MISSIONS, rotation=30, ha="right", fontsize=fs)
    ax.set_yticks(range(len(FAMILY_ORDER)))
    ax.set_yticklabels(FAMILY_ORDER, fontsize=fs)
    ax.set_title(title, fontsize=fs + 1)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            if np.isfinite(m[i, j]):
                v = m[i, j]
                # Pick the label colour from the luminance of the cell's
                # actual fill. Guessing from the colormap's direction is
                # wrong for maps whose low end is light (Blues) versus dark
                # (magma, cividis), and wrong again for diverging maps that
                # are pale in the middle.
                lo = vmin if vmin is not None else np.nanmin(m)
                hi = vmax if vmax is not None else np.nanmax(m)
                rel = 0.5 if hi == lo else (v - lo) / (hi - lo)
                r, g, b, _ = lut(float(np.clip(rel, 0.0, 1.0)))
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                ax.text(j, i, format(v, fmt), ha="center", va="center",
                        fontsize=fs - 0.5,
                        color="white" if luminance < 0.5 else "black")
    cb = ax.figure.colorbar(im, ax=ax, shrink=0.9, pad=0.02)
    cb.set_label(cbar_label, fontsize=fs)
    cb.ax.tick_params(labelsize=fs - 1)
    ax.tick_params(length=2, width=0.6)
    for sp in ax.spines.values():
        sp.set_linewidth(0.6)


def build(records, platform, kind):
    if kind == "col":
        metrics = ("improvement_pct", "residual_utilization_rms")
        fig, axes = plt.subplots(2, 1, figsize=(COL_IN, 5.4),
                                 constrained_layout=True)
        fs = 6.5
    else:
        metrics = tuple(SPECS)
        fig, axes = plt.subplots(2, 2, figsize=(WIDE_IN, 5.6),
                                 constrained_layout=True)
        fs = 7.0

    for ax, metric in zip(np.atleast_1d(axes).flat, metrics):
        title, cbar, cmap, vmin, vmax, fmt = SPECS[metric]
        heatmap(ax, matrix(records, platform, metric), title, cbar,
                cmap, vmin, vmax, fmt, fs=fs)

    name = f"{platform}_mechanism_{kind}"
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=400, bbox_inches="tight")
    plt.close(fig)

    w_in = COL_IN if kind == "col" else WIDE_IN
    print(f"  {name:34s} {w_in * 25.4:5.0f} mm wide, "
          f"body text {fs - 0.5:.1f} pt at 1:1")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    records = json.loads(SRC.read_text(encoding="utf-8"))
    if isinstance(records, dict):
        records = records.get("records", records.get("results", []))
    print(f"{len(records)} benchmark records\n")
    for platform in ("x2", "cf2-rotor"):
        for kind in ("col", "wide"):
            build(records, platform, kind)
    print(f"\nwritten to {OUT}")
