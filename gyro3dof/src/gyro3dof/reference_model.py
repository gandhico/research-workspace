"""Quanser's linear reaction-torque model (red gimbal locked, constant disc speed).

    Jx phi_ddot = tau2 + h psi_dot - b_x phi_dot
    Jz psi_ddot =      - h phi_dot - b_z psi_dot

(quanser_3dof_gyro_reaction_torque.mlx; b_x = b_z = 0 there). This is the
reference the MuJoCo multibody model is validated against near the nominal pose.
"""
from __future__ import annotations

import numpy as np

from .params import PARAMS, QuanserGyroParams


def linear_rhs(x, tau2, p: QuanserGyroParams = PARAMS, b_x=0.0, b_z=0.0, h=None):
    """x = [phi, psi, phi_dot, psi_dot]."""
    h = p.h if h is None else h
    phi, psi, dphi, dpsi = x
    return np.array([dphi, dpsi,
                     (tau2 + h * dpsi - b_x * dphi) / p.Jx,
                     (-h * dphi - b_z * dpsi) / p.Jz])


def simulate(controller, x0, t_end, dt=1e-3, p: QuanserGyroParams = PARAMS, **kw):
    """RK4 with the controller sampled once per step (zero-order hold)."""
    n = int(round(t_end / dt))
    xs = np.zeros((n + 1, 4))
    us = np.zeros(n + 1)
    xs[0] = x0
    for k in range(n):
        t = k * dt
        u = float(np.clip(controller(t, xs[k]), -p.tau_max, p.tau_max))
        us[k] = u
        f = lambda x: linear_rhs(x, u, p, **kw)  # noqa: E731
        k1 = f(xs[k]); k2 = f(xs[k] + dt / 2 * k1); k3 = f(xs[k] + dt / 2 * k2); k4 = f(xs[k] + dt * k3)
        xs[k + 1] = xs[k] + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    us[n] = us[n - 1]
    return np.arange(n + 1) * dt, xs, us
