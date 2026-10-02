"""
Reference trajectory generators.
All functions return Euler angles [roll, pitch, yaw] in radians,
plus a helper that returns the quaternion form.
"""
from __future__ import annotations

import numpy as np
from quad.math_utils import euler_to_quat

KNOWN_MISSIONS = [
    "hover", "roll", "full3", "step", "hard45",
    "hardstep", "yaw360", "roll360", "hard45_long",
]


def reference_euler(t: float, mission: str, sim_time: float = 20.0) -> np.ndarray:
    """Return desired [roll, pitch, yaw] in radians for given time t."""

    if mission == "hover":
        return np.zeros(3, dtype=float)

    if mission == "roll":
        return np.array([0.25 * np.sin(0.7 * t), 0.0, 0.0], dtype=float)

    if mission == "full3":
        return 0.5 * np.sin(t + np.array([0.0, np.pi / 2.0, np.pi], dtype=float))

    if mission == "step":
        return np.array([
            1.0 if t >= 1.0 else 0.0,
            1.0 if t >= 5.0 else 0.0,
            1.0 if t >= 9.0 else 0.0,
        ], dtype=float)

    if mission in ("hard45", "hard45_long"):
        phi   = 0.55 * np.sin(0.75*t) + 0.20 * np.sin(2.10*t + 0.40)
        theta = 0.45 * np.sin(0.95*t + np.pi/3) + 0.18 * np.sin(1.75*t)
        psi   = 0.65 * np.sin(0.55*t + np.pi) + 0.25 * np.sin(1.35*t + 0.20)
        return np.array([phi, theta, psi], dtype=float)

    if mission == "hardstep":
        if t < 5.0:  return np.array([0.0,   0.0,   0.0],  dtype=float)
        if t < 12.0: return np.array([0.75, -0.45,  0.55], dtype=float)
        if t < 20.0: return np.array([-0.65, 0.55, -0.70], dtype=float)
        if t < 30.0: return np.array([0.50,  0.50,  0.90], dtype=float)
        if t < 40.0: return np.array([-0.80,-0.35,  0.20], dtype=float)
        return np.zeros(3, dtype=float)

    if mission == "yaw360":
        T = max(sim_time, 1e-9)
        s = np.clip(t / T, 0.0, 1.0)
        psi_ref = 2.0 * np.pi * (3.0*s**2 - 2.0*s**3)
        return np.array([0.0, 0.0, psi_ref], dtype=float)

    if mission == "roll360":
        t_start, T_flip = 1.0, 1.2
        if t < t_start:
            phi_ref = 0.0
        else:
            s = np.clip((t - t_start) / T_flip, 0.0, 1.0)
            phi_ref = 2.0 * np.pi * (3.0*s**2 - 2.0*s**3)
        return np.array([phi_ref, 0.0, 0.0], dtype=float)

    raise ValueError(f"Unknown mission '{mission}'. Known: {KNOWN_MISSIONS}")


def reference_quat(t: float, mission: str, sim_time: float = 20.0) -> np.ndarray:
    """Return desired quaternion [w,x,y,z] for given time t."""
    eul = reference_euler(t, mission, sim_time)
    return euler_to_quat(*eul)
