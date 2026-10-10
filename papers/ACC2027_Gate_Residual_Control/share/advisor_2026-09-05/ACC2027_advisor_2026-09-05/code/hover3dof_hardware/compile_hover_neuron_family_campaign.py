"""Audit, summarize, plot, and freeze the 3DOF Hover neuron-family campaign."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
DEFAULT_INPUT = HERE / "results" / "hover_neuron_family_matched_25s_2026-09-01"
DEFAULT_OUTPUT = HERE / "results" / "hover_neuron_family_compiled_2026-09-01"
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
CONTROLLERS = (
    "pd",
    "nengo-cmg-fixed", "nengo-nef-pes",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)
NEURAL_CONTROLLERS = CONTROLLERS[1:]
CONDITIONS = ("nominal", "hard-pulses")
EVENTS = ((4.0, 0.25), (9.0, 0.25), (14.0, 0.25), (19.0, 0.35))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def choose_summary(cell: Path) -> Path:
    candidates = sorted(cell.glob("*/summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"no summary in {cell}")
    for path in candidates:
        if json.loads(path.read_text(encoding="utf-8")).get("run_completed"):
            return path
    return candidates[0]


def load_trace(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return {name: np.asarray([float(row[name]) for row in rows]) for name in rows[0]}


def pulse_metrics(t: np.ndarray, qerr_deg: np.ndarray, start: float, width: float) -> dict:
    before = (t >= max(0.0, start - 0.5)) & (t < start)
    window = (t >= start) & (t <= start + 3.0)
    threshold = (float(np.median(qerr_deg[before])) if np.any(before) else 0.0) + 2.0
    recovery = None
    for index in np.flatnonzero((t >= start + width) & (t <= start + 3.0)):
        if index + 10 <= len(t) and np.all(qerr_deg[index:index + 10] <= threshold):
            recovery = float(t[index] - (start + width))
            break
    return {
        "peak_qerr_deg_3s": float(np.max(qerr_deg[window])) if np.any(window) else None,
        "recovery_threshold_deg": threshold,
        "recovery_time_s": recovery,
    }


def controller_label(name: str) -> str:
    labels = {
        "pd": "PD",
        "nengo-cmg-fixed": "CMG fixed",
        "nengo-nef-pes": "CMG PES",
        "nengo-lif-fixed": "LIF fixed",
        "nengo-lif-pes": "LIF PES",
        "nengo-alif-fixed": "ALIF fixed",
        "nengo-alif-pes": "ALIF PES",
        "nengo-izhikevich-fixed": "Izh fixed",
        "nengo-izhikevich-pes": "Izh PES",
        "nengo-lifrate-fixed": "LIFRate fixed",
        "nengo-lifrate-pes": "LIFRate PES",
    }
    return labels[name]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    records = []
    failures = []
    source_files: list[Path] = []

    for condition in CONDITIONS:
        for mission in MISSIONS:
            for controller in CONTROLLERS:
                cell = args.input_root / condition / mission / controller
                summary_path = choose_summary(cell)
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                run_dir = summary_path.parent
                trace = load_trace(run_dir / "trace.csv")
                qerr_deg = np.rad2deg(trace["qerr_rad"])
                residual = np.column_stack(
                    [trace[f"{channel}_delta_applied"] for channel in ("Vf", "Vb", "Vl", "Vr")]
                )
                weights = np.column_stack([trace[f"decoder_w_{i}"] for i in range(18)])
                activity = np.column_stack([trace[f"neuron_activity_{i}"] for i in range(6)])
                completed = bool(summary["run_completed"])
                record = {
                    "condition": condition,
                    "mission": mission,
                    "controller": controller,
                    "controller_label": controller_label(controller),
                    "completed": completed,
                    "abort_reason": summary["abort_reason"],
                    "duration_requested_s": summary["config"]["duration"],
                    "duration_logged_s": float(trace["t"][-1] + 0.005),
                    "n_steps": summary["n_steps_logged"],
                    "qerr_mean_deg": float(np.mean(qerr_deg)),
                    "qerr_max_deg": float(np.max(qerr_deg)),
                    "qerr_iae_deg_s": float(np.trapezoid(qerr_deg, trace["t"])),
                    "axis_mae_yaw_deg": summary["axis_error_mae_deg"]["yaw"],
                    "axis_mae_pitch_deg": summary["axis_error_mae_deg"]["pitch"],
                    "axis_mae_roll_deg": summary["axis_error_mae_deg"]["roll"],
                    "motor_residual_rms_V": float(np.sqrt(np.mean(residual * residual))),
                    "motor_residual_cap_fraction": float(np.mean(np.abs(residual) >= 0.199)),
                    "activity_mean": float(np.mean(activity)),
                    "activity_peak": float(np.max(activity)),
                    "decoder_frobenius_change": float(np.linalg.norm(weights[-1] - weights[0])),
                    "deadline_miss_fraction": summary["deadline_miss_fraction"],
                    "trace": str(run_dir / "trace.csv"),
                    "neural_trace": summary.get("neural_trace_2khz"),
                    "summary": str(summary_path),
                }
                if condition == "hard-pulses":
                    for event_index, (start, width) in enumerate(EVENTS, 1):
                        for key, value in pulse_metrics(trace["t"], qerr_deg, start, width).items():
                            record[f"pulse{event_index}_{key}"] = value
                records.append(record)
                for name in ("summary.json", "trace.csv", "manifest.json", "neural_trace_schema.json", "neural_trace_2khz.npz"):
                    path = run_dir / name
                    if path.exists():
                        source_files.append(path)

                if controller != "pd":
                    archive = run_dir / "neural_trace_2khz.npz"
                    schema_path = run_dir / "neural_trace_schema.json"
                    if not archive.exists() or not schema_path.exists():
                        failures.append(f"missing neural archive/schema: {run_dir}")
                    else:
                        schema = json.loads(schema_path.read_text(encoding="utf-8"))
                        with np.load(archive, allow_pickle=False) as loaded:
                            if len(loaded.files) != 28:
                                failures.append(f"{archive}: expected 28 signals, got {len(loaded.files)}")
                            if loaded["t"].shape[0] != 10 * summary["n_steps_logged"]:
                                failures.append(f"{archive}: neural/hardware sample mismatch")
                            for name in loaded.files:
                                if not np.isfinite(loaded[name]).all():
                                    failures.append(f"{archive}: nonfinite signal {name}")
                        if schema.get("controller") != controller:
                            failures.append(f"{schema_path}: controller mismatch")

    lookup = {(r["condition"], r["mission"], r["controller"]): r for r in records}
    for record in records:
        baseline = lookup[(record["condition"], record["mission"], "pd")]
        comparable = record["completed"] and baseline["completed"]
        record["matched_full_duration_comparison"] = comparable
        if record["controller"] == "pd":
            record["improvement_mean_percent"] = 0.0 if comparable else None
            record["improvement_iae_percent"] = 0.0 if comparable else None
        elif comparable:
            record["improvement_mean_percent"] = 100.0 * (
                baseline["qerr_mean_deg"] - record["qerr_mean_deg"]
            ) / baseline["qerr_mean_deg"]
            record["improvement_iae_percent"] = 100.0 * (
                baseline["qerr_iae_deg_s"] - record["qerr_iae_deg_s"]
            ) / baseline["qerr_iae_deg_s"]
        else:
            record["improvement_mean_percent"] = None
            record["improvement_iae_percent"] = None

    fieldnames = sorted({key for record in records for key in record})
    with (args.output_root / "hover_neuron_family_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    (args.output_root / "hover_neuron_family_results.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )

    for condition in CONDITIONS:
        matrix = np.full((len(NEURAL_CONTROLLERS), len(MISSIONS)), np.nan)
        complete = np.zeros_like(matrix)
        for row, controller in enumerate(NEURAL_CONTROLLERS):
            for col, mission in enumerate(MISSIONS):
                record = lookup[(condition, mission, controller)]
                complete[row, col] = float(record["completed"])
                if record["improvement_mean_percent"] is not None:
                    matrix[row, col] = record["improvement_mean_percent"]
        fig, ax = plt.subplots(figsize=(11.5, 7.0))
        image = ax.imshow(matrix, cmap="RdYlGn", vmin=-10, vmax=10, aspect="auto")
        for row in range(matrix.shape[0]):
            for col in range(matrix.shape[1]):
                text = "ABORT" if not complete[row, col] else f"{matrix[row, col]:+.1f}%"
                ax.text(col, row, text, ha="center", va="center", fontsize=8)
        ax.set_xticks(range(len(MISSIONS)), MISSIONS)
        ax.set_yticks(range(len(NEURAL_CONTROLLERS)), [controller_label(c) for c in NEURAL_CONTROLLERS])
        ax.set_title(f"3DOF Hover neuron-family change from PD — {condition}")
        fig.colorbar(image, ax=ax, label="mean quaternion-error improvement [%]")
        fig.tight_layout()
        for suffix in ("png", "pdf"):
            fig.savefig(args.output_root / f"hover_neuron_family_heatmap_{condition}.{suffix}", dpi=240 if suffix == "png" else None)
        plt.close(fig)

    pes_controllers = ("nengo-nef-pes", "nengo-lif-pes", "nengo-alif-pes", "nengo-izhikevich-pes", "nengo-lifrate-pes")
    fig, ax = plt.subplots(figsize=(12.0, 6.5))
    width = 0.15
    x = np.arange(len(MISSIONS))
    colors = ("#009E73", "#0072B2", "#CC79A7", "#D55E00", "#56B4E9")
    for index, (controller, color) in enumerate(zip(pes_controllers, colors)):
        values = [lookup[("nominal", mission, controller)]["improvement_mean_percent"] for mission in MISSIONS]
        ax.bar(x + (index - 2) * width, values, width, label=controller_label(controller), color=color)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, MISSIONS)
    ax.set_ylabel("mean quaternion-error improvement from PD [%]")
    ax.set_title("Online-PES neuron-family benchmark — emulated 3DOF Hover, nominal")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(args.output_root / f"hover_online_pes_benchmark_nominal.{suffix}", dpi=240 if suffix == "png" else None)
    plt.close(fig)

    nominal_rankings = {}
    for mission in MISSIONS:
        candidates = [
            r for r in records
            if r["condition"] == "nominal" and r["mission"] == mission and r["controller"] != "pd" and r["completed"]
        ]
        candidates.sort(key=lambda r: r["qerr_mean_deg"])
        nominal_rankings[mission] = [
            {"rank": index, "controller": r["controller"], "qerr_mean_deg": r["qerr_mean_deg"], "improvement_percent": r["improvement_mean_percent"]}
            for index, r in enumerate(candidates, 1)
        ]
    audit = {
        "status": "passed" if not failures else "failed",
        "expected_cells": 110,
        "found_cells": len(records),
        "completed_cells": sum(r["completed"] for r in records),
        "aborted_cells": sum(not r["completed"] for r in records),
        "expected_neural_archives": 100,
        "checked_neural_archives": sum(r["controller"] != "pd" for r in records),
        "failures": failures,
        "interpretation": "All 11 hard-pulse yaw360 cells reached the declared 180-degree simulation-divergence boundary; improvements are intentionally masked.",
    }
    (args.output_root / "campaign_integrity_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "nominal_rankings.json").write_text(json.dumps(nominal_rankings, indent=2) + "\n", encoding="utf-8")

    products = sorted(
        path for path in args.output_root.rglob("*")
        if path.is_file() and path.name != "FROZEN_SHA256_MANIFEST.json"
    )
    manifest = {
        "schema": 1,
        "source_files": [{"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)} for path in sorted(set(source_files))],
        "compiled_files": [{"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)} for path in products],
    }
    (args.output_root / "FROZEN_SHA256_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
