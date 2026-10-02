"""Nonlinear controllers: backstepping, SMC, NMPC (Ref 3, Eqs. 48-55)."""
from __future__ import annotations

from aero2.control.nonlinear.backstepping import Backstepping2DOF
from aero2.control.nonlinear.nmpc import NMPC2DOF
from aero2.control.nonlinear.smc import SlidingMode2DOF

__all__ = ["Backstepping2DOF", "SlidingMode2DOF", "NMPC2DOF"]
