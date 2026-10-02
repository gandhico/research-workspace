"""Flexible single-link arm model from the DILISIC paper."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FlexibleSingleLinkArmParameters:
    c: float = 2276.3
    gravity: float = 9.81
    mass: float = 2.27
    length: float = 0.96
    alpha: float = -36.52


@dataclass
class FlexibleSingleLinkArm:
    """Fourth-order affine-in-control flexible arm.

    State is [x, x_dot, x_ddot, x_dddot].
    """

    params: FlexibleSingleLinkArmParameters = FlexibleSingleLinkArmParameters()

    def f(self, state: np.ndarray) -> float:
        x, x_dot, x_ddot, x_3 = np.asarray(state, dtype=float)
        p = self.params
        c = p.c
        g = p.gravity
        m = p.mass
        l = p.length
        alpha = p.alpha
        return float(
            ((g * x_dot**2 / l) - (g / (l * alpha**2))) * np.cos(x)
            + ((2.0 * g * x_dot**2 / (l * alpha)) + (g * x_ddot / l)) * np.sin(x)
            - c * x / (m * l**2 * alpha**2)
            - 2.0 * c * x_dot / (m * l**2 * alpha)
            - c * x_ddot / (m * l**2)
            + x_ddot / alpha**2
            - 2.0 * x_3 / alpha
        )

    def g(self, state: np.ndarray) -> float:
        p = self.params
        return float(p.c / (p.mass * p.length**2 * p.alpha**2))

    def derivative(self, state: np.ndarray, control: float, disturbance: float = 0.0) -> np.ndarray:
        dx = np.zeros(4, dtype=float)
        dx[0] = state[1]
        dx[1] = state[2]
        dx[2] = state[3]
        dx[3] = self.f(state) + self.g(state) * control + disturbance
        return dx

    def rk4_step(
        self, state: np.ndarray, control: float, disturbance: float, dt: float
    ) -> np.ndarray:
        k1 = self.derivative(state, control, disturbance)
        k2 = self.derivative(state + 0.5 * dt * k1, control, disturbance)
        k3 = self.derivative(state + 0.5 * dt * k2, control, disturbance)
        k4 = self.derivative(state + dt * k3, control, disturbance)
        return state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
