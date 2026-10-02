"""Standalone Adaptive HyperLIF implementation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .hyperlif import (
    HyperLIFParams,
    event_level,
    exact_gate_update,
    gate_target,
    stable_voltage_update,
)


@dataclass(frozen=True)
class AdaptiveHyperLIFParams(HyperLIFParams):
    """Parameters for Adaptive HyperLIF.

    The adaptive model replaces the fixed reset gain with:

        dynamic_gain = base_gain + gain_scaling * abs(input_current)
    """

    reset_gain: float = 100.0
    base_gain: float = 20.0
    gain_scaling: float = 80.0


def adaptive_hyperlif_derivatives(
    voltage: float,
    gate: float,
    current: float,
    p: AdaptiveHyperLIFParams,
) -> tuple[float, float]:
    """Continuous-time Adaptive HyperLIF derivatives ``(dv/dt, dr/dt)``."""

    target = gate_target(voltage, gate, p)
    dr = (target - gate) / p.tau_r
    drift = (-(voltage - p.v_rest) + current) / p.tau
    dyn_gain = p.base_gain + p.gain_scaling * abs(current)
    conductance = dyn_gain * gate**2
    reset_force = -conductance * (voltage - p.v_reset)
    dv = drift + reset_force
    return float(dv), float(dr)


class AdaptiveHyperLIFNeuron:
    """Stateful single-neuron Adaptive HyperLIF simulator."""

    def __init__(self, params: AdaptiveHyperLIFParams | None = None):
        self.params = params or AdaptiveHyperLIFParams()
        self.voltage = self.params.v_rest
        self.reset_gate = 0.0
        self.previous_voltage = self.params.v_rest
        self.dynamic_gain = 0.0

    def reset(self) -> None:
        self.voltage = self.params.v_rest
        self.reset_gate = 0.0
        self.previous_voltage = self.params.v_rest
        self.dynamic_gain = 0.0

    def step(self, current: float, dt: float, method: str = "julia") -> dict[str, float]:
        """Advance one time step using ``julia`` or ``stable`` stepping."""

        p = self.params
        v_prev = self.voltage
        r = exact_gate_update(self.voltage, self.reset_gate, dt, p)
        dyn_gain = p.base_gain + p.gain_scaling * abs(current)
        conductance = dyn_gain * r**2

        if method == "stable":
            v_next = stable_voltage_update(
                self.voltage,
                current,
                conductance,
                dt,
                p.tau,
                p.v_rest,
                p.v_reset,
            )
            v_next = float(v_next)
        elif method == "julia":
            drift = (-(self.voltage - p.v_rest) + current) / p.tau
            reset_force = -conductance * (self.voltage - p.v_reset)
            v_next = self.voltage + dt * (drift + reset_force)
        else:
            raise ValueError("method must be 'julia' or 'stable'")

        v_next = max(float(v_next), p.min_voltage)
        threshold = event_level(p)
        event = p.amplitude / dt if v_prev < threshold <= v_next else 0.0

        self.previous_voltage = v_prev
        self.voltage = v_next
        self.reset_gate = float(r)
        self.dynamic_gain = float(dyn_gain)

        return {
            "voltage": self.voltage,
            "reset_gate": self.reset_gate,
            "dynamic_gain": self.dynamic_gain,
            "conductance": float(conductance),
            "events": event,
        }


def simulate_adaptive_hyperlif(
    current: np.ndarray,
    dt: float,
    params: AdaptiveHyperLIFParams | None = None,
    method: str = "julia",
) -> dict[str, np.ndarray]:
    """Simulate a single Adaptive HyperLIF neuron."""

    neuron = AdaptiveHyperLIFNeuron(params)
    current = np.asarray(current, dtype=float)
    n_steps = current.size

    voltage = np.zeros(n_steps, dtype=float)
    gate = np.zeros(n_steps, dtype=float)
    dynamic_gain = np.zeros(n_steps, dtype=float)
    conductance = np.zeros(n_steps, dtype=float)
    events = np.zeros(n_steps, dtype=float)

    for k, j in enumerate(current):
        state = neuron.step(float(j), dt, method=method)
        voltage[k] = state["voltage"]
        gate[k] = state["reset_gate"]
        dynamic_gain[k] = state["dynamic_gain"]
        conductance[k] = state["conductance"]
        events[k] = state["events"]

    return {
        "input_current": current,
        "voltage": voltage,
        "reset_gate": gate,
        "dynamic_gain": dynamic_gain,
        "conductance": conductance,
        "events": events,
    }
