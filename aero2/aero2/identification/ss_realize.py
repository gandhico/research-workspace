"""DARX -> discrete state-space realization + controllability/observability (Ref 3 §VIII).

Realizes a SISO DARX channel in controllable companion form (order = max(na, nb))
and records ctrb/obsv ranks. Caveat (carried from M6): a realization being
observable/controllable here does not by itself justify every LQR/LQG/MPC design;
the linear parameter model (`models.linear_2dof`) is the practical control backbone.
"""
from __future__ import annotations

import numpy as np

from aero2.identification.arx import ArxModel


def darx_to_ss(denominator_z_minus_1, numerator_z_minus_1):
    """A(z^-1)=1-a1 z^-1-... , B=b1 z^-1+...  ->  (A,B,C,D) controllable companion."""
    a = -np.asarray(denominator_z_minus_1[1:], dtype=float)   # [a1..ana]
    b = np.asarray(numerator_z_minus_1, dtype=float)          # [b1..bnb]
    na, nb = len(a), len(b)
    n = max(na, nb, 1)
    a_pad = np.zeros(n); a_pad[:na] = a
    b_pad = np.zeros(n); b_pad[:nb] = b

    A = np.zeros((n, n))
    A[0, :] = a_pad
    if n > 1:
        A[1:, :-1] = np.eye(n - 1)
    B = np.zeros((n, 1)); B[0, 0] = 1.0
    C = b_pad.reshape(1, n)
    D = np.zeros((1, 1))
    return A, B, C, D


def controllability(A, B) -> np.ndarray:
    n = A.shape[0]
    cols = [B]
    for i in range(1, n):
        cols.append(np.linalg.matrix_power(A, i) @ B)
    return np.hstack(cols)


def observability(A, C) -> np.ndarray:
    n = A.shape[0]
    rows = [C]
    for i in range(1, n):
        rows.append(C @ np.linalg.matrix_power(A, i))
    return np.vstack(rows)


def ranks(A, B, C) -> dict:
    n = A.shape[0]
    return {
        "n": n,
        "ctrb_rank": int(np.linalg.matrix_rank(controllability(A, B))),
        "obsv_rank": int(np.linalg.matrix_rank(observability(A, C))),
    }


def realize(model: ArxModel):
    """Realize the first input channel of an ARX/DARX model."""
    A, B, C, D = darx_to_ss(model.denominator_z_minus_1, model.b(model.inputs[0]))
    return A, B, C, D


__all__ = ["darx_to_ss", "controllability", "observability", "ranks", "realize"]
