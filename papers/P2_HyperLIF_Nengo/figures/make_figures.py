"""Generate every publication figure from the canonical experiment CSVs.

This script never runs a simulation. It reads the CSV files written by the
``experiments`` scripts and renders each figure as a 300-dpi PNG plus a vector
PDF, into both ``results/figures`` and ``paper/figures``. Each figure function is
documented with the CSV it consumes and the manuscript label it supports.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import matplotlib.pyplot as plt  # noqa: E402

from visualization.plotting import configure, style_for  # noqa: E402

CSV_DIR = PROJECT_ROOT / "results" / "csv"
OUT_DIRS = [PROJECT_ROOT / "results" / "figures", PROJECT_ROOT / "paper" / "figures"]

V_THRESH = 1.0
DB_ONSET = 2.4  # analytical fixed-gain DB onset (see 03_db_analysis.csv)


def load_csv(name: str) -> dict[str, np.ndarray]:
    """Load a CSV into a dict of columns (float arrays where possible)."""

    path = CSV_DIR / name
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        cols: list[list[str]] = [[] for _ in header]
        for row in reader:
            for i, val in enumerate(row):
                cols[i].append(val)
    out: dict[str, np.ndarray] = {}
    for name_i, col in zip(header, cols):
        try:
            out[name_i] = np.array([float(x) for x in col])
        except ValueError:
            out[name_i] = np.array(col, dtype=object)
    return out


def _save_both(name: str) -> None:
    """Save current figure to all output dirs as PNG + PDF, then close."""

    primary = OUT_DIRS[0] / f"{name}.png"
    primary.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(primary, dpi=300)
    plt.savefig(primary.with_suffix(".pdf"))
    for d in OUT_DIRS[1:]:
        d.mkdir(parents=True, exist_ok=True)
        plt.savefig(d / f"{name}.png", dpi=300)
        plt.savefig(d / f"{name}.pdf")
    plt.close()


# --------------------------------------------------------------------------- #
# Figure: step response (LIF vs HyperLIF) -- from 01_lif_vs_hyperlif.csv
# --------------------------------------------------------------------------- #
def fig_step() -> None:
    d = load_csv("01_lif_vs_hyperlif.csv")
    t = d["t"]
    fig, ax = plt.subplots(4, 1, sharex=True, figsize=(7.0, 6.4))

    ax[0].plot(t, d["input_current"], color="black")
    ax[0].set_ylabel("Input $J$")
    ax[0].set_title("Step response: hard-reset LIF vs continuous-reset HyperLIF")

    s_lif, s_hyp = style_for("LIF"), style_for("HyperLIF")
    ax[1].plot(t, d["lif_voltage"], label="LIF", color=s_lif["color"])
    ax[1].plot(t, d["hyperlif_voltage"], label="HyperLIF", color=s_hyp["color"])
    ax[1].axhline(V_THRESH, color="0.4", lw=0.8, ls="--", label="$v_{thresh}$")
    ax[1].set_ylabel("Voltage $v$")
    ax[1].legend(loc="upper right", ncol=3)

    ax[2].plot(t, d["hyperlif_reset_gate"], color=style_for("Gate")["color"])
    ax[2].set_ylabel("Reset gate $r$")
    ax[2].set_ylim(-0.05, 1.05)

    lif_ev = (d["lif_events"] > 0).astype(float)
    hyp_ev = (d["hyperlif_events"] > 0).astype(float)
    ax[3].vlines(t[lif_ev > 0], 0.55, 1.0, color=s_lif["color"], label="LIF")
    ax[3].vlines(t[hyp_ev > 0], 0.05, 0.5, color=s_hyp["color"], label="HyperLIF")
    ax[3].set_ylabel("Events")
    ax[3].set_yticks([])
    ax[3].set_ylim(0, 1.05)
    ax[3].set_xlabel("Time (s)")
    ax[3].legend(loc="upper right", ncol=2)
    _save_both("fig_step")


# --------------------------------------------------------------------------- #
# Figure: stress response (HyperLIF vs Adaptive) -- from 02_hyperlif_vs_adaptive
# --------------------------------------------------------------------------- #
def fig_stress() -> None:
    d = load_csv("02_hyperlif_vs_adaptive.csv")
    t = d["t"]
    s_hyp, s_ad = style_for("HyperLIF"), style_for("Adaptive HyperLIF")
    fig, ax = plt.subplots(5, 1, sharex=True, figsize=(7.0, 7.6))

    ax[0].plot(t, d["input_current"], color="black")
    ax[0].set_ylabel("Input $J$")
    ax[0].set_title("Stress current: fixed vs adaptive reset conductance")

    ax[1].plot(t, d["hyperlif_voltage"], label="HyperLIF", color=s_hyp["color"])
    ax[1].plot(t, d["adaptive_voltage"], label="Adaptive", color=s_ad["color"])
    ax[1].axhline(V_THRESH, color="0.4", lw=0.8, ls="--")
    ax[1].set_ylabel("Voltage $v$")
    ax[1].legend(loc="upper right", ncol=2)

    ax[2].plot(t, d["hyperlif_reset_gate"], label="HyperLIF", color=s_hyp["color"])
    ax[2].plot(t, d["adaptive_reset_gate"], label="Adaptive", color=s_ad["color"])
    ax[2].set_ylabel("Reset gate $r$")
    ax[2].set_ylim(-0.05, 1.05)

    ax[3].plot(t, d["hyperlif_conductance"], label="Fixed $G_b r^2$", color=s_hyp["color"])
    ax[3].plot(t, d["adaptive_conductance"], label="Adaptive $G(r,J)$", color=s_ad["color"])
    ax[3].set_ylabel("Reset cond.")
    ax[3].legend(loc="upper right", ncol=2)

    ax[4].plot(t, d["adaptive_dynamic_gain"], color=s_ad["color"])
    ax[4].set_ylabel("$G_{dyn}$")
    ax[4].set_xlabel("Time (s)")
    _save_both("fig_stress")


# --------------------------------------------------------------------------- #
# Figure: f-I curves and depolarization block -- from 03_current_sweep.csv
# --------------------------------------------------------------------------- #
def fig_fi() -> None:
    d = load_csv("03_current_sweep.csv")
    model = d["model"].astype(str)

    def sel(m: str, col: str) -> tuple[np.ndarray, np.ndarray]:
        mask = model == m
        order = np.argsort(d["input_current"][mask])
        return d["input_current"][mask][order], d[col][mask][order]

    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(7.0, 7.0))
    models = ["LIF", "HyperLIF", "Adaptive HyperLIF"]

    for m in models:
        s = style_for(m)
        x, y = sel(m, "event_rate_hz")
        ax[0].plot(x, y, color=s["color"], marker=s["marker"], ms=3.5, lw=1.3, label=m)
    ax[0].axvline(DB_ONSET, color="0.5", ls=":", lw=1.0)
    ax[0].text(DB_ONSET - 0.12, ax[0].get_ylim()[1] * 0.40, "fixed-gain DB onset",
               rotation=90, va="center", ha="right", fontsize=7.5, color="0.35")
    ax[0].set_ylabel("Firing rate (Hz)")
    ax[0].set_title("Frequency-current response and depolarization block")
    ax[0].legend(loc="upper left")

    for m in models:
        s = style_for(m)
        x, y = sel(m, "voltage_mean")
        ax[1].plot(x, y, color=s["color"], marker=s["marker"], ms=3.5, lw=1.3, label=f"{m} mean")
    ax[1].axhline(V_THRESH, color="0.4", lw=0.8, ls="--")
    ax[1].plot([], [], color="0.4", ls="--", label="$v_{thresh}$")
    ax[1].set_ylabel("Mean voltage")
    ax[1].legend(loc="upper left", fontsize=7.5)

    for m in ["HyperLIF", "Adaptive HyperLIF"]:
        s = style_for(m)
        x, y = sel(m, "conductance_mean")
        ax[2].plot(x, y, color=s["color"], marker=s["marker"], ms=3.5, lw=1.3, label=m)
    ax[2].set_ylabel("Mean reset cond.")
    ax[2].set_xlabel("Constant input current $J$")
    ax[2].legend(loc="upper left")
    _save_both("fig_fi")


# --------------------------------------------------------------------------- #
# Figure: depolarization-block latch -- from 04_depolarization_block.csv
# --------------------------------------------------------------------------- #
def fig_db() -> None:
    d = load_csv("04_depolarization_block.csv")
    t = d["t"]
    s_hyp, s_ad = style_for("HyperLIF"), style_for("Adaptive HyperLIF")
    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(7.0, 6.0))

    ax[0].plot(t, d["hyperlif_voltage"], label="HyperLIF (latches)", color=s_hyp["color"])
    ax[0].plot(t, d["adaptive_voltage"], label="Adaptive (spikes)", color=s_ad["color"])
    ax[0].axhline(V_THRESH, color="0.4", lw=0.8, ls="--", label="$v_{thresh}$")
    ax[0].set_ylabel("Voltage $v$")
    ax[0].set_title(f"Sustained drive $J=3.3$ (above DB onset $\\approx{DB_ONSET}$)")
    ax[0].legend(loc="lower right", ncol=3, fontsize=7.5)

    ax[1].plot(t, d["hyperlif_reset_gate"], label="HyperLIF", color=s_hyp["color"])
    ax[1].plot(t, d["adaptive_reset_gate"], label="Adaptive", color=s_ad["color"])
    ax[1].set_ylabel("Reset gate $r$")
    ax[1].set_ylim(-0.05, 1.05)
    ax[1].legend(loc="center right", ncol=2)

    ax[2].plot(t, d["hyperlif_conductance"], label="HyperLIF $G_b r^2$", color=s_hyp["color"])
    ax[2].plot(t, d["adaptive_conductance"], label="Adaptive $G(r,J)$", color=s_ad["color"])
    ax[2].set_ylabel("Reset cond.")
    ax[2].set_xlabel("Time (s)")
    ax[2].legend(loc="center right", ncol=2)
    _save_both("fig_db")


# --------------------------------------------------------------------------- #
# Figure: integration accuracy + stability -- from 06_*.csv
# --------------------------------------------------------------------------- #
def fig_integration() -> None:
    acc = load_csv("06_integration_accuracy.csv")
    stab = load_csv("06_stability.csv")
    method = acc["method"].astype(str)

    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.4))

    for m, color, mk in [("julia", "#1f77b4", "o"), ("stable", "#d62728", "s")]:
        mask = method == m
        order = np.argsort(acc["dt"][mask])
        x = acc["dt"][mask][order]
        y = acc["voltage_rmse"][mask][order]
        label = "explicit Euler (julia)" if m == "julia" else "exp. Euler (stable)"
        ax[0].loglog(x, y, marker=mk, color=color, label=label, ms=4)
    # first-order reference slope
    xr = np.array([acc["dt"].min(), acc["dt"].max()])
    y0 = acc["voltage_rmse"].min()
    ax[0].loglog(xr, y0 * (xr / xr.min()), color="0.6", ls=":", lw=1.0, label="$O(\\Delta t)$")
    ax[0].set_xlabel("Time step $\\Delta t$ (s)")
    ax[0].set_ylabel("Voltage RMSE vs RK4 reference")
    ax[0].set_title("(a) Convergence")
    ax[0].legend(fontsize=7.5)

    order = np.argsort(stab["lambda_dt_at_full_gate"])
    x = stab["lambda_dt_at_full_gate"][order]
    ax[1].plot(x, stab["julia_max_abs_voltage"][order], marker="o", color="#1f77b4",
               label="explicit Euler (julia)")
    ax[1].plot(x, stab["stable_max_abs_voltage"][order], marker="s", color="#d62728",
               label="exp. Euler (stable)")
    ax[1].axhline(4.0 / 3.0, color="0.4", ls="--", lw=0.9, label="true $v^*=J/3$")
    ax[1].axvline(2.0, color="0.6", ls=":", lw=1.0, label="$\\lambda\\Delta t=2$ (explicit limit)")
    ax[1].set_xlabel("$\\lambda\\,\\Delta t$ (gate open, $J=4$)")
    ax[1].set_ylabel("max $|v|$ over run")
    ax[1].set_title("(b) Large-step stability")
    ax[1].legend(fontsize=7.5, loc="upper left")
    _save_both("fig_integration")


# --------------------------------------------------------------------------- #
# Figure: Python vs Nengo parity -- from 07_python_vs_nengo.csv
# --------------------------------------------------------------------------- #
def fig_parity() -> None:
    d = load_csv("07_python_vs_nengo.csv")
    t = d["t"]
    ref = style_for("Reference")
    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(7.0, 6.0))

    ax[0].plot(t, d["python_hyper_voltage"], color=style_for("HyperLIF")["color"],
               label="Python (stable)", lw=2.2)
    ax[0].plot(t, d["nengo_hyper_voltage"], color="black", ls="--", lw=1.0, label="Nengo")
    ax[0].set_ylabel("HyperLIF $v$")
    ax[0].set_title("Standalone stable stepping vs Nengo port (RMSE $=0$)")
    ax[0].legend(loc="upper right", ncol=2)

    ax[1].plot(t, d["python_adaptive_voltage"], color=style_for("Adaptive HyperLIF")["color"],
               label="Python (stable)", lw=2.2)
    ax[1].plot(t, d["nengo_adaptive_voltage"], color="black", ls="--", lw=1.0, label="Nengo")
    ax[1].set_ylabel("Adaptive $v$")
    ax[1].legend(loc="upper right", ncol=2)

    dv_h = d["python_hyper_voltage"] - d["nengo_hyper_voltage"]
    dv_a = d["python_adaptive_voltage"] - d["nengo_adaptive_voltage"]
    ax[2].plot(t, dv_h, color=style_for("HyperLIF")["color"], label="HyperLIF $\\Delta v$")
    ax[2].plot(t, dv_a, color=style_for("Adaptive HyperLIF")["color"], label="Adaptive $\\Delta v$")
    ax[2].set_ylabel("Python $-$ Nengo")
    ax[2].set_ylim(-1e-15, 1e-15)
    ax[2].ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax[2].set_xlabel("Time (s)")
    ax[2].legend(loc="upper right", ncol=2)
    _save_both("fig_parity")


# --------------------------------------------------------------------------- #
# Figure: gate-state decoding -- from 05_gate_state_decoding.csv
# --------------------------------------------------------------------------- #
def fig_decode() -> None:
    d = load_csv("05_gate_state_decoding.csv")
    t = d["t"]
    fig, ax = plt.subplots(4, 1, sharex=True, figsize=(7.0, 7.2))

    ax[0].plot(t, d["input_current"], color="black", label="Input current")
    ax[0].plot(t, d["decoded_current_from_voltage"], color=style_for("LIF")["color"],
               lw=1.1, alpha=0.9, label="Decoded from voltage")
    ax[0].plot(t, d["decoded_current_from_events"], color=style_for("HyperLIF")["color"],
               lw=1.1, alpha=0.9, label="Decoded from events")
    ax[0].set_ylabel("Current")
    ax[0].set_title("Decoding input current and readiness from internal signals")
    ax[0].legend(loc="upper right", ncol=3, fontsize=7.5)

    ax[1].plot(t, d["voltage"], color=style_for("LIF")["color"])
    ax[1].axhline(V_THRESH, color="0.4", lw=0.8, ls="--")
    ax[1].set_ylabel("Voltage $v$")

    ax[2].plot(t, d["filtered_events"], color=style_for("HyperLIF")["color"])
    ax[2].set_ylabel("Filt. events")

    ax[3].plot(t, d["readiness_target"], color="black", label="Readiness target")
    ax[3].plot(t, d["reset_gate"], color=style_for("Gate")["color"], lw=0.8, alpha=0.8,
               label="Gate $r(t)$")
    ax[3].plot(t, d["decoded_readiness_from_gate"], color=style_for("Adaptive HyperLIF")["color"],
               lw=1.3, label="Decoded readiness")
    ax[3].set_ylabel("Readiness")
    ax[3].set_xlabel("Time (s)")
    ax[3].set_ylim(-0.05, 1.15)
    ax[3].legend(loc="upper right", ncol=3, fontsize=7.5)
    _save_both("fig_decode")


def main() -> None:
    configure()
    fig_step()
    fig_stress()
    fig_fi()
    fig_db()
    fig_integration()
    fig_parity()
    fig_decode()
    print("Wrote figures to:")
    for d in OUT_DIRS:
        print(f"  {d}")


if __name__ == "__main__":
    main()
