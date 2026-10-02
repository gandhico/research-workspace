"""Classical baselines and HyperLIF residual augmentation controllers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .hyperlif import AdaptiveHyperLIFGate, HyperLIFParams


@dataclass(frozen=True)
class ControlResult:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    gate: np.ndarray
    feature: np.ndarray


class LinearBaselineController:
    """Saturated linear baseline u = -Kx."""

    def __init__(self, gain: np.ndarray, limits: np.ndarray):
        self.gain = np.asarray(gain, dtype=float)
        self.limits = np.asarray(limits, dtype=float)

    def reset(self) -> None:
        pass

    def compute(self, state: np.ndarray, dt: float) -> ControlResult:
        del dt
        state = np.asarray(state, dtype=float)
        raw = -self.gain @ state
        command = np.clip(raw, -self.limits, self.limits)
        zeros = np.zeros_like(command)
        return ControlResult(
            command=command,
            baseline=command.copy(),
            residual=zeros,
            gate=np.zeros(2 * command.size, dtype=float),
            feature=np.zeros(command.size, dtype=float),
        )


class HyperLIFResidualController:
    """Bounded residual wrapper around a classical baseline.

    The residual does not replace the baseline. The baseline command is
    normalized, pair-coded into positive and negative currents, transformed by
    HyperLIF gate states, decoded as a signed correction, and blended back:

        u = clip(u_base + blend * residual_limit * (r_pos - r_neg), limits)
    """

    def __init__(
        self,
        baseline: LinearBaselineController,
        limits: np.ndarray,
        blend: float = 0.25,
        current_bias: float = 1.0,
        current_gain: float = 3.0,
        gate_gain: float = 1.0,
        neuron_params: HyperLIFParams | None = None,
    ):
        self.baseline = baseline
        self.limits = np.asarray(limits, dtype=float)
        self.blend = float(blend)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.gate_gain = float(gate_gain)
        self.neuron = AdaptiveHyperLIFGate(n=2 * self.limits.size, params=neuron_params)

    def reset(self) -> None:
        self.baseline.reset()
        self.neuron.reset()

    def compute(self, state: np.ndarray, dt: float) -> ControlResult:
        base = self.baseline.compute(state, dt).command
        feature = np.clip(base / np.maximum(self.limits, 1e-12), -1.0, 1.0)

        currents = np.zeros(2 * feature.size, dtype=float)
        currents[: feature.size] = self.current_bias + self.current_gain * np.maximum(feature, 0.0)
        currents[feature.size :] = self.current_bias + self.current_gain * np.maximum(-feature, 0.0)

        step = self.neuron.step(currents, dt)
        gate = np.clip(step.gate * self.gate_gain, 0.0, 1.0)
        signed = np.clip(gate[: feature.size] - gate[feature.size :], -1.0, 1.0)
        residual = self.blend * self.limits * signed
        command = np.clip(base + residual, -self.limits, self.limits)

        return ControlResult(
            command=command,
            baseline=base,
            residual=residual,
            gate=gate,
            feature=feature,
        )

