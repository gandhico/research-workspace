"""
quadrotor.py  —  full 12-state quadrotor (Victor's baseline, faithful port).

Source: Quad_control_2026.py (E. Espinoza), itself eqs. 2.30-2.35, p.28 of
García-Carrillo, Dzul, Lozano, Pégard, *Quad Rotorcraft Control* (Springer, 2013).

State (z-up):
    X = [x, dx, y, dy, z, dz, psi, dpsi, theta, dtheta, phi, dphi]
         0   1  2   3  4   5    6     7     8      9     10    11
Inputs:  u (total thrust / mass-normalised), and the three angular-acceleration
commands tau_psi, tau_theta, tau_phi (inertia is folded into the gains, exactly
as in the baseline — dX[7]=tau_psi, etc.).

    x_ddot = u (sin phi sin psi + cos phi cos psi sin theta)/m
    y_ddot = u (cos phi sin theta sin psi - cos psi sin phi)/m
    z_ddot = u (cos theta cos phi)/m - g
    psi_ddot = tau_psi,  theta_ddot = tau_theta,  phi_ddot = tau_phi
"""
from dataclasses import dataclass
import numpy as np

M = 0.9
G = 9.81


@dataclass
class QuadParams:
    m: float = M
    g: float = G


def quad_deriv(X, u, tau_psi, tau_theta, tau_phi, P: QuadParams = QuadParams()):
    x, dx, y, dy, z, dz, psi, dpsi, theta, dtheta, phi, dphi = X
    m, g = P.m, P.g
    dX = np.empty(12)
    dX[0] = dx
    dX[1] = u * (np.sin(phi) * np.sin(psi) + np.cos(phi) * np.cos(psi) * np.sin(theta)) / m
    dX[2] = dy
    dX[3] = u * (np.cos(phi) * np.sin(theta) * np.sin(psi) - np.cos(psi) * np.sin(phi)) / m
    dX[4] = dz
    dX[5] = u * (np.cos(theta) * np.cos(phi)) / m - g
    dX[6] = dpsi
    dX[7] = tau_psi
    dX[8] = dtheta
    dX[9] = tau_theta
    dX[10] = dphi
    dX[11] = tau_phi
    return dX


def quad_rk4(X, u, tau_psi, tau_theta, tau_phi, dt, P: QuadParams = QuadParams()):
    a = (u, tau_psi, tau_theta, tau_phi, P)
    k1 = quad_deriv(X, *a)
    k2 = quad_deriv(X + 0.5 * dt * k1, *a)
    k3 = quad_deriv(X + 0.5 * dt * k2, *a)
    k4 = quad_deriv(X + dt * k3, *a)
    return X + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


# ---------------------------------------------------------------- references
# (faithful to Quad_control_2026.py: z ramp/hold, x & y slow sinusoid)
_F = 0.1 / (2 * np.pi)   # so that 2*pi*f = 0.1 rad/s


def z_ref(t):
    if t < 0:
        return 0.0
    if t < 10:
        return t / 10.0
    if t < 20:
        return 1.0
    if t < 30:
        return t * (0.5 - 1) / (30 - 20) + (1 - 20 * (0.5 - 1) / (30 - 20))
    return 0.5


def x_ref(t):
    return np.sin(2 * np.pi * _F * t)


def x_ref_dot(t):
    return np.cos(2 * np.pi * _F * t) * 2 * np.pi * _F


def y_ref(t):
    return np.sin(2 * np.pi * _F * t)


def y_ref_dot(t):
    return np.cos(2 * np.pi * _F * t) * 2 * np.pi * _F


# initial condition from the baseline
X0 = np.array([0.1, 0, -0.1, 0, 0, 0, 0.1, 0, 0, 0, 0, 0], float)


class QuadPlantNode:
    """Stateful nengo Node: input [u, tau_psi, tau_theta, tau_phi] -> 12 states."""

    def __init__(self, dt, x0=None, P: QuadParams = QuadParams()):
        self.dt = dt
        self.P = P
        self.state = (X0.copy() if x0 is None else np.array(x0, float))

    def __call__(self, t, v):
        u, tp, tt, tph = v
        self.state = quad_rk4(self.state, u, tp, tt, tph, self.dt, self.P)
        return self.state
