from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from quanser_residual_campaign.hyperlif import AdaptiveHyperLIFGate, HyperLIFParams

from .types import QubeCommand, QubeState


QUBE3_BALANCE_GAIN = np.array([-1.2247, 24.9044, -0.6877, 3.1321], dtype=float)


@dataclass(frozen=True)
class BalanceControllerConfig:
    gains: np.ndarray
    voltage_limit: float = 5.0
    capture_angle_deg: float = 10.0
    command_angle_deg: float = 0.0


class QuanserBalanceController:
    """Quanser-style upright balance law for Qube Servo 3."""

    def __init__(self, config: BalanceControllerConfig):
        self.config = config
        self.gains = np.asarray(config.gains, dtype=float).reshape(4)

    def reset(self) -> None:
        pass

    def compute(self, state: QubeState, dt: float) -> QubeCommand:
        del dt
        command_rad = math.radians(float(self.config.command_angle_deg))
        measured = np.array(
            [
                state.theta_rad,
                state.alpha_rad,
                state.theta_dot_rad_s,
                state.alpha_dot_rad_s,
            ],
            dtype=float,
        )
        reference = np.array([command_rad, 0.0, 0.0, 0.0], dtype=float)
        error_state = reference - measured

        in_capture = abs(math.degrees(state.alpha_rad)) <= float(self.config.capture_angle_deg)
        raw_voltage = -float(np.dot(self.gains, error_state)) if in_capture else 0.0
        voltage = float(np.clip(raw_voltage, -self.config.voltage_limit, self.config.voltage_limit))

        return QubeCommand(
            voltage=voltage,
            baseline_voltage=voltage,
            control_mode="baseline_balance" if in_capture else "outside_capture_zero",
            info={
                "raw_baseline_voltage": raw_voltage,
                "in_capture": float(in_capture),
                "capture_angle_deg": float(self.config.capture_angle_deg),
                "error_theta_rad": float(error_state[0]),
                "error_alpha_rad": float(error_state[1]),
                "error_theta_dot_rad_s": float(error_state[2]),
                "error_alpha_dot_rad_s": float(error_state[3]),
            },
        )


class HyperLIFResidualBalanceController:
    """Bounded HyperLIF gate-state residual around the Quanser balance law."""

    def __init__(
        self,
        base: QuanserBalanceController,
        residual_limit: float = 0.75,
        residual_blend: float = 0.25,
        current_bias: float = 0.0,
        current_gain: float = 3.5,
        gate_gain: float = 1.0,
        neuron_params: HyperLIFParams | None = None,
    ):
        self.base = base
        self.residual_limit = abs(float(residual_limit))
        self.residual_blend = float(residual_blend)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.gate_gain = float(gate_gain)
        self.neuron = AdaptiveHyperLIFGate(n=2, params=neuron_params)

    def reset(self) -> None:
        self.base.reset()
        self.neuron.reset()

    def compute(self, state: QubeState, dt: float) -> QubeCommand:
        base_cmd = self.base.compute(state, dt)
        if base_cmd.control_mode != "baseline_balance":
            self.neuron.reset()
            return QubeCommand(
                voltage=0.0,
                baseline_voltage=base_cmd.baseline_voltage,
                residual_voltage=0.0,
                control_mode=base_cmd.control_mode,
                info={**base_cmd.info, "residual_enabled": 0.0},
            )

        limit = max(float(self.base.config.voltage_limit), 1e-12)
        feature = float(np.clip(base_cmd.baseline_voltage / limit, -1.0, 1.0))
        currents = np.array(
            [
                self.current_bias + self.current_gain * max(feature, 0.0),
                self.current_bias + self.current_gain * max(-feature, 0.0),
            ],
            dtype=float,
        )
        step = self.neuron.step(currents, dt)
        gate = np.clip(step.gate * self.gate_gain, 0.0, 1.0)
        signed_gate = float(np.clip(gate[0] - gate[1], -1.0, 1.0))
        residual = float(self.residual_blend * self.residual_limit * signed_gate)
        voltage = float(np.clip(base_cmd.baseline_voltage + residual, -limit, limit))

        return QubeCommand(
            voltage=voltage,
            baseline_voltage=base_cmd.baseline_voltage,
            residual_voltage=residual,
            gate_pos=float(gate[0]),
            gate_neg=float(gate[1]),
            control_mode="hyperlif_residual_balance",
            info={
                **base_cmd.info,
                "residual_enabled": 1.0,
                "feature_voltage_norm": feature,
                "current_pos": float(currents[0]),
                "current_neg": float(currents[1]),
                "gate_pos_raw": float(step.gate[0]),
                "gate_neg_raw": float(step.gate[1]),
                "signed_gate": signed_gate,
                "residual_limit": self.residual_limit,
                "residual_blend": self.residual_blend,
            },
        )
