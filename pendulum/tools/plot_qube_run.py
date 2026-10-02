#!/usr/bin/env python3
"""
Post-run plot for a single run_simulink_balance.py CSV log — the same
angle/voltage view as --live-plot, but rendered AFTER the run instead of
during it. Use this instead of --live-plot for anything where control quality
matters (a live hardware demo): the control loop stays at full rate with zero
GUI overhead, and you still get the visual afterward.

Usage:
  python tools/plot_qube_run.py results/online/qube3_gate_cap020_60s_simulink_balance_<timestamp>.csv
  python tools/plot_qube_run.py <csv> --out my_plot.png   # save instead of / in addition to showing
  python tools/plot_qube_run.py <csv> --no-show           # save only, don't open a window
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot a single run_simulink_balance.py CSV log after the fact.")
    parser.add_argument("csv", type=Path, help="Path to a qube3_..._simulink_balance_<timestamp>.csv log.")
    parser.add_argument("--out", type=Path, default=None, help="Save the figure to this PNG path (default: alongside the CSV, same stem).")
    parser.add_argument("--no-show", action="store_true", help="Don't open a window — just save.")
    args = parser.parse_args()

    with args.csv.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f"No rows in {args.csv}")

    def col(name: str, default: str = "0.0") -> np.ndarray:
        return np.array([float(r.get(name, default) or default) for r in rows], dtype=float)

    t = col("time_s")
    alpha_deg = col("alpha_control_rad") * (180.0 / math.pi)
    theta_deg = col("theta_rad") * (180.0 / math.pi)
    voltage = col("command_voltage")
    residual = col("u_residual_applied") if "u_residual_applied" in rows[0] else None
    control_mode = [r.get("control_mode", "") for r in rows]
    residual_mode = rows[-1].get("residual_mode", "")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    title_bits = [args.csv.stem]
    if residual_mode:
        title_bits.append(f"residual_mode={residual_mode}")
    fig.suptitle(" | ".join(title_bits))

    ax1.plot(t, alpha_deg, label="alpha (upright err, deg)", color="tab:orange")
    ax1.plot(t, theta_deg, label="theta (arm, deg)", color="tab:blue", alpha=0.6)
    ax1.axhline(0.0, color="gray", linewidth=0.5)
    ax1.set_ylabel("deg")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.plot(t, voltage, label="command voltage (V)", color="tab:green")
    if residual is not None:
        ax2.plot(t, residual, label="applied residual (V)", color="tab:purple")
    ax2.set_ylabel("V")
    ax2.set_xlabel("time (s)")
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3)

    engaged_idx = [i for i, m in enumerate(control_mode) if m == "simulink_balance"]
    if engaged_idx:
        first_engage_t = t[engaged_idx[0]]
        for ax in (ax1, ax2):
            ax.axvline(first_engage_t, color="black", linestyle="--", linewidth=1, alpha=0.5)
        ax1.text(first_engage_t, ax1.get_ylim()[1], " engaged", va="top", fontsize=7)

    fig.tight_layout()

    out_path = args.out or args.csv.with_suffix(".png")
    fig.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")

    if not args.no_show:
        plt.show()


if __name__ == "__main__":
    main()
