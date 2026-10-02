"""Replay the new torque-space CMG signal path on a frozen classical trace.

This is a controller/safety-envelope check, not a counterfactual plant simulation.
It reads files and prints metrics only; no Quanser import and no file writes.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ACC_SRC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\src")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ACC_SRC))

from pd_baseline import (  # noqa: E402
    VendorPlant,
    euler_rates_ypr_to_body_omega_ypr,
    limit_and_slew_motor_residual,
    mujoco_pd_parameters_ypr,
    mujoco_pes_target_ypr,
    mujoco_quaternion_pd_torque_ypr,
    realized_torque,
    torque_to_motor_differential,
)
from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from gra_control.math3d import euler_to_quat, quat_error  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--beta", type=float, default=.5)
    parser.add_argument("--motor-residual-cap-volts", type=float, default=1.2)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=8.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument("--residual-slew-v-per-s", type=float, default=4.0)
    parser.add_argument("--neural-substeps", type=int, default=10)
    args = parser.parse_args()

    with (args.run_dir / "trace.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    summary = json.loads((args.run_dir / "summary.json").read_text(encoding="utf-8"))
    if summary.get("controller") != "classical":
        raise SystemExit("Replay input must be a classical trace")

    plant = VendorPlant()
    dt = 1.0 / float(summary["rate_hz"])
    _, _, limits = mujoco_pd_parameters_ypr(plant)
    augmentor = CMGResidualAugmentor(3, limits, "online_pes", True, args.beta, learning_rate=args.learning_rate)
    previous = np.zeros(4)
    applied_history = []
    command_history = []
    requested_tau_history = []
    realized_tau_history = []
    gates = []

    for row in rows:
        desired = np.deg2rad([float(row["yaw_ref_deg"]), float(row["pitch_ref_deg"]), float(row["roll_ref_deg"])])
        angle = np.deg2rad([float(row["yaw_deg"]), float(row["pitch_deg"]), float(row["roll_deg"])])
        rate = np.deg2rad([float(row["yaw_rate_dps"]), float(row["pitch_rate_dps"]), float(row["roll_rate_dps"])])
        q_ref = euler_to_quat(desired[2], desired[1], desired[0])
        q_meas = euler_to_quat(angle[2], angle[1], angle[0])
        _, eq_xyz = quat_error(q_ref, q_meas)
        eq_ypr = eq_xyz[[2, 1, 0]]
        body_omega = euler_rates_ypr_to_body_omega_ypr(angle, rate)
        tau0 = mujoco_quaternion_pd_torque_ypr(eq_ypr, body_omega, plant)
        baseline_raw = plant.bias_voltage + torque_to_motor_differential(tau0, plant)
        baseline = np.clip(baseline_raw, 0.0, 24.0)
        gate_drive = tau0
        target = mujoco_pes_target_ypr(eq_ypr, body_omega, args.k_error, args.k_rate)
        out = None
        for _ in range(args.neural_substeps):
            out = augmentor.step(gate_drive, dt / args.neural_substeps, target)
        requested_tau = out.residual
        requested_v = torque_to_motor_differential(requested_tau, plant)
        applied_v = limit_and_slew_motor_residual(
            requested_v, previous, args.motor_residual_cap_volts,
            args.residual_slew_v_per_s, dt,
        )
        previous = applied_v
        command = np.clip(baseline_raw + applied_v, 0.0, 24.0)
        realized_delta_tau = realized_torque(command, plant) - realized_torque(baseline, plant)
        applied_history.append(applied_v)
        command_history.append(command)
        requested_tau_history.append(requested_tau)
        realized_tau_history.append(realized_delta_tau)
        gates.append(float(np.mean(out.gate)))

    applied = np.vstack(applied_history)
    command = np.vstack(command_history)
    requested_tau = np.vstack(requested_tau_history)
    realized_tau = np.vstack(realized_tau_history)
    slew = np.abs(np.diff(applied, axis=0)) / dt
    result = {
        "source_run": args.run_dir.name,
        "mission": summary["mission"],
        "samples": len(rows),
        "actual_motor_residual_cap_V": args.motor_residual_cap_volts,
        "beta": args.beta,
        "learning_rate": args.learning_rate,
        "k_error": args.k_error,
        "neural_substeps": args.neural_substeps,
        "neural_dt_s": dt / args.neural_substeps,
        "max_abs_applied_motor_residual_V": float(np.max(np.abs(applied))),
        "max_applied_motor_residual_slew_V_per_s": float(np.max(slew)),
        "command_min_V": float(np.min(command)),
        "command_max_V": float(np.max(command)),
        "requested_residual_torque_rms_Nm": float(np.sqrt(np.mean(requested_tau**2))),
        "realized_residual_torque_rms_Nm": float(np.sqrt(np.mean(realized_tau**2))),
        "mean_gate": float(np.mean(gates)),
        "all_bounds_pass": bool(
            np.max(np.abs(applied)) <= args.motor_residual_cap_volts + 1e-12
            and np.max(slew) <= args.residual_slew_v_per_s + 1e-9
            and np.min(command) >= 0.0
            and np.max(command) <= 24.0
        ),
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["all_bounds_pass"] else 1)


if __name__ == "__main__":
    main()
