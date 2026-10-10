"""Freeze and visualize the final armed Nengo/PD 3DOF Hover campaign.

The script deliberately distinguishes completed matched pairs from the
safety-aborted Yaw360 feasibility run. Positive improvement means CMG-PES
reduced the corresponding PD error metric.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np



# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import HOVER_RESULTS  # noqa: E402

PROJECT = HOVER_RESULTS
HARDWARE = PROJECT / "results" / "hardware"
OUTPUT = PROJECT / "results" / "final_hardware_campaign_2026-09-01"

PAIRS = {
    "full3": (
        "pd_full3_none_armed_20260901_151111",
        "nengo-pes_full3_none_armed_20260901_152413",
    ),
    "hard45": (
        "pd_hard45_none_armed_20260901_152529",
        "nengo-pes_hard45_none_armed_20260901_152621",
    ),
    "hardstep": (
        "pd_hardstep_none_armed_20260901_152724",
        "nengo-pes_hardstep_none_armed_20260901_152815",
    ),
}
YAW_ABORT = "pd_yaw360_none_armed_20260901_152926"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_run(name: str) -> dict:
    directory = HARDWARE / name
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    trace = np.genfromtxt(directory / "trace.csv", delimiter=",", names=True)
    return {"name": name, "directory": directory, "summary": summary, "trace": trace}


def improvement(pd_value: float, cmg_value: float) -> float:
    return 100.0 * (pd_value - cmg_value) / pd_value


def plot_pair(mission: str, pd: dict, cmg: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 7.5), sharex=True)
    colors = {"PD": "#374151", "CMG-PES": "#0f766e", "reference": "#d97706"}
    for label, run in (("PD", pd), ("CMG-PES", cmg)):
        tr = run["trace"]
        axes[0, 0].plot(tr["t"], np.rad2deg(tr["qerr_rad"]), lw=1.5, color=colors[label], label=label)
        axes[0, 1].plot(tr["t"], tr["yaw_deg"], lw=1.3, color=colors[label], label=label)
        axes[1, 0].plot(tr["t"], tr["pitch_deg"], lw=1.3, color=colors[label], label=label)
        axes[1, 1].plot(tr["t"], tr["roll_deg"], lw=1.3, color=colors[label], label=label)
    refs = pd["trace"]
    axes[0, 1].plot(refs["t"], refs["yaw_ref_deg"], "--", lw=1.2, color=colors["reference"], label="reference")
    axes[1, 0].plot(refs["t"], refs["pitch_ref_deg"], "--", lw=1.2, color=colors["reference"], label="reference")
    axes[1, 1].plot(refs["t"], refs["roll_ref_deg"], "--", lw=1.2, color=colors["reference"], label="reference")
    axes[0, 0].set_title("Quaternion-angle error")
    axes[0, 1].set_title("Yaw tracking")
    axes[1, 0].set_title("Pitch tracking")
    axes[1, 1].set_title("Roll tracking")
    axes[0, 0].set_ylabel("error [deg]")
    axes[0, 1].set_ylabel("yaw [deg]")
    axes[1, 0].set_ylabel("pitch [deg]")
    axes[1, 1].set_ylabel("roll [deg]")
    for ax in axes.flat:
        ax.set_xlabel("time [s]")
        ax.grid(alpha=0.25)
        ax.legend(frameon=False, fontsize=8)
    pds = pd["summary"]
    cms = cmg["summary"]
    fig.suptitle(
        f"Quanser 3DOF Hover: {mission} | mean {pds['angle_err_mean_deg']:.3f}° → "
        f"{cms['angle_err_mean_deg']:.3f}° ({improvement(pds['angle_err_mean_deg'], cms['angle_err_mean_deg']):+.2f}%)"
    )
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT / f"{mission}_pd_vs_nengo_cmg_pes.{suffix}", dpi=220 if suffix == "png" else None, bbox_inches="tight")
    plt.close(fig)


def plot_yaw_abort(run: dict) -> None:
    tr = run["trace"]
    summary = run["summary"]
    fig, axes = plt.subplots(3, 1, figsize=(10.5, 8.5), sharex=True)
    axes[0].plot(tr["t"], tr["yaw_ref_deg"], "--", color="#d97706", label="yaw reference")
    axes[0].plot(tr["t"], tr["yaw_deg"], color="#374151", label="measured yaw")
    axes[0].set_ylabel("yaw [deg]")
    axes[1].plot(tr["t"], tr["pitch_deg"], label="pitch", color="#2563eb")
    axes[1].plot(tr["t"], tr["roll_deg"], label="roll", color="#dc2626")
    axes[1].axhline(20, color="#111827", ls=":", lw=1, label="±20° safety limit")
    axes[1].axhline(-20, color="#111827", ls=":", lw=1)
    axes[1].set_ylabel("cross-axis angle [deg]")
    axes[2].plot(tr["t"], np.rad2deg(tr["qerr_rad"]), color="#7c3aed", label="quaternion error")
    axes[2].set_ylabel("error [deg]")
    axes[2].set_xlabel("time [s]")
    for ax in axes:
        ax.grid(alpha=0.25)
        ax.legend(frameon=False)
    fig.suptitle(f"Yaw360 PD feasibility run — SAFETY ABORT: {summary['abort_reason']}")
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        fig.savefig(OUTPUT / f"yaw360_pd_safety_abort.{suffix}", dpi=220 if suffix == "png" else None, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = []
    loaded = []
    for mission, (pd_name, cmg_name) in PAIRS.items():
        pd = load_run(pd_name)
        cmg = load_run(cmg_name)
        loaded.extend((pd, cmg))
        pds, cms = pd["summary"], cmg["summary"]
        rows.append(
            {
                "mission": mission,
                "status": "completed matched pair" if pds["run_completed"] and cms["run_completed"] else "incomplete",
                "reference_scale": pds["config"]["reference_scale"],
                "duration_s": pds["config"]["duration"],
                "pd_mean_error_deg": pds["angle_err_mean_deg"],
                "cmg_mean_error_deg": cms["angle_err_mean_deg"],
                "mean_error_improvement_percent": improvement(pds["angle_err_mean_deg"], cms["angle_err_mean_deg"]),
                "pd_max_error_deg": pds["angle_err_max_deg"],
                "cmg_max_error_deg": cms["angle_err_max_deg"],
                "max_error_improvement_percent": improvement(pds["angle_err_max_deg"], cms["angle_err_max_deg"]),
                "pd_raw_home_yaw_deg": pds["raw_home_ypr_deg"][0],
                "cmg_raw_home_yaw_deg": cms["raw_home_ypr_deg"][0],
                "pd_run": pd_name,
                "cmg_run": cmg_name,
            }
        )
        plot_pair(mission, pd, cmg)

    yaw = load_run(YAW_ABORT)
    loaded.append(yaw)
    ys = yaw["summary"]
    rows.append(
        {
            "mission": "yaw360",
            "status": f"PD safety abort; CMG not run: {ys['abort_reason']}",
            "reference_scale": ys["config"]["reference_scale"],
            "duration_s": ys["config"]["duration"],
            "pd_mean_error_deg": ys["angle_err_mean_deg"],
            "cmg_mean_error_deg": "",
            "mean_error_improvement_percent": "",
            "pd_max_error_deg": ys["angle_err_max_deg"],
            "cmg_max_error_deg": "",
            "max_error_improvement_percent": "",
            "pd_raw_home_yaw_deg": ys["raw_home_ypr_deg"][0],
            "cmg_raw_home_yaw_deg": "",
            "pd_run": YAW_ABORT,
            "cmg_run": "not run for safety",
        }
    )
    plot_yaw_abort(yaw)

    with (OUTPUT / "campaign_results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    package = {
        "schema": 1,
        "date": "2026-09-01",
        "platform": "Quanser 3DOF Hover",
        "comparison": "MuJoCo-matched PD baseline vs Nengo CMG-PES residual controller",
        "coordinate_policy": "Each run tares current raw yaw/pitch/roll as its local zero; raw pose is retained in summary.json.",
        "cmg_configuration": {
            "beta": 0.2,
            "motor_residual_cap_V": 0.2,
            "learning_rate": 0.0002,
            "k_error": 2.0,
            "k_rate": 0.0,
            "residual_slew_V_per_s": 1.0,
        },
        "interpretation": {
            "positive_improvement_percent": "CMG-PES reduced error relative to PD",
            "yaw360": "No CMG performance comparison is permitted because the PD reference run safety-aborted.",
        },
        "results": rows,
    }
    (OUTPUT / "campaign_results.json").write_text(json.dumps(package, indent=2), encoding="utf-8")

    sources = []
    for run in loaded:
        for name in ("summary.json", "trace.csv", "manifest.json", "neural_trace_2khz.npz", "neural_trace_schema.json"):
            path = run["directory"] / name
            if path.exists():
                sources.append(path)
        analysis = run["directory"] / "analysis"
        if analysis.exists():
            sources.extend(sorted(path for path in analysis.iterdir() if path.is_file()))
    products = sorted(path for path in OUTPUT.iterdir() if path.is_file())
    manifest = {
        "schema": 1,
        "source_files": [{"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)} for path in sources],
        "compiled_files": [{"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)} for path in products],
    }
    (OUTPUT / "FROZEN_SHA256_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(package, indent=2))


if __name__ == "__main__":
    main()
