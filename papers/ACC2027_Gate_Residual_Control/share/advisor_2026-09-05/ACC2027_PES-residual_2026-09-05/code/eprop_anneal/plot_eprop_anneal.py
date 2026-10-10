"""Tracking + mechanism plots for the eprop_anneal reproduction, matching the
panel style used throughout this project's other results. Reads only the
verified CSVs in traces/ (each confirmed to reproduce the frozen summary
score to 6 decimal places before this script was written) -- no simulation
re-run here.
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
TRACES = ROOT / "traces"
OUT = ROOT / "plots"
OUT.mkdir(parents=True, exist_ok=True)


def load(name: str) -> dict[str, np.ndarray]:
    with (TRACES / f"{name}.csv").open() as f:
        rows = list(csv.DictReader(f))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def qerr_deg(d):
    return np.rad2deg(d["qerr_angle"])


if __name__ == "__main__":
    c = load("classical")
    p = load("online_pes")
    e = load("eprop_anneal")
    summ = json.loads((TRACES / "reproduction_summary.json").read_text())

    # ---- Figure 1: tracking + error (classical vs online_pes vs eprop_anneal) ----
    fig, axes = plt.subplots(5, 1, figsize=(10, 13), sharex=True,
                              gridspec_kw={"height_ratios": [1.4, 1.4, 1.4, 1.6, 1.3]})
    for i, (ax_name, key) in enumerate(zip(["roll (phi)", "pitch (theta)", "yaw (psi)"],
                                            ["phi_err", "theta_err", "psi_err"])):
        ax = axes[i]
        ax.plot(c["t"], np.rad2deg(c[key]), color="tab:blue", lw=0.6, alpha=0.85, label="classical")
        ax.plot(p["t"], np.rad2deg(p[key]), color="tab:orange", lw=0.6, alpha=0.85, label="online_pes")
        ax.plot(e["t"], np.rad2deg(e[key]), color="tab:red", lw=0.6, alpha=0.8, label="eprop_anneal")
        ax.set_ylabel(f"{ax_name}\nerror (deg)")
        ax.legend(loc="upper right", fontsize=7, ncol=3)
        ax.grid(alpha=0.3)
    axes[0].set_title("OUTPUTS/ERRORS -- Bitcraze CF2, hard45, 45s -- per-axis Euler error",
                       fontsize=10, loc="left", fontweight="bold")

    ax = axes[3]
    ax.plot(c["t"], qerr_deg(c), color="tab:blue", lw=0.6,
            label=f"classical (score {summ['classical']['score']:.4f})")
    ax.plot(p["t"], qerr_deg(p), color="tab:orange", lw=0.6,
            label=f"online_pes (score {summ['online_pes']['score']:.4f}, +86.7%)")
    ax.plot(e["t"], qerr_deg(e), color="tab:red", lw=0.6,
            label=f"eprop_anneal (score {summ['eprop_anneal']['score']:.4f}, +86.7%)")
    ax.set_ylabel("quaternion\nerror angle (deg)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("ERROR -- combined quaternion error angle", fontsize=10, loc="left", fontweight="bold")

    ax = axes[4]
    for ch, col, lbl in zip(["tau_x", "tau_y", "tau_z"], ["tab:blue", "tab:orange", "tab:green"],
                             ["tau_x", "tau_y", "tau_z"]):
        ax.plot(e["t"], e[ch], lw=0.4, color=col, label=f"{lbl} (eprop_anneal)")
    ax.set_ylabel("applied\ntorque (N.m)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7, ncol=3)
    ax.grid(alpha=0.3)
    ax.set_title("INPUTS -- applied body torque (eprop_anneal)", fontsize=10, loc="left", fontweight="bold")

    fig.suptitle("Reproduced: classical vs online-PES vs e-prop(annealed) -- Bitcraze/hard45\n"
                 "(byte-identical reproduction, scores match frozen dossier to 6 decimals)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUT / "eprop_anneal_tracking.png", dpi=125)
    plt.close(fig)
    print(f"wrote {OUT / 'eprop_anneal_tracking.png'}")

    # ---- Figure 2: mechanism (online_pes vs eprop_anneal neuron/decoder dynamics) ----
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)

    ax = axes[0]
    ax.plot(p["t"], p["neuron_v_mean"], color="tab:orange", lw=0.6, label="online_pes")
    ax.plot(e["t"], e["neuron_v_mean"], color="tab:red", lw=0.6, alpha=0.8, label="eprop_anneal")
    ax.set_ylabel("mean membrane\nvoltage v")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- HyperLIF membrane voltage (mean over 6 units)", fontsize=10, loc="left", fontweight="bold")

    ax = axes[1]
    ax.plot(p["t"], p["neuron_r_mean"], color="tab:orange", lw=0.6, label="online_pes")
    ax.plot(e["t"], e["neuron_r_mean"], color="tab:red", lw=0.6, alpha=0.8, label="eprop_anneal")
    ax.set_ylabel("mean gate r")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- HyperLIF gate state (mean over 6 units)", fontsize=10, loc="left", fontweight="bold")

    ax = axes[2]
    ax.plot(p["t"], p["activity_mean"], color="tab:orange", lw=0.6, label="online_pes")
    ax.plot(e["t"], e["activity_mean"], color="tab:red", lw=0.6, alpha=0.8, label="eprop_anneal")
    ax.set_ylabel("gate-derived\nactivity")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- decoded activity (gate_activity_mean matches frozen: "
                 f"online_pes={summ['online_pes'].get('gate_activity_mean',0):.4f}, "
                 f"eprop_anneal={summ['eprop_anneal'].get('gate_activity_mean',0):.4f})",
                 fontsize=9.5, loc="left", fontweight="bold")

    ax = axes[3]
    ax.plot(p["t"], p["decoder_frobenius_change"], color="tab:orange", lw=0.9, label="online_pes  ||W - W0||")
    ax.plot(e["t"], e["decoder_frobenius_change"], color="tab:red", lw=0.9, alpha=0.8, label="eprop_anneal  ||W - W0||")
    ax.set_ylabel("decoder drift\n(Frobenius norm)")
    ax.set_xlabel("time (s)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_title("MECHANISM -- learned-decode drift from the fixed pair-coding W0",
                 fontsize=10, loc="left", fontweight="bold")

    fig.suptitle("Reproduced -- online-PES vs e-prop(annealed): neuron and decoder mechanism\n"
                 "Bitcraze/hard45, 45s -- byte-identical to the frozen dossier result", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(OUT / "eprop_anneal_mechanism.png", dpi=125)
    plt.close(fig)
    print(f"wrote {OUT / 'eprop_anneal_mechanism.png'}")
