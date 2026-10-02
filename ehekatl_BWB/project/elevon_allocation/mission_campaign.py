"""Paired Monte Carlo campaign for the standard-vs-allocated mission."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from elevon_allocation.mission_comparison import simulate_architecture


METRICS = (
    "attitude_rmse_deg",
    "peak_attitude_error_deg",
    "post_fault_rmse_deg",
    "allocation_rmse_deg_s2",
    "surface_rms_command",
    "total_variation",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "results" / "mission_comparison")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    paired: dict[str, list[float]] = {metric: [] for metric in METRICS}
    for trial in range(args.trials):
        seed = args.seed + 1009 * trial
        standard, _ = simulate_architecture("thesis_grouped_acs", seed)
        allocated, _ = simulate_architecture("distributed_elevon_qp", seed)
        row: dict[str, object] = {"trial": trial, "seed": seed}
        for metric in METRICS:
            baseline = float(getattr(standard, metric))
            extension = float(getattr(allocated, metric))
            reduction = 100.0 * (baseline - extension) / baseline
            row[f"standard_{metric}"] = baseline
            row[f"allocated_{metric}"] = extension
            row[f"reduction_percent_{metric}"] = reduction
            paired[metric].append(reduction)
        rows.append(row)
        print(json.dumps({"completed_trial": trial + 1, "total": args.trials}), flush=True)

    with (args.output / "mission_monte_carlo.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary: list[dict[str, object]] = []
    for metric in METRICS:
        values = np.asarray(paired[metric])
        half_width = 1.96 * values.std(ddof=1) / np.sqrt(len(values)) if len(values) > 1 else 0.0
        summary.append({
            "metric": metric,
            "mean_reduction_percent": float(values.mean()),
            "ci95_low_percent": float(values.mean() - half_width),
            "ci95_high_percent": float(values.mean() + half_width),
            "trials": int(len(values)),
        })
    (args.output / "mission_monte_carlo_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    display = ["attitude_rmse_deg", "post_fault_rmse_deg", "allocation_rmse_deg_s2", "surface_rms_command", "total_variation"]
    labels = ["overall attitude\nRMSE", "post-fault attitude\nRMSE", "allocation\nRMSE", "surface RMS\ncommand", "total\nvariation"]
    means = np.array([next(item["mean_reduction_percent"] for item in summary if item["metric"] == metric) for metric in display])
    low = np.array([next(item["ci95_low_percent"] for item in summary if item["metric"] == metric) for metric in display])
    high = np.array([next(item["ci95_high_percent"] for item in summary if item["metric"] == metric) for metric in display])
    fig, ax = plt.subplots(figsize=(9.6, 4.8), constrained_layout=True)
    x = np.arange(len(display))
    ax.bar(x, means, color="#1f77b4", width=0.62)
    ax.errorbar(x, means, yerr=np.vstack((means - low, high - means)), fmt="none", ecolor="black", capsize=4, lw=1.1)
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("reduction relative to thesis grouped ACS [%]")
    ax.set_title(f"Distributed elevon allocation benefit across {args.trials} paired mission trials")
    ax.grid(axis="y", alpha=0.25)
    for position, value in zip(x, means):
        ax.text(position, value + (1.0 if value >= 0 else -1.0), f"{value:.1f}%", ha="center", va="bottom" if value >= 0 else "top")
    fig.savefig(args.output / "mission_monte_carlo_improvement.png", dpi=240)
    fig.savefig(args.output / "mission_monte_carlo_improvement.pdf")
    plt.close(fig)
    print(json.dumps({"summary": summary, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
