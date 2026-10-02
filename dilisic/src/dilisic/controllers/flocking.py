"""A compact double-integrator formation controller for the reproduction scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class DoubleIntegratorFormationController:
    """1-D outer controller that supplies u_DI to each DILISIC-wrapped agent."""

    n_agents: int = 7
    spacing: float = 0.16
    kp: float = 50.0
    kd: float = 2.0 * np.sqrt(50.0)
    consensus_damping: float = 8.0
    obstacle_position: float = 0.9
    obstacle_start: float = 30.0
    obstacle_end: float = 45.0
    obstacle_gain: float = 0.08
    obstacle_margin: float = 0.22
    obstacle_ramp_time: float = 3.0
    u_limit: float = 2.0e4
    offsets: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        half = 0.5 * (self.n_agents - 1)
        self.offsets = (np.arange(self.n_agents, dtype=float) - half) * self.spacing

    def reference(self, t: float) -> tuple[float, float, float]:
        q_r = -np.pi * np.sin(t) / 10.0
        p_r = -np.pi * np.cos(t) / 10.0
        a_r = np.pi * np.sin(t) / 10.0
        return float(q_r), float(p_r), float(a_r)

    def compute(self, t: float, positions: np.ndarray, velocities: np.ndarray) -> np.ndarray:
        q_r, p_r, a_r = self.reference(t)
        targets = q_r + self.offsets
        u = a_r - self.kp * (positions - targets) - self.kd * (velocities - p_r)

        mean_velocity = float(np.mean(velocities))
        u += -self.consensus_damping * (velocities - mean_velocity)

        envelope = self._obstacle_envelope(t)
        if envelope > 0.0:
            distance = self.obstacle_position - positions
            active = (distance > 0.0) & (distance < self.obstacle_margin)
            repulsion = np.zeros_like(positions)
            z = np.zeros_like(positions)
            z[active] = 1.0 - distance[active] / self.obstacle_margin
            repulsion[active] = -self.obstacle_gain * envelope * z[active] ** 2
            u += repulsion

        return np.clip(u, -self.u_limit, self.u_limit)

    def _obstacle_envelope(self, t: float) -> float:
        if t < self.obstacle_start or t > self.obstacle_end:
            return 0.0
        rise = min(1.0, (t - self.obstacle_start) / self.obstacle_ramp_time)
        fall = min(1.0, (self.obstacle_end - t) / self.obstacle_ramp_time)
        return _smoothstep(max(0.0, min(rise, fall)))


def _smoothstep(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)
