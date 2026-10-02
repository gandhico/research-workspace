"""Plot classical-vs-CMG tracking comparisons from results\\hardware\\ traces.

Pure Python, reads local CSV/JSON files only -- no hardware access. For each
mission, overlays actual angle vs. reference for classical and CMG-PES,
plus a residual/gate diagnostic panel underneath.
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

HOVER_ROOT = Path(__file__).resolve().parents[1]
RESULTS = HOVER_ROOT/"results"/"hardware"


def load_trace(run_dir: Path) -> dict[str, np.ndarray]:
    with (run_dir/"trace.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_mission(mission: str, classical_dir: Path, cmg_dir: Path, out_path: Path) -> None:
    c = load_trace(classical_dir)
    g = load_trace(cmg_dir)
    c_summary = json.loads((classical_dir/"summary.json").read_text())
    g_summary = json.loads((cmg_dir/"summary.json").read_text())

    fig, axes = plt.subplots(6, 1, figsize=(10, 15), sharex=True,
                              gridspec_kw={"height_ratios": [2.2, 2.2, 2.2, 2.2, 2, 2]})
    axis_names = ["yaw", "pitch", "roll"]

    # --- OUTPUTS: tracking vs reference, one row per axis ---
    for i, name in enumerate(axis_names):
        ax = axes[i]
        ax.plot(c["t"], c[f"{name}_ref_deg"], "k--", lw=1.2, label="reference")
        ax.plot(c["t"], c[f"{name}_deg"], color="tab:blue", lw=1.1, alpha=0.85, label="classical")
        ax.plot(g["t"], g[f"{name}_deg"], color="tab:orange", lw=1.1, alpha=0.85, label="CMG-PES")
        ax.set_ylabel(f"{name} (deg)")
        ax.legend(loc="upper right", fontsize=8, ncol=3)
        ax.grid(alpha=0.3)
    axes[0].set_title("OUTPUTS -- angle tracking vs. reference", fontsize=10, loc="left", fontweight="bold")

    # --- ERROR: tracking error magnitude over time, classical vs CMG overlaid ---
    ax = axes[3]
    c_err = np.linalg.norm(np.stack([c["yaw_deg"]-c["yaw_ref_deg"], c["pitch_deg"]-c["pitch_ref_deg"],
                                      c["roll_deg"]-c["roll_ref_deg"]], axis=1), axis=1)
    g_err = np.linalg.norm(np.stack([g["yaw_deg"]-g["yaw_ref_deg"], g["pitch_deg"]-g["pitch_ref_deg"],
                                      g["roll_deg"]-g["roll_ref_deg"]], axis=1), axis=1)
    ax.plot(c["t"], c_err, color="tab:blue", lw=1,
            label=f"classical (mean {c_summary['angle_err_mean_deg']:.2f}, max {c_summary['angle_err_max_deg']:.2f} deg)")
    ax.plot(g["t"], g_err, color="tab:orange", lw=1,
            label=f"CMG-PES (mean {g_summary['angle_err_mean_deg']:.2f}, max {g_summary['angle_err_max_deg']:.2f} deg)")
    ax.axhline(c_summary["angle_err_mean_deg"], color="tab:blue", lw=0.8, ls=":")
    ax.axhline(g_summary["angle_err_mean_deg"], color="tab:orange", lw=0.8, ls=":")
    ax.set_ylabel("|error| (deg)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- combined tracking error magnitude (dotted = run mean)", fontsize=10, loc="left", fontweight="bold")

    # --- INPUTS: motor voltages, classical vs CMG, one row each ---
    channels = ["Vf", "Vb", "Vl", "Vr"]
    colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]
    ax = axes[4]
    for ch, col in zip(channels, colors):
        ax.plot(c["t"], c[ch], color=col, lw=0.8, alpha=0.85, label=ch)
    ax.set_ylabel("classical\nvoltage (V)")
    ax.legend(loc="upper right", fontsize=7, ncol=4)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- motor voltages [Vf, Vb, Vl, Vr]", fontsize=10, loc="left", fontweight="bold")

    ax = axes[5]
    for ch, col in zip(channels, colors):
        ax.plot(g["t"], g[ch], color=col, lw=0.8, alpha=0.85, label=ch)
    ax.set_ylabel("CMG-PES\nvoltage (V)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7, ncol=4)
    ax.grid(alpha=0.3)

    imp = 100*(c_summary["angle_err_mean_deg"]-g_summary["angle_err_mean_deg"])/c_summary["angle_err_mean_deg"]
    fig.suptitle(f"3DOF Hover hardware -- mission: {mission}  |  classical vs CMG-PES "
                 f"(beta={g_summary.get('beta')}, max_res={g_summary.get('max_residual_volts')}V, "
                 f"lr={g_summary.get('learning_rate')}, k_error={g_summary.get('k_error')})\n"
                 f"mean tracking error: classical {c_summary['angle_err_mean_deg']:.3f} deg -> "
                 f"CMG-PES {g_summary['angle_err_mean_deg']:.3f} deg  ({imp:+.2f}%)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--classical", nargs="+", required=True, metavar="MISSION=RUN_DIR")
    parser.add_argument("--cmg", nargs="+", required=True, metavar="MISSION=RUN_DIR")
    parser.add_argument("--out-dir", default=str(HOVER_ROOT/"results"/"plots"))
    args = parser.parse_args()

    classical = dict(pair.split("=", 1) for pair in args.classical)
    cmg = dict(pair.split("=", 1) for pair in args.cmg)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for mission in classical:
        if mission not in cmg:
            continue
        plot_mission(mission, RESULTS/classical[mission], RESULTS/cmg[mission],
                     out_dir/f"{mission}_classical_vs_cmg.png")


if __name__ == "__main__":
    main()
