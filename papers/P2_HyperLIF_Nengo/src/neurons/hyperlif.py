"""Standalone HyperLIF implementation matching the Julia reference equations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HyperLIFParams:
    """Parameters for the two-state HyperLIF model."""

    tau: float = 0.02
    v_rest: float = 0.0
    v_thresh: float = 1.0
    v_reset: float = 0.0
    alpha: float = 100.0
    reset_gain: float = 100.0
    tau_r: float = 0.002
    gamma: float = 0.2
    amplitude: float = 1.0
    min_voltage: float = 0.0
    event_threshold: float | None = None


def event_level(p: HyperLIFParams) -> float:
    """Voltage level used for event/spike output."""

    return p.v_thresh if p.event_threshold is None else p.event_threshold


def sigmoid_switch(x: np.ndarray | float) -> np.ndarray | float:
    """Stable logistic switch used by the reset gate."""

    x = np.clip(x, -700.0, 700.0)
    return 1.0 / (1.0 + np.exp(-x))


def gate_target(voltage: np.ndarray | float, gate: np.ndarray | float, p: HyperLIFParams):
    """Return the target reset-gate value."""

    effective_thresh = p.v_thresh - p.gamma * gate
    return sigmoid_switch(p.alpha * (voltage - effective_thresh))


def hyperlif_derivatives(
    voltage: float,
    gate: float,
    current: float,
    p: HyperLIFParams,
) -> tuple[float, float]:
    """Continuous-time HyperLIF derivatives ``(dv/dt, dr/dt)``."""

    target = gate_target(voltage, gate, p)
    dr = (target - gate) / p.tau_r
    drift = (-(voltage - p.v_rest) + current) / p.tau
    conductance = p.reset_gain * gate**2
    reset_force = -conductance * (voltage - p.v_reset)
    dv = drift + reset_force
    return float(dv), float(dr)


def exact_gate_update(
    voltage: np.ndarray | float,
    gate: np.ndarray | float,
    dt: float,
    p: HyperLIFParams,
):
    """First-order exact update for ``r`` with target fixed over one step."""

    target = gate_target(voltage, gate, p)
    decay = np.exp(-dt / p.tau_r)
    return np.clip(target + (gate - target) * decay, 0.0, 1.0)


def stable_voltage_update(
    voltage: np.ndarray | float,
    current: np.ndarray | float,
    conductance: np.ndarray | float,
    dt: float,
    tau: float,
    v_rest: float,
    v_reset: float,
):
    """Exact update for the linearized voltage equation over one step.

    With current and reset conductance held fixed:

        dv/dt = drive - lambda * v
    """

    lam = (1.0 / tau) + conductance
    drive = (v_rest / tau) + (current / tau) + conductance * v_reset
    decay = np.exp(-lam * dt)
    return np.where(
        lam > 1e-12,
        voltage * decay + (drive / lam) * (1.0 - decay),
        voltage + dt * drive,
    )


class HyperLIFNeuron:
    """Stateful single-neuron HyperLIF simulator."""

    def __init__(self, params: HyperLIFParams | None = None):
        self.params = params or HyperLIFParams()
        self.voltage = self.params.v_rest
        self.reset_gate = 0.0
        self.previous_voltage = self.params.v_rest

    def reset(self) -> None:
        self.voltage = self.params.v_rest
        self.reset_gate = 0.0
        self.previous_voltage = self.params.v_rest

    def step(self, current: float, dt: float, method: str = "julia") -> dict[str, float]:
        """Advance one time step.

        ``method="julia"`` matches the current Julia stepping code: exact
        first-order gate update followed by explicit Euler voltage update.

        ``method="stable"`` uses the same gate update but advances voltage with
        the exact linearized update used for Nengo validation.
        """

        p = self.params
        v_prev = self.voltage
        r = exact_gate_update(self.voltage, self.reset_gate, dt, p)
        conductance = p.reset_gain * r**2

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

        return {
            "voltage": self.voltage,
            "reset_gate": self.reset_gate,
            "conductance": float(conductance),
            "events": event,
        }


def simulate_hyperlif(
    current: np.ndarray,
    dt: float,
    params: HyperLIFParams | None = None,
    method: str = "julia",
) -> dict[str, np.ndarray]:
    """Simulate a single HyperLIF neuron."""

    neuron = HyperLIFNeuron(params)
    current = np.asarray(current, dtype=float)
    n_steps = current.size

    voltage = np.zeros(n_steps, dtype=float)
    gate = np.zeros(n_steps, dtype=float)
    conductance = np.zeros(n_steps, dtype=float)
    events = np.zeros(n_steps, dtype=float)

    for k, j in enumerate(current):
        state = neuron.step(float(j), dt, method=method)
        voltage[k] = state["voltage"]
        gate[k] = state["reset_gate"]
        conductance[k] = state["conductance"]
        events[k] = state["events"]

    return {
        "input_current": current,
        "voltage": voltage,
        "reset_gate": gate,
        "conductance": conductance,
        "events": events,
    }
