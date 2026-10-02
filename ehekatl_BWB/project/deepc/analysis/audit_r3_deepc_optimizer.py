#!/usr/bin/env python3
"""Audit constrained DeePC feasibility and runtime on training temporal folds."""

from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from deepc.src.regularized_deepc import RegularizedDeePC  # noqa: E402


INPUT = ROOT / "logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv"
OUTPUT = ROOT / "configs/rich_R3_deepc_optimizer_fast_audit.json"


def load() -> np.ndarray:
    with INPUT.open(newline="") as stream:
        return np.asarray(
            [
                [float(row[name]) for name in ["t_s", "yoke_roll_ratio", "p_deg_s"]]
                for row in csv.DictReader(stream)
            ],
            dtype=float,
        )


def main() -> None:
    raw = load()
    library = raw[(raw[:, 0] >= 5) & (raw[:, 0] < 15), 1:]
    test = raw[(raw[:, 0] >= 15) & (raw[:, 0] <= 25), 1:]
    center, scale = library.mean(axis=0), library.std(axis=0, ddof=1)
    library = (library - center) / scale
    test = (test - center) / scale
    controller = RegularizedDeePC(library[:, 0], library[:, 1], 5, 5, 10.0)

    normalized_input_limit = 0.0002 / scale[0]
    normalized_slew_limit = 0.00005 / scale[0]
    normalized_zero_p = (0.0 - center[1]) / scale[1]
    starts = np.unique(np.linspace(0, len(test) - 10, 80, dtype=int))
    records = []
    for start in starts:
        u_ini = test[start : start + 5, 0]
        y_ini = test[start : start + 5, 1]
        hold = np.full(5, u_ini[-1])
        reference = np.full(5, normalized_zero_p)
        hold_prediction = controller.predict(u_ini, y_ini, hold)
        hold_cost = float(np.sum((hold_prediction - reference) ** 2))
        began = time.perf_counter()
        result = controller.optimize(
            u_ini,
            y_ini,
            reference,
            normalized_input_limit,
            normalized_slew_limit,
            tolerance=1e-7,
            max_iterations=300,
        )
        elapsed = time.perf_counter() - began
        records.append(
            {
                "start_sample": int(start),
                "runtime_ms": elapsed * 1000,
                "converged": result.converged,
                "iterations": result.iterations,
                "objective": result.objective,
                "hold_output_cost": hold_cost,
                "optimized_output_cost": float(np.sum((result.predicted_y - reference) ** 2)),
                "cost_ratio_to_hold": float(
                    np.sum((result.predicted_y - reference) ** 2) / max(hold_cost, 1e-15)
                ),
                "maximum_input_physical": result.maximum_input * scale[0],
                "maximum_slew_physical": result.maximum_slew * scale[0],
                "first_input_physical": result.future_u[0] * scale[0],
            }
        )
    runtime = np.asarray([item["runtime_ms"] for item in records])
    ratios = np.asarray([item["cost_ratio_to_hold"] for item in records])
    artifact = {
        "schema_version": 1,
        "purpose": "training-only constrained DeePC optimizer feasibility audit",
        "input_file": str(INPUT.relative_to(ROOT)),
        "held_out_response_files_opened": [],
        "formulation": {
            "t_ini": 5,
            "horizon": 5,
            "lambda_g": 10.0,
            "q_y": 1.0,
            "r_u": 0.01,
            "r_du": 0.05,
            "physical_input_limit": 0.0002,
            "physical_slew_limit": 0.00005,
            "solver": "NumPy deterministic projected gradient",
            "solver_tolerance": 1e-7,
            "solver_max_iterations": 300,
        },
        "cases": len(records),
        "converged_cases": sum(item["converged"] for item in records),
        "runtime_ms_median": float(np.median(runtime)),
        "runtime_ms_p95": float(np.percentile(runtime, 95)),
        "runtime_ms_max": float(np.max(runtime)),
        "control_period_ms": 1000 / 35,
        "deadline_pass_all": bool(np.max(runtime) < 1000 / 35),
        "median_predicted_output_cost_ratio_to_hold": float(np.median(ratios)),
        "p95_predicted_output_cost_ratio_to_hold": float(np.percentile(ratios, 95)),
        "input_limit_pass_all": all(
            item["maximum_input_physical"] <= 0.0002 + 1e-15 for item in records
        ),
        "slew_limit_pass_all": all(
            item["maximum_slew_physical"] <= 0.00005 + 1e-15 for item in records
        ),
        "case_records": records,
        "decision": "PASS" if all(item["converged"] for item in records) and np.max(runtime) < 1000 / 35 else "FAIL",
        "claim_boundary": "Self-predicted optimizer feasibility only; no plant-response or superiority claim.",
    }
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({k: v for k, v in artifact.items() if k != "case_records"}, indent=2))


if __name__ == "__main__":
    main()
