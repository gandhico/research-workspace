"""Plot classical-vs-CMG-PES for the Option-A realistic cascade experiment.

Max two figures per mission, per user direction: Figure 1 = tracking
(6-DOF outputs + position/attitude error), Figure 2 = mechanism (applied
inputs, residual norm, gate activation, neuron activity, decoder norm --
the "neurons, PES, etc" the user asked to see). Pure Python, reads
trace.csv/summary.json only -- no simulation re-run.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_tracking(mission: str, c: dict, n: dict, c_s: dict, n_s: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(5, 1, figsize=(10, 12.5), sharex=True,
                              gridspec_kw={"height_ratios": [1.6, 1.6, 1.6, 1.5, 1.5]})

    for i, ax_name in enumerate(["x", "y", "z"]):
        ax = axes[i]
        ax.plot(c["t"], c[f"{ax_name}_ref"], "k--", lw=1.1, label="reference")
        ax.plot(c["t"], c[ax_name], color="tab:blue", lw=1, alpha=0.85, label="classical")
        ax.plot(n["t"], n[ax_name], color="tab:red", lw=1, alpha=0.85, label="CMG-PES")
        ax.set_ylabel(f"{ax_name} (m)")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)
    axes[0].set_title(f"OUTPUTS -- 6DOF cascade (Option A), {mission}: position vs. reference",
                       fontsize=10, loc="left", fontweight="bold")

    ax = axes[3]
    ax.plot(c["t"], c["pos_err"], color="tab:blue", lw=1, label=f"classical (mean {c_s['pos_err_mean_m']:.3f}m)")
    ax.plot(n["t"], n["pos_err"], color="tab:red", lw=1, label=f"CMG-PES (mean {n_s['pos_err_mean_m']:.3f}m)")
    ax.set_ylabel("|pos error| (m)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- position error magnitude", fontsize=10, loc="left", fontweight="bold")

    ax = axes[4]
    ax.plot(c["t"], np.rad2deg(c["qerr"]), color="tab:blue", lw=1, label=f"classical (mean {np.rad2deg(c_s['qerr_mean_rad']):.2f} deg)")
    ax.plot(n["t"], np.rad2deg(n["qerr"]), color="tab:red", lw=1, label=f"CMG-PES (mean {np.rad2deg(n_s['qerr_mean_rad']):.2f} deg)")
    ax.set_ylabel("attitude\nerror (deg)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- attitude error", fontsize=10, loc="left", fontweight="bold")

    pos_imp = 100*(c_s["pos_err_mean_m"]-n_s["pos_err_mean_m"])/max(1e-9, c_s["pos_err_mean_m"])
    att_imp = 100*(c_s["qerr_mean_rad"]-n_s["qerr_mean_rad"])/max(1e-9, c_s["qerr_mean_rad"])
    fig.suptitle(f"Option A (realistic underactuated cascade) -- mission: {mission}\n"
                 f"position improvement {pos_imp:+.2f}%   attitude improvement {att_imp:+.2f}%", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


def plot_mechanism(mission: str, c: dict, n: dict, out_path: Path) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True,
                              gridspec_kw={"height_ratios": [1.6, 1.3, 1.3, 1.3]})

    ax = axes[0]
    for ch, col in zip(["Fcmd_x", "Fcmd_y", "Fcmd_z"], ["tab:blue", "tab:orange", "tab:green"]):
        ax.plot(n["t"], n[ch], lw=0.7, color=col, label=f"{ch} (CMG-PES)")
    for ch, col in zip(["tau_x", "tau_y", "tau_z"], ["tab:red", "tab:purple", "tab:brown"]):
        ax.plot(n["t"], n[ch], lw=0.6, color=col, alpha=0.7, label=f"{ch} (CMG-PES)")
    ax.set_ylabel("applied\ncommand")
    ax.legend(loc="upper right", fontsize=6, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title(f"INPUTS -- 6DOF cascade (Option A), {mission}: commanded force + torque (CMG-PES)",
                 fontsize=10, loc="left", fontweight="bold")

    ax = axes[1]
    ax.plot(n["t"], n["residual_norm"], color="tab:red", lw=1, label="||residual|| (CMG-PES)")
    ax.set_ylabel("residual\nnorm")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- CMG-PES residual magnitude", fontsize=10, loc="left", fontweight="bold")

    ax = axes[2]
    ax.plot(n["t"], n["gate_mean"], color="tab:red", lw=1, label="mean gate r (CMG-PES)")
    ax2 = ax.twinx()
    ax2.plot(n["t"], n["activity_mean"], color="tab:orange", lw=1, alpha=0.8, label="mean neuron activity")
    ax.set_ylabel("gate r")
    ax2.set_ylabel("activity")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, labels1+labels2, loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- gate activation and neuron activity (12 CMG units, 6 channels)",
                 fontsize=10, loc="left", fontweight="bold")

    ax = axes[3]
    ax.plot(n["t"], n["decoder_norm"], color="tab:red", lw=1, label="||W|| (online-PES decoder)")
    ax.set_ylabel("decoder\nnorm")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- PES decoder weight norm (learning signal)", fontsize=10, loc="left", fontweight="bold")

    fig.suptitle(f"Option A (realistic underactuated cascade) -- mission: {mission} -- CMG-PES mechanism", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="optionA")
    p.add_argument("--tag", default="optionA")
    a = p.parse_args()

    out_dir = ROOT/"results"/"plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    for mission in ["hover3d", "waypoint_step", "circle_xy", "full6_stress"]:
        c_dir = ROOT/"results"/a.results_dir/f"{mission}_classical"
        n_dir = ROOT/"results"/a.results_dir/f"{mission}_pes"
        c, n = load_trace(c_dir), load_trace(n_dir)
        c_s = json.loads((c_dir/"summary.json").read_text())
        n_s = json.loads((n_dir/"summary.json").read_text())
        plot_tracking(mission, c, n, c_s, n_s, out_dir/f"{mission}_{a.tag}_tracking.png")
        plot_mechanism(mission, c, n, out_dir/f"{mission}_{a.tag}_mechanism.png")
