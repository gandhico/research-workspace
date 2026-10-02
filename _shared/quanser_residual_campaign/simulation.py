"""Offline simulation loop for the cross-platform validation campaign."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .controllers import HyperLIFResidualController, LinearBaselineController
from .platforms import PlatformConfig


@dataclass
class SimulationResult:
    mode: str
    time: np.ndarray
    states: np.ndarray
    commands: np.ndarray
    baseline_commands: np.ndarray
    residuals: np.ndarray
    gates: np.ndarray
    features: np.ndarray


def build_controller(config: PlatformConfig, mode: str):
    baseline = LinearBaselineController(config.baseline_gain, config.control_limits)
    if mode == "baseline":
        return baseline
    if mode == "residual":
        return HyperLIFResidualController(
            baseline=baseline,
            limits=config.control_limits,
            blend=0.35,
            current_bias=1.0,
            current_gain=3.5,
            gate_gain=1.0,
        )
    raise ValueError(f"unknown controller mode: {mode}")


def simulate(config: PlatformConfig, mode: str, duration: float) -> SimulationResult:
    dt = float(config.dt)
    n_steps = int(round(float(duration) / dt)) + 1
    n_state = len(config.state_labels)
    n_control = len(config.control_labels)

    time = np.arange(n_steps, dtype=float) * dt
    states = np.zeros((n_steps, n_state), dtype=float)
    commands = np.zeros((n_steps, n_control), dtype=float)
    baseline_commands = np.zeros_like(commands)
    residuals = np.zeros_like(commands)
    gates = np.zeros((n_steps, 2 * n_control), dtype=float)
    features = np.zeros_like(commands)

    x = config.initial_state.astype(float).copy()
    controller = build_controller(config, mode)
    controller.reset()

    for k, t in enumerate(time):
        states[k] = x
        control = controller.compute(x, dt)
        u = control.command
        commands[k] = u
        baseline_commands[k] = control.baseline
        residuals[k] = control.residual
        gates[k] = control.gate
        features[k] = control.feature

        dx = config.a_matrix @ x + config.b_matrix @ u + config.disturbance(float(t))
        x = x + dt * dx

    return SimulationResult(
        mode=mode,
        time=time,
        states=states,
        commands=commands,
        baseline_commands=baseline_commands,
        residuals=residuals,
        gates=gates,
        features=features,
    )

