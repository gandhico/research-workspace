"""One comprehensive dashboard per (platform, mission): outputs, inputs,
errors, neurons, decoder, and activity, all in a single figure.

Pure Python, reads matched_45s/{platform}_{mission}_{classical,nengo_nef_pes}
trace.csv/summary.json only -- no simulation re-run. Complements (does not
replace) the existing tracking/neurons plot pair from compile_and_plot.py --
this merges both into one dashboard and adds the actual 4-channel actuator
(motor) commands, which neither existing plot shows on its own.
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

ROOT = Path(__file__).resolve().parent
NEURON_LABELS = ["+x", "+y", "+z", "-x", "-y", "-z"]
NEURON_COLORS = ["tab:blue", "tab:green", "tab:purple", "tab:pink", "tab:olive", "tab:cyan"]
AXIS_LABELS = ["roll/x", "pitch/y", "yaw/z"]
AXIS_COLORS = ["tab:red", "tab:green", "tab:purple"]


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_dashboard(platform: str, mission: str, classical_dir: Path, nengo_dir: Path, out_path: Path) -> None:
    c = load_trace(classical_dir)
    n = load_trace(nengo_dir)
    c_summary = json.loads((classical_dir/"summary.json").read_text())
    n_summary = json.loads((nengo_dir/"summary.json").read_text())

    fig, axes = plt.subplots(8, 1, figsize=(11, 22), sharex=True,
                              gridspec_kw={"height_ratios": [2.2, 1.6, 1.6, 1.6, 1.6, 1.6, 1.4, 1.6]})

    c_deg, n_deg = np.rad2deg(c["qerr"]), np.rad2deg(n["qerr"])
    c_mean, n_mean = c_deg.mean(), n_deg.mean()
    imp = 100*(c_mean-n_mean)/c_mean if c_mean > 1e-9 else 0.0

    # 1) OUTPUT/ERROR: quaternion tracking error, classical vs Nengo
    ax = axes[0]
    ax.plot(c["t"], c_deg, color="tab:blue", lw=1, label=f"Quaternion PD (mean {c_mean:.2f} deg)")
    ax.plot(n["t"], n_deg, color="tab:red", lw=1, label=f"Nengo CMG+PES (mean {n_mean:.2f} deg)")
    ax.axhline(c_mean, color="tab:blue", lw=0.7, ls=":")
    ax.axhline(n_mean, color="tab:red", lw=0.7, ls=":")
    ax.set_ylabel("attitude error (deg)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_title(f"OUTPUT / ERROR -- quaternion-angle tracking error, {platform} {mission} "
                 f"(mean improvement {imp:+.2f}%)", fontsize=10, loc="left", fontweight="bold")

    # 2) INPUTS: actual 4-channel actuator/motor commands (Nengo run)
    ax = axes[1]
    for i in range(4):
        ax.plot(n["t"], n[f"actuator_{i}"], lw=0.6, alpha=0.85, label=f"motor {i}")
    ax.set_ylabel("actuator\ncommand")
    ax.legend(loc="upper right", fontsize=7, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- actual mixed motor/actuator commands", fontsize=10, loc="left", fontweight="bold")

    # 3) Applied residual torque (the CMG's contribution, in physical units)
    ax = axes[2]
    for ax_name, col, color in zip(AXIS_LABELS, ["residual_x", "residual_y", "residual_z"], AXIS_COLORS):
        ax.plot(n["t"], n[col], lw=0.7, color=color, label=ax_name)
    ax.set_ylabel("residual\ntorque (N*m)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title("APPLIED RESIDUAL -- delta_tau added on top of the baseline", fontsize=10, loc="left", fontweight="bold")

    # 4) Membrane potential v, all 6 neurons
    ax = axes[3]
    for i, (lbl, color) in enumerate(zip(NEURON_LABELS, NEURON_COLORS)):
        ax.plot(n["t"], n[f"voltage_{i}"], lw=0.6, color=color, label=lbl)
    ax.set_ylabel("membrane v")
    ax.legend(loc="upper right", fontsize=7, ncol=6)
    ax.grid(alpha=0.3)
    ax.set_title("NEURONS -- membrane potential v, paired +/- population", fontsize=10, loc="left", fontweight="bold")

    # 5) Gate r, all 6 neurons
    ax = axes[4]
    for i, (lbl, color) in enumerate(zip(NEURON_LABELS, NEURON_COLORS)):
        ax.plot(n["t"], n[f"gate_{i}"], lw=0.6, color=color, label=lbl)
    ax.set_ylabel("gate r")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="upper right", fontsize=7, ncol=6)
    ax.grid(alpha=0.3)
    ax.set_title("NEURONS -- gate state r (0=closed, 1=fully open)", fontsize=10, loc="left", fontweight="bold")

    # 6) Activity a, all 6 neurons (decoder input)
    ax = axes[5]
    for i, (lbl, color) in enumerate(zip(NEURON_LABELS, NEURON_COLORS)):
        ax.plot(n["t"], n[f"activity_{i}"], lw=0.6, color=color, label=lbl)
    ax.set_ylabel("activity a")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="upper right", fontsize=7, ncol=6)
    ax.grid(alpha=0.3)
    ax.set_title("ACTIVITY -- gate-derived decoder input a = clip(1e5 * r, 0, 1)", fontsize=10, loc="left", fontweight="bold")

    # 7) Decoder row norms (per output axis) -- summarizes the 3x6 W matrix's evolution
    ax = axes[6]
    w_cols = [[f"decoder_w_{ax_i*6+ch}" for ch in range(6)] for ax_i in range(3)]
    for ax_name, cols, color in zip(AXIS_LABELS, w_cols, AXIS_COLORS):
        row_norm = np.linalg.norm(np.stack([n[c] for c in cols], axis=1), axis=1)
        ax.plot(n["t"], row_norm, lw=1, color=color, label=ax_name)
    ax.set_ylabel("||W_row||_2")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title("DECODER -- online-PES learned weight row norms (3x6 matrix W)", fontsize=10, loc="left", fontweight="bold")

    # 8) PES teaching error (target - decoded output), per axis -- the learning signal itself
    ax = axes[7]
    for ax_name, col, color in zip(AXIS_LABELS, ["pes_error_x", "pes_error_y", "pes_error_z"], AXIS_COLORS):
        ax.plot(n["t"], n[col], lw=0.6, color=color, label=ax_name)
    ax.set_ylabel("PES error\n(y*-y)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title("LEARNING SIGNAL -- PES teaching error driving the decoder update", fontsize=10, loc="left", fontweight="bold")

    fig.suptitle(f"{platform} -- {mission} -- comprehensive dashboard\n"
                 f"beta={n_summary.get('beta')}  lr={n_summary.get('learning_rate_direct_equivalent')} "
                 f"(Nengo-native {n_summary.get('nengo_pes_learning_rate')})  "
                 f"k_error={n_summary.get('k_error')}  duration={n_summary.get('duration')}s",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}  (improvement: {imp:+.2f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platforms", nargs="+", default=["x2", "cf2_rotor"])
    parser.add_argument("--missions", nargs="+",
                         default=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"])
    parser.add_argument("--results-root", type=Path, default=ROOT/"results"/"matched_45s")
    parser.add_argument("--out-dir", type=Path, default=ROOT/"results"/"plots"/"comprehensive")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for platform in args.platforms:
        for mission in args.missions:
            classical_dir = args.results_root/f"{platform}_{mission}_classical"
            nengo_dir = args.results_root/f"{platform}_{mission}_nengo_nef_pes"
            if not (classical_dir/"trace.csv").exists() or not (nengo_dir/"trace.csv").exists():
                print(f"skip {platform}/{mission}: missing trace.csv")
                continue
            out_path = args.out_dir/f"{platform}_{mission}_dashboard.png"
            plot_dashboard(platform, mission, classical_dir, nengo_dir, out_path)
