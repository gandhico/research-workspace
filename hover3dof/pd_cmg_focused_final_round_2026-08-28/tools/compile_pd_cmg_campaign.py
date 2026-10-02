"""Compile and audit every PD/PD-CMG hardware run into reproducible tables.

The compiler never opens hardware. It validates trace schemas, recomputes
wrapped-yaw/axis metrics, checks full-duration completion, pairs each armed CMG
run with the nearest preceding matched armed PD run, and records neuron/decoder
coverage. Aborted or incomplete runs remain visible but are not valid results.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np


AXES = ("yaw", "pitch", "roll")
MOTORS = ("Vf", "Vb", "Vl", "Vr")
BASE_COLUMNS = {
    "t", "yaw_deg", "pitch_deg", "roll_deg",
    "yaw_ref_deg", "pitch_ref_deg", "roll_ref_deg",
    "qerr_rad", "loop_elapsed_s", "deadline_miss",
    *(f"tau0_{axis}" for axis in AXES),
    *(f"requested_delta_tau_{axis}" for axis in AXES),
    *(f"realized_delta_tau_{axis}" for axis in AXES),
    *(motor for motor in MOTORS),
    *(f"{motor}_computed" for motor in MOTORS),
}
NEURON_COLUMNS = {
    *(f"neuron_v_{i}" for i in range(6)),
    *(f"neuron_r_{i}" for i in range(6)),
    *(f"neuron_activity_{i}" for i in range(6)),
    *(f"neuron_current_{i}" for i in range(6)),
    *(f"decoder_w_{i}" for i in range(18)),
}


def load_trace(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        return rows, set(reader.fieldnames or [])


def vector(rows: list[dict[str, str]], names: tuple[str, ...] | list[str]) -> np.ndarray:
    return np.array([[float(row[name]) for name in names] for row in rows], dtype=float)


def wrapped_metrics(rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    measured = vector(rows, [f"{axis}_deg" for axis in AXES])
    reference = vector(rows, [f"{axis}_ref_deg" for axis in AXES])
    error = reference - measured
    error[:, 0] = np.rad2deg(np.arctan2(
        np.sin(np.deg2rad(error[:, 0])), np.cos(np.deg2rad(error[:, 0]))
    ))
    return (
        np.mean(np.abs(error), axis=0),
        np.sqrt(np.mean(error**2, axis=0)),
        np.linalg.norm(error, axis=1),
    )


def inspect_run(folder: Path) -> dict[str, Any]:
    summary_path = folder / "summary.json"
    trace_path = folder / "trace.csv"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows, columns = load_trace(trace_path)
    mae, rmse, combined = wrapped_metrics(rows)
    planned_run_duration = float(summary.get("planned_run_duration_s", summary["duration"]))
    expected_steps = int(round(planned_run_duration * float(summary["rate_hz"])))
    complete = (
        not summary.get("abort_reason")
        and len(rows) == expected_steps
        and int(summary.get("n_steps_logged", len(rows))) == expected_steps
    )
    base_schema_ok = BASE_COLUMNS <= columns
    is_cmg = summary["controller"] == "pd-cmg"
    neuron_schema_ok = (NEURON_COLUMNS <= columns) if is_cmg else True
    raw_home = summary.get("raw_home_ypr_deg")
    qerr = np.array([float(row["qerr_rad"]) for row in rows]) if "qerr_rad" in columns else None
    result: dict[str, Any] = {
        "run": folder.name,
        "path": str(folder),
        "mtime": folder.stat().st_mtime,
        "controller": summary["controller"],
        "armed": bool(summary.get("armed")),
        "mission": summary["mission"],
        "duration_s": float(summary["duration"]),
        "planned_run_duration_s": planned_run_duration,
        "rate_hz": float(summary["rate_hz"]),
        "reference_scale": float(summary.get("reference_scale", 1.0)),
        "hardstep_transition_s": float(summary.get("hardstep_transition_s", 0.0)),
        "pd_profile": summary.get("pd_profile", "legacy-unspecified"),
        "beta": float(summary.get("beta", 0.0)),
        "motor_residual_cap_V": float(summary.get("actual_motor_residual_cap_volts", 0.0)),
        "learning_rate": float(summary.get("learning_rate", 0.0)),
        "k_error": float(summary.get("k_error", 0.0)),
        "k_rate": float(summary.get("k_rate", 0.0)),
        "neural_substeps": int(summary.get("neural_substeps", 0)),
        "neural_dt_s": float(summary.get("neural_dt_s", 0.0)),
        "allocation_policy": summary.get("allocation_policy", "fixed-bias"),
        "motor_floor_volts": float(summary.get("motor_floor_volts", 0.0)),
        "samples": len(rows),
        "expected_samples": expected_steps,
        "complete": complete,
        "full_mission_completed": bool(summary.get("full_mission_completed", complete and planned_run_duration == float(summary["duration"]))),
        "abort_reason": summary.get("abort_reason", ""),
        "base_schema_ok": base_schema_ok,
        "neuron_schema_ok": neuron_schema_ok,
        "result_valid": bool(
            summary.get("armed") and complete
            and summary.get("full_mission_completed", planned_run_duration == float(summary["duration"]))
            and base_schema_ok and neuron_schema_ok
        ),
        "raw_home_logged": raw_home is not None,
        "raw_home_yaw_deg": raw_home[0] if raw_home is not None else None,
        "raw_home_yaw_tolerance_deg": float(summary.get("raw_home_yaw_tolerance_deg", 5.0)),
        "wrapped_error_mean_deg": float(np.mean(combined)),
        "wrapped_error_max_deg": float(np.max(combined)),
        "qerr_mean_rad": float(np.mean(qerr)) if qerr is not None else None,
        "qerr_max_rad": float(np.max(qerr)) if qerr is not None else None,
        "yaw_mae_deg": float(mae[0]),
        "pitch_mae_deg": float(mae[1]),
        "roll_mae_deg": float(mae[2]),
        "yaw_rmse_deg": float(rmse[0]),
        "pitch_rmse_deg": float(rmse[1]),
        "roll_rmse_deg": float(rmse[2]),
        "deadline_miss_fraction": float(np.mean([float(row["deadline_miss"]) for row in rows])),
        "lower_saturation_fraction": float(summary.get("lower_saturation_fraction", 0.0)),
        "upper_saturation_fraction": float(summary.get("upper_saturation_fraction", 0.0)),
        "allocator_yaw_scale_min": summary.get("allocator_yaw_scale_min"),
        "allocator_yaw_scale_mean": summary.get("allocator_yaw_scale_mean"),
        "allocator_pitch_roll_scale_min": summary.get("allocator_pitch_roll_scale_min"),
        "allocator_pitch_roll_scale_mean": summary.get("allocator_pitch_roll_scale_mean"),
    }
    if is_cmg and neuron_schema_ok:
        requested = vector(rows, [f"requested_delta_tau_{axis}" for axis in AXES])
        realized = vector(rows, [f"realized_delta_tau_{axis}" for axis in AXES])
        gate = vector(rows, [f"neuron_r_{i}" for i in range(6)])
        activity = vector(rows, [f"neuron_activity_{i}" for i in range(6)])
        weights = vector(rows, [f"decoder_w_{i}" for i in range(18)]).reshape(-1, 3, 6)
        requested_rms = float(np.sqrt(np.mean(requested**2)))
        realized_rms = float(np.sqrt(np.mean(realized**2)))
        result.update({
            "requested_residual_rms_Nm": requested_rms,
            "realized_residual_rms_Nm": realized_rms,
            "residual_realization_ratio": realized_rms / requested_rms if requested_rms else 0.0,
            "gate_min": float(np.min(gate)),
            "gate_max": float(np.max(gate)),
            "activity_min": float(np.min(activity)),
            "activity_max": float(np.max(activity)),
            "decoder_row_norm_end_yaw": float(np.linalg.norm(weights[-1, 0])),
            "decoder_row_norm_end_pitch": float(np.linalg.norm(weights[-1, 1])),
            "decoder_row_norm_end_roll": float(np.linalg.norm(weights[-1, 2])),
        })
    return result


def match_key(run: dict[str, Any]) -> tuple[Any, ...]:
    return (
        run["mission"], run["duration_s"], run["planned_run_duration_s"], run["rate_hz"], run["pd_profile"],
        run["reference_scale"], run["hardstep_transition_s"],
        run["learning_rate"], run["k_error"], run["k_rate"], run["neural_substeps"],
        run["allocation_policy"], run["motor_floor_volts"],
    )


def compile_pairs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for cmg in [run for run in runs if run["controller"] == "pd-cmg" and run["armed"]]:
        candidates = [
            run for run in runs
            if run["controller"] == "pd" and run["armed"]
            and run["mtime"] <= cmg["mtime"] and match_key(run) == match_key(cmg)
        ]
        baseline = max(candidates, key=lambda run: run["mtime"], default=None)
        raw_home_delta = (
            cmg["raw_home_yaw_deg"] - baseline["raw_home_yaw_deg"]
            if baseline and cmg["raw_home_yaw_deg"] is not None and baseline["raw_home_yaw_deg"] is not None
            else None
        )
        home_match_required = cmg["mission"] == "yaw360"
        home_match_ok = (
            not home_match_required
            or raw_home_delta is not None
            and abs(raw_home_delta) <= cmg["raw_home_yaw_tolerance_deg"]
        )
        pair: dict[str, Any] = {
            "mission": cmg["mission"],
            "duration_s": cmg["duration_s"],
            "pd_run": baseline["run"] if baseline else None,
            "cmg_run": cmg["run"],
            "motor_residual_cap_V": cmg["motor_residual_cap_V"],
            "reference_scale": cmg["reference_scale"],
            "hardstep_transition_s": cmg["hardstep_transition_s"],
            "allocation_policy": cmg["allocation_policy"],
            "motor_floor_volts": cmg["motor_floor_volts"],
            "pd_valid": baseline["result_valid"] if baseline else False,
            "cmg_valid": cmg["result_valid"],
            "home_match_required": home_match_required,
            "home_match_ok": home_match_ok,
            "pair_valid": bool(
                baseline and baseline["result_valid"] and cmg["result_valid"] and home_match_ok
            ),
            "pd_raw_home_yaw_deg": baseline["raw_home_yaw_deg"] if baseline else None,
            "cmg_raw_home_yaw_deg": cmg["raw_home_yaw_deg"],
        }
        if baseline:
            pair["raw_home_yaw_delta_deg"] = raw_home_delta
            for field in ("wrapped_error_mean_deg", "wrapped_error_max_deg", "qerr_mean_rad", "qerr_max_rad"):
                pair[f"pd_{field}"] = baseline[field]
                pair[f"cmg_{field}"] = cmg[field]
                pair[f"{field}_improvement_pct"] = (
                    100.0 * (baseline[field] - cmg[field]) / baseline[field]
                    if baseline[field] is not None and cmg[field] is not None and baseline[field] != 0.0
                    else None
                )
        pairs.append(pair)
    return pairs


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    run_folders = sorted(
        (path.parent for path in args.hardware_root.glob("*/summary.json") if (path.parent / "trace.csv").exists()),
        key=lambda path: path.stat().st_mtime,
    )
    runs = [inspect_run(folder) for folder in run_folders]
    pairs = compile_pairs(runs)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.out_dir / "campaign_runs.csv", runs)
    write_csv(args.out_dir / "campaign_pairs.csv", pairs)
    payload = {
        "hardware_root": str(args.hardware_root),
        "runs": runs,
        "pairs": pairs,
        "counts": {
            "runs": len(runs),
            "valid_runs": sum(run["result_valid"] for run in runs),
            "pairs": len(pairs),
            "valid_pairs": sum(pair["pair_valid"] for pair in pairs),
            "aborted_runs": sum(bool(run["abort_reason"]) for run in runs),
            "cmg_runs_with_complete_neuron_schema": sum(
                run["controller"] == "pd-cmg" and run["neuron_schema_ok"] for run in runs
            ),
        },
    }
    (args.out_dir / "campaign.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload["counts"], indent=2))
    print(args.out_dir)


if __name__ == "__main__":
    main()
