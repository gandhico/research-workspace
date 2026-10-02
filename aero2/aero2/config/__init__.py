"""Single source of truth for every Aero2 constant.

Import sub-modules explicitly to keep provenance obvious, e.g.::

    from aero2.config import params, gains, sensors, timing, references
    Kp = gains.PD_KP_PITCH

No magic numbers live in controllers, models, or runners — they all import
from here. See docs/math_code_map.md for the equation -> symbol mapping.
"""
from __future__ import annotations

from . import params, gains, sensors, timing, references, hyperlif

__all__ = ["params", "gains", "sensors", "timing", "references", "hyperlif"]
