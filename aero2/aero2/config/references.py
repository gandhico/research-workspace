"""Reference-signal definitions for tracking experiments (Ref 3, Eqs. 3-4).

The main 2DOF tracking references are square waves:
    theta_r(t) = -A_theta if frac(f_theta t) < 0.5 else +A_theta
    psi_r(t)   = -A_psi   if frac(f_psi   t) < 0.5 else +A_psi
"""
from __future__ import annotations

import math

# Square-wave amplitudes / frequencies (Ref 3 final scripts) ----------------
A_THETA_DEG: float = 20.0
A_PSI_DEG: float = 45.0
A_THETA_RAD: float = math.radians(A_THETA_DEG)
A_PSI_RAD: float = math.radians(A_PSI_DEG)
F_THETA_HZ: float = 0.05
F_PSI_HZ: float = 0.04

# Large-yaw / wrap-crossing setpoints (quaternion positioning experiments) ---
A_PSI_LARGE_RAD: float = 2.9670597283903604   # 170 deg


def square_reference(t: float, amplitude: float, freq_hz: float) -> float:
    """Bipolar square wave used for pitch/yaw references (Ref 3, Eq. 3)."""
    return -amplitude if (freq_hz * t) % 1.0 < 0.5 else amplitude


__all__ = [
    "A_THETA_DEG", "A_PSI_DEG", "A_THETA_RAD", "A_PSI_RAD",
    "F_THETA_HZ", "F_PSI_HZ", "square_reference",
]
