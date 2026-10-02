"""CSV and JSON output helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .platforms import PlatformConfig
from .simulation import SimulationResult


def write_csv(path: Path, config: PlatformConfig, result: SimulationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    state_cols = [f"state_{name}" for name in config.state_labels]
    control_cols = [f"command_{name}" for name in config.control_labels]
    baseline_cols = [f"baseline_{name}" for name in config.control_labels]
    residual_cols = [f"residual_{name}" for name in config.control_labels]
    gate_cols = [f"gate_{i}" for i in range(result.gates.shape[1])]
    feature_cols = [f"feature_{name}" for name in config.control_labels]
    fieldnames = ["time_s", "mode"] + state_cols + control_cols + baseline_cols + residual_cols + gate_cols + feature_cols

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, t in enumerate(result.time):
            row: dict[str, Any] = {"time_s": float(t), "mode": result.mode}
            row.update({col: float(value) for col, value in zip(state_cols, result.states[i])})
            row.update({col: float(value) for col, value in zip(control_cols, result.commands[i])})
            row.update({col: float(value) for col, value in zip(baseline_cols, result.baseline_commands[i])})
            row.update({col: float(value) for col, value in zip(residual_cols, result.residuals[i])})
            row.update({col: float(value) for col, value in zip(gate_cols, result.gates[i])})
            row.update({col: float(value) for col, value in zip(feature_cols, result.features[i])})
            writer.writerow(row)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

