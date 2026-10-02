"""Prove explicit axis PD reproduces frozen classical LQR voltage traces.

Reads existing CSV/JSON only. No Quanser import and no file writes.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pd_baseline import VendorPlant, pd_voltage_raw  # noqa: E402


CHANNELS = ("Vf", "Vb", "Vl", "Vr")


def validate(run_dir: Path) -> dict:
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    if summary.get("controller") != "classical":
        raise ValueError(f"{run_dir} is not a classical run")
    with (run_dir / "trace.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    differences: list[np.ndarray] = []
    plant = VendorPlant()
    for row in rows:
        desired = np.deg2rad([float(row["yaw_ref_deg"]), float(row["pitch_ref_deg"]), float(row["roll_ref_deg"])])
        angle = np.deg2rad([float(row["yaw_deg"]), float(row["pitch_deg"]), float(row["roll_deg"])])
        rate = np.deg2rad([float(row["yaw_rate_dps"]), float(row["pitch_rate_dps"]), float(row["roll_rate_dps"])])
        reconstructed = np.clip(pd_voltage_raw(desired, angle, rate, plant), 0.0, 24.0)
        recorded = np.array([float(row[channel]) for channel in CHANNELS])
        differences.append(reconstructed - recorded)
    delta = np.vstack(differences)
    return {
        "run": run_dir.name,
        "mission": summary.get("mission"),
        "samples": len(rows),
        "max_abs_voltage_difference": float(np.max(np.abs(delta))),
        "rms_voltage_difference": float(np.sqrt(np.mean(delta**2))),
        "passed_1e-9_volts": bool(np.max(np.abs(delta)) < 1e-9),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for run_dir in args.run_dirs:
        result = validate(run_dir)
        print(json.dumps(result, indent=2))
        failed |= not result["passed_1e-9_volts"]
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()

