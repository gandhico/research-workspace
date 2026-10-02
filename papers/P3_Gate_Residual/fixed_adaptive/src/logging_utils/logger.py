"""
Logging utilities: CSV, JSON summary, NPZ, and run configuration.
"""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any

import numpy as np


def make_stem(quad: str, mission: str, controller: str,
              dt: float, sim_time: float, seed: int,
              extra: str = "") -> str:
    """Build a descriptive, collision-resistant filename stem."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    parts = [quad, mission, controller,
             f"dt{dt:g}", f"T{sim_time:g}", f"s{seed}", ts]
    if extra:
        parts.append(extra.replace(" ", "_"))
    return "_".join(parts)


def save_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def save_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)


def save_npz(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = {k: np.array([r[k] for r in rows], dtype=float) for k in rows[0]}
    np.savez_compressed(str(path), **arr)


def save_run_config(config: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, default=str)


def compute_summary(rows: list[dict], tau_limit: np.ndarray, params_info: dict = {}) -> dict:
    """Compute benchmark summary metrics from simulation log rows."""
    if not rows:
        return {"status": "empty"}

    arr = {k: np.array([r[k] for r in rows], dtype=float) for k in rows[0]}
    tau = np.column_stack([arr["tau_x"], arr["tau_y"], arr["tau_z"]])
    tau_norm = np.linalg.norm(tau, axis=1)
    sat = np.any(np.isclose(np.abs(tau), tau_limit, atol=1e-9), axis=1)

    euler_err = np.column_stack([arr["phi_err"], arr["theta_err"], arr["psi_err"]])

    summary = {
        "status":          "ok",
        "rmse_phi":        float(np.sqrt(np.mean(euler_err[:, 0]**2))),
        "rmse_theta":      float(np.sqrt(np.mean(euler_err[:, 1]**2))),
        "rmse_psi":        float(np.sqrt(np.mean(euler_err[:, 2]**2))),
        "rmse_euler_mean": float(np.mean(np.sqrt(np.mean(euler_err**2, axis=0)))),
        "qerr_mean":       float(np.mean(arr["qerr_angle"])),
        "qerr_max":        float(np.max(arr["qerr_angle"])),
        "tau_mean":        float(np.mean(tau_norm)),
        "tau_max":         float(np.max(tau_norm)),
        "sat_fraction":    float(np.mean(sat)),
        "z_mean":          float(np.mean(arr["z"])),
        "z_std":           float(np.std(arr["z"])),
        "event_count":     float(np.sum(arr.get("event_count", np.zeros(len(rows))))),
        "activity_mean":   float(np.mean(arr.get("activity_mean", np.zeros(len(rows))))),
        "gate_mean":       float(np.mean(arr.get("gate_mean", np.zeros(len(rows))))),
    }

    # Rotor metrics (if present)
    rotor_keys = ["motor_1", "motor_2", "motor_3", "motor_4"]
    if all(k in arr for k in rotor_keys):
        motors = np.column_stack([arr[k] for k in rotor_keys])
        summary["rotor_f_mean"] = float(np.mean(motors))
        summary["rotor_f_max"]  = float(np.max(motors))
        summary["rotor_f_min"]  = float(np.min(motors))
        if "rotor_sat_flag" in arr:
            summary["rotor_sat_fraction"] = float(np.mean(arr["rotor_sat_flag"] > 0))

    summary["score"] = (
        summary["qerr_mean"]
        + 0.02 * summary["tau_mean"]
        + 0.20 * summary["sat_fraction"]
        + 0.05 * summary["z_std"]
    )

    summary.update(params_info)
    return summary
