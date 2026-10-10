"""One figure* replacing the two per-platform mechanism dashboards.

Rows are the two platforms, columns the two quantities the Neuron-Family
Comparison actually argues from: mean q-error improvement and normalized
residual effort. Row labels appear once per row, so the grid is wider and
much shorter than a 2x2 per platform -- about 90 mm tall instead of two
figures at 145 mm each -- while the text stays at its authored size.

The four-panel per-platform versions remain available for the data package.

Run:  python make_combined_mechanism_fig.py
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
WIDE_IN = 181.0 / 25.4
FS = 6.8

PANELS = (
    ("improvement_pct", "mean $q$-error improvement [%]", "RdYlGn", -60, 60, "+.0f"),
    ("residual_utilization_rms", "normalized residual effort", "magma", 0, None, ".2f"),
)
PLATFORMS = (("x2", "X2"), ("cf2-rotor", "CF2"))


def matrix(records, platform, metric):
    m = np.full((len(FAMILY_ORDER), len(MISSIONS)), np.nan)
    for r in records:
        if r["platform"] == platform and metric in r:
            m[FAMILY_ORDER.index(r["family_mode"]),
              MISSIONS.index(r["mission"])] = r[metric]
    return m


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    records = json.loads(SRC.read_text(encoding="utf-8"))
    if isinstance(records, dict):
        records = records.get("records", records.get("results", []))

    fig, axes = plt.subplots(2, 2, figsize=(WIDE_IN, 4.6),
                             constrained_layout=True)

    for row, (plat, plat_label) in enumerate(PLATFORMS):
        for col, (metric, title, cmap, vmin, vmax, fmt) in enumerate(PANELS):
            ax = axes[row, col]
            m = matrix(records, plat, metric)
            im = ax.imshow(m, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
            lut = plt.get_cmap(cmap)

            ax.set_xticks(range(len(MISSIONS)))
            if row == len(PLATFORMS) - 1:
                ax.set_xticklabels(MISSIONS, rotation=30, ha="right", fontsize=FS)
            else:
                ax.set_xticklabels([])
            ax.set_yticks(range(len(FAMILY_ORDER)))
            if col == 0:
                ax.set_yticklabels(FAMILY_ORDER, fontsize=FS)
                ax.set_ylabel(plat_label, fontsize=FS + 2, fontweight="bold",
                              labelpad=6)
            else:
                ax.set_yticklabels([])
            if row == 0:
                ax.set_title(title, fontsize=FS + 1)

            lo = vmin if vmin is not None else np.nanmin(m)
            hi = vmax if vmax is not None else np.nanmax(m)
            for i in range(m.shape[0]):
                for j in range(m.shape[1]):
                    if np.isfinite(m[i, j]):
                        rel = 0.5 if hi == lo else (m[i, j] - lo) / (hi - lo)
                        r, g, b, _ = lut(float(np.clip(rel, 0, 1)))
                        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                        ax.text(j, i, format(m[i, j], fmt), ha="center",
                                va="center", fontsize=FS - 0.6,
                                color="white" if lum < 0.5 else "black")

            cb = fig.colorbar(im, ax=ax, shrink=0.92, pad=0.02)
            cb.ax.tick_params(labelsize=FS - 1.2)
            ax.tick_params(length=2, width=0.6)
            for sp in ax.spines.values():
                sp.set_linewidth(0.6)

    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"mechanism_both_platforms.{ext}", dpi=400,
                    bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'mechanism_both_platforms.pdf'}")
    print(f"  {WIDE_IN * 25.4:.0f} mm wide, body text {FS - 0.6:.1f} pt at 1:1")


if __name__ == "__main__":
    main()
