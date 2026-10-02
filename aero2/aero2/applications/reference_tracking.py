"""Reference-tracking application (brief §10) — follow square-wave references.

The existing benchmark scenario: square-wave pitch/yaw references (Ref 3, Eqs. 3-4,
A_θ=20°, A_ψ=45°, f_θ=0.05 Hz, f_ψ=0.04 Hz). Works on every model variant and
backend. Shares the closed-loop runner in `applications.base.Application`.
"""
from __future__ import annotations

from aero2.applications.base import Application
from aero2.config import references
from aero2.control.base import Reference


class SquareWaveTracking(Application):
    name = "reference_tracking"

    def __init__(
        self,
        duration_s: float = 40.0,
        nominal_hz: float = 200.0,
        a_theta_rad: float = references.A_THETA_RAD,
        a_psi_rad: float = references.A_PSI_RAD,
        f_theta_hz: float = references.F_THETA_HZ,
        f_psi_hz: float = references.F_PSI_HZ,
    ) -> None:
        super().__init__(duration_s, nominal_hz)
        self.a_theta = float(a_theta_rad)
        self.a_psi = float(a_psi_rad)
        self.f_theta = float(f_theta_hz)
        self.f_psi = float(f_psi_hz)

    def reference(self, t: float) -> Reference:
        return Reference(
            theta=references.square_reference(t, self.a_theta, self.f_theta),
            psi=references.square_reference(t, self.a_psi, self.f_psi),
        )


class PitchSquareWaveTracking(SquareWaveTracking):
    """Pitch-only square-wave tracking with yaw held at zero."""

    name = "pitch_reference_tracking"

    def reference(self, t: float) -> Reference:
        return Reference(
            theta=references.square_reference(t, self.a_theta, self.f_theta),
            psi=0.0,
        )


class YawSquareWaveTracking(SquareWaveTracking):
    """Yaw-only square-wave tracking with pitch held at zero."""

    name = "yaw_reference_tracking"

    def reference(self, t: float) -> Reference:
        return Reference(
            theta=0.0,
            psi=references.square_reference(t, self.a_psi, self.f_psi),
        )


__all__ = ["SquareWaveTracking", "PitchSquareWaveTracking", "YawSquareWaveTracking"]
