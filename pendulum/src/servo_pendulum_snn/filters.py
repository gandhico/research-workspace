from __future__ import annotations

import math


def wrap_to_pi(angle_rad: float) -> float:
    """Wrap an angle to [-pi, pi)."""
    return (float(angle_rad) + math.pi) % (2.0 * math.pi) - math.pi


class DerivativeFilter:
    """Tustin derivative filter matching the Quanser example implementation."""

    def __init__(self, bandwidth_rad_s: float, sample_time_s: float):
        self.bandwidth_rad_s = float(bandwidth_rad_s)
        self.sample_time_s = float(sample_time_s)
        self.previous_input = 0.0
        self.previous_output = 0.0

    def reset(self, value: float = 0.0) -> None:
        self.previous_input = float(value)
        self.previous_output = 0.0

    def step(self, value: float, sample_time_s: float | None = None) -> float:
        ts = float(sample_time_s if sample_time_s is not None else self.sample_time_s)
        a = self.bandwidth_rad_s
        y = (2.0 * a * float(value) - 2.0 * a * self.previous_input - self.previous_output * (a * ts - 2.0)) / (
            a * ts + 2.0
        )
        self.previous_input = float(value)
        self.previous_output = float(y)
        return float(y)
