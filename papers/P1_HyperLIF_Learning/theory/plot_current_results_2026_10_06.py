"""Small, source-linked figures for the 2026-10-06 HyperLIF status."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent / "results"
STAMP = "2026-10-06"


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def style() -> None:
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def readout_figure() -> None:
    data = rows(f"hh_hyperlif_tiny_pes_{STAMP}.csv")
    models = [
        ("hh_rest", "HH, resting"),
        ("hh_tonic", "HH, tonic"),
        ("hyper_g0", "HyperLIF, non-latching"),
        ("leaky_adaptive", "Leaky adaptive control"),
    ]
    features = [
        ("voltage", "membrane", "#7B8C98"),
        ("gate", "gate", "#1C78A7"),
        ("voltage_gate", "membrane + gate", "#E69F00"),
        ("voltage_conductance", "membrane + conductance", "#B55B8F"),
        ("gate_lp20", "gate + 20 ms filter", "#12976D"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.2), constrained_layout=True)
    for ax, (model, title) in zip(axes.flat, models):
        subset = {r["readout"]: r for r in data if r["model"] == model and r["delay_s"] == "0.020"}
        present = [(label, float(subset[key]["pes_test_rmse"]), color) for key, label, color in features if key in subset]
        x = np.arange(len(present))
        ax.bar(x, [value for _, value, _ in present], color=[color for _, _, color in present], width=0.72)
        ax.set_xticks(x, [label.replace(" + ", "\n+ ") for label, _, _ in present])
        ax.tick_params(axis="x", labelsize=8)
        ax.set_title(title)
        ax.set_ylabel("held-out PES RMSE")
        ax.grid(axis="y", alpha=0.2)
        ax.set_axisbelow(True)
        top = max(value for _, value, _ in present)
        ax.set_ylim(0, 1.26 * top)
        for xi, (_, value, _) in zip(x, present):
            ax.text(xi, value + top * 0.02, f"{value:.3f}", ha="center", va="bottom", fontsize=8)
    fig.suptitle("Readout choice changes what a one-neuron learner can see", fontsize=15, fontweight="bold")
    fig.supxlabel("20 ms delayed target; same PES study within each model. Scales differ by panel.", fontsize=9)
    out = ROOT / f"current_readout_results_{STAMP}.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(out)


def learning_figure() -> None:
    external = rows(f"coupled_external_delay_{STAMP}.csv")
    combos = [
        ("hyper_g0", "voltage_gate", "HyperLIF γ=0\nmembrane + gate"),
        ("hyper_g2", "voltage_gate", "HyperLIF γ=2\nmembrane + gate"),
        ("leaky", "voltage_gate", "Leaky control\nmembrane + gate"),
    ]
    methods = [("baseline", "none", "baseline", "#7B8C98"), ("selected", "exact", "exact", "#1C78A7"), ("selected", "local", "local", "#E69F00")]
    horizon = rows(f"hh_coupled_horizon_audit_{STAMP}.csv")
    gradient = sorted(
        [r for r in horizon if r["row"] == "gradient" and r["model"] == "hh_tonic"],
        key=lambda r: float(r["horizon_ms"]),
    )
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.7), constrained_layout=True)
    for i, (model, readout, label) in enumerate(combos):
        group = [r for r in external if r["model"] == model and r["readout"] == readout]
        base = float(next(r for r in group if r["row"] == "baseline")["test_rmse"])
        for j, (kind, method, method_label, color) in enumerate(methods):
            hit = next(r for r in group if r["row"] == kind and r["method"] == method)
            ratio = float(hit["test_rmse"]) / base
            xpos = i + (j - 1) * 0.23
            ax1.bar(xpos, ratio, width=0.21, color=color, label=method_label if i == 0 else None)
            ax1.text(xpos, ratio + 0.07, f"{ratio:.2f}×", ha="center", va="bottom", fontsize=8)
    ax1.axhline(1, color="#444", linewidth=0.8)
    ax1.set_xticks(range(len(combos)), [x[2] for x in combos], fontsize=9)
    ax1.set_ylim(0, 5.9)
    ax1.set_ylabel("held-out RMSE / baseline RMSE")
    ax1.set_title("Independent delayed target: local update can cross basins")
    ax1.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)
    ax1.grid(axis="y", alpha=0.2)
    ax1.set_axisbelow(True)

    x = np.array([float(r["horizon_ms"]) for r in gradient])
    exact = np.array([float(r["exact_gradient_at_zero"]) for r in gradient])
    local = np.array([float(r["local_gradient_at_zero"]) for r in gradient])
    ax2.plot(x, exact, "o-", color="#1C78A7", linewidth=2, label="exact sensitivity")
    ax2.plot(x, local, "s--", color="#E69F00", linewidth=1.5, label="local sensitivity")
    ax2.axhline(0, color="#444", linewidth=0.8)
    ax2.set_xscale("log")
    ax2.set_xticks(x, [f"{int(value)}" for value in x])
    ax2.set_xlabel("training horizon (ms)")
    ax2.set_ylabel("loss gradient at θ = 0")
    ax2.set_title("HH tonic: the full-horizon gradient reverses sign")
    ax2.legend(frameon=False, fontsize=8, loc="upper left")
    ax2.grid(alpha=0.2)
    ax2.set_axisbelow(True)
    fig.suptitle("Learning depends on the target, horizon, and gate regime", fontsize=15, fontweight="bold")
    out = ROOT / f"current_learning_limits_{STAMP}.png"
    fig.savefig(out, dpi=180)
    plt.close(fig)
    print(out)


if __name__ == "__main__":
    style()
    readout_figure()
    learning_figure()
