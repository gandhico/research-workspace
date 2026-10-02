"""1-DOF pitch about trim (Ref 2 §IV) — the trim-search / doublet configuration.

Pitch dynamics with yaw held inert. Near-integrating: the small restoring term
KSP places a pole near the origin, so small errors accumulate (this is exactly
why pitch free-run simulation drifts while one-step prediction stays strong).

Implemented in the canonical 4-state layout with yaw frozen (psi == psi_dot == 0),
so it composes unchanged with the generic OfflineBackend and pitch controllers /
applications. Only the pitch command u_p acts; the yaw command u_y is ignored.
Trim U0 ~ 1.4 V is the physical collective operating point about which u_p is
centered (config.params.U0_TRIM).
"""
from __future__ import annotations

import math

import numpy as np

from aero2.config import params
from aero2.models.base import Model


class PitchOnly(Model):
    state_dim, input_dim, output_dim = 4, 2, 2
    name = "pitch_only"
    active_axis = "pitch"

    def __init__(self, voltage_limit: float = params.V_MAX) -> None:
        self.voltage_limit = float(voltage_limit)

    def f(self, x, u, t=0.0):
        theta, theta_dot, psi, psi_dot = np.asarray(x, dtype=float).reshape(4)
        u_p = float(np.asarray(u, dtype=float).reshape(-1)[0])
        accel_theta = (
            (-params.KSP * math.sin(theta) - params.DP * theta_dot) / params.J_PITCH
            + (params.DT_ARM * params.KPP / params.J_PITCH) * u_p
        )
        return np.array([theta_dot, accel_theta, 0.0, 0.0], dtype=float)  # yaw inert

    def output(self, x):
        x = np.asarray(x, dtype=float).reshape(4)
        return np.array([x[0], x[2]], dtype=float)


__all__ = ["PitchOnly"]
