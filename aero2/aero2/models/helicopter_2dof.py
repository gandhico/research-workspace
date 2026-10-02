"""2-DOF coupled twin-rotor — the primary plant (Ref 3, Eqs. 5-10, 13-25).

This is the exact model used by backstepping, SMC, and NMPC, not a generic
textbook twin-rotor. Traced to
`M8_Aero2_Nonlinear_Controllers/src/nonlinear_aero2_model.py`.

    xdot = [theta_dot, ddot_theta, psi_dot, ddot_psi]
    [ddot_theta, ddot_psi]^T = b(theta,theta_dot,psi,psi_dot) + M(theta) u

with u = [u_p, u_y]. The yaw input effectiveness is scaled by cos(theta), clipped
to |cos(theta)| >= MIN_COS_THETA (config.params) — an implementation detail that
must not be dropped (it bounds yaw authority at large pitch).
"""
from __future__ import annotations

import math

import numpy as np

from aero2.config import params
from aero2.models.base import Model
from aero2.models.linear_2dof import linear_plant_matrices


def input_matrix(theta: float) -> np.ndarray:
    """M(theta) (Ref 3, Eq. 7) with the cos(theta) clip."""
    c = math.cos(float(theta))
    if abs(c) < params.MIN_COS_THETA:
        c = math.copysign(params.MIN_COS_THETA, c if c != 0.0 else 1.0)
    return np.array([
        [params.DT_ARM * params.KPP / params.J_PITCH, params.DT_ARM * params.KPY / params.J_PITCH],
        [c * params.KYP / params.J_YAW, c * params.KYY / params.J_YAW],
    ], dtype=float)


def drift(theta: float, theta_dot: float, psi: float, psi_dot: float) -> np.ndarray:
    """Drift term b (Ref 3, Eq. 6)."""
    return np.array([
        (-params.KSP * math.sin(float(theta)) - params.DP * float(theta_dot)) / params.J_PITCH,
        (-params.DY * float(psi_dot)) / params.J_YAW,
    ], dtype=float)


def inverse_dynamics(x, desired_accel, voltage_limit: float = params.V_MAX):
    """Least-squares inverse dynamics (Ref 3, Eqs. 9-10), NOT a symbolic inverse.

    Solves min_u || M(theta) u - (v - b) ||_2 then clips. Returns (u_clipped, u_raw).
    Used by the nonlinear controllers (Phase 7).
    """
    theta, theta_dot, psi, psi_dot = np.asarray(x, dtype=float).reshape(4)
    M = input_matrix(theta)
    b = drift(theta, theta_dot, psi, psi_dot)
    v = np.asarray(desired_accel, dtype=float).reshape(2)
    u_raw = np.linalg.lstsq(M, v - b, rcond=None)[0]
    u = np.clip(u_raw, -abs(voltage_limit), abs(voltage_limit))
    return u, u_raw


class Helicopter2DOF(Model):
    """Primary coupled nonlinear plant."""

    state_dim, input_dim, output_dim = 4, 2, 2
    name = "helicopter_2dof"

    def __init__(self, voltage_limit: float = params.V_MAX) -> None:
        self.voltage_limit = float(voltage_limit)

    def f(self, x, u, t=0.0):
        theta, theta_dot, psi, psi_dot = np.asarray(x, dtype=float).reshape(4)
        u = np.asarray(u, dtype=float).reshape(2)
        accel = drift(theta, theta_dot, psi, psi_dot) + input_matrix(theta) @ u
        return np.array([theta_dot, accel[0], psi_dot, accel[1]], dtype=float)

    def output(self, x):
        x = np.asarray(x, dtype=float).reshape(4)
        return np.array([x[0], x[2]], dtype=float)

    def linearize(self, x0=None, u0=None, eps: float = 1e-6):
        """Return the paper's nominal linear model (Ref 3, Eqs. 13-25).

        Independent of (x0, u0): this is the documented small-pitch linearization.
        For a Jacobian at an arbitrary point use `Model.linearize(self, x0, u0)`.
        """
        A, B, C = linear_plant_matrices()
        return A, B, C, np.zeros((2, 2))

    def inverse_dynamics(self, x, desired_accel, voltage_limit=None):
        vl = self.voltage_limit if voltage_limit is None else voltage_limit
        return inverse_dynamics(x, desired_accel, vl)


__all__ = ["Helicopter2DOF", "input_matrix", "drift", "inverse_dynamics"]
