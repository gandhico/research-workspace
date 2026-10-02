"""Regenerate comparison figures from the latest saved benchmark run."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def _read_csv(path: Path) -> dict[str, np.ndarray]:
    columns: dict[str, list[float]] = {}
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, value in row.items():
                try:
                    columns.setdefault(key, []).append(float(value))
                except ValueError:
                    pass
    return {key: np.asarray(value, dtype=float) for key, value in columns.items()}


def plot_latest(results_dir: Path) -> Path:
    import matplotlib.pyplot as plt

    summaries = sorted(results_dir.glob("*/summary.json"))
    if not summaries:
        raise FileNotFoundError(f"No summary.json files found below {results_dir}")

    summary_path = summaries[-1]
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    baseline = _read_csv(Path(payload["artifacts"]["baseline_csv"]))
    residual = _read_csv(Path(payload["artifacts"]["residual_csv"]))

    state_labels = payload["state_labels"]
    control_labels = payload["control_labels"]
    target_indices = payload["target_state_indices"]
    target_cols = [f"state_{state_labels[i]}" for i in target_indices]
    control_cols = [f"command_{label}" for label in control_labels]
    residual_cols = [f"residual_{label}" for label in control_labels]

    base_error = np.sqrt(sum(baseline[col] ** 2 for col in target_cols))
    residual_error = np.sqrt(sum(residual[col] ** 2 for col in target_cols))

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    axes[0].plot(baseline["time_s"], base_error, label="baseline")
    axes[0].plot(residual["time_s"], residual_error, label="HyperLIF residual")
    axes[0].set_ylabel("tracked error norm")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="best")

    for col in control_cols:
        axes[1].plot(baseline["time_s"], baseline[col], label=f"baseline {col.replace('command_', '')}")
        axes[1].plot(residual["time_s"], residual[col], linestyle="--", label=f"residual {col.replace('command_', '')}")
    axes[1].set_ylabel("command")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(loc="best", ncol=2)

    for col in residual_cols:
        axes[2].plot(residual["time_s"], residual[col], label=col.replace("residual_", ""))
    axes[2].set_ylabel("residual")
    axes[2].set_xlabel("time (s)")
    axes[2].grid(True, alpha=0.25)
    axes[2].legend(loc="best", ncol=2)

    fig.suptitle(f"{payload['label']}: latest baseline vs HyperLIF residual")
    figure_dir = summary_path.parent / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    figure_path = figure_dir / f"{payload['platform']}_latest_replot.png"
    fig.tight_layout()
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    return figure_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate the latest comparison figure from saved CSV/JSON results.")
    parser.add_argument("--results-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    figure_path = plot_latest(args.results_dir)
    print(f"Saved figure: {figure_path}")


if __name__ == "__main__":
    main()

