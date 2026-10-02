"""Half-rotor (half-quadrotor) variant — FUTURE WORK, hardware NotValidated.

Ref 3 lists the half-rotor as future work; no hardware results or identified
parameters exist for it. This module provides a *plausible* offline/virtual model
so the pipeline can exercise the variant, but every number below is an ASSUMPTION,
not an identified constant.

ASSUMPTIONS (documented in docs/02_modelling.md):
  * Configuration: a single rotor arm interpreted as "half a quadrotor" with two
    DOF — elevation q1 (collective lift) and roll q2 (differential).
  * Dynamics structure mirrors the 2-DOF helicopter (drift + cos-clipped input
    matrix), with parameters borrowed from the Aero2 constants as placeholders.
  * The roll axis reuses the yaw constants; elevation reuses the pitch constants.

Until a half-rotor is built and identified, treat ALL half-rotor results as
preliminary. The hardware path is `NotValidated` by design (brief §3, §16).
"""
from __future__ import annotations

import math

import numpy as np

from aero2.config import params
from aero2.models.base import Model

#: machine-readable flags so runners/docs never present this as validated
VALIDATED = False
HARDWARE_STATUS = "NotValidated"


class HalfRotor(Model):
    state_dim, input_dim, output_dim = 4, 2, 2
    name = "half_rotor"
    validated = VALIDATED
    hardware_status = HARDWARE_STATUS

    def __init__(self, voltage_limit: float = params.V_MAX) -> None:
        self.voltage_limit = float(voltage_limit)

    def _input_matrix(self, q1: float) -> np.ndarray:
        # placeholder: same structure as the helicopter, cos-clipped roll authority
        c = math.cos(float(q1))
        if abs(c) < params.MIN_COS_THETA:
            c = math.copysign(params.MIN_COS_THETA, c if c != 0.0 else 1.0)
        return np.array([
            [params.DT_ARM * params.KPP / params.J_PITCH, params.DT_ARM * params.KPY / params.J_PITCH],
            [c * params.KYP / params.J_YAW, c * params.KYY / params.J_YAW],
        ], dtype=float)

    def f(self, x, u, t=0.0):
        q1, q1d, q2, q2d = np.asarray(x, dtype=float).reshape(4)   # elevation, roll
        u = np.asarray(u, dtype=float).reshape(2)
        drift = np.array([
            (-params.KSP * math.sin(q1) - params.DP * q1d) / params.J_PITCH,
            (-params.DY * q2d) / params.J_YAW,
        ])
        accel = drift + self._input_matrix(q1) @ u
        return np.array([q1d, accel[0], q2d, accel[1]], dtype=float)

    def output(self, x):
        x = np.asarray(x, dtype=float).reshape(4)
        return np.array([x[0], x[2]], dtype=float)


__all__ = ["HalfRotor", "VALIDATED", "HARDWARE_STATUS"]
