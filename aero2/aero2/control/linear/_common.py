"""Shared helpers for the linear controllers (Ref 3 §Linear control).

Plant matrices come from `models.linear_2dof` (single source). `u_ff` enforces
zero pitch/yaw acceleration at the reference by least squares.
"""
from __future__ import annotations

import numpy as np
from scipy.linalg import expm

from aero2.models.linear_2dof import linear_plant_matrices


def plant_matrices():
    return linear_plant_matrices()


def discretize(A, B, dt):
    n, m = A.shape[0], B.shape[1]
    block = np.zeros((n + m, n + m))
    block[:n, :n] = A
    block[:n, n:] = B
    out = expm(block * float(dt))
    return out[:n, :n], out[:n, n:]


def reference_state(theta_ref, psi_ref) -> np.ndarray:
    return np.array([float(theta_ref), 0.0, float(psi_ref), 0.0])


def feedforward_for_reference(A, B, x_ref, voltage_limit) -> np.ndarray:
    """Least-squares u_ff for zero pitch/yaw acceleration at x_ref (Ref 3)."""
    accel_rows = np.array([1, 3])
    M = B[accel_rows, :]
    rhs = -(A @ x_ref)[accel_rows]
    u_ff = np.linalg.lstsq(M, rhs, rcond=None)[0]
    return np.clip(u_ff, -abs(float(voltage_limit)), abs(float(voltage_limit)))


def clamp(u, voltage_limit) -> np.ndarray:
    return np.clip(np.asarray(u, dtype=float).reshape(2), -abs(float(voltage_limit)), abs(float(voltage_limit)))


__all__ = ["plant_matrices", "discretize", "reference_state", "feedforward_for_reference", "clamp"]
