"""Fit and gate a QArm joint's command-to-position servo contract.

This is deliberately offline: it never imports PAL and cannot actuate hardware.
Input CSV columns are ``time_s``, ``command``, and ``position``.  The fitted
ARX(2) model is

    q[k+1] = a1 q[k] + a2 q[k-1] + b u[k-d] + c + epsilon[k].

The model is a compatibility screen for a position-servo interface.  It is not
evidence that the paper's fourth-order, highest-derivative input assumption is
satisfied.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


REQUIRED_COLUMNS = ("time_s", "command", "position")


def read_log(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = [name for name in REQUIRED_COLUMNS if name not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"missing CSV columns: {', '.join(missing)}")
        rows = list(reader)
    if len(rows) < 50:
        raise ValueError("at least 50 samples are required")
    values = np.asarray(
        [[float(row[name]) for name in REQUIRED_COLUMNS] for row in rows], dtype=float
    )
    if not np.all(np.isfinite(values)):
        raise ValueError("log contains non-finite values")
    t, u, q = values.T
    if np.any(np.diff(t) <= 0):
        raise ValueError("time_s must be strictly increasing")
    return t, u, q


def _fit_delay(t: np.ndarray, u: np.ndarray, q: np.ndarray, delay: int,
               train_fraction: float) -> dict:
    first = max(1, delay)
    k = np.arange(first, len(q) - 1)
    x = np.column_stack((q[k], q[k - 1], u[k - delay]))
    y = q[k + 1]
    split = int(np.floor(train_fraction * len(y)))
    if split < 20 or len(y) - split < 10:
        raise ValueError("log is too short for chronological train/validation split")

    x_train, y_train = x[:split], y[:split]
    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    if scale[2] < 1e-9:
        raise ValueError("command is not persistently excited in the training segment")
    scale = np.maximum(scale, 1e-12)
    xs = (x_train - mean) / scale
    design = np.column_stack((xs, np.ones(split)))
    theta_scaled, *_ = np.linalg.lstsq(design, y_train, rcond=None)
    theta = theta_scaled[:3] / scale
    intercept = float(theta_scaled[3] - theta @ mean)

    prediction = x[split:] @ theta + intercept
    residual = y[split:] - prediction
    rmse = float(np.sqrt(np.mean(residual**2)))
    variance = float(np.sum((y[split:] - np.mean(y[split:])) ** 2))
    r2 = float(1.0 - np.sum(residual**2) / variance) if variance > 0 else float("nan")
    nrmse = rmse / max(float(np.ptp(y[split:])), 1e-12)
    a1, a2, b = (float(value) for value in theta)
    poles = np.roots([1.0, -a1, -a2])
    denominator = 1.0 - a1 - a2
    dc_gain = float(b / denominator) if abs(denominator) > 1e-9 else float("inf")
    return {
        "delay_samples": delay,
        "a1": a1,
        "a2": a2,
        "b": b,
        "c": intercept,
        "poles": [[float(p.real), float(p.imag)] for p in poles],
        "max_pole_magnitude": float(np.max(np.abs(poles))),
        "dc_gain": dc_gain,
        "validation_rmse": rmse,
        "validation_nrmse_range": float(nrmse),
        "validation_r2": r2,
        "standardized_design_condition": float(np.linalg.cond(design)),
        "train_samples": split,
        "validation_samples": len(y) - split,
    }


def identify(t: np.ndarray, u: np.ndarray, q: np.ndarray, max_delay: int = 5,
             train_fraction: float = 0.7) -> dict:
    if max_delay < 0:
        raise ValueError("max_delay must be nonnegative")
    if not 0.5 <= train_fraction <= 0.9:
        raise ValueError("train_fraction must be between 0.5 and 0.9")
    dt = np.diff(t)
    dt_median = float(np.median(dt))
    jitter = float(np.max(np.abs(dt - dt_median)) / dt_median)
    candidates = [_fit_delay(t, u, q, delay, train_fraction)
                  for delay in range(max_delay + 1)]
    best = min(candidates, key=lambda result: result["validation_nrmse_range"])
    checks = {
        "sample_time_jitter_le_5pct": jitter <= 0.05,
        "validation_r2_ge_0_70": np.isfinite(best["validation_r2"])
        and best["validation_r2"] >= 0.70,
        "discrete_model_stable": best["max_pole_magnitude"] < 1.0,
        "finite_nonzero_dc_gain": np.isfinite(best["dc_gain"])
        and abs(best["dc_gain"]) >= 1e-4,
        "standardized_condition_le_1e4": best["standardized_design_condition"] <= 1e4,
    }
    return {
        "contract": "QArm position-servo ARX(2) compatibility screen",
        "samples": len(t),
        "median_dt_s": dt_median,
        "max_relative_sample_time_jitter": jitter,
        "command_standard_deviation": float(np.std(u)),
        "best_model": best,
        "candidate_models": candidates,
        "checks": {key: bool(value) for key, value in checks.items()},
        "shadow_ready": bool(all(checks.values())),
        "direct_dilisic_actuation_ready": False,
        "interpretation": (
            "A passing result permits recorded-data replay and shadow-mode work. "
            "It does not validate direct DILISIC actuation: identify the actual "
            "torque/PWM plant or design a rigorously bounded outer setpoint loop."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--max-delay", type=int, default=5)
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = identify(*read_log(args.csv), args.max_delay, args.train_fraction)
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
