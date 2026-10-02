#!/usr/bin/env python3
"""Select a defensible DeePC output set using training-only temporal folds."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv"
OUTPUT = ROOT / "configs/rich_R3_deepc_channel_audit.json"
FIELDS = ["t_s", "yoke_roll_ratio", "p_deg_s", "roll_deg", "total_roll_ratio"]


def load() -> np.ndarray:
    with INPUT.open(newline="") as stream:
        return np.asarray(
            [[float(row[name]) for name in FIELDS] for row in csv.DictReader(stream)],
            dtype=float,
        )


def hankel(x: np.ndarray, depth: int) -> np.ndarray:
    columns = len(x) - depth + 1
    return np.vstack([x[k : k + columns].T for k in range(depth)])


def ridge(a: np.ndarray, b: np.ndarray, value: float) -> np.ndarray:
    return a.T @ np.linalg.solve(a @ a.T + value * np.eye(a.shape[0]), b)


def score(u_library, y_library, u_test, y_test, t_ini, future, value):
    depth = t_ini + future
    hu, hy = hankel(u_library, depth), hankel(y_library, depth)
    output_count = y_library.shape[1]
    up, uf = hu[:t_ini], hu[t_ini:]
    yp, yf = hy[: output_count * t_ini], hy[output_count * t_ini :]
    a = np.vstack([up, yp, uf])
    starts = np.unique(np.linspace(0, len(u_test) - depth, 40, dtype=int))
    numerator = np.zeros(output_count)
    denominator = np.zeros(output_count)
    norms = []
    for start in starts:
        b = np.concatenate(
            [
                u_test[start : start + t_ini].reshape(-1),
                y_test[start : start + t_ini].T.reshape(-1),
                u_test[start + t_ini : start + depth].reshape(-1),
            ]
        )
        g = ridge(a, b, value)
        prediction = (yf @ g).reshape(output_count, future).T
        actual = y_test[start + t_ini : start + depth]
        numerator += np.sum((prediction - actual) ** 2, axis=0)
        denominator += np.sum(actual**2, axis=0)
        norms.append(np.linalg.norm(g))
    nrmse = np.sqrt(numerator / np.maximum(denominator, 1e-15))
    return nrmse, float(np.median(norms)), int(np.linalg.matrix_rank(a)), a.shape[0]


def main() -> None:
    raw = load()
    library = raw[(raw[:, 0] >= 5) & (raw[:, 0] < 15), 1:]
    test = raw[(raw[:, 0] >= 15) & (raw[:, 0] <= 25), 1:]
    center, scale = library.mean(axis=0), library.std(axis=0, ddof=1)
    library, test = (library - center) / scale, (test - center) / scale
    u_library, u_test = library[:, :1], test[:, :1]
    output_sets = {
        "P": [1],
        "P_roll": [1, 2],
        "P_total_roll": [1, 3],
        "P_roll_total_roll": [1, 2, 3],
    }
    horizons = [(5, 5), (5, 10), (10, 10), (10, 15), (15, 20)]
    regularization = [1e-4, 1e-2, 1.0, 10.0, 100.0, 1000.0]
    results = []
    for label, columns in output_sets.items():
        y_library, y_test = library[:, columns], test[:, columns]
        names = [FIELDS[index + 1] for index in columns]
        for t_ini, future in horizons:
            options = []
            for value in regularization:
                nrmse, median_norm, rank, rows = score(
                    u_library, y_library, u_test, y_test, t_ini, future, value
                )
                options.append(
                    {
                        "lambda_g": value,
                        "nrmse": dict(zip(names, nrmse.tolist())),
                        "mean_nrmse": float(nrmse.mean()),
                        "median_g_norm": median_norm,
                        "constraint_rank": rank,
                        "constraint_rows": rows,
                    }
                )
            best = min(options, key=lambda item: item["mean_nrmse"])
            results.append(
                {
                    "output_set": label,
                    "outputs": names,
                    "t_ini_samples": t_ini,
                    "prediction_samples": future,
                    "prediction_seconds": future / 35,
                    "best": best,
                    "regularization_scores": options,
                }
            )
    ranked = sorted(results, key=lambda item: item["best"]["mean_nrmse"])
    passing = [
        item
        for item in ranked
        if item["best"]["mean_nrmse"] <= 1.0
        and item["best"]["constraint_rank"] == item["best"]["constraint_rows"]
    ]
    artifact = {
        "schema_version": 1,
        "purpose": "training-only DeePC output-channel and regularization audit",
        "input_file": str(INPUT.relative_to(ROOT)),
        "held_out_response_files_opened": [],
        "library_window_s": [5, 15],
        "temporal_test_window_s": [15, 25],
        "all_results": results,
        "top_five": ranked[:5],
        "provisional_pass_rule": "mean scaled NRMSE <= 1 and full constraint row rank",
        "passing_candidates": passing,
        "decision": (
            "PASS: a training-only output/horizon candidate is viable"
            if passing
            else "FAIL: channel reduction does not make existing data predictively viable"
        ),
        "claim_boundary": "Channel/horizon design only; no controller or confirmation claim.",
    }
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({k: artifact[k] for k in ["top_five", "decision"]}, indent=2))


if __name__ == "__main__":
    main()

