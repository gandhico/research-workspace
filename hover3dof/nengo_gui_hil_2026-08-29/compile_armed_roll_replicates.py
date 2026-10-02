"""Compile the n=3 armed PD versus Nengo CMG-PES Roll campaign."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from compile_armed_roll_validation import load_run


def mean_sd(values: list[float]) -> tuple[float, float]:
    data = np.asarray(values, dtype=float)
    return float(np.mean(data)), float(np.std(data, ddof=1))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pd", type=Path, nargs=3, required=True)
    parser.add_argument("--cmg", type=Path, nargs=3, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    pd_runs = [load_run(path, f"PD trial {i}") for i, path in enumerate(args.pd, 1)]
    cmg_runs = [load_run(path, f"CMG-PES trial {i}") for i, path in enumerate(args.cmg, 1)]
    runs = pd_runs + cmg_runs

    trial_rows = []
    for i, (pd, cmg) in enumerate(zip(pd_runs, cmg_runs), 1):
        pd_mean = pd["metrics"]["angle_error_mean_deg"]
        cmg_mean = cmg["metrics"]["angle_error_mean_deg"]
        pd_max = pd["metrics"]["angle_error_max_deg"]
        cmg_max = cmg["metrics"]["angle_error_max_deg"]
        trial_rows.append(
            {
                "pair": i,
                "pd_directory": str(pd["directory"]),
                "cmg_directory": str(cmg["directory"]),
                "pd_mean_error_deg": pd_mean,
                "cmg_mean_error_deg": cmg_mean,
                "paired_mean_improvement_percent": 100.0 * (pd_mean - cmg_mean) / pd_mean,
                "pd_max_error_deg": pd_max,
                "cmg_max_error_deg": cmg_max,
                "paired_max_improvement_percent": 100.0 * (pd_max - cmg_max) / pd_max,
                "cmg_deadline_miss_fraction": cmg["metrics"]["deadline_miss_fraction"],
                "cmg_max_consecutive_misses": cmg["metrics"]["max_consecutive_deadline_misses"],
                "cmg_residual_rms_V": cmg["metrics"]["motor_residual_rms_V"],
                "cmg_residual_cap_fraction": cmg["metrics"]["motor_residual_cap_fraction"],
                "cmg_decoder_frobenius_change": cmg["metrics"]["decoder_frobenius_change"],
            }
        )

    pd_means = [r["metrics"]["angle_error_mean_deg"] for r in pd_runs]
    cmg_means = [r["metrics"]["angle_error_mean_deg"] for r in cmg_runs]
    pd_maxima = [r["metrics"]["angle_error_max_deg"] for r in pd_runs]
    cmg_maxima = [r["metrics"]["angle_error_max_deg"] for r in cmg_runs]
    paired_mean = [r["paired_mean_improvement_percent"] for r in trial_rows]
    paired_max = [r["paired_max_improvement_percent"] for r in trial_rows]
    pd_mean_mu, pd_mean_sd = mean_sd(pd_means)
    cmg_mean_mu, cmg_mean_sd = mean_sd(cmg_means)
    pd_max_mu, pd_max_sd = mean_sd(pd_maxima)
    cmg_max_mu, cmg_max_sd = mean_sd(cmg_maxima)
    imp_mean_mu, imp_mean_sd = mean_sd(paired_mean)
    imp_max_mu, imp_max_sd = mean_sd(paired_max)

    gate_means = np.asarray([r["metrics"]["gate_mean"] for r in cmg_runs])
    aggregate = {
        "schema": 1,
        "platform": "Quanser 3DOF Hover",
        "mission": "roll",
        "n_per_controller": 3,
        "cmg_configuration": {
            "beta": 0.2,
            "per_motor_residual_cap_V": 0.2,
            "learning_rate": 0.0002,
            "k_error": 2.0,
            "k_rate": 0.0,
            "residual_slew_V_per_s": 1.0,
        },
        "pd_mean_error_deg": {"mean": pd_mean_mu, "sample_sd": pd_mean_sd},
        "cmg_mean_error_deg": {"mean": cmg_mean_mu, "sample_sd": cmg_mean_sd},
        "pd_max_error_deg": {"mean": pd_max_mu, "sample_sd": pd_max_sd},
        "cmg_max_error_deg": {"mean": cmg_max_mu, "sample_sd": cmg_max_sd},
        "paired_mean_improvement_percent": {"mean": imp_mean_mu, "sample_sd": imp_mean_sd},
        "paired_max_improvement_percent": {"mean": imp_max_mu, "sample_sd": imp_max_sd},
        "aggregate_improvement_from_group_means_percent": 100.0 * (pd_mean_mu - cmg_mean_mu) / pd_mean_mu,
        "cmg_gate_mean_across_trials": np.mean(gate_means, axis=0).tolist(),
        "cmg_gate_between_trial_sample_sd": np.std(gate_means, axis=0, ddof=1).tolist(),
        "all_runs_completed": all(run["summary"]["run_completed"] for run in runs),
        "all_abort_reasons_empty": all(not run["summary"]["abort_reason"] for run in runs),
    }

    (args.output / "armed_roll_n3_summary.json").write_text(
        json.dumps({"aggregate": aggregate, "paired_trials": trial_rows}, indent=2),
        encoding="utf-8",
    )
    with (args.output / "armed_roll_n3_paired_trials.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(trial_rows[0]))
        writer.writeheader()
        writer.writerows(trial_rows)

    colors = ("#374151", "#0f766e")
    fig, axes = plt.subplots(2, 2, figsize=(11.0, 8.5))
    for i, (pd, cmg) in enumerate(zip(pd_runs, cmg_runs), 1):
        axes[0, 0].plot(pd["trace"]["t"], np.rad2deg(pd["trace"]["qerr_rad"]), color=colors[0], alpha=0.35, lw=1.0)
        axes[0, 0].plot(cmg["trace"]["t"], np.rad2deg(cmg["trace"]["qerr_rad"]), color=colors[1], alpha=0.35, lw=1.0)
        axes[0, 1].plot(i, pd["metrics"]["angle_error_mean_deg"], "o", color=colors[0])
        axes[0, 1].plot(i, cmg["metrics"]["angle_error_mean_deg"], "o", color=colors[1])
        axes[0, 1].plot([i, i], [pd["metrics"]["angle_error_mean_deg"], cmg["metrics"]["angle_error_mean_deg"]], color="#9ca3af", lw=1)
    axes[0, 0].plot([], [], color=colors[0], label="PD")
    axes[0, 0].plot([], [], color=colors[1], label="Nengo CMG-PES")
    axes[0, 0].set(xlabel="time [s]", ylabel="quaternion error [deg]", title="All six physical traces")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].grid(alpha=0.25)
    axes[0, 1].set(xlabel="matched pair", ylabel="mean error [deg]", title="Paired trial outcome", xticks=(1, 2, 3))
    axes[0, 1].grid(alpha=0.25)

    axes[1, 0].bar((0, 1), (pd_mean_mu, cmg_mean_mu), yerr=(pd_mean_sd, cmg_mean_sd), capsize=5, color=colors)
    axes[1, 0].set_xticks((0, 1), ("PD", "Nengo\nCMG-PES"))
    axes[1, 0].set(ylabel="mean error [deg]", title="Group mean ± sample SD")
    axes[1, 0].grid(axis="y", alpha=0.25)

    axes[1, 1].bar(np.arange(3), paired_mean, color="#d97706")
    axes[1, 1].axhline(imp_mean_mu, color="k", ls="--", lw=1.2, label=f"mean={imp_mean_mu:.2f}%")
    axes[1, 1].set_xticks(np.arange(3), ("pair 1", "pair 2", "pair 3"))
    axes[1, 1].set(ylabel="mean-error improvement [%]", title="Paired improvement")
    axes[1, 1].legend(frameon=False)
    axes[1, 1].grid(axis="y", alpha=0.25)
    fig.suptitle("Armed Quanser 3DOF Hover Roll validation (n=3 per controller)")
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(args.output / f"armed_roll_n3_comparison.{suffix}", dpi=220 if suffix == "png" else None, bbox_inches="tight")
    plt.close(fig)

    source_files = []
    for run in runs:
        for name in ("summary.json", "trace.csv", "manifest.json", "neural_trace_2khz.npz", "neural_trace_schema.json"):
            path = run["directory"] / name
            if path.exists():
                source_files.append(path)
    products = sorted(path for path in args.output.iterdir() if path.is_file())
    manifest = {
        "schema": 1,
        "source_files": [{"path": str(p), "size": p.stat().st_size, "sha256": sha256(p)} for p in source_files],
        "compiled_files": [{"path": str(p), "size": p.stat().st_size, "sha256": sha256(p)} for p in products],
    }
    (args.output / "FROZEN_SHA256_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(aggregate, indent=2))


if __name__ == "__main__":
    main()
