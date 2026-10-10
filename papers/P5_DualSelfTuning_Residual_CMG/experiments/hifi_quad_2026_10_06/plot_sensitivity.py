"""Compact scientific figure for the declared synthetic-lag screen."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "l1_sensitivity_hover_init_2026-10-06"


def main():
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.2), sharex=True, constrained_layout=True)
    styles = {
        ("base", 0.0): ("#174ea6", "-"),
        ("base", 0.03): ("#174ea6", "--"),
        ("dual", 0.0): ("#c5221f", "-"),
        ("dual", 0.03): ("#c5221f", "--"),
    }
    for col, platform in enumerate(("cf2-rotor", "x2")):
        for (arm, tau), (color, style) in styles.items():
            path = RESULTS / platform / arm / f"tau_{tau:.3f}" / "trace.csv"
            with path.open(newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            t = [float(r["t"]) for r in rows]
            label = f"{arm}, τ={tau * 1000:.0f} ms"
            axes[0, col].plot(t, [float(r["qerr"]) for r in rows], color=color,
                              ls=style, lw=1.25, label=label)
            axes[1, col].plot(t, [float(r["z"]) for r in rows], color=color,
                              ls=style, lw=1.25)
        axes[0, col].set_title("CF2 design (P5 1.5× authority)" if col == 0 else "X2 design")
        axes[0, col].set_ylabel("Quaternion error (rad)")
        axes[1, col].set_ylabel("Height (m)")
        axes[1, col].set_xlabel("Time (s)")
        axes[0, col].grid(alpha=0.2)
        axes[1, col].grid(alpha=0.2)
        axes[1, col].set_xlim(0, 8)
    axes[0, 0].legend(loc="upper left", fontsize=8, ncol=2)
    fig.suptitle("Hardstep LQR: ideal motors vs synthetic 30 ms rotor lag\n"
                 "Hover-initialized actuators; 20 Hz displayed trace; not physical calibration", fontsize=11)
    out = RESULTS / "hardstep_lag_screen.png"
    fig.savefig(out, dpi=150)
    print(out)


if __name__ == "__main__":
    main()
