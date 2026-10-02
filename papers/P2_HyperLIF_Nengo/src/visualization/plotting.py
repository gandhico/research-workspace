"""Shared plotting helpers tuned for publication-quality figures.

The styling here is intentionally restrained and consistent across every
figure in the paper: a serif font family that pairs with the LaTeX body text,
a fixed per-model colour/line-style palette, and vector (PDF) + raster (PNG)
output for each figure. Nothing in this module changes any model equation; it
only controls appearance.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


# Consistent per-model visual identity used across all figures.
MODEL_STYLE: dict[str, dict[str, object]] = {
    "LIF": {"color": "#1f77b4", "ls": "-", "marker": "o"},
    "HyperLIF": {"color": "#d62728", "ls": "-", "marker": "s"},
    "Adaptive HyperLIF": {"color": "#9467bd", "ls": "-", "marker": "^"},
    "Adaptive": {"color": "#9467bd", "ls": "-", "marker": "^"},
    "Gate": {"color": "#2ca02c", "ls": "-", "marker": "D"},
    "Reference": {"color": "black", "ls": "--", "marker": None},
}


def configure() -> None:
    """Apply a restrained, paper-friendly Matplotlib style."""

    plt.rcParams.update(
        {
            "figure.figsize": (7.0, 4.6),
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif", "Times New Roman", "Times"],
            "mathtext.fontset": "dejavuserif",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.6,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.4,
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "legend.fontsize": 8.5,
            "legend.framealpha": 0.9,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.direction": "out",
            "ytick.direction": "out",
        }
    )


def style_for(model: str) -> dict[str, object]:
    """Return a copy of the colour/line style for a named model."""

    base = MODEL_STYLE.get(model, {"color": "0.3", "ls": "-", "marker": "o"})
    return dict(base)


def save_figure(path: str | Path, dpi: int = 300, also_pdf: bool = True) -> None:
    """Save the current figure as a high-resolution PNG and a vector PDF."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=dpi)
    if also_pdf and path.suffix.lower() == ".png":
        plt.savefig(path.with_suffix(".pdf"))
    plt.close()
