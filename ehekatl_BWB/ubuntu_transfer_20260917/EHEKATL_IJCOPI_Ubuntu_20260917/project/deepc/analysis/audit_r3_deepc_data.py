#!/usr/bin/env python3
"""Audit existing R3 data for DeePC without opening held-out response logs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv"
OUTPUT = ROOT / "configs/rich_R3_deepc_data_audit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def block_hankel(signal: np.ndarray, depth: int) -> np.ndarray:
    """Return a block Hankel matrix for samples-by-channels data."""
    samples, channels = signal.shape
    columns = samples - depth + 1
    if columns <= 0:
        raise ValueError(f"depth {depth} exceeds available samples {samples}")
    return np.vstack(
        [signal[offset : offset + columns].T for offset in range(depth)]
    )


def numerical_rank(matrix: np.ndarray) -> tuple[int, float, list[float]]:
    singular = np.linalg.svd(matrix, compute_uv=False)
    tolerance = max(matrix.shape) * np.finfo(float).eps * singular[0]
    rank = int(np.sum(singular > tolerance))
    positive = singular[singular > tolerance]
    condition = float(positive[0] / positive[-1]) if positive.size else float("inf")
    return rank, condition, singular[: min(20, singular.size)].tolist()


def load_training() -> tuple[list[str], np.ndarray]:
    fields = [
        "t_s",
        "sent_roll_command",
        "yoke_roll_ratio",
        "total_roll_ratio",
        "aileron_wing2l_deg",
        "p_deg_s",
        "roll_deg",
    ]
    rows: list[list[float]] = []
    with TRAINING.open(newline="") as stream:
        reader = csv.DictReader(stream)
        missing = set(fields).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing fields: {sorted(missing)}")
        for row in reader:
            rows.append([float(row[field]) for field in fields])
    return fields, np.asarray(rows, dtype=float)


def main() -> None:
    fields, data = load_training()
    index = {name: position for position, name in enumerate(fields)}
    time = data[:, index["t_s"]]
    mask = (time >= 5.0) & (time <= 25.0)
    selected = data[mask]

    # The written yoke command is the upstream manipulated variable. Remove its
    # pre-run bias; outputs are centered over the selected design window.
    u = selected[:, [index["yoke_roll_ratio"]]]
    u = u - np.mean(u, axis=0, keepdims=True)
    y_names = ["p_deg_s", "roll_deg", "total_roll_ratio"]
    y = selected[:, [index[name] for name in y_names]]
    y = y - np.mean(y, axis=0, keepdims=True)

    horizons = []
    for t_ini, prediction in [(5, 10), (10, 15), (15, 20), (20, 35)]:
        depth = t_ini + prediction
        hu = block_hankel(u, depth)
        h_uy = np.vstack([hu, block_hankel(y, depth)])
        u_rank, u_condition, u_singular = numerical_rank(hu)
        uy_rank, uy_condition, uy_singular = numerical_rank(h_uy)
        horizons.append(
            {
                "t_ini_samples": t_ini,
                "prediction_samples": prediction,
                "depth_samples": depth,
                "hankel_columns": int(hu.shape[1]),
                "input_hankel_rank": u_rank,
                "input_full_row_rank_required": int(hu.shape[0]),
                "input_full_row_rank_pass": u_rank == hu.shape[0],
                "input_condition_nonzero": u_condition,
                "input_singular_values_head": u_singular,
                "stacked_uy_rank": uy_rank,
                "stacked_uy_rows": int(h_uy.shape[0]),
                "stacked_uy_condition_nonzero": uy_condition,
                "stacked_uy_singular_values_head": uy_singular,
            }
        )

    result = {
        "schema_version": 1,
        "purpose": "training-only R3 DeePC data feasibility audit",
        "input_file": str(TRAINING.relative_to(ROOT)),
        "input_sha256": sha256(TRAINING),
        "held_out_response_files_opened": [],
        "source_role": "design/training evidence; rejected only under obsolete yoke-equals-total gate",
        "sample_rate_hz_nominal": 35.0,
        "window_s": [5.0, 25.0],
        "samples": int(selected.shape[0]),
        "manipulated_input": "yoke_roll_ratio perturbation",
        "candidate_outputs": y_names,
        "horizon_audits": horizons,
        "decision": (
            "PASS for at least one tested input Hankel full-row-rank horizon"
            if any(item["input_full_row_rank_pass"] for item in horizons)
            else "FAIL: existing deterministic multisine is not persistently rich enough for tested DeePC horizons"
        ),
        "claim_boundary": "Rank/conditioning audit only; no DeePC performance claim.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()

