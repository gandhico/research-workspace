"""Offline replay of the stability-priority allocator on a saved hardware trace.

This does not predict a new closed-loop trajectory. It answers whether the new
allocation would keep motors active and better preserve the requested
pitch/roll moments at the exact states recorded in an old run.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pd_baseline import (  # noqa: E402
    VendorPlant,
    allocate_stability_priority_torque,
    realized_torque,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--motor-floor-volts", type=float, default=2.0)
    args = parser.parse_args()
    with (args.run_dir / "trace.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    summary = json.loads((args.run_dir / "summary.json").read_text(encoding="utf-8"))
    plant = VendorPlant()
    axes = ("yaw", "pitch", "roll")
    motors = ("Vf", "Vb", "Vl", "Vr")
    requested = []
    old_realized = []
    new_realized = []
    new_voltage = []
    yaw_scale = []
    pitch_roll_scale = []
    common = []
    for row in rows:
        tau0 = np.array([float(row[f"tau0_{axis}"]) for axis in axes])
        if summary["controller"] == "pd-cmg":
            applied_delta_v = np.array([float(row[f"{motor}_delta_applied"]) for motor in motors])
            tau = tau0 + realized_torque(applied_delta_v, plant)
        else:
            tau = tau0
        old_voltage = np.array([float(row[f"{motor}_computed"]) for motor in motors])
        allocation = allocate_stability_priority_torque(tau, plant, args.motor_floor_volts)
        requested.append(tau)
        old_realized.append(realized_torque(old_voltage, plant))
        new_realized.append(allocation.realized_torque_ypr)
        new_voltage.append(allocation.voltage_fblr)
        yaw_scale.append(allocation.yaw_scale)
        pitch_roll_scale.append(allocation.pitch_roll_scale)
        common.append(allocation.common_mode_voltage)
    requested_a = np.vstack(requested)
    old_a = np.vstack(old_realized)
    new_a = np.vstack(new_realized)
    voltage_a = np.vstack(new_voltage)
    result = {
        "source_run": args.run_dir.name,
        "mission": summary["mission"],
        "controller": summary["controller"],
        "source_abort": summary.get("abort_reason", ""),
        "samples": len(rows),
        "motor_floor_V": args.motor_floor_volts,
        "new_motor_min_V": float(np.min(voltage_a)),
        "new_motor_max_V": float(np.max(voltage_a)),
        "new_motor_below_floor_count": int(np.sum(voltage_a < args.motor_floor_volts - 1e-9)),
        "old_torque_error_rms_ypr_Nm": np.sqrt(np.mean((requested_a - old_a)**2, axis=0)).tolist(),
        "new_torque_error_rms_ypr_Nm": np.sqrt(np.mean((requested_a - new_a)**2, axis=0)).tolist(),
        "old_pitch_roll_error_rms_Nm": float(np.sqrt(np.mean((requested_a[:, 1:] - old_a[:, 1:])**2))),
        "new_pitch_roll_error_rms_Nm": float(np.sqrt(np.mean((requested_a[:, 1:] - new_a[:, 1:])**2))),
        "yaw_scale_min": float(np.min(yaw_scale)),
        "yaw_scale_mean": float(np.mean(yaw_scale)),
        "pitch_roll_scale_min": float(np.min(pitch_roll_scale)),
        "pitch_roll_scale_mean": float(np.mean(pitch_roll_scale)),
        "common_mode_V_min": float(np.min(common)),
        "common_mode_V_max": float(np.max(common)),
        "closed_loop_prediction": False,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
