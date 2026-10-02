"""Reusable current protocols for validation experiments."""

from __future__ import annotations

import numpy as np


def time_axis(duration: float, dt: float) -> np.ndarray:
    """Return a time axis starting at zero with fixed step ``dt``."""

    return np.arange(0.0, duration, dt, dtype=float)


def piecewise_constant(
    t: np.ndarray,
    segments: list[tuple[float, float, float]],
    default: float = 0.0,
) -> np.ndarray:
    """Build a piecewise-constant current from ``(start, stop, value)`` rows."""

    current = np.full_like(t, default, dtype=float)
    for start, stop, value in segments:
        mask = (t >= start) & (t < stop)
        current[mask] = value
    return current


def step_protocol(t: np.ndarray, low: float = 0.0, high: float = 1.4) -> np.ndarray:
    """Simple on/off current step."""

    return piecewise_constant(
        t,
        [
            (0.03, 0.20, high),
        ],
        default=low,
    )


def stress_protocol(t: np.ndarray) -> np.ndarray:
    """Current protocol that exposes reset-stability differences."""

    return piecewise_constant(
        t,
        [
            (0.02, 0.10, 1.2),
            (0.10, 0.18, 2.2),
            (0.18, 0.26, 4.0),
            (0.26, 0.32, 0.6),
        ],
        default=0.0,
    )


def decoding_protocol(t: np.ndarray) -> np.ndarray:
    """Smooth current for voltage/event/gate decoding comparisons."""

    current = 0.95 + 0.55 * np.sin(2.0 * np.pi * 3.0 * t)
    current += 0.25 * np.sin(2.0 * np.pi * 11.0 * t + 0.4)
    return np.clip(current, 0.05, 1.85)
