"""Plotting helpers for offline validation results."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .platforms import PlatformConfig
from .simulation import SimulationResult


def plot_comparison(
    config: PlatformConfig,
    baseline: SimulationResult,
    residual: SimulationResult,
    output_path: Path,
) -> None:
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    target_indices = list(config.target_state_indices)
    base_error = np.linalg.norm(baseline.states[:, target_indices], axis=1)
    residual_error = np.linalg.norm(residual.states[:, target_indices], axis=1)

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

    axes[0].plot(baseline.time, base_error, label="baseline", linewidth=1.4)
    axes[0].plot(residual.time, residual_error, label="HyperLIF residual", linewidth=1.4)
    axes[0].set_ylabel("tracked error norm")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend(loc="best")

    for i, label in enumerate(config.control_labels):
        axes[1].plot(baseline.time, baseline.commands[:, i], label=f"baseline {label}", linewidth=1.2)
        axes[1].plot(residual.time, residual.commands[:, i], label=f"residual {label}", linewidth=1.2, linestyle="--")
    axes[1].set_ylabel("command")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(loc="best", ncol=2)

    for i, label in enumerate(config.control_labels):
        axes[2].plot(residual.time, residual.residuals[:, i], label=f"{label} residual", linewidth=1.2)
    axes[2].set_ylabel("residual")
    axes[2].set_xlabel("time (s)")
    axes[2].grid(True, alpha=0.25)
    axes[2].legend(loc="best", ncol=2)

    fig.suptitle(f"{config.label}: classical baseline vs HyperLIF residual")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

