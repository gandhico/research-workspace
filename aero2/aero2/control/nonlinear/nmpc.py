"""Lightweight real-time NMPC (Ref 3, Eqs. 54-55).

Grid search over constant voltage offsets around an inverse-dynamics nominal
command; RK4 prediction of the nonlinear model over a short horizon; terminal
scaling. Defaults are the realtime variant benchmarked in Table IV (N=5,
dt_p=0.06, Q=diag(80,2.5,50,1.5), R=diag(.10,.10), terminal 1.5, grid (-2.5,0,2.5)).
Benchmarkable but not competitive in pure Python (timing/saturation).
"""
from __future__ import annotations

import numpy as np

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.models.helicopter_2dof import Helicopter2DOF, inverse_dynamics


class NMPC2DOF(BaseController):
    name = "nmpc"

    def __init__(self, k1_pitch=gains.NMPC_NOMINAL_K1_PITCH, k2_pitch=gains.NMPC_NOMINAL_K2_PITCH,
                 k1_yaw=gains.NMPC_NOMINAL_K1_YAW, k2_yaw=gains.NMPC_NOMINAL_K2_YAW,
                 prediction_dt=gains.NMPC_RT_DT_P, horizon=gains.NMPC_RT_HORIZON,
                 q_diag=gains.NMPC_RT_Q_DIAG, r_diag=gains.NMPC_RT_R_DIAG,
                 terminal_scale=gains.NMPC_RT_TERMINAL_SCALE, offset_grid=gains.NMPC_RT_OFFSET_GRID,
                 voltage_limit=params.V_MAX):
        super().__init__()
        self.k1_pitch, self.k2_pitch = float(k1_pitch), float(k2_pitch)
        self.k1_yaw, self.k2_yaw = float(k1_yaw), float(k2_yaw)
        self.prediction_dt = float(prediction_dt)
        self.horizon = int(horizon)
        self.Q = np.diag(np.asarray(q_diag, dtype=float))
        self.R = np.diag(np.asarray(r_diag, dtype=float))
        self.terminal_scale = float(terminal_scale)
        self.grid = np.asarray(offset_grid, dtype=float)
        self.voltage_limit = abs(float(voltage_limit))
        self._model = Helicopter2DOF(voltage_limit=self.voltage_limit)

    def _nominal(self, x, ref: Reference) -> np.ndarray:
        theta, theta_dot, psi, psi_dot = x
        desired = np.array([
            -self.k1_pitch * (theta - ref.theta) - self.k2_pitch * theta_dot,
            -self.k1_yaw * (psi - ref.psi) - self.k2_yaw * psi_dot,
        ])
        u, _ = inverse_dynamics(x, desired, self.voltage_limit)
        return u

    def compute(self, x_est, ref: Reference, dt):
        x0 = np.asarray(x_est, dtype=float).reshape(4)
        x_ref = np.array([ref.theta, 0.0, ref.psi, 0.0])
        u_nom = self._nominal(x0, ref)

        best_u, best_cost = u_nom.copy(), float("inf")
        for d_pitch in self.grid:
            for d_yaw in self.grid:
                u_c = np.clip(u_nom + np.array([d_pitch, d_yaw]), -self.voltage_limit, self.voltage_limit)
                xp, cost = x0.copy(), 0.0
                for k in range(self.horizon):
                    err = xp - x_ref
                    w = self.terminal_scale if k == self.horizon - 1 else 1.0
                    cost += w * float(err @ self.Q @ err) + float(u_c @ self.R @ u_c)
                    xp = self._model.step(xp, u_c, self.prediction_dt)
                if cost < best_cost:
                    best_cost, best_u = cost, u_c
        self.info = {"nmpc_cost": best_cost, "u_nom": u_nom}
        return best_u


__all__ = ["NMPC2DOF"]
