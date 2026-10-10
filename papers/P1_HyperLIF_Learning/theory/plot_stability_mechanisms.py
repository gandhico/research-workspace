"""Plot constant-current stability and sampled event visibility (small arrays)."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def branch(q: np.ndarray, adaptive: bool):
    r = 1 / (1 + np.exp(-q))
    theta_voltage = 1 - 0.2 * r + q / 100
    g0, g1 = (20, 80) if adaptive else (100, 0)
    denominator = 1 - 0.02 * g1 * r**2 * theta_voltage
    current = theta_voltage * (1 + 0.02 * g0 * r**2) / denominator
    conductance = (g0 + g1 * current) * r**2
    rate = 50 + conductance
    voltage = current / (1 + 0.02 * conductance)
    voltage_prime = -2 * 0.02 * (g0 + g1 * current) * r * current / (
        1 + 0.02 * conductance
    ) ** 2
    hprime = 100 * r * (1 - r) * (voltage_prime + 0.2) - 1
    determinant = -rate * hprime / 0.002
    trace = -rate + (20 * r * (1 - r) - 1) / 0.002
    valid = (current >= 0.7) & (current <= 20) & (denominator > 0)
    stable = (trace < 0) & (determinant > 0)
    return current, voltage, valid, stable


def plot_segments(ax, current, voltage, valid, stable, color):
    ax.plot(
        np.where(valid & stable, current, np.nan),
        np.where(valid & stable, voltage, np.nan),
        color=color,
        linewidth=2.3,
        label="locally stable equilibrium",
    )
    ax.plot(
        np.where(valid & ~stable, current, np.nan),
        np.where(valid & ~stable, voltage, np.nan),
        color=color,
        linewidth=2.0,
        linestyle="--",
        label="linearly unstable equilibrium",
    )
    ax.axhline(1, color="#7a7a7a", linewidth=1, linestyle=":")
    ax.set_xlim(0.7, 20)
    ax.set_xlabel("constant current $I$")
    ax.set_ylabel("equilibrium voltage $v^*$")
    ax.grid(alpha=0.2)


def main():
    fixed_q = np.concatenate([np.linspace(-15, 6, 1800), np.linspace(6, 700, 2400)])
    adaptive_q = np.linspace(-15, 2.1, 2500)
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.4), constrained_layout=True)
    blue, green = "#2457a7", "#178268"

    plot_segments(axes[0], *branch(fixed_q, False), blue)
    axes[0].axvline(0.9670795963, color="black", linewidth=0.8, alpha=0.5)
    axes[0].axvline(2.2976216645, color="black", linewidth=0.8, alpha=0.5)
    axes[0].set_ylim(0.6, 6.9)
    axes[0].set_title("Canonical fixed HyperLIF")
    axes[0].legend(frameon=False, fontsize=7.6, loc="upper left")

    plot_segments(axes[1], *branch(adaptive_q, True), green)
    axes[1].axvline(0.9669056279, color="black", linewidth=0.8, alpha=0.5)
    axes[1].axvline(15.77602938, color="black", linewidth=0.8, alpha=0.5)
    axes[1].set_ylim(0.6, 1.15)
    axes[1].set_title("Canonical adaptive HyperLIF")
    axes[1].annotate(
        "stable subthreshold\nbranch at high drive",
        xy=(17, 0.85),
        xytext=(7.2, 0.72),
        arrowprops={"arrowstyle": "->", "color": green},
        fontsize=8,
        color=green,
    )

    with (RESULTS / "canonical_high_drive_probe_2026-10-06.csv").open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        rows = [r for r in csv.DictReader(stream) if float(r["dt"]) == 1e-4]
    for family, color in (("fixed", blue), ("adaptive", green)):
        subset = sorted((r for r in rows if r["family"] == family), key=lambda r: float(r["current"]))
        axes[2].scatter(
            [float(r["current"]) for r in subset],
            [int(r["last_second_upcrossings"]) for r in subset],
            marker="o",
            s=27,
            color=color,
            label=family,
        )
    axes[2].set_xlim(0.7, 20)
    axes[2].set_ylim(bottom=0)
    axes[2].set_xlabel("constant current $I$")
    axes[2].set_ylabel("upward crossings in final second")
    axes[2].set_title("From-rest trajectories at sampled currents")
    axes[2].grid(alpha=0.2)
    axes[2].legend(frameon=False, fontsize=8)
    fig.suptitle("Equilibrium stability and event visibility are different questions", fontsize=13)
    output = RESULTS / "hyperlif_stability_mechanisms_2026-10-06.png"
    fig.savefig(output, dpi=170, facecolor="white")
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
