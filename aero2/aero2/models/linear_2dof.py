"""Linear 2-DOF state-space realization (Ref 3, Eqs. 13-25).

This is the linearization of `helicopter_2dof` about the origin/trim (small
pitch, cos(theta)=1). It is the practical backbone for the M7 linear controllers
(LQR/LQG/MPC) and can also be used directly as a linear offline plant.

Matrices are defined ONCE here (single source of truth) and reused by
`Helicopter2DOF.linearize()`. Traced to
`M7_Aero2_Linear_Controllers/src/controllers/linear_2dof.py -> plant_matrices`.
"""
from __future__ import annotations

import numpy as np

from aero2.config import params
from aero2.models.base import Model


def linear_plant_matrices():
    """Continuous (A, B, C) for x=[theta,theta_dot,psi,psi_dot], u=[u_p,u_y], y=[theta,psi].

    Note the yaw input row uses KYP/KYY without the cos(theta) factor — this is
    the small-pitch linearization (cos 0 = 1); the nonlinear model keeps the
    clipped cos(theta) in `helicopter_2dof.input_matrix`.
    """
    A = np.array([
        [0.0, 1.0, 0.0, 0.0],
        [-params.KSP / params.J_PITCH, -params.DP / params.J_PITCH, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, -params.DY / params.J_YAW],
    ])
    B = np.array([
        [0.0, 0.0],
        [params.DT_ARM * params.KPP / params.J_PITCH, params.DT_ARM * params.KPY / params.J_PITCH],
        [0.0, 0.0],
        [params.KYP / params.J_YAW, params.KYY / params.J_YAW],
    ])
    C = np.array([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
    ])
    return A, B, C


class Linear2DOF(Model):
    """Purely linear plant xdot = A x + B u, y = C x."""

    state_dim, input_dim, output_dim = 4, 2, 2
    name = "linear_2dof"

    def __init__(self) -> None:
        self.A, self.B, self.C = linear_plant_matrices()

    def f(self, x, u, t=0.0):
        x = np.asarray(x, dtype=float).reshape(4)
        u = np.asarray(u, dtype=float).reshape(2)
        return self.A @ x + self.B @ u

    def output(self, x):
        return self.C @ np.asarray(x, dtype=float).reshape(4)

    def linearize(self, x0=None, u0=None, eps: float = 1e-6):
        return self.A, self.B, self.C, np.zeros((2, 2))


__all__ = ["linear_plant_matrices", "Linear2DOF"]
