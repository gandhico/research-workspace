"""Aero2 gate-state residual augmentation (HyperLIF / Adaptive HyperLIF).

Bounded, demand-triggered assistive residual ported from the Qube/Servo-Pendulum
result. The classical Aero2 controller remains the stability anchor; the residual is
optional, capped, and (in shadow mode) never applied. See docs/aero2_residual_*.md.
"""
from .residual_gate import Aero2GateResidual, ShuffleSource, str2bool

__all__ = ["Aero2GateResidual", "ShuffleSource", "str2bool"]
