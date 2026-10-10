"""Tracking + mechanism plots for every quad/mission combination produced by
reproduce_5missions.py. Two figures per (quad, mission), matching this
project's established convention. Reads only the CSVs already on disk.
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
TRACES = ROOT / "traces_5missions"
OUT = ROOT / "plots_5missions"
OUT.mkdir(parents=True, exist_ok=True)

QUADS = ["bitcraze_crazyflie_2", "skydio_x2"]
MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
QUAD_LABEL = {"bitcraze_crazyflie_2": "CF2", "skydio_x2": "X2"}


def load(quad, mission, name):
    p = TRACES / quad / mission / f"{name}.csv"
    with p.open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def plot_tracking(quad, mission, c, p, e, summ, out_path):
    fig, axes = plt.subplots(4, 1, figsize=(10, 10.5), sharex=True,
                              gridspec_kw={"height_ratios": [1.4, 1.4, 1.6, 1.3]})
    for i, (ax_name, key) in enumerate(zip(["roll (phi)", "pitch (theta)"], ["phi_err", "theta_err"])):
        ax = axes[i]
        ax.plot(c["t"], np.rad2deg(c[key]), color="tab:blue", lw=0.5, alpha=0.85, label="classical")
        ax.plot(p["t"], np.rad2deg(p[key]), color="tab:orange", lw=0.5, alpha=0.85, label="online_pes")
        ax.plot(e["t"], np.rad2deg(e[key]), color="tab:red", lw=0.5, alpha=0.8, label="eprop_anneal")
        ax.set_ylabel(f"{ax_name}\nerror (deg)")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)
    axes[0].set_title(f"OUTPUTS/ERRORS -- {QUAD_LABEL[quad]}, {mission}, 45s",
                       fontsize=10, loc="left", fontweight="bold")

    ax = axes[2]
    ax.plot(c["t"], np.rad2deg(c["qerr_angle"]), color="tab:blue", lw=0.5,
            label=f"classical (score {summ['classical']['score']:.4f})")
    ax.plot(p["t"], np.rad2deg(p["qerr_angle"]), color="tab:orange", lw=0.5,
            label=f"online_pes (score {summ['online_pes']['score']:.4f})")
    ax.plot(e["t"], np.rad2deg(e["qerr_angle"]), color="tab:red", lw=0.5,
            label=f"eprop_anneal (score {summ['eprop_anneal']['score']:.4f})")
    ax.set_ylabel("quaternion\nerror angle (deg)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- combined quaternion error angle", fontsize=10, loc="left", fontweight="bold")

    ax = axes[3]
    for ch, col in zip(["tau_x", "tau_y", "tau_z"], ["tab:blue", "tab:orange", "tab:green"]):
        ax.plot(e["t"], e[ch], lw=0.35, color=col, label=f"{ch} (eprop_anneal)")
    ax.set_ylabel("applied\ntorque (N.m)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- applied body torque (eprop_anneal)", fontsize=10, loc="left", fontweight="bold")

    imp_c = 100 * (summ["classical"]["score"] - summ["eprop_anneal"]["score"]) / max(1e-9, summ["classical"]["score"])
    fig.suptitle(f"{QUAD_LABEL[quad]} / {mission} -- classical vs online-PES vs e-prop(annealed)\n"
                 f"eprop_anneal vs classical: {imp_c:+.1f}%", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


def plot_mechanism(quad, mission, p, e, summ, out_path):
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    ax = axes[0]
    ax.plot(p["t"], p["neuron_v_mean"], color="tab:orange", lw=0.5, label="online_pes")
    ax.plot(e["t"], e["neuron_v_mean"], color="tab:red", lw=0.5, alpha=0.8, label="eprop_anneal")
    ax.set_ylabel("mean membrane\nvoltage v")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title(f"MECHANISM -- {QUAD_LABEL[quad]}/{mission}: HyperLIF membrane voltage",
                 fontsize=10, loc="left", fontweight="bold")

    ax = axes[1]
    ax.plot(p["t"], p["neuron_r_mean"], color="tab:orange", lw=0.5, label="online_pes")
    ax.plot(e["t"], e["neuron_r_mean"], color="tab:red", lw=0.5, alpha=0.8, label="eprop_anneal")
    ax.set_ylabel("mean gate r")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- HyperLIF gate state", fontsize=10, loc="left", fontweight="bold")

    ax = axes[2]
    ax.plot(p["t"], p["activity_mean"], color="tab:orange", lw=0.5, label="online_pes")
    ax.plot(e["t"], e["activity_mean"], color="tab:red", lw=0.5, alpha=0.8, label="eprop_anneal")
    ax.set_ylabel("decoded\nactivity")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title(f"MECHANISM -- decoded activity (gate_activity_mean: online_pes="
                 f"{summ['online_pes'].get('gate_activity_mean',0):.4f}, eprop_anneal="
                 f"{summ['eprop_anneal'].get('gate_activity_mean',0):.4f})", fontsize=9.5, loc="left", fontweight="bold")

    fig.suptitle(f"{QUAD_LABEL[quad]} / {mission} -- online-PES vs e-prop(annealed) mechanism", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(out_path, dpi=125)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    all_summ = json.loads((TRACES / "all_summaries.json").read_text())
    table_rows = []
    for quad in QUADS:
        for mission in MISSIONS:
            key = f"{quad}/{mission}"
            summ = all_summ[key]
            c = load(quad, mission, "classical")
            p = load(quad, mission, "online_pes")
            e = load(quad, mission, "eprop_anneal")
            tag = f"{QUAD_LABEL[quad]}_{mission}"
            plot_tracking(quad, mission, c, p, e, summ, OUT / f"{tag}_tracking.png")
            plot_mechanism(quad, mission, p, e, summ, OUT / f"{tag}_mechanism.png")
            imp = 100 * (summ["classical"]["score"] - summ["eprop_anneal"]["score"]) / max(1e-9, summ["classical"]["score"])
            table_rows.append((QUAD_LABEL[quad], mission, summ["classical"]["score"],
                                summ["online_pes"]["score"], summ["eprop_anneal"]["score"], imp))

    print("\n=== SUMMARY TABLE ===")
    print(f"{'platform':<8}{'mission':<10}{'classical':>12}{'online_pes':>12}{'eprop_anneal':>14}{'eprop vs classical':>20}")
    for row in table_rows:
        print(f"{row[0]:<8}{row[1]:<10}{row[2]:>12.6f}{row[3]:>12.6f}{row[4]:>14.6f}{row[5]:>19.2f}%")
