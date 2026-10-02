"""Shared second-order derivative filter (Ref 3, Eqs. 28-30).

Exact replica of `SimulinkSecondOrderDerivative` from
`M7_aero2_simulink_2dof_pd_replicate.py`. Explicit Euler with the ACTUAL measured
loop dt (the project's headline lesson: the PD baseline only became the strongest
controller once this filter used measured dt, not the nominal 0.002 s).

Usage contract (matches the original loop): read `filtered_rate` to get the
current rate estimate, compute the command, THEN call `update(angle, dt)` once per
loop. So the rate at step k reflects measurements through step k-1.
"""
from __future__ import annotations

from aero2.config import gains


class SecondOrderDerivative:
    """Filtered-derivative state: x1≈filtered value, rate = wn·x2."""

    def __init__(self, wn: float = gains.DERIV_FILTER_WN, zeta: float = gains.DERIV_FILTER_ZETA) -> None:
        self.wn = float(wn)
        self.zeta = float(zeta)
        self.x1 = 0.0
        self.x2 = 0.0

    def reset(self) -> None:
        self.x1 = 0.0
        self.x2 = 0.0

    @property
    def filtered_value(self) -> float:
        return self.x1

    @property
    def filtered_rate(self) -> float:
        return self.wn * self.x2

    def update(self, value: float, dt: float) -> float:
        """Advance the filter one explicit-Euler step with measured dt."""
        value = float(value)
        dt = float(dt)
        x1_dot = self.wn * self.x2
        x2_dot = self.wn * ((value - self.x1) - 2.0 * self.zeta * self.x2)
        self.x1 += dt * x1_dot
        self.x2 += dt * x2_dot
        return self.filtered_rate


__all__ = ["SecondOrderDerivative"]
