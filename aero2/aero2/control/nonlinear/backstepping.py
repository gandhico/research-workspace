"""Backstepping / computed torque (Ref 3, Eqs. 48-50).

v = [-k1p e_theta - k2p theta_dot, -k1y e_psi - k2y psi_dot], then LS inverse
dynamics. e = state - reference. `yawboost=True` uses the higher-authority yaw gains.
"""
from __future__ import annotations

import numpy as np

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.models.helicopter_2dof import inverse_dynamics


class Backstepping2DOF(BaseController):
    name = "backstepping"

    def __init__(self, k1_pitch=gains.BS_K1_THETA, k2_pitch=gains.BS_K2_THETA,
                 k1_yaw=gains.BS_K1_PSI, k2_yaw=gains.BS_K2_PSI,
                 yawboost=False, voltage_limit=params.V_MAX):
        super().__init__()
        if yawboost:
            k1_yaw, k2_yaw = gains.BS_YAWBOOST_K1_PSI, gains.BS_YAWBOOST_K2_PSI
        self.k1_pitch, self.k2_pitch = float(k1_pitch), float(k2_pitch)
        self.k1_yaw, self.k2_yaw = float(k1_yaw), float(k2_yaw)
        self.voltage_limit = abs(float(voltage_limit))

    def compute(self, x_est, ref: Reference, dt):
        theta, theta_dot, psi, psi_dot = np.asarray(x_est, dtype=float).reshape(4)
        e_theta = theta - ref.theta
        e_psi = psi - ref.psi
        desired_accel = np.array([
            -self.k1_pitch * e_theta - self.k2_pitch * theta_dot,
            -self.k1_yaw * e_psi - self.k2_yaw * psi_dot,
        ])
        u, u_raw = inverse_dynamics(np.asarray(x_est, dtype=float).reshape(4), desired_accel, self.voltage_limit)
        self.info = {"u_raw": u_raw, "desired_accel": desired_accel}
        return u


__all__ = ["Backstepping2DOF"]
