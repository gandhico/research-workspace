"""1-DOF yaw via pure differential drive (Ref 1 §F, Ref 3 Eq. 27).

Yaw dynamics with pitch held inert at a fixed angle. Driven by the differential
virtual input u_y (which the IO layer realizes as u_L = -v_psi, u_R = +v_psi).

Breakaway / stiction (brief §6, §17): small differential does not move yaw from
rest. Modelled as a Coulomb-style deadzone — if yaw is near rest and |u_y| is
below the breakaway threshold, yaw acceleration is zero. Thresholds are OFFLINE
modelling approximations (config.params.YAW_BREAKAWAY_V / YAW_STICTION_RATE),
grounded in the observed first-yaw-motion around v_yaw ~ 2.0 V — NOT identified
plant constants.

Canonical 4-state layout with pitch frozen (theta == theta_dot == 0), so the
generic backend's angle mapping stays correct (yaw is reported as psi = x[2]).
"""
from __future__ import annotations

import math

import numpy as np

from aero2.config import params
from aero2.models.base import Model


class YawOnly(Model):
    state_dim, input_dim, output_dim = 4, 2, 2
    name = "yaw_only"
    active_axis = "yaw"

    def __init__(
        self,
        pitch_fixed: float = 0.0,
        breakaway_v: float = params.YAW_BREAKAWAY_V,
        stiction_rate: float = params.YAW_STICTION_RATE,
        voltage_limit: float = params.V_MAX,
    ) -> None:
        self.pitch_fixed = float(pitch_fixed)
        self.breakaway_v = float(breakaway_v)
        self.stiction_rate = float(stiction_rate)
        self.voltage_limit = float(voltage_limit)
        c = math.cos(self.pitch_fixed)
        if abs(c) < params.MIN_COS_THETA:
            c = math.copysign(params.MIN_COS_THETA, c if c != 0.0 else 1.0)
        self._cos_pitch = c

    def f(self, x, u, t=0.0):
        theta, theta_dot, psi, psi_dot = np.asarray(x, dtype=float).reshape(4)
        u_y = float(np.asarray(u, dtype=float).reshape(-1)[1])

        # breakaway/stiction: at rest, small differential cannot start motion
        if abs(psi_dot) < self.stiction_rate and abs(u_y) < self.breakaway_v:
            accel_psi = 0.0
        else:
            accel_psi = (
                (-params.DY * psi_dot) / params.J_YAW
                + (self._cos_pitch * params.KYY / params.J_YAW) * u_y
            )
        return np.array([0.0, 0.0, psi_dot, accel_psi], dtype=float)  # pitch inert

    def output(self, x):
        x = np.asarray(x, dtype=float).reshape(4)
        return np.array([x[0], x[2]], dtype=float)


__all__ = ["YawOnly"]
