"""Run the complete emulated 3DOF Hover neuron-family benchmark.

This runner never opens Q8.  It covers nominal and hard-pulse conditions with
one classical PD baseline plus fixed/PES CMG, LIF, ALIF, Izhikevich, and
LIFRate residual controllers.  Every neural run stores lossless 2-kHz data.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTROLLERS = (
    "pd",
    "nengo-cmg-fixed", "nengo-nef-pes",
    "nengo-lif-fixed", "nengo-lif-pes",
    "nengo-alif-fixed", "nengo-alif-pes",
    "nengo-izhikevich-fixed", "nengo-izhikevich-pes",
    "nengo-lifrate-fixed", "nengo-lifrate-pes",
)
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
PROFILES = {
    "roll": {"pulse_factor": 1.0, "reference_scale": 1.0, "transition": 0.0, "allocator": "fixed-bias"},
    "full3": {"pulse_factor": 1.0, "reference_scale": 1.0, "transition": 0.0, "allocator": "fixed-bias"},
    "hard45": {"pulse_factor": 0.05, "reference_scale": 1.0, "transition": 0.0, "allocator": "fixed-bias"},
    "hardstep": {"pulse_factor": 0.10, "reference_scale": 0.7, "transition": 0.5, "allocator": "stability-priority"},
    "yaw360": {"pulse_factor": 0.05, "reference_scale": 0.8, "transition": 0.0, "allocator": "stability-priority"},
}


def completed_summary(cell: Path) -> Path | None:
    for path in sorted(cell.glob("*/summary.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            if json.loads(path.read_text(encoding="utf-8")).get("run_completed"):
                return path
        except (OSError, json.JSONDecodeError):
            pass
    return None


def run_cell(spec: dict) -> dict:
    cell = Path(spec["cell"])
    cell.mkdir(parents=True, exist_ok=True)
    existing = completed_summary(cell)
    if existing is not None:
        return {**spec, "status": "existing", "summary": str(existing)}
    profile = PROFILES[spec["mission"]]
    command = [
        sys.executable, str(HERE / "run_hover_headless.py"),
        "--io", "emulated",
        "--controller", spec["controller"],
        "--mission", spec["mission"],
        "--duration", str(spec["duration"]),
        "--disturbance", spec["condition"],
        "--disturbance-scale", str(spec["disturbance_scale"]),
        "--output-root", str(cell),
        "--reference-scale", str(profile["reference_scale"]),
        "--hardstep-transition-s", str(profile["transition"]),
        "--allocation-policy", profile["allocator"],
        "--beta", "0.2",
        "--motor-residual-cap-volts", "0.2",
        "--learning-rate", "0.0002",
        "--k-error", "2",
        "--k-rate", "0",
        "--residual-slew-v-per-s", "1",
        "--max-abs-pitch-deg", "180",
        "--max-abs-roll-deg", "180",
    ]
    started = time.perf_counter()
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    summary = completed_summary(cell)
    return {
        **spec,
        "status": "completed" if result.returncode == 0 and summary else "failed",
        "returncode": result.returncode,
        "wall_seconds": time.perf_counter() - started,
        "summary": None if summary is None else str(summary),
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path,
        default=HERE / "results" / "hover_neuron_family_matched_25s_2026-09-01",
    )
    parser.add_argument("--duration", type=float, default=25.0)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument(
        "--conditions", nargs="+", choices=("none", "hard-pulses"),
        default=("none", "hard-pulses"),
    )
    args = parser.parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    specs = []
    for condition in args.conditions:
        condition_label = "nominal" if condition == "none" else "hard-pulses"
        for mission in MISSIONS:
            disturbance_scale = 0.0 if condition == "none" else PROFILES[mission]["pulse_factor"]
            for controller in CONTROLLERS:
                specs.append({
                    "condition": condition,
                    "condition_label": condition_label,
                    "mission": mission,
                    "controller": controller,
                    "duration": args.duration,
                    "disturbance_scale": disturbance_scale,
                    "cell": str(args.output_root / condition_label / mission / controller),
                })
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(run_cell, spec): spec for spec in specs}
        for index, future in enumerate(as_completed(futures), 1):
            record = future.result()
            results.append(record)
            print(
                f"[{index:03d}/{len(specs):03d}] {record['status']:9s} "
                f"{record['condition_label']}/{record['mission']}/{record['controller']}",
                flush=True,
            )
            (args.output_root / "campaign_manifest.partial.json").write_text(
                json.dumps({"schema": 1, "runs": results}, indent=2) + "\n",
                encoding="utf-8",
            )
    results.sort(key=lambda r: (r["condition_label"], MISSIONS.index(r["mission"]), CONTROLLERS.index(r["controller"])))
    payload = {
        "schema": 1,
        "platform": "emulated Quanser 3DOF Hover",
        "hardware_output": False,
        "duration_s": args.duration,
        "hardware_dt_s": 0.005,
        "neural_dt_s": 0.0005,
        "beta": 0.2,
        "motor_residual_cap_V": 0.2,
        "learning_rate": 0.0002,
        "k_error": 2.0,
        "k_rate": 0.0,
        "residual_slew_V_per_s": 1.0,
        "simulation_divergence_limit_deg": 180.0,
        "mission_profiles": PROFILES,
        "controllers": list(CONTROLLERS),
        "conditions": list(args.conditions),
        "full_neural_archive": True,
        "runs": results,
    }
    (args.output_root / "campaign_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    failures = [record for record in results if record["status"] == "failed"]
    print(f"Campaign cells={len(results)} failures={len(failures)} output={args.output_root}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
