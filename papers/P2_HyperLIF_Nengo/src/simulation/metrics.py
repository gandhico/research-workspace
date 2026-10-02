"""Metrics and CSV helpers for HyperLIF experiments."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


def binary_events(events: np.ndarray) -> np.ndarray:
    """Convert event amplitudes to a binary event vector."""

    return (np.asarray(events) > 0.0).astype(float)


def event_count(events: np.ndarray) -> int:
    return int(np.count_nonzero(np.asarray(events) > 0.0))


def event_rate_hz(events: np.ndarray, duration: float) -> float:
    return event_count(events) / duration if duration > 0.0 else 0.0


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def exp_filter_events(events: np.ndarray, dt: float, tau: float = 0.02) -> np.ndarray:
    """Filter binary events with a first-order exponential synapse."""

    events = binary_events(events)
    y = np.zeros_like(events, dtype=float)
    decay = np.exp(-dt / tau)
    for k in range(1, events.size):
        y[k] = y[k - 1] * decay + events[k] * (1.0 - decay) / dt
    return y


def linear_decode(
    feature: np.ndarray,
    target: np.ndarray,
    train_fraction: float = 0.7,
) -> tuple[np.ndarray, float, float]:
    """Fit a scalar linear decoder and return prediction plus train/test RMSE."""

    x = np.asarray(feature, dtype=float).reshape(-1, 1)
    y = np.asarray(target, dtype=float)
    design = np.column_stack([x[:, 0], np.ones_like(y)])
    split = max(2, int(train_fraction * y.size))
    weights, *_ = np.linalg.lstsq(design[:split], y[:split], rcond=None)
    pred = design @ weights
    return pred, rmse(pred[:split], y[:split]), rmse(pred[split:], y[split:])


def trace_summary(name: str, trace: dict[str, np.ndarray], duration: float) -> dict[str, float | str]:
    """Summarize a neuron trace with common scalar metrics."""

    row: dict[str, float | str] = {"name": name}
    row["event_count"] = event_count(trace.get("events", np.array([])))
    row["event_rate_hz"] = event_rate_hz(trace.get("events", np.array([])), duration)
    if "voltage" in trace:
        row["voltage_min"] = float(np.min(trace["voltage"]))
        row["voltage_max"] = float(np.max(trace["voltage"]))
    if "reset_gate" in trace:
        row["gate_mean"] = float(np.mean(trace["reset_gate"]))
        row["gate_max"] = float(np.max(trace["reset_gate"]))
        row["gate_saturation_fraction"] = float(np.mean(trace["reset_gate"] > 0.95))
    if "conductance" in trace:
        row["conductance_mean"] = float(np.mean(trace["conductance"]))
        row["conductance_max"] = float(np.max(trace["conductance"]))
    return row


def write_csv(path: str | Path, columns: dict[str, np.ndarray]) -> None:
    """Write aligned vector columns to CSV."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    names = list(columns)
    arrays = [np.asarray(columns[name]) for name in names]
    n = min(array.size for array in arrays)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(names)
        for k in range(n):
            writer.writerow([array[k] for array in arrays])


def write_rows(path: str | Path, rows: list[dict[str, object]]) -> None:
    """Write a list of dictionaries to CSV."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
