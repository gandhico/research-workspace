"""A minimal four-rotor L1 response layer in normalized rotor-speed coordinates.

This is a model variant, not an identified X2/CF2 propulsion model. Per-rotor
time constants must be supplied from a declared source. The zero-lag mode
exactly returns the ideal commanded forces within the existing force box.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class RotorResponse:
    f_max: np.ndarray
    tau_s: np.ndarray
    force_initial: np.ndarray | None = None

    def __post_init__(self) -> None:
        self.f_max = np.asarray(self.f_max, dtype=float).copy()
        self.tau_s = np.asarray(self.tau_s, dtype=float).copy()
        if self.f_max.shape != (4,) or self.tau_s.shape != (4,):
            raise ValueError("f_max and tau_s must each have four entries")
        if not np.all(np.isfinite(self.f_max)) or np.any(self.f_max <= 0):
            raise ValueError("each rotor must have finite positive f_max")
        if not np.all(np.isfinite(self.tau_s)) or np.any(self.tau_s < 0):
            raise ValueError("each rotor must have finite nonnegative tau_s")
        initial = np.zeros(4) if self.force_initial is None else np.asarray(self.force_initial, dtype=float)
        if initial.shape != (4,) or not np.all(np.isfinite(initial)):
            raise ValueError("force_initial must have four finite entries")
        self.speed_fraction = np.sqrt(np.clip(initial, 0, self.f_max) / self.f_max)

    def step(self, force_command: np.ndarray, dt_s: float) -> np.ndarray:
        """Return realized thrust after an exact frozen-command motor-speed step."""
        command = np.asarray(force_command, dtype=float)
        if command.shape != (4,) or not np.all(np.isfinite(command)):
            raise ValueError("force_command must have four finite entries")
        if not math.isfinite(dt_s) or dt_s < 0:
            raise ValueError("dt_s must be finite and nonnegative")
        command = np.clip(command, 0, self.f_max)
        target = np.sqrt(command / self.f_max)
        for i in range(4):
            if self.tau_s[i] == 0:
                self.speed_fraction[i] = target[i]
            else:
                blend = -math.expm1(-dt_s / self.tau_s[i])
                self.speed_fraction[i] += blend * (target[i] - self.speed_fraction[i])
        realized = self.f_max * self.speed_fraction**2
        # Preserve bit-exact L0 control values when a rotor's lag is disabled.
        realized[self.tau_s == 0] = command[self.tau_s == 0]
        return realized

    def reachable_force_interval(self, dt_s: float) -> tuple[np.ndarray, np.ndarray]:
        """Exact next-step force box for any held command in [0, f_max].

        This is conditional on the model's current speed state and declared
        time constants. It is an actuator reachability calculation, not a
        certificate for the full vehicle.
        """
        if not math.isfinite(dt_s) or dt_s <= 0:
            raise ValueError("dt_s must be finite and positive")
        lo = np.zeros(4)
        hi = self.f_max.copy()
        for i in range(4):
            if self.tau_s[i] > 0:
                a = math.exp(-dt_s / self.tau_s[i])
                lo[i] = self.f_max[i] * (a * self.speed_fraction[i]) ** 2
                hi[i] = self.f_max[i] * (a * self.speed_fraction[i] + 1 - a) ** 2
        return lo, hi

    def command_for_next_force(self, next_force: np.ndarray, dt_s: float) -> np.ndarray:
        """Invert one frozen-command motor step for a feasible next force."""
        desired = np.asarray(next_force, dtype=float)
        if desired.shape != (4,) or not np.all(np.isfinite(desired)):
            raise ValueError("next_force must have four finite entries")
        lo, hi = self.reachable_force_interval(dt_s)
        if np.any(desired < lo - 1e-12) or np.any(desired > hi + 1e-12):
            raise ValueError("next_force lies outside the one-step reachable box")
        desired = np.clip(desired, lo, hi)
        command = desired.copy()
        for i in range(4):
            if self.tau_s[i] > 0:
                a = math.exp(-dt_s / self.tau_s[i])
                target_speed = (math.sqrt(desired[i] / self.f_max[i])
                                - a * self.speed_fraction[i]) / (1 - a)
                command[i] = self.f_max[i] * np.clip(target_speed, 0.0, 1.0) ** 2
        return command
