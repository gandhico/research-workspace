#!/usr/bin/env python3
"""Identify a physics-structured roll/pitch model from an X-Plane CSV log."""

import argparse
import json
from pathlib import Path

import numpy as np


def smooth(values, window):
    if window <= 1:
        return values.copy()
    kernel = np.ones(window) / window
    pad = window // 2
    return np.vstack([
        np.convolve(np.pad(values[:, i], pad, mode="edge"), kernel, mode="valid")[: len(values)]
        for i in range(values.shape[1])
    ]).T


def identify(path, ridge=1.0, smooth_window=5):
    if smooth_window < 1 or smooth_window % 2 == 0:
        raise ValueError("smooth_window must be a positive odd integer")
    if ridge < 0:
        raise ValueError("ridge must be non-negative")
    data = np.genfromtxt(path, delimiter=",", names=True, encoding=None)
    required = {"t_s", "roll_deg", "pitch_deg", "xpc_ctrl_aileron", "xpc_ctrl_elevator"}
    missing = required.difference(data.dtype.names or ())
    if missing:
        raise ValueError("missing CSV columns: " + ", ".join(sorted(missing)))
    t = np.asarray(data["t_s"])
    dt = float(np.median(np.diff(t)))
    angles = np.c_[data["roll_deg"], data["pitch_deg"]]
    controls = np.c_[data["xpc_ctrl_aileron"], data["xpc_ctrl_elevator"]]
    filtered = smooth(angles, smooth_window)
    rates = np.gradient(filtered, dt, axis=0)
    accelerations = np.gradient(rates, dt, axis=0)
    state = np.c_[filtered, rates]

    # Fit only the acceleration rows. The angle rows retain exact kinematics.
    use = slice(2, len(t) - 2)
    features = np.c_[state[use], controls[use], np.ones(len(state[use]))]
    targets = accelerations[use]
    scale = features.std(axis=0)
    scale[scale < 1e-12] = 1.0
    scale[-1] = 1.0
    z = features / scale
    penalty = np.eye(z.shape[1]) * ridge
    penalty[-1, -1] = 0.0
    coefficients = np.linalg.solve(z.T @ z + penalty, z.T @ targets) / scale[:, None]
    F = coefficients[:4].T
    G = coefficients[4:6].T
    bias = coefficients[6].T

    A = np.eye(4)
    A[0, 2] = dt
    A[1, 3] = dt
    A[2:, :] += dt * F
    B = np.zeros((4, 2))
    B[2:, :] = dt * G
    trim_state = np.r_[np.mean(angles[use], axis=0), [0.0, 0.0]]
    trim_input = np.mean(controls[use], axis=0)
    prediction = features @ coefficients
    rmse = np.sqrt(np.mean((targets - prediction) ** 2, axis=0))
    controllability = np.c_[B, A @ B, A @ A @ B, A @ A @ A @ B]
    return {
        "source_csv": str(Path(path).resolve()), "dt_s": dt,
        "A": A.tolist(), "B": B.tolist(), "acceleration_bias": bias.tolist(),
        "trim_state": trim_state.tolist(), "trim_input": trim_input.tolist(),
        "acceleration_fit_rmse_deg_s2": rmse.tolist(),
        "controllability_rank": int(np.linalg.matrix_rank(controllability)),
        "samples": int(len(t)), "ridge": ridge, "smooth_window": smooth_window,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv")
    parser.add_argument("--out", default="lqr_model.json")
    parser.add_argument("--ridge", type=float, default=1.0)
    parser.add_argument("--smooth-window", type=int, default=5)
    args = parser.parse_args()
    try:
        model = identify(args.csv, args.ridge, args.smooth_window)
    except ValueError as error:
        parser.error(str(error))
    Path(args.out).write_text(json.dumps(model, indent=2) + "\n")
    print("Saved model:", Path(args.out).resolve())
    print("Controllability rank:", model["controllability_rank"])
    print("Acceleration-fit RMSE [roll, pitch]:", model["acceleration_fit_rmse_deg_s2"])


if __name__ == "__main__":
    main()
