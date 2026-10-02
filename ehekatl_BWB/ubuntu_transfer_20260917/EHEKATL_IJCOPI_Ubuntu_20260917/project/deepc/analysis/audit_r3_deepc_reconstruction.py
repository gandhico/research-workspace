#!/usr/bin/env python3
"""Training-only temporal DeePC reconstruction and conditioning audit."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv"
OUTPUT = ROOT / "configs/rich_R3_deepc_reconstruction_audit.json"
FIELDS = ["t_s", "yoke_roll_ratio", "p_deg_s", "roll_deg", "total_roll_ratio"]


def load() -> np.ndarray:
    rows = []
    with INPUT.open(newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            rows.append([float(row[name]) for name in FIELDS])
    return np.asarray(rows, dtype=float)


def hankel(signal: np.ndarray, depth: int) -> np.ndarray:
    count = signal.shape[0] - depth + 1
    return np.vstack([signal[offset : offset + count].T for offset in range(depth)])


def effective_rank(matrix: np.ndarray, relative: float) -> int:
    singular = np.linalg.svd(matrix, compute_uv=False)
    return int(np.sum(singular >= relative * singular[0]))


def solve_ridge(a: np.ndarray, b: np.ndarray, regularization: float) -> np.ndarray:
    # Dual form is substantially cheaper because constraint rows are fewer than
    # trajectory columns for every candidate tested here.
    gram = a @ a.T
    return a.T @ np.linalg.solve(
        gram + regularization * np.eye(gram.shape[0]), b
    )


def main() -> None:
    raw = load()
    time = raw[:, 0]
    design = raw[(time >= 5.0) & (time < 15.0), 1:]
    temporal_test = raw[(time >= 15.0) & (time <= 25.0), 1:]

    center = np.mean(design, axis=0)
    scale = np.std(design, axis=0, ddof=1)
    if np.any(scale <= 0):
        raise ValueError("non-positive training scale")
    design = (design - center) / scale
    temporal_test = (temporal_test - center) / scale
    u_lib, y_lib = design[:, :1], design[:, 1:]
    u_test, y_test = temporal_test[:, :1], temporal_test[:, 1:]

    lambdas = [1e-10, 1e-8, 1e-6, 1e-4, 1e-2, 1.0]
    candidates = [(5, 10), (10, 15), (15, 20), (20, 35)]
    audits = []

    for t_ini, prediction in candidates:
        depth = t_ini + prediction
        hu = hankel(u_lib, depth)
        hy = hankel(y_lib, depth)
        up = hu[:t_ini]
        uf = hu[t_ini:]
        yp = hy[: 3 * t_ini]
        yf = hy[3 * t_ini :]
        constraint = np.vstack([up, yp, uf])

        max_start = temporal_test.shape[0] - depth
        starts = np.unique(np.linspace(0, max_start, 40, dtype=int))
        lambda_scores = []
        for ridge in lambdas:
            squared = np.zeros(3)
            denominator = np.zeros(3)
            past_squared = 0.0
            coefficient_norms = []
            for start in starts:
                past_u = u_test[start : start + t_ini].reshape(-1)
                past_y = y_test[start : start + t_ini].T.reshape(-1)
                future_u = u_test[
                    start + t_ini : start + depth
                ].reshape(-1)
                actual = y_test[start + t_ini : start + depth]
                right = np.concatenate([past_u, past_y, future_u])
                g = solve_ridge(constraint, right, ridge)
                predicted = (yf @ g).reshape(3, prediction).T
                past_fit = constraint[: t_ini + 3 * t_ini] @ g
                past_squared += float(np.sum((past_fit - right[: 4 * t_ini]) ** 2))
                error = predicted - actual
                squared += np.sum(error**2, axis=0)
                denominator += np.sum(actual**2, axis=0)
                coefficient_norms.append(float(np.linalg.norm(g)))
            nrmse = np.sqrt(squared / np.maximum(denominator, 1e-15))
            lambda_scores.append(
                {
                    "lambda_g": ridge,
                    "future_nrmse_scaled": dict(zip(FIELDS[2:], nrmse.tolist())),
                    "future_mean_nrmse_scaled": float(np.mean(nrmse)),
                    "past_fit_rmse_scaled": float(
                        np.sqrt(past_squared / (len(starts) * 4 * t_ini))
                    ),
                    "median_g_norm": float(np.median(coefficient_norms)),
                    "max_g_norm": float(np.max(coefficient_norms)),
                }
            )

        best = min(lambda_scores, key=lambda item: item["future_mean_nrmse_scaled"])
        singular = np.linalg.svd(constraint, compute_uv=False)
        audits.append(
            {
                "t_ini_samples": t_ini,
                "prediction_samples": prediction,
                "prediction_seconds": prediction / 35.0,
                "library_columns": int(hu.shape[1]),
                "constraint_rows": int(constraint.shape[0]),
                "constraint_exact_rank": int(np.linalg.matrix_rank(constraint)),
                "effective_rank_relative_1e-3": effective_rank(constraint, 1e-3),
                "effective_rank_relative_1e-4": effective_rank(constraint, 1e-4),
                "effective_rank_relative_1e-6": effective_rank(constraint, 1e-6),
                "condition_exact_nonzero": float(singular[0] / singular[-1]),
                "temporal_test_windows": int(len(starts)),
                "regularization_scores": lambda_scores,
                "best_training_only_regularization": best,
            }
        )

    viable = [
        item
        for item in audits
        if item["best_training_only_regularization"]["future_mean_nrmse_scaled"] <= 1.0
        and item["effective_rank_relative_1e-4"] == item["constraint_rows"]
    ]
    result = {
        "schema_version": 1,
        "purpose": "training-only scaled DeePC temporal reconstruction audit",
        "input_file": str(INPUT.relative_to(ROOT)),
        "held_out_response_files_opened": [],
        "library_window_s": [5.0, 15.0],
        "temporal_test_window_s": [15.0, 25.0],
        "normalization_center": dict(zip(FIELDS[1:], center.tolist())),
        "normalization_scale": dict(zip(FIELDS[1:], scale.tolist())),
        "candidate_outputs": FIELDS[2:],
        "candidate_audits": audits,
        "provisional_viability_rule": (
            "mean scaled future NRMSE <= 1.0 and full effective constraint rank at 1e-4"
        ),
        "viable_candidates": [
            {
                "t_ini_samples": item["t_ini_samples"],
                "prediction_samples": item["prediction_samples"],
                "lambda_g": item["best_training_only_regularization"]["lambda_g"],
                "mean_nrmse": item["best_training_only_regularization"][
                    "future_mean_nrmse_scaled"
                ],
            }
            for item in viable
        ],
        "decision": (
            "PASS: at least one training-only horizon is numerically and predictively viable"
            if viable
            else "FAIL: no tested horizon passes provisional reconstruction and effective-rank gates"
        ),
        "claim_boundary": "Temporal design evidence only; no confirmation or control-performance claim.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

