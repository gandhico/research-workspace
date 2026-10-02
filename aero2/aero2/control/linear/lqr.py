"""LQR (Ref 3, Eqs. 43-44). CARE; u = clip(u_ff - K(x - x_ref))."""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_continuous_are

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.control.linear._common import clamp, feedforward_for_reference, plant_matrices, reference_state


class LQR2DOF(BaseController):
    name = "lqr"

    def __init__(self, q_diag=gains.LQR_Q_DIAG, r_diag=gains.LQR_R_DIAG, voltage_limit=params.V_MAX):
        super().__init__()
        self.A, self.B, self.C = plant_matrices()
        self.Q = np.diag(np.asarray(q_diag, dtype=float))
        self.R = np.diag(np.asarray(r_diag, dtype=float))
        self.P = solve_continuous_are(self.A, self.B, self.Q, self.R)
        self.K = np.linalg.solve(self.R, self.B.T @ self.P)
        self.voltage_limit = abs(float(voltage_limit))

    def compute(self, x_est, ref: Reference, dt):
        x = np.asarray(x_est, dtype=float).reshape(4)
        x_ref = reference_state(ref.theta, ref.psi)
        u_ff = feedforward_for_reference(self.A, self.B, x_ref, self.voltage_limit)
        u_raw = u_ff - self.K @ (x - x_ref)
        u = clamp(u_raw, self.voltage_limit)
        self.info = {"u_ff": u_ff, "u_raw": u_raw}
        return u


__all__ = ["LQR2DOF"]
