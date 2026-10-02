"""Frozen delay-aware EHEKATL inner-rate LQR runtime primitives."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


RATE_GAINS = {
    "roll": (-0.002726230955066341, 0.07881743562285519, 0.07853430242425911, 0.07825218631544166),
    "pitch": (-0.0019913193146360608, 0.044127808679216333, 0.04324197104959773, 0.0423739160457096),
}


@dataclass
class DelayAwareRateLQR:
    axis: str
    trim_control: float
    command_limit: float = 0.003
    slew_per_sample: float = 0.0005
    rate_reference_deg_s: float = 0.0
    history: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    previous_perturbation: float = 0.0

    def __post_init__(self):
        if self.axis not in RATE_GAINS:
            raise ValueError(f"unsupported axis: {self.axis}")
        if len(self.history) != 3:
            raise ValueError("exactly three prior perturbation commands are required")

    @property
    def gain(self) -> np.ndarray:
        return np.asarray(RATE_GAINS[self.axis], dtype=float)

    def reset(self, trim_control: float | None = None) -> None:
        if trim_control is not None:
            self.trim_control = float(trim_control)
        self.history = [0.0, 0.0, 0.0]
        self.previous_perturbation = 0.0

    def preview(self, rate_deg_s: float, additive_perturbation: float = 0.0) -> tuple[float, float]:
        state = np.asarray([rate_deg_s - self.rate_reference_deg_s, *self.history], dtype=float)
        requested = float(-self.gain @ state) + float(additive_perturbation)
        perturbation = float(np.clip(
            requested,
            self.previous_perturbation - self.slew_per_sample,
            self.previous_perturbation + self.slew_per_sample,
        ))
        perturbation = float(np.clip(perturbation, -self.command_limit, self.command_limit))
        return self.trim_control + perturbation, perturbation

    def step(self, rate_deg_s: float, additive_perturbation: float = 0.0) -> tuple[float, float]:
        total, perturbation = self.preview(rate_deg_s, additive_perturbation)
        self.history = [perturbation, self.history[0], self.history[1]]
        self.previous_perturbation = perturbation
        return total, perturbation
