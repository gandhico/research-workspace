from __future__ import annotations

import numpy as np


def rmse(x: np.ndarray, axis=0) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return np.sqrt(np.mean(x**2, axis=axis))


def summarize_controller_run(rows: list[dict], tau_limit: np.ndarray) -> dict:
    if not rows:
        return {"status": "empty"}

    arr = {key: np.array([row[key] for row in rows], dtype=float) for key in rows[0]}

    euler_err = np.column_stack(
        [
            arr["phi_err"],
            arr["theta_err"],
            arr["psi_err"],
        ]
    )

    tau = np.column_stack(
        [
            arr["tau_x"],
            arr["tau_y"],
            arr["tau_z"],
        ]
    )

    tau_norm = np.linalg.norm(tau, axis=1)

    sat = np.any(np.isclose(np.abs(tau), tau_limit, atol=1e-9), axis=1)

    summary = {
        "status": "ok",
        "rmse_phi": float(np.sqrt(np.mean(euler_err[:, 0] ** 2))),
        "rmse_theta": float(np.sqrt(np.mean(euler_err[:, 1] ** 2))),
        "rmse_psi": float(np.sqrt(np.mean(euler_err[:, 2] ** 2))),
        "rmse_euler_mean": float(np.mean(np.sqrt(np.mean(euler_err**2, axis=0)))),
        "qerr_mean": float(np.mean(arr["qerr_angle"])),
        "qerr_max": float(np.max(arr["qerr_angle"])),
        "tau_mean": float(np.mean(tau_norm)),
        "tau_max": float(np.max(tau_norm)),
        "sat_fraction": float(np.mean(sat)),
        "z_mean": float(np.mean(arr["z"])),
        "z_std": float(np.std(arr["z"])),
        "event_count": float(np.sum(arr.get("event_count_step", np.zeros_like(arr["t"])))),
        "activity_mean": float(np.mean(arr.get("activity_mean", np.zeros_like(arr["t"])))),
        "activity_max": float(np.max(arr.get("activity_max", np.zeros_like(arr["t"])))),
    }

    summary["score"] = (
        summary["qerr_mean"]
        + 0.02 * summary["tau_mean"]
        + 0.20 * summary["sat_fraction"]
        + 0.05 * summary["z_std"]
    )

    if "allocation_error_norm" in arr:
        summary["allocation_error_mean"] = float(np.mean(arr["allocation_error_norm"]))
        summary["allocation_error_max"] = float(np.max(arr["allocation_error_norm"]))

    rotor_keys = ["rotor_f1", "rotor_f2", "rotor_f3", "rotor_f4"]
    if all(key in arr for key in rotor_keys):
        rotor_f = np.column_stack([arr[key] for key in rotor_keys])
        summary["rotor_f_mean"] = float(np.mean(rotor_f))
        summary["rotor_f_max"] = float(np.max(rotor_f))
        summary["rotor_f_min"] = float(np.min(rotor_f))

    if "rotor_saturation_flag" in arr:
        summary["rotor_saturation_fraction"] = float(np.mean(arr["rotor_saturation_flag"] > 0.5))
    elif "rotor_saturation_count" in arr:
        summary["rotor_saturation_fraction"] = float(np.mean(arr["rotor_saturation_count"] > 0.0))

    return summary
