#!/usr/bin/env python3
"""Fit frozen Stage-3 angle/rate models and evaluate sealed validation logs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


SAMPLE_DELAY = 3
FIT_START_S = 10.0
FIT_END_S = 50.0
HORIZONS = (1, 5, 10, 20)


def read_log(path: Path, angle: str, rate: str, control: str) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    get = lambda name: np.asarray([float(row[name]) for row in rows], dtype=float)
    t = get("t_s")
    baseline = t < FIT_START_S
    return {
        "t": t,
        "angle": get(angle) - get(angle)[baseline].mean(),
        "rate": get(rate) - get(rate)[baseline].mean(),
        "control": get(control) - get(control)[baseline].mean(),
    }


def regression(logs: list[dict[str, np.ndarray]], delay: int = SAMPLE_DELAY):
    blocks = []
    targets = []
    run_ids = []
    for run_id, log in enumerate(logs):
        t, angle, rate, control = (log[k] for k in ("t", "angle", "rate", "control"))
        keep = np.flatnonzero((t >= FIT_START_S) & (t <= FIT_END_S))
        first, last = int(keep[0]), int(keep[-1])
        indices = np.arange(first + delay, last)
        dt = t[indices + 1] - t[indices]
        blocks.append(np.column_stack((angle[indices], rate[indices], control[indices - delay])))
        targets.append((rate[indices + 1] - rate[indices]) / dt)
        run_ids.append(np.full(indices.size, run_id, dtype=int))
    return np.vstack(blocks), np.concatenate(targets), np.concatenate(run_ids)


def fit(logs: list[dict[str, np.ndarray]]) -> dict:
    x, y, run_ids = regression(logs)
    beta, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    dof = max(len(y) - len(beta), 1)
    covariance = (residual @ residual / dof) * np.linalg.inv(x.T @ x)
    stderr = np.sqrt(np.diag(covariance))
    a = np.array([[0.0, 1.0], [beta[0], beta[1]]])
    b = np.array([[0.0], [beta[2]]])
    poles = np.linalg.eigvals(a)
    controllability = np.column_stack((b, a @ b))
    loo = []
    for held_out in range(len(logs)):
        mask = run_ids != held_out
        candidate = np.linalg.lstsq(x[mask], y[mask], rcond=None)[0]
        error = y[~mask] - x[~mask] @ candidate
        loo.append(float(np.sqrt(np.mean(error**2))))
    return {
        "beta": beta,
        "stderr": stderr,
        "A_continuous": a,
        "B_continuous": b,
        "poles_continuous": poles,
        "controllability_rank": int(np.linalg.matrix_rank(controllability)),
        "condition_number": float(np.linalg.cond(x)),
        "training_qdot_rmse": float(np.sqrt(np.mean(residual**2))),
        "training_qdot_nrmse": float(np.sqrt(np.mean(residual**2)) / np.std(y)),
        "leave_one_run_out_qdot_rmse": loo,
        "residual_lag_correlations": autocorrelations(residual, 10),
        "residual_input_correlation": float(np.corrcoef(residual, x[:, 2])[0, 1]),
        "sample_count": int(len(y)),
    }


def autocorrelations(values: np.ndarray, count: int) -> list[float]:
    centered = values - values.mean()
    denominator = centered @ centered
    return [float(centered[:-lag] @ centered[lag:] / denominator) for lag in range(1, count + 1)]


def prediction_metrics(model: dict, logs: list[dict[str, np.ndarray]]) -> list[dict]:
    beta = model["beta"]
    reports = []
    for log in logs:
        t, angle, rate, control = (log[k] for k in ("t", "angle", "rate", "control"))
        active = np.flatnonzero((t >= FIT_START_S) & (t <= FIT_END_S))
        first, last = int(active[0]), int(active[-1])
        horizons = {}
        for horizon in HORIZONS:
            errors_angle, errors_rate = [], []
            for start in range(first + SAMPLE_DELAY, last - horizon + 1):
                predicted_angle, predicted_rate = angle[start], rate[start]
                for step in range(horizon):
                    k = start + step
                    dt = t[k + 1] - t[k]
                    delayed_control = control[k - SAMPLE_DELAY]
                    acceleration = beta @ np.array((predicted_angle, predicted_rate, delayed_control))
                    predicted_angle += dt * predicted_rate
                    predicted_rate += dt * acceleration
                errors_angle.append(predicted_angle - angle[start + horizon])
                errors_rate.append(predicted_rate - rate[start + horizon])
            horizons[str(horizon)] = {
                "angle_rmse_deg": float(np.sqrt(np.mean(np.square(errors_angle)))),
                "rate_rmse_deg_s": float(np.sqrt(np.mean(np.square(errors_rate)))),
            }
        reports.append({"horizons_samples": horizons})
    return reports


def serializable(value):
    if isinstance(value, np.ndarray):
        return serializable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, dict):
        return {key: serializable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serializable(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    definitions = {
        "roll": {
            "columns": ("roll_deg", "p_deg_s", "total_roll_ratio"),
            "training": ("stage2_roll_training_01_20260710_142240.csv", "stage2_roll_training_02_20260710_142615.csv"),
            "validation": ("stage2_roll_validation_01_20260710_143047.csv", "stage2_roll_validation_02_20260712_135450.csv"),
        },
        "pitch": {
            "columns": ("pitch_deg", "q_deg_s", "total_pitch_ratio"),
            "training": ("stage2_pitch_training_01_20260712_140739.csv", "stage2_pitch_training_02_20260712_141515.csv"),
            "validation": ("stage2_pitch_validation_01_20260712_142028.csv", "stage2_pitch_validation_02_20260712_142348.csv"),
        },
    }
    report = {"sample_delay": SAMPLE_DELAY, "nominal_delay_s": 0.3, "fit_window_s": [FIT_START_S, FIT_END_S], "models": {}}
    for axis, definition in definitions.items():
        columns = definition["columns"]
        training = [read_log(root / "logs" / name, *columns) for name in definition["training"]]
        validation = [read_log(root / "logs" / name, *columns) for name in definition["validation"]]
        model = fit(training)
        model["training_files"] = list(definition["training"])
        model["validation_files"] = list(definition["validation"])
        model["training_prediction"] = prediction_metrics(model, training)
        model["validation_prediction"] = prediction_metrics(model, validation)
        report["models"][axis] = model
    args.out.write_text(json.dumps(serializable(report), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(serializable(report), indent=2))


if __name__ == "__main__":
    main()
