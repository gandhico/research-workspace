"""Adaptive HyperLIF neuron core (modelling) — pure numpy, no extra deps.

Ported from `01_HyperLIF_Gate_Residual/v2_clean/src/controllers/neuron_dynamics.py`
(and consistent with `04_Adaptive_HyperLIF_Nengo` MATH_NOTES). Equations:

    theta_eff = v_thresh - gamma*r
    r*        = sigmoid(alpha (v - theta_eff))
    r_{t+1}   = r* + (r - r*) exp(-dt/tau_r)                 (exact gate relaxation)
    G         = (G_base + beta|I|) r^2   (adaptive)  or  G_base r^2  (base)
    lam       = 1/tau + G ;  drive = v_rest/tau + I/tau + G v_reset
    v_{t+1}   = v exp(-lam dt) + (drive/lam)(1 - exp(-lam dt))   (exact linearized)

`activity_mode`: "gate" (r, the residual feature), "voltage" (v/v_thresh), or "events".
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from aero2.config import hyperlif as cfg


@dataclass
class NeuronStepResult:
    activity: np.ndarray   # output signal used by the controller / readout
    events: np.ndarray     # threshold-crossing indicator
    voltage: np.ndarray    # membrane potential (diagnostics)
    gate: np.ndarray       # gate state r (HyperLIF only; zeros otherwise)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, -700.0, 700.0)
    return 1.0 / (1.0 + np.exp(-x))


class BaseDirectNeuron:
    n: int
    activity_mode: str

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError


class StandardLIFDirect(BaseDirectNeuron):
    def __init__(self, n, tau=10.0, v_rest=0.0, v_thresh=1.0, v_reset=0.0, activity_mode="voltage"):
        self.n, self.tau = n, tau
        self.v_rest, self.v_thresh, self.v_reset = v_rest, v_thresh, v_reset
        self.activity_mode = activity_mode
        self.v = np.zeros(n)

    def reset(self):
        self.v[:] = 0.0

    def step(self, current, dt):
        current = np.asarray(current, dtype=float)
        target = self.v_rest + current
        decay = np.exp(-dt / self.tau)
        self.v[:] = target + (self.v - target) * decay
        events = (self.v >= self.v_thresh).astype(float)
        if np.any(events):
            self.v[events > 0] = self.v_reset
        activity = events.copy() if self.activity_mode == "events" else np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)
        return NeuronStepResult(activity, events, self.v.copy(), np.zeros(self.n))


class HyperLIFDirect(BaseDirectNeuron):
    def __init__(self, n, tau=10.0, v_rest=0.0, v_thresh=1.0, v_reset=0.0,
                 alpha=cfg.NEURON_ALPHA, reset_gain=800.0, tau_r=0.2, gamma=3.0,
                 event_threshold=0.5, activity_mode="voltage"):
        self.n, self.tau = n, tau
        self.v_rest, self.v_thresh, self.v_reset = v_rest, v_thresh, v_reset
        self.alpha, self.reset_gain, self.tau_r, self.gamma = alpha, reset_gain, tau_r, gamma
        self.event_threshold, self.activity_mode = event_threshold, activity_mode
        self.v = np.zeros(n)
        self.r = np.zeros(n)

    def reset(self):
        self.v[:] = 0.0
        self.r[:] = 0.0

    def _conductance(self, current):
        return self.reset_gain * self.r ** 2

    def step(self, current, dt):
        current = np.asarray(current, dtype=float)
        v_prev = self.v.copy()
        eff_thresh = self.v_thresh - self.gamma * self.r
        target_r = _sigmoid(self.alpha * (self.v - eff_thresh))
        self.r[:] = target_r + (self.r - target_r) * np.exp(-dt / self.tau_r)

        G = self._conductance(current)
        lam = (1.0 / self.tau) + G
        drive = (self.v_rest / self.tau) + (current / self.tau) + G * self.v_reset
        decay = np.exp(-lam * dt)
        self.v[:] = np.where(lam > 1e-12, self.v * decay + (drive / lam) * (1.0 - decay), self.v + dt * drive)

        events = ((v_prev < self.event_threshold) & (self.v >= self.event_threshold)).astype(float)
        if self.activity_mode == "events":
            activity = events.copy()
        elif self.activity_mode == "gate":
            activity = np.clip(self.r, 0.0, 1.0)
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)
        return NeuronStepResult(activity, events, self.v.copy(), self.r.copy())


class AdaptiveHyperLIFDirect(HyperLIFDirect):
    """HyperLIF with input-dependent conductance G = (base_gain + gain_scaling|I|) r^2."""

    def __init__(self, n, tau=10.0, v_rest=0.0, v_thresh=1.0, v_reset=0.0,
                 alpha=cfg.NEURON_ALPHA, base_gain=800.0, gain_scaling=100.0,
                 tau_r=0.2, gamma=3.0, event_threshold=0.5, activity_mode="voltage"):
        super().__init__(n, tau, v_rest, v_thresh, v_reset, alpha, base_gain, tau_r, gamma,
                         event_threshold, activity_mode)
        self.base_gain = base_gain
        self.gain_scaling = gain_scaling

    def _conductance(self, current):
        return (self.base_gain + self.gain_scaling * np.abs(current)) * self.r ** 2


def make_direct_neuron(name: str, n: int, activity_mode: str = "voltage", scale: str = "control") -> BaseDirectNeuron:
    """Factory. scale='control' applies fast-loop presets (config.hyperlif.NEURON_PRESETS)."""
    name = name.lower()
    extra = {} if scale == "paper" else cfg.NEURON_PRESETS.get(name, {})
    if name in {"standard_lif", "lif", "direct_lif"}:
        return StandardLIFDirect(n=n, activity_mode=activity_mode, **extra)
    if name in {"hyperlif", "direct_hyperlif"}:
        return HyperLIFDirect(n=n, activity_mode=activity_mode, **extra)
    if name in {"adaptive_hyperlif", "direct_adaptive_hyperlif"}:
        return AdaptiveHyperLIFDirect(n=n, activity_mode=activity_mode, **extra)
    raise ValueError(f"unknown neuron type: {name!r}")


__all__ = [
    "NeuronStepResult", "BaseDirectNeuron",
    "StandardLIFDirect", "HyperLIFDirect", "AdaptiveHyperLIFDirect", "make_direct_neuron",
]
