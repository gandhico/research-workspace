"""Metrics for baseline vs HyperLIF residual comparisons."""

from __future__ import annotations

import numpy as np

from .platforms import PlatformConfig
from .simulation import SimulationResult


def _error_norm(config: PlatformConfig, result: SimulationResult) -> np.ndarray:
    tracked = result.states[:, list(config.target_state_indices)]
    return np.linalg.norm(tracked, axis=1)


def summarize(config: PlatformConfig, result: SimulationResult) -> dict[str, float | str]:
    err = _error_norm(config, result)
    command_abs = np.abs(result.commands)
    residual_abs = np.abs(result.residuals)
    limit = np.asarray(config.control_limits, dtype=float)
    saturation = np.any(command_abs >= 0.98 * limit.reshape(1, -1), axis=1)

    return {
        "platform": config.key,
        "mode": result.mode,
        "duration_s": float(result.time[-1] - result.time[0]),
        "samples": int(result.time.size),
        "dt_s": float(config.dt),
        "mean_error_norm": float(np.mean(err)),
        "rms_error_norm": float(np.sqrt(np.mean(err**2))),
        "max_error_norm": float(np.max(err)),
        "final_error_norm": float(err[-1]),
        "mean_abs_command": float(np.mean(command_abs)),
        "max_abs_command": float(np.max(command_abs)),
        "saturation_fraction": float(np.mean(saturation)),
        "mean_abs_residual": float(np.mean(residual_abs)),
        "max_abs_residual": float(np.max(residual_abs)),
        "mean_gate": float(np.mean(result.gates)),
        "max_gate": float(np.max(result.gates)),
    }


def compare(baseline: dict[str, float | str], residual: dict[str, float | str]) -> dict[str, float | str]:
    base_rms = float(baseline["rms_error_norm"])
    res_rms = float(residual["rms_error_norm"])
    base_mean = float(baseline["mean_error_norm"])
    res_mean = float(residual["mean_error_norm"])
    base_effort = float(baseline["mean_abs_command"])
    res_effort = float(residual["mean_abs_command"])

    return {
        "platform": baseline["platform"],
        "baseline_mode": baseline["mode"],
        "residual_mode": residual["mode"],
        "mean_error_delta_percent": 100.0 * (res_mean - base_mean) / max(base_mean, 1e-12),
        "rms_error_delta_percent": 100.0 * (res_rms - base_rms) / max(base_rms, 1e-12),
        "control_effort_delta_percent": 100.0 * (res_effort - base_effort) / max(base_effort, 1e-12),
        "baseline_rms_error_norm": base_rms,
        "residual_rms_error_norm": res_rms,
        "baseline_mean_abs_command": base_effort,
        "residual_mean_abs_command": res_effort,
    }

