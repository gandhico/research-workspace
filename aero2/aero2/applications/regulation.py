"""Regulation-under-disturbance application (brief §10, Phase 8).

Holds a fixed setpoint (default theta=psi=0) while injecting scheduled additive
command disturbances [V] on pitch/yaw. Shares the closed-loop runner in
`Application`; the disturbance is added to the controller command inside
`Application.run` (`u_applied = u + disturbance`). Companion to reference
tracking — it exposes each controller's *rejection* rather than its tracking.
"""
from __future__ import annotations

import numpy as np

from aero2.applications.base import Application
from aero2.control.base import Reference

#: Disturbance schedule: (t_start_s, t_end_s, (d_pitch_V, d_yaw_V)). Additive on u.
DISTURBANCE_PULSES = [
    (3.0, 4.0, (4.0, 0.0)),     # pitch kick +
    (7.0, 8.0, (0.0, 4.0)),     # yaw kick +
    (11.0, 12.0, (-4.0, 0.0)),  # pitch kick -
    (15.0, 16.0, (0.0, -4.0)),  # yaw kick -
]


class RegulationUnderDisturbance(Application):
    name = "regulation_disturbance"

    def __init__(self, duration_s: float = 20.0, nominal_hz: float = 200.0,
                 theta_set: float = 0.0, psi_set: float = 0.0, pulses=None) -> None:
        super().__init__(duration_s, nominal_hz)
        self.theta_set = float(theta_set)
        self.psi_set = float(psi_set)
        self.pulses = DISTURBANCE_PULSES if pulses is None else pulses

    def reference(self, t: float) -> Reference:
        return Reference(theta=self.theta_set, psi=self.psi_set)

    def disturbance(self, t: float):
        d = np.zeros(2)
        for ts, te, amp in self.pulses:
            if ts <= t < te:
                d = d + np.asarray(amp, dtype=float)
        return d


__all__ = ["RegulationUnderDisturbance", "DISTURBANCE_PULSES"]
