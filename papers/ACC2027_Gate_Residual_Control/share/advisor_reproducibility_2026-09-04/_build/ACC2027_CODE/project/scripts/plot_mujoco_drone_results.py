"""Plot classical-vs-CMG comparisons from MuJoCo X2/CF2 trace.csv results.

Pure Python, reads local CSV/JSON files only -- no simulation re-run.
Mirrors the layout of the 3DOF Hover hardware plots (outputs / error /
inputs), adapted to what the drone controllers actually log
(gra_control.platforms.drone.py): a scalar quaternion-error attitude
metric rather than per-axis Euler angles, since the drone state is a full
SO(3) attitude, not a fixed-base Euler gimbal. There is no logged
"reference angle" trace to overlay the way the Hover plots do -- qerr=0
*is* perfect tracking of the reference, so qerr itself doubles as the
error signal and altitude z (regulated near 1.0 m) stands in as the one
directly-tracked scalar output that IS logged.
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


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_platform(platform: str, classical_dir: Path, cmg_dir: Path, out_path: Path) -> None:
    c = load_trace(classical_dir)
    g = load_trace(cmg_dir)
    c_summary_path, g_summary_path = classical_dir/"summary.json", cmg_dir/"summary.json"
    c_summary = json.loads(c_summary_path.read_text()) if c_summary_path.exists() else {}
    g_summary = json.loads(g_summary_path.read_text()) if g_summary_path.exists() else {}
    has_euler = "roll_deg" in c and "roll_deg" in g

    n_rows = 6 if has_euler else 4
    fig, axes = plt.subplots(n_rows, 1, figsize=(10, 15 if has_euler else 11), sharex=True,
                              gridspec_kw={"height_ratios": ([2, 2, 2] if has_euler else [])+[2.2, 2, 2]})

    if has_euler:
        for i, name in enumerate(["roll", "pitch", "yaw"]):
            ax = axes[i]
            ax.plot(c["t"], c[f"{name}_ref_deg"], "k--", lw=1.2, label="reference")
            ax.plot(c["t"], c[f"{name}_deg"], color="tab:blue", lw=1, alpha=0.85, label="classical")
            ax.plot(g["t"], g[f"{name}_deg"], color="tab:orange", lw=1, alpha=0.85, label="CMG-PES")
            ax.set_ylabel(f"{name} (deg)")
            ax.legend(loc="upper right", fontsize=8, ncol=3)
            ax.grid(alpha=0.3)
        axes[0].set_title("OUTPUTS -- attitude tracking vs. reference (roll/pitch/yaw)",
                           fontsize=10, loc="left", fontweight="bold")
        err_row = 3
    else:
        ax = axes[0]
        ax.axhline(1.0, color="k", ls="--", lw=1.2, label="reference (z=1.0 m)")
        ax.plot(c["t"], c["z"], color="tab:blue", lw=1, alpha=0.85, label="classical")
        ax.plot(g["t"], g["z"], color="tab:orange", lw=1, alpha=0.85, label="CMG-PES")
        ax.set_ylabel("altitude z (m)")
        ax.legend(loc="upper right", fontsize=8, ncol=3)
        ax.grid(alpha=0.3)
        ax.set_title("OUTPUT -- altitude hold vs. reference (attitude is full SO(3); see ERROR below)",
                      fontsize=9.5, loc="left", fontweight="bold")
        err_row = 1

    # --- ERROR: quaternion attitude error magnitude (0 = perfect reference tracking) ---
    c_err_mean, c_err_max = np.rad2deg(c["qerr"].mean()), np.rad2deg(c["qerr"].max())
    g_err_mean, g_err_max = np.rad2deg(g["qerr"].mean()), np.rad2deg(g["qerr"].max())
    ax = axes[err_row]
    c_deg, g_deg = np.rad2deg(c["qerr"]), np.rad2deg(g["qerr"])
    ax.plot(c["t"], c_deg, color="tab:blue", lw=1,
            label=f"classical (mean {c_err_mean:.2f}, max {c_err_max:.2f} deg)")
    ax.plot(g["t"], g_deg, color="tab:orange", lw=1,
            label=f"CMG-PES (mean {g_err_mean:.2f}, max {g_err_max:.2f} deg)")
    ax.axhline(c_err_mean, color="tab:blue", lw=0.8, ls=":")
    ax.axhline(g_err_mean, color="tab:orange", lw=0.8, ls=":")
    ax.set_ylabel("attitude error\n(deg, 0=aligned w/ ref)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- quaternion attitude-tracking error magnitude (dotted = run mean)",
                 fontsize=9.5, loc="left", fontweight="bold")

    # --- INPUTS: torque commands, classical vs CMG ---
    chans, colors = ["tau_x", "tau_y", "tau_z"], ["tab:blue", "tab:green", "tab:red"]
    ax = axes[err_row+1]
    for ch, col in zip(chans, colors):
        ax.plot(c["t"], c[ch], color=col, lw=0.7, alpha=0.85, label=ch)
    ax.set_ylabel("classical\ntorque (N*m)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- torque commands [tau_x, tau_y, tau_z]", fontsize=9.5, loc="left", fontweight="bold")

    ax = axes[err_row+2]
    for ch, col in zip(chans, colors):
        ax.plot(g["t"], g[ch], color=col, lw=0.7, alpha=0.85, label=ch)
    ax.set_ylabel("CMG-PES\ntorque (N*m)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)

    imp = 100*(c_err_mean-g_err_mean)/c_err_mean
    duration = float(c["t"][-1])
    mission = g_summary.get("mission") or c_summary.get("mission") or "unknown"
    fig.suptitle(f"MuJoCo {platform} -- mission: {mission}, {duration:.0f}s  |  "
                 f"classical vs CMG-PES ({g_summary.get('controller')}, beta={g_summary.get('beta')})\n"
                 f"mean attitude error: classical {c_err_mean:.3f} deg -> "
                 f"CMG-PES {g_err_mean:.3f} deg  ({imp:+.2f}%)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"wrote {out_path}  (improvement: {imp:+.2f}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--classical", required=True, type=Path)
    parser.add_argument("--cmg", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    plot_platform(args.platform, args.classical, args.cmg, args.out)
