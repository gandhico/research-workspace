"""Linear MPC (Ref 3, Eqs. 46-47) — unconstrained finite-horizon FIRST-MOVE + clip.

Not an online QP: it precomputes the first-move gain K0 of the unconstrained
finite-horizon quadratic law, then applies u = clip(u_ff - K0(x - x_ref)).
"""
from __future__ import annotations

import numpy as np

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.control.linear._common import (
    clamp, discretize, feedforward_for_reference, plant_matrices, reference_state,
)


class MPC2DOF(BaseController):
    name = "mpc"

    def __init__(self, prediction_dt=gains.MPC_PREDICTION_DT, horizon=gains.MPC_HORIZON,
                 q_diag=gains.MPC_Q_DIAG, r_diag=gains.MPC_R_DIAG, voltage_limit=params.V_MAX):
        super().__init__()
        self.A, self.B, self.C = plant_matrices()
        self.Ad, self.Bd = discretize(self.A, self.B, prediction_dt)
        self.Q = np.diag(np.asarray(q_diag, dtype=float))
        self.R = np.diag(np.asarray(r_diag, dtype=float))
        self.horizon = int(horizon)
        self.voltage_limit = abs(float(voltage_limit))
        self.K0 = self._finite_horizon_first_gain()

    def _finite_horizon_first_gain(self):
        n, m, N = self.Ad.shape[0], self.Bd.shape[1], self.horizon
        Sx = np.zeros((N * n, n))
        Su = np.zeros((N * n, N * m))
        A_power = np.eye(n)
        for i in range(N):
            A_power = self.Ad @ A_power
            Sx[i * n:(i + 1) * n, :] = A_power
            for j in range(i + 1):
                Aij = np.linalg.matrix_power(self.Ad, i - j)
                Su[i * n:(i + 1) * n, j * m:(j + 1) * m] = Aij @ self.Bd
        Qbar = np.kron(np.eye(N), self.Q)
        Rbar = np.kron(np.eye(N), self.R)
        H = Su.T @ Qbar @ Su + Rbar
        F = Su.T @ Qbar @ Sx
        Kseq = np.linalg.solve(H + 1e-9 * np.eye(H.shape[0]), F)
        return Kseq[:m, :]

    def compute(self, x_est, ref: Reference, dt):
        x = np.asarray(x_est, dtype=float).reshape(4)
        x_ref = reference_state(ref.theta, ref.psi)
        u_ff = feedforward_for_reference(self.A, self.B, x_ref, self.voltage_limit)
        u_raw = u_ff - self.K0 @ (x - x_ref)
        u = clamp(u_raw, self.voltage_limit)
        self.info = {"u_ff": u_ff, "u_raw": u_raw}
        return u


__all__ = ["MPC2DOF"]
