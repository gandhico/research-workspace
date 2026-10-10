"""Plot classical-vs-CMG-PES for the Option-B 6-DOF wrench experiment.

Pure Python, reads trace.csv/summary.json only -- no simulation re-run.
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


def plot_mission(mission: str, classical_dir: Path, pes_dir: Path, out_path: Path) -> None:
    c, n = load_trace(classical_dir), load_trace(pes_dir)
    c_s = json.loads((classical_dir/"summary.json").read_text())
    n_s = json.loads((pes_dir/"summary.json").read_text())

    fig, axes = plt.subplots(6, 1, figsize=(10, 15), sharex=True,
                              gridspec_kw={"height_ratios": [1.8, 1.8, 1.8, 1.6, 1.6, 1.6]})

    for i, ax_name in enumerate(["x", "y", "z"]):
        ax = axes[i]
        ax.plot(c["t"], c[f"{ax_name}_ref"], "k--", lw=1.1, label="reference")
        ax.plot(c["t"], c[ax_name], color="tab:blue", lw=1, alpha=0.85, label="classical")
        ax.plot(n["t"], n[ax_name], color="tab:red", lw=1, alpha=0.85, label="CMG-PES")
        ax.set_ylabel(f"{ax_name} (m)")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)
    axes[0].set_title(f"OUTPUTS -- 6DOF wrench, {mission}: position vs. reference", fontsize=10, loc="left", fontweight="bold")

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
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- attitude error", fontsize=10, loc="left", fontweight="bold")

    ax = axes[5]
    for ch, col in zip(["Fx", "Fy", "Fz", "tau_x", "tau_y", "tau_z"],
                        ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]):
        ax.plot(n["t"], n[ch], lw=0.6, color=col, label=ch)
    ax.set_ylabel("wrench\n(CMG-PES)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=6, ncol=6)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- applied 6-DOF wrench [Fx,Fy,Fz,tau_x,tau_y,tau_z]", fontsize=10, loc="left", fontweight="bold")

    pos_imp = 100*(c_s["pos_err_mean_m"]-n_s["pos_err_mean_m"])/max(1e-9, c_s["pos_err_mean_m"])
    att_imp = 100*(c_s["qerr_mean_rad"]-n_s["qerr_mean_rad"])/max(1e-9, c_s["qerr_mean_rad"])
    fig.suptitle(f"6-DOF wrench (Option B) -- mission: {mission}\n"
                 f"position improvement {pos_imp:+.2f}%   attitude improvement {att_imp:+.2f}%", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    out_dir = ROOT/"results"/"plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    for mission in ["hover3d", "waypoint_step", "circle_xy", "full6_stress"]:
        plot_mission(mission, ROOT/"results"/"optionB"/f"{mission}_classical",
                     ROOT/"results"/"optionB"/f"{mission}_pes", out_dir/f"{mission}_optionB.png")
