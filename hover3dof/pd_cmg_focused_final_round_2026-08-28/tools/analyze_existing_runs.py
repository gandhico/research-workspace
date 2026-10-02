"""Read-only audit of existing 3DOF Hover result folders.

The script never imports Quanser, never opens hardware, and never writes files.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(r"C:\Research\hover3dof\results\hardware")
DOCUMENTED_EXTERNAL_TOUCH = "online-pes-adaptive_armed_20260828_112330"


def load_runs() -> list[dict]:
    runs: list[dict] = []
    for folder in sorted(ROOT.iterdir()):
        summary_path = folder / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["run"] = folder.name
        trace_path = folder / "trace.csv"
        if trace_path.exists():
            with trace_path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            if rows and "residual_norm" in rows[0]:
                summary["residual_mean"] = mean(float(row["residual_norm"]) for row in rows)
                summary["gate_mean"] = mean(float(row["gate_mean"]) for row in rows)
                for channel in ("Vf", "Vb", "Vl", "Vr"):
                    summary[f"{channel}_zero_fraction"] = mean(
                        float(row[channel]) <= 1e-9 for row in rows
                    )
        runs.append(summary)
    return runs


def describe(values: list[float]) -> str:
    if not values:
        return "n=0"
    if len(values) == 1:
        return f"n=1, {values[0]:.4f}"
    return f"n={len(values)}, {mean(values):.4f} +/- {stdev(values):.4f}"


def same_condition(run: dict, *, controller: str, mission: str, duration: float, **cfg: float) -> bool:
    if run.get("controller") != controller or run.get("mission") != mission:
        return False
    if float(run.get("duration", -1)) != duration:
        return False
    return all(float(run.get(key, float("nan"))) == value for key, value in cfg.items())


def main() -> None:
    runs = load_runs()
    print(f"Loaded {len(runs)} result folders from {ROOT}")

    classical_25 = [r for r in runs if r.get("controller") == "classical" and r.get("mission") == "yaw360" and r.get("duration") == 25.0]
    classical_30 = [r for r in runs if r.get("controller") == "classical" and r.get("mission") == "yaw360" and r.get("duration") == 30.0]
    set_k = [r for r in runs if same_condition(
        r, controller="online-pes-adaptive", mission="yaw360", duration=30.0,
        beta=0.4, learning_rate=0.0003, max_residual_volts=3.0,
        k_error=2.0, k_rate=0.0,
    )]

    print("\nYaw360 condition audit")
    print("classical 25 s mean error:", describe([r["angle_err_mean_deg"] for r in classical_25]))
    print("classical 30 s mean error:", describe([r["angle_err_mean_deg"] for r in classical_30]))
    print("Set K 30 s mean error:    ", describe([r["angle_err_mean_deg"] for r in set_k]))
    print("Set K 30 s peak error:    ", describe([r["angle_err_max_deg"] for r in set_k]))

    clean_k = [r for r in set_k if r["run"] != DOCUMENTED_EXTERNAL_TOUCH]
    print("Set K clean mean error:   ", describe([r["angle_err_mean_deg"] for r in clean_k]))
    print("Set K clean peak error:   ", describe([r["angle_err_max_deg"] for r in clean_k]))

    if classical_30 and clean_k:
        base_mean = mean(r["angle_err_mean_deg"] for r in classical_30)
        base_peak = mean(r["angle_err_max_deg"] for r in classical_30)
        k_mean = mean(r["angle_err_mean_deg"] for r in clean_k)
        k_peak = mean(r["angle_err_max_deg"] for r in clean_k)
        print(f"Clean-subset mean improvement: {100.0*(base_mean-k_mean)/base_mean:+.3f}%")
        print(f"Clean-subset peak improvement: {100.0*(base_peak-k_peak)/base_peak:+.3f}% (positive means lower/better)")
        print(f"Excluded documented external-touch run: {DOCUMENTED_EXTERNAL_TOUCH}")

    if classical_30:
        baseline = mean(r["angle_err_mean_deg"] for r in classical_30)
        for run in set_k:
            improvement = 100.0 * (baseline - run["angle_err_mean_deg"]) / baseline
            print(f"  {run['run']}: matched-30s mean improvement = {improvement:+.3f}%")

    print("\nAll Set-K trace diagnostics")
    for run in set_k:
        payload = {
            key: run.get(key) for key in (
                "run", "angle_err_mean_deg", "angle_err_max_deg", "residual_mean",
                "gate_mean", "Vf_zero_fraction", "Vb_zero_fraction",
                "Vl_zero_fraction", "Vr_zero_fraction",
            )
        }
        payload["documented_external_touch"] = run["run"] == DOCUMENTED_EXTERNAL_TOUCH
        print(json.dumps(payload, indent=2))

    if classical_25 and set_k:
        print("\nWARNING: Comparing Set K (30 s) to classical (25 s) is invalid: yaw360 uses duration inside the reference trajectory.")


if __name__ == "__main__":
    main()
