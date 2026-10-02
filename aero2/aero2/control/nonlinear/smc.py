"""Sliding-mode control (Ref 3, Eqs. 51-53). Boundary-layer sat, not sign.

s = q_dot + lambda*(q - q_ref);  v = -lambda*q_dot - eta*sat(s/phi), then LS
inverse dynamics. `sat` is the clipped boundary-layer function (smooth_sign).
"""
from __future__ import annotations

import numpy as np

from aero2.config import gains, params
from aero2.control.base import BaseController, Reference
from aero2.models.helicopter_2dof import inverse_dynamics


def smooth_sign(value: float, boundary: float) -> float:
    boundary = max(1e-9, abs(float(boundary)))
    return float(np.clip(float(value) / boundary, -1.0, 1.0))


class SlidingMode2DOF(BaseController):
    name = "smc"

    def __init__(self, lambda_pitch=gains.SMC_LAMBDA_THETA, eta_pitch=gains.SMC_ETA_THETA,
                 phi_pitch=gains.SMC_PHI_THETA, lambda_yaw=gains.SMC_LAMBDA_PSI,
                 eta_yaw=gains.SMC_ETA_PSI, phi_yaw=gains.SMC_PHI_PSI,
                 yawboost=False, voltage_limit=params.V_MAX):
        super().__init__()
        if yawboost:
            lambda_yaw = gains.SMC_YAWBOOST_LAMBDA_PSI
            eta_yaw = gains.SMC_YAWBOOST_ETA_PSI
            phi_yaw = gains.SMC_YAWBOOST_PHI_PSI
        self.lambda_pitch, self.eta_pitch, self.phi_pitch = float(lambda_pitch), float(eta_pitch), float(phi_pitch)
        self.lambda_yaw, self.eta_yaw, self.phi_yaw = float(lambda_yaw), float(eta_yaw), float(phi_yaw)
        self.voltage_limit = abs(float(voltage_limit))

    def compute(self, x_est, ref: Reference, dt):
        theta, theta_dot, psi, psi_dot = np.asarray(x_est, dtype=float).reshape(4)
        e_theta = theta - ref.theta
        e_psi = psi - ref.psi
        s_theta = theta_dot + self.lambda_pitch * e_theta
        s_psi = psi_dot + self.lambda_yaw * e_psi
        desired_accel = np.array([
            -self.lambda_pitch * theta_dot - self.eta_pitch * smooth_sign(s_theta, self.phi_pitch),
            -self.lambda_yaw * psi_dot - self.eta_yaw * smooth_sign(s_psi, self.phi_yaw),
        ])
        u, u_raw = inverse_dynamics(np.asarray(x_est, dtype=float).reshape(4), desired_accel, self.voltage_limit)
        self.info = {"u_raw": u_raw, "s_theta": s_theta, "s_psi": s_psi}
        return u


__all__ = ["SlidingMode2DOF", "smooth_sign"]
