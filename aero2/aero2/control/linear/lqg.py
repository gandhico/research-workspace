"""LQG (Ref 3, Eq. 45) — LQR gain + Luenberger observer, Euler with measured dt."""
from __future__ import annotations

import numpy as np
from scipy.linalg import solve_continuous_are

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.control.linear._common import clamp, feedforward_for_reference, reference_state
from aero2.control.linear.lqr import LQR2DOF


class LQG2DOF(BaseController):
    name = "lqg"

    def __init__(self, q_diag=gains.LQR_Q_DIAG, r_diag=gains.LQR_R_DIAG,
                 process_diag=gains.LQG_PROCESS_DIAG, measurement_diag=gains.LQG_MEASUREMENT_DIAG,
                 voltage_limit=params.V_MAX):
        super().__init__()
        self.lqr = LQR2DOF(q_diag=q_diag, r_diag=r_diag, voltage_limit=voltage_limit)
        self.A, self.B, self.C = self.lqr.A, self.lqr.B, self.lqr.C
        Qn = np.diag(np.asarray(process_diag, dtype=float))
        Rn = np.diag(np.asarray(measurement_diag, dtype=float))
        Pn = solve_continuous_are(self.A.T, self.C.T, Qn, Rn)
        self.L = Pn @ self.C.T @ np.linalg.inv(Rn)
        self.voltage_limit = abs(float(voltage_limit))
        self.x_hat = np.zeros(4)
        self.u_prev = np.zeros(2)
        self.initialized = False

    def reset(self):
        super().reset()
        self.x_hat[:] = 0.0
        self.u_prev[:] = 0.0
        self.initialized = False

    def compute(self, x_est, ref: Reference, dt):
        x_est = np.asarray(x_est, dtype=float).reshape(4)
        y = np.array([x_est[0], x_est[2]])               # measured angles only
        if not self.initialized:
            self.x_hat[:] = [y[0], 0.0, y[1], 0.0]
            self.initialized = True
        innovation = y - self.C @ self.x_hat
        x_dot = self.A @ self.x_hat + self.B @ self.u_prev + self.L @ innovation
        self.x_hat = self.x_hat + max(1e-6, float(dt)) * x_dot

        x_ref = reference_state(ref.theta, ref.psi)
        u_ff = feedforward_for_reference(self.A, self.B, x_ref, self.voltage_limit)
        u_raw = u_ff - self.lqr.K @ (self.x_hat - x_ref)
        u = clamp(u_raw, self.voltage_limit)
        self.u_prev = u.copy()
        self.info = {"u_ff": u_ff, "u_raw": u_raw, "x_hat": self.x_hat.copy()}
        return u


__all__ = ["LQG2DOF"]
