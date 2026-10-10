"""Plot CMG neuron (membrane potential v, gate state r) activity during a mission.

Pure Python, reads a trace.csv produced by scripts/rerun_with_euler_logging.py
(needs the neuron_v_*/neuron_r_* columns) -- no simulation re-run. Six
neurons per CMGResidualAugmentor call: indices 0-2 are the positive-current
branch for [tau_x, tau_y, tau_z] (or [Vf-axis analog] on other platforms),
indices 3-5 are the negative-current branch, per
gra_control.gate.CMGResidualAugmentor.step's own current construction.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AXIS_NAMES = ["x", "y", "z"]
AXIS_COLORS = ["tab:blue", "tab:green", "tab:red"]


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_neurons(platform: str, mission: str, run_dir: Path, out_path: Path, zoom_s: float = 3.0) -> None:
    d = load_trace(run_dir)
    t = d["t"]
    zoom_mask = t <= zoom_s

    fig, axes = plt.subplots(4, 1, figsize=(10, 12))

    def draw(ax, mask, title):
        for i in range(3):
            ax.plot(t[mask], d[f"neuron_v_{i}"][mask], color=AXIS_COLORS[i], lw=1.1,
                     label=f"{AXIS_NAMES[i]}+ (v)")
            ax.plot(t[mask], d[f"neuron_v_{i+3}"][mask], color=AXIS_COLORS[i], lw=1.1, ls="--",
                     label=f"{AXIS_NAMES[i]}- (v)")
        ax.set_ylabel("membrane\npotential v")
        ax.set_title(title, fontsize=10, loc="left", fontweight="bold")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)

    def draw_r(ax, mask, title):
        for i in range(3):
            ax.plot(t[mask], d[f"neuron_r_{i}"][mask], color=AXIS_COLORS[i], lw=1.1,
                     label=f"{AXIS_NAMES[i]}+ (r)")
            ax.plot(t[mask], d[f"neuron_r_{i+3}"][mask], color=AXIS_COLORS[i], lw=1.1, ls="--",
                     label=f"{AXIS_NAMES[i]}- (r)")
        ax.set_ylabel("gate state r\n(0=closed, 1=open)")
        ax.set_ylim(-0.05, 1.05)
        ax.set_title(title, fontsize=10, loc="left", fontweight="bold")
        ax.legend(loc="right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)

    draw(axes[0], slice(None), f"MEMBRANE POTENTIAL v -- full mission (0-{t[-1]:.0f}s)")
    axes[0].set_xlabel("time (s)")
    draw_r(axes[1], slice(None), f"GATE STATE r -- full mission (0-{t[-1]:.0f}s)")
    axes[1].set_xlabel("time (s)")
    draw(axes[2], zoom_mask, f"MEMBRANE POTENTIAL v -- zoomed activation transient (0-{zoom_s}s)")
    axes[2].set_xlabel("time (s)")
    draw_r(axes[3], zoom_mask, f"GATE STATE r -- zoomed activation transient (0-{zoom_s}s)")
    axes[3].set_xlabel("time (s)")

    fig.suptitle(f"CMG neuron activity -- {platform}, mission {mission}\n"
                 f"6 units: 3 axes (x/y/z) x 2 branches (+/- current), "
                 f"solid=positive branch, dashed=negative branch", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--platform", required=True)
    p.add_argument("--mission", required=True)
    p.add_argument("--run-dir", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--zoom-s", type=float, default=3.0)
    a = p.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    plot_neurons(a.platform, a.mission, a.run_dir, a.out, a.zoom_s)
