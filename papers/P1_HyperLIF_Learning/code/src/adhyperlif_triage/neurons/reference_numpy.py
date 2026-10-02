"""Vendored NumPy reference for HyperLIF / Adaptive HyperLIF (the parity target).

This is a faithful, self-contained copy of the *validated* ``stable`` stepping from
``04_Adaptive_HyperLIF_Nengo/src/neurons/{hyperlif,adaptive_hyperlif}.py``.

That stable path is the one proven (RMSE = 0) to equal the Nengo ``NeuronType`` port
(see ``05_Adaptive_HyperLIF_Nengo_Paper/RESULTS_AUDIT.md`` result #1). We vendor it here
so the parity gate has an unambiguous, dependency-free reference: any PyTorch neuron in
this project must reproduce these traces to machine precision before its benchmark numbers
are trusted.

DO NOT "improve" this file. It is a frozen reference. New dynamics (e.g. the origin
variants) belong in ``hyperlif_torch.py`` and are validated *against* this.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HyperLIFParams:
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


@dataclass(frozen=True)
class AdaptiveHyperLIFParams(HyperLIFParams):
    reset_gain: float = 100.0
    base_gain: float = 20.0
    gain_scaling: float = 80.0


def event_level(p: HyperLIFParams) -> float:
    return p.v_thresh if p.event_threshold is None else p.event_threshold


def sigmoid_switch(x):
    x = np.clip(x, -700.0, 700.0)
    return 1.0 / (1.0 + np.exp(-x))


def gate_target(voltage, gate, p: HyperLIFParams):
    effective_thresh = p.v_thresh - p.gamma * gate
    return sigmoid_switch(p.alpha * (voltage - effective_thresh))


def exact_gate_update(voltage, gate, dt, p: HyperLIFParams):
    target = gate_target(voltage, gate, p)
    decay = np.exp(-dt / p.tau_r)
    return np.clip(target + (gate - target) * decay, 0.0, 1.0)


def stable_voltage_update(voltage, current, conductance, dt, tau, v_rest, v_reset):
    lam = (1.0 / tau) + conductance
    drive = (v_rest / tau) + (current / tau) + conductance * v_reset
    decay = np.exp(-lam * dt)
    return np.where(
        lam > 1e-12,
        voltage * decay + (drive / lam) * (1.0 - decay),
        voltage + dt * drive,
    )


def simulate_hyperlif(current, dt, params: HyperLIFParams | None = None):
    """Single-neuron HyperLIF, ``stable`` stepping (the Nengo-equivalent path)."""
    p = params or HyperLIFParams()
    current = np.asarray(current, dtype=float)
    n = current.size
    v = float(p.v_rest)
    r = 0.0
    out = {k: np.zeros(n) for k in ("voltage", "reset_gate", "conductance", "events")}
    thr = event_level(p)
    for k, j in enumerate(current):
        v_prev = v
        r = float(exact_gate_update(v, r, dt, p))
        g = p.reset_gain * r**2
        v = float(stable_voltage_update(v, float(j), g, dt, p.tau, p.v_rest, p.v_reset))
        v = max(v, p.min_voltage)
        out["voltage"][k] = v
        out["reset_gate"][k] = r
        out["conductance"][k] = g
        out["events"][k] = p.amplitude / dt if v_prev < thr <= v else 0.0
    out["input_current"] = current
    return out


def simulate_adaptive_hyperlif(current, dt, params: AdaptiveHyperLIFParams | None = None):
    """Single-neuron Adaptive HyperLIF, ``stable`` stepping."""
    p = params or AdaptiveHyperLIFParams()
    current = np.asarray(current, dtype=float)
    n = current.size
    v = float(p.v_rest)
    r = 0.0
    out = {k: np.zeros(n) for k in ("voltage", "reset_gate", "dynamic_gain", "conductance", "events")}
    thr = event_level(p)
    for k, j in enumerate(current):
        v_prev = v
        r = float(exact_gate_update(v, r, dt, p))
        dyn = p.base_gain + p.gain_scaling * abs(float(j))
        g = dyn * r**2
        v = float(stable_voltage_update(v, float(j), g, dt, p.tau, p.v_rest, p.v_reset))
        v = max(v, p.min_voltage)
        out["voltage"][k] = v
        out["reset_gate"][k] = r
        out["dynamic_gain"][k] = dyn
        out["conductance"][k] = g
        out["events"][k] = p.amplitude / dt if v_prev < thr <= v else 0.0
    out["input_current"] = current
    return out
