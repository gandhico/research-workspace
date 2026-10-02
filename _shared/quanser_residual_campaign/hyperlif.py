"""Pure NumPy Adaptive HyperLIF gate used by the residual controllers.

The residual signal uses the smooth gate state r, not spike events:

    theta_eff = v_thresh - gamma*r
    r_star = sigmoid(alpha*(v - theta_eff))
    r_next = r_star + (r - r_star)*exp(-dt/tau_r)
    G = (base_gain + gain_scaling*abs(I))*r_next**2
    v_next = v*exp(-lambda*dt) + (drive/lambda)*(1 - exp(-lambda*dt))

This matches the control-ready formulation used in the Aero2 project while
keeping the campaign runners dependency-light.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HyperLIFParams:
    tau: float = 0.05
    tau_r: float = 0.005
    v_rest: float = 0.0
    v_thresh: float = 1.0
    v_reset: float = 0.0
    alpha: float = 50.0
    gamma: float = 2.0
    base_gain: float = 120.0
    gain_scaling: float = 30.0


@dataclass
class HyperLIFStep:
    gate: np.ndarray
    voltage: np.ndarray
    activity: np.ndarray


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -700.0, 700.0)
    return 1.0 / (1.0 + np.exp(-x))


class AdaptiveHyperLIFGate:
    """Adaptive HyperLIF gate-only direct neuron."""

    def __init__(self, n: int, params: HyperLIFParams | None = None):
        self.n = int(n)
        self.params = params or HyperLIFParams()
        self.v = np.zeros(self.n, dtype=float)
        self.r = np.zeros(self.n, dtype=float)

    def reset(self) -> None:
        self.v[:] = 0.0
        self.r[:] = 0.0

    def step(self, current: np.ndarray, dt: float) -> HyperLIFStep:
        p = self.params
        current = np.asarray(current, dtype=float).reshape(self.n)
        dt = max(float(dt), 1e-9)

        theta_eff = p.v_thresh - p.gamma * self.r
        r_star = _sigmoid(p.alpha * (self.v - theta_eff))
        self.r[:] = r_star + (self.r - r_star) * np.exp(-dt / p.tau_r)

        conductance = (p.base_gain + p.gain_scaling * np.abs(current)) * self.r**2
        lam = 1.0 / p.tau + conductance
        drive = p.v_rest / p.tau + current / p.tau + conductance * p.v_reset
        decay = np.exp(-lam * dt)
        self.v[:] = self.v * decay + (drive / np.maximum(lam, 1e-12)) * (1.0 - decay)

        gate = np.clip(self.r.copy(), 0.0, 1.0)
        return HyperLIFStep(gate=gate, voltage=self.v.copy(), activity=gate)

