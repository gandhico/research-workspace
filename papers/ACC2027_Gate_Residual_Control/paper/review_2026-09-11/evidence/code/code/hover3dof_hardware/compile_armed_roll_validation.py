"""Compile the staged armed 3DOF Hover PD/CMG-PES Roll validation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


MOTOR_RESIDUAL_COLUMNS = (
    "Vf_delta_applied",
    "Vb_delta_applied",
    "Vl_delta_applied",
    "Vr_delta_applied",
)
UNIT_LABELS = ("+yaw", "+pitch", "+roll", "-yaw", "-pitch", "-roll")


def read_trace(path: Path) -> dict[str, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"empty trace: {path}")
    return {
        key: np.asarray([float(row[key]) for row in rows], dtype=float)
        for key in rows[0]
    }


def max_consecutive(values: np.ndarray) -> int:
    longest = current = 0
    for value in values.astype(bool):
        current = current + 1 if value else 0
        longest = max(longest, current)
    return longest


def load_run(directory: Path, label: str) -> dict:
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    trace = read_trace(directory / "trace.csv")
    residual = np.column_stack([trace[name] for name in MOTOR_RESIDUAL_COLUMNS])
    gate = np.column_stack([trace[f"neuron_r_{i}"] for i in range(6)])
    weights = np.column_stack([trace[f"decoder_w_{i}"] for i in range(18)])
    cap = float(summary["config"]["motor_residual_cap_volts"])
    is_pd = summary["config"]["controller"] == "pd"
    return {
        "label": label,
        "directory": directory,
        "summary": summary,
        "trace": trace,
        "residual": residual,
        "gate": gate,
        "weights": weights,
        "metrics": {
            "label": label,
            "source_directory": str(directory),
            "controller": summary["config"]["controller"],
            "beta": 0.0 if is_pd else float(summary["config"]["beta"]),
            "motor_residual_cap_V": 0.0 if is_pd else cap,
            "learning_rate": 0.0 if is_pd else float(summary["config"]["learning_rate"]),
            "k_error": 0.0 if is_pd else float(summary["config"]["k_error"]),
            "duration_s": float(summary["config"]["duration"]),
            "completed": bool(summary["run_completed"]),
            "abort_reason": summary["abort_reason"],
            "samples_200Hz": int(summary["n_steps_logged"]),
            "neural_samples_2kHz": 0 if summary["neural_trace_2khz"] is None else 10 * int(summary["n_steps_logged"]),
            "angle_error_mean_deg": float(summary["angle_err_mean_deg"]),
            "angle_error_max_deg": float(summary["angle_err_max_deg"]),
            "roll_error_mae_deg": float(summary["axis_error_mae_deg"]["roll"]),
            "max_abs_yaw_deg": float(np.max(np.abs(trace["yaw_deg"]))),
            "max_abs_pitch_deg": float(np.max(np.abs(trace["pitch_deg"]))),
            "max_abs_roll_deg": float(np.max(np.abs(trace["roll_deg"]))),
            "deadline_miss_fraction": float(summary["deadline_miss_fraction"]),
            "max_consecutive_deadline_misses": max_consecutive(trace["deadline_miss"]),
            "motor_residual_rms_V": float(np.sqrt(np.mean(residual**2))),
            "motor_residual_cap_fraction": 0.0 if is_pd else float(np.mean(np.abs(residual) >= cap - 1e-9)),
            "decoder_frobenius_change": float(np.linalg.norm(weights[-1] - weights[0])),
            "gate_mean": np.mean(gate, axis=0).tolist(),
            "gate_max": np.max(gate, axis=0).tolist(),
        },
    }


def save_figure(fig: plt.Figure, prefix: Path) -> None:
    fig.savefig(prefix.with_suffix(".png"), dpi=220, bbox_inches="tight")
    fig.savefig(prefix.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def tracking_figure(runs: list[dict], output: Path) -> None:
    colors = ("#1f2937", "#2a9d8f", "#d97706")
    fig, axes = plt.subplots(3, 1, figsize=(10.5, 9.0), sharex=True)
    reference = runs[0]["trace"]
    axes[0].plot(reference["t"], reference["roll_ref_deg"], "k--", lw=1.7, label="reference")
    for run, color in zip(runs, colors):
        trace = run["trace"]
        axes[0].plot(trace["t"], trace["roll_deg"], color=color, lw=1.4, label=run["label"])
        axes[1].plot(trace["t"], np.rad2deg(trace["qerr_rad"]), color=color, lw=1.4, label=run["label"])
    axes[0].set_ylabel("roll [deg]")
    axes[0].legend(ncol=2, frameon=False)
    axes[0].grid(alpha=0.25)
    axes[1].set_ylabel("quaternion error [deg]")
    axes[1].grid(alpha=0.25)

    names = ("PD\nbaseline", "CMG-PES\nbeta=0.10", "CMG-PES\nbeta=0.20")
    means = [run["metrics"]["angle_error_mean_deg"] for run in runs]
    maxima = [run["metrics"]["angle_error_max_deg"] for run in runs]
    x = np.arange(len(runs))
    axes[2].bar(x - 0.18, means, 0.36, color=colors, alpha=0.9, label="mean")
    axes[2].bar(x + 0.18, maxima, 0.36, color=colors, alpha=0.42, label="maximum")
    axes[2].set_xticks(x, names)
    axes[2].set_ylabel("attitude error [deg]")
    axes[2].set_xlabel("matched 8 s physical Roll experiment")
    axes[2].legend(frameon=False)
    axes[2].grid(axis="y", alpha=0.25)
    fig.suptitle("Quanser 3DOF Hover: armed PD vs Nengo CMG-PES Roll validation")
    fig.tight_layout()
    save_figure(fig, output / "armed_roll_tracking_comparison")


def neural_figure(run: dict, output: Path) -> None:
    trace = run["trace"]
    t = trace["t"]
    fig, axes = plt.subplots(4, 1, figsize=(10.5, 11.0), sharex=True)
    for i, name in enumerate(MOTOR_RESIDUAL_COLUMNS):
        axes[0].plot(t, trace[name], lw=1.0, label=name.replace("_delta_applied", ""))
    axes[0].set_ylabel("applied residual [V]")
    axes[0].legend(ncol=4, frameon=False)
    axes[0].grid(alpha=0.25)

    for i, label in enumerate(UNIT_LABELS):
        axes[1].plot(t, trace[f"neuron_r_{i}"], lw=1.0, label=label)
        axes[2].plot(t, trace[f"neuron_v_{i}"], lw=1.0, label=label)
    axes[1].set_ylabel("gate r")
    axes[1].legend(ncol=6, frameon=False)
    axes[1].grid(alpha=0.25)
    axes[2].set_ylabel("membrane v")
    axes[2].grid(alpha=0.25)

    for axis, color in zip(("yaw", "pitch", "roll"), ("#2563eb", "#059669", "#dc2626")):
        axes[3].plot(t, trace[f"decoder_update_norm_{axis}"], color=color, lw=1.1, label=axis)
    axes[3].set_ylabel("PES update norm")
    axes[3].set_xlabel("time [s]")
    axes[3].legend(ncol=3, frameon=False)
    axes[3].grid(alpha=0.25)
    fig.suptitle(f"Nengo CMG-PES neural diagnostics: {run['label']}")
    fig.tight_layout()
    save_figure(fig, output / "armed_roll_neural_diagnostics")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pd", type=Path, required=True)
    parser.add_argument("--low", type=Path, required=True)
    parser.add_argument("--moderate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    runs = [
        load_run(args.pd, "PD baseline"),
        load_run(args.low, "CMG-PES beta=0.10"),
        load_run(args.moderate, "CMG-PES beta=0.20"),
    ]
    baseline_mean = runs[0]["metrics"]["angle_error_mean_deg"]
    baseline_max = runs[0]["metrics"]["angle_error_max_deg"]
    for run in runs:
        metrics = run["metrics"]
        metrics["mean_improvement_vs_PD_percent"] = 100.0 * (baseline_mean - metrics["angle_error_mean_deg"]) / baseline_mean
        metrics["max_improvement_vs_PD_percent"] = 100.0 * (baseline_max - metrics["angle_error_max_deg"]) / baseline_max

    tracking_figure(runs, args.output)
    neural_figure(runs[-1], args.output)
    rows = [run["metrics"] for run in runs]
    (args.output / "armed_roll_validation.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    scalar_rows = [{key: value for key, value in row.items() if not isinstance(value, list)} for row in rows]
    with (args.output / "armed_roll_validation.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scalar_rows[0]))
        writer.writeheader()
        writer.writerows(scalar_rows)

    source_files = []
    for run in runs:
        for name in ("summary.json", "trace.csv", "manifest.json", "neural_trace_2khz.npz", "neural_trace_schema.json"):
            path = run["directory"] / name
            if path.exists():
                source_files.append(path)
    products = sorted(path for path in args.output.iterdir() if path.is_file())
    manifest = {
        "schema": 1,
        "purpose": "staged armed Quanser 3DOF Hover PD/Nengo-CMG-PES Roll validation",
        "source_files": [{"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)} for path in source_files],
        "compiled_files": [{"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)} for path in products],
    }
    (args.output / "FROZEN_SHA256_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": "passed", "output": str(args.output), "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
