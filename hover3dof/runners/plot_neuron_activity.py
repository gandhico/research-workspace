"""Plot CMG neuron (membrane potential v, gate state r) activity during a
3DOF Hover hardware run.

Pure Python, reads a trace.csv with neuron_v_0..7/neuron_r_0..7 columns
(added to hover3dof_hil_cmg_control.py 2026-08-28) -- no hardware access.
8 neurons = 2 branches (positive-current, negative-current) x 4 motor
channels [Vf, Vb, Vl, Vr], matching gate.py's CMGResidualAugmentor.step():
current = concat[bias+gain*max(normalized,0), bias+gain*max(-normalized,0)].
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CHANNEL_NAMES = ["Vf", "Vb", "Vl", "Vr"]


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_neurons(run_dir: Path, out_path: Path) -> None:
    t_data = load_trace(run_dir)
    summary = json.loads((run_dir/"summary.json").read_text())
    t = t_data["t"]
    if "neuron_v_0" not in t_data:
        raise SystemExit(f"{run_dir} has no neuron_v_* columns -- run predates the 2026-08-28 logging fix.")

    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True)

    # Row 1-2: membrane potential v, positive branch (0-3) then negative branch (4-7)
    for branch, (ax, label) in enumerate(zip(axes[:2], ["positive-current branch (+)", "negative-current branch (-)"])):
        for ch in range(4):
            idx = branch*4+ch
            ax.plot(t, t_data[f"neuron_v_{idx}"], lw=0.8, label=CHANNEL_NAMES[ch])
        ax.set_ylabel(f"membrane v\n{label}")
        ax.legend(loc="upper right", fontsize=7, ncol=4)
        ax.grid(alpha=0.3)
    axes[0].set_title("MEMBRANE POTENTIAL -- CoupledMembraneGateBank.v, per motor channel, both branches",
                       fontsize=10, loc="left", fontweight="bold")

    # Row 3-4: gate state r (0-1 bounded), positive branch then negative branch
    for branch, (ax, label) in enumerate(zip(axes[2:], ["positive-current branch (+)", "negative-current branch (-)"])):
        for ch in range(4):
            idx = branch*4+ch
            ax.plot(t, t_data[f"neuron_r_{idx}"], lw=0.8, label=CHANNEL_NAMES[ch])
        ax.set_ylabel(f"gate r\n{label}")
        ax.set_ylim(-0.05, 1.05)
        ax.legend(loc="upper right", fontsize=7, ncol=4)
        ax.grid(alpha=0.3)
    axes[2].set_title("GATE STATE -- CoupledMembraneGateBank.r (0=closed, 1=fully open)",
                       fontsize=10, loc="left", fontweight="bold")
    axes[3].set_xlabel("time (s)")

    fig.suptitle(f"3DOF Hover hardware -- neuron activity -- mission: {summary.get('mission')}  "
                 f"(beta={summary.get('beta')}, max_res={summary.get('max_residual_volts')}V, "
                 f"lr={summary.get('learning_rate')}, k_error={summary.get('k_error')})\n"
                 f"gate_mean over run: {np.mean(t_data['gate_mean']):.3f}   "
                 f"residual_norm mean/max: {np.mean(t_data['residual_norm']):.3f} / {np.max(t_data['residual_norm']):.3f} V",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    plot_neurons(a.run_dir, a.out)
