"""
Direct neuron dynamics: LIF, HyperLIF, Adaptive HyperLIF, Izhikevich.
All models implement BaseDirectNeuron with step() and reset() methods.
Returns NeuronStepResult with activity, events, and voltage arrays.

HyperLIF key insight:
    The gate state r captures the reset conductance dynamics. When used in
    activity_mode="gate", r becomes a continuous signal that reflects the
    neuron's readiness to fire. This gate signal can act as a residual
    control feature even without explicit spike events.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass
class NeuronStepResult:
    activity: np.ndarray   # output signal used by controller
    events: np.ndarray     # spike / threshold-crossing indicator
    voltage: np.ndarray    # membrane potential for diagnostics
    gate: np.ndarray       # gate state r (HyperLIF only; zeros otherwise)


class BaseDirectNeuron:
    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        raise NotImplementedError
    def reset(self) -> None:
        raise NotImplementedError


class StandardLIFDirect(BaseDirectNeuron):
    """
    Standard Leaky Integrate-and-Fire neuron.

    dv/dt = (-(v - v_rest) + I) / tau
    Fire when v >= v_thresh, reset to v_reset.
    """
    def __init__(self, n: int, tau: float = 10.0, v_rest: float = 0.0,
                 v_thresh: float = 1.0, v_reset: float = 0.0,
                 activity_mode: str = "voltage"):
        self.n = n
        self.tau = tau
        self.v_rest = v_rest
        self.v_thresh = v_thresh
        self.v_reset = v_reset
        self.activity_mode = activity_mode
        self.v = np.zeros(n, dtype=float)

    def reset(self) -> None:
        self.v[:] = 0.0

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)
        target = self.v_rest + current
        decay  = np.exp(-dt / self.tau)
        self.v[:] = target + (self.v - target) * decay
        events = (self.v >= self.v_thresh).astype(float)
        if np.any(events):
            self.v[events > 0] = self.v_reset
        if self.activity_mode == "events":
            activity = events.copy()
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)
        return NeuronStepResult(activity=activity, events=events,
                                voltage=self.v.copy(), gate=np.zeros(self.n))


class HyperLIFDirect(BaseDirectNeuron):
    """
    HyperLIF: standard LIF extended with a gate/reset state r.

    dv/dt = (-(v - v_rest) + I) / tau  -  reset_gain * r^2 * (v - v_reset)
    dr/dt = (sigmoid(alpha * (v - eff_thresh)) - r) / tau_r
    eff_thresh = v_thresh - gamma * r

    activity_mode="gate": r is the output activity (the key insight for
        gate-state residual control — r is a smooth, continuous signal
        that reflects the neuron's activation state without requiring
        explicit spike event detection).
    """
    def __init__(self, n: int, tau: float = 10.0, v_rest: float = 0.0,
                 v_thresh: float = 1.0, v_reset: float = 0.0,
                 alpha: float = 50.0, reset_gain: float = 800.0,
                 tau_r: float = 0.2, gamma: float = 3.0,
                 event_threshold: float = 0.5,
                 activity_mode: str = "voltage"):
        self.n = n
        self.tau = tau
        self.v_rest = v_rest
        self.v_thresh = v_thresh
        self.v_reset = v_reset
        self.alpha = alpha
        self.reset_gain = reset_gain
        self.tau_r = tau_r
        self.gamma = gamma
        self.event_threshold = event_threshold
        self.activity_mode = activity_mode
        self.v = np.zeros(n, dtype=float)
        self.r = np.zeros(n, dtype=float)

    def reset(self) -> None:
        self.v[:] = 0.0
        self.r[:] = 0.0

    @staticmethod
    def _sig(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, -700.0, 700.0)
        return 1.0 / (1.0 + np.exp(-x))

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)
        v_prev = self.v.copy()

        eff_thresh = self.v_thresh - self.gamma * self.r
        target_r   = self._sig(self.alpha * (self.v - eff_thresh))
        r_decay    = np.exp(-dt / self.tau_r)
        self.r[:]  = target_r + (self.r - target_r) * r_decay

        conductance = self.reset_gain * self.r ** 2
        lam  = (1.0 / self.tau) + conductance
        drive = (self.v_rest / self.tau) + (current / self.tau) + conductance * self.v_reset
        decay = np.exp(-lam * dt)
        self.v[:] = np.where(lam > 1e-12,
                             self.v * decay + (drive / lam) * (1.0 - decay),
                             self.v + dt * drive)

        events = ((v_prev < self.event_threshold) & (self.v >= self.event_threshold)).astype(float)

        if self.activity_mode == "events":
            activity = events.copy()
        elif self.activity_mode == "gate":
            activity = np.clip(self.r, 0.0, 1.0)
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)

        return NeuronStepResult(activity=activity, events=events,
                                voltage=self.v.copy(), gate=self.r.copy())


class AdaptiveHyperLIFDirect(BaseDirectNeuron):
    """
    Adaptive HyperLIF: HyperLIF where reset conductance scales with |I|.

    dynamic_gain = base_gain + gain_scaling * |I|

    This lets the gate state respond more strongly to larger input currents,
    giving input-dependent adaptive dynamics useful for varying maneuver intensities.
    """
    def __init__(self, n: int, tau: float = 10.0, v_rest: float = 0.0,
                 v_thresh: float = 1.0, v_reset: float = 0.0,
                 alpha: float = 50.0, base_gain: float = 800.0,
                 gain_scaling: float = 100.0, tau_r: float = 0.2,
                 gamma: float = 3.0, event_threshold: float = 0.5,
                 activity_mode: str = "voltage"):
        self.n = n
        self.tau = tau
        self.v_rest = v_rest
        self.v_thresh = v_thresh
        self.v_reset = v_reset
        self.alpha = alpha
        self.base_gain = base_gain
        self.gain_scaling = gain_scaling
        self.tau_r = tau_r
        self.gamma = gamma
        self.event_threshold = event_threshold
        self.activity_mode = activity_mode
        self.v = np.zeros(n, dtype=float)
        self.r = np.zeros(n, dtype=float)

    def reset(self) -> None:
        self.v[:] = 0.0
        self.r[:] = 0.0

    @staticmethod
    def _sig(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, -700.0, 700.0)
        return 1.0 / (1.0 + np.exp(-x))

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)
        v_prev = self.v.copy()

        eff_thresh = self.v_thresh - self.gamma * self.r
        target_r   = self._sig(self.alpha * (self.v - eff_thresh))
        r_decay    = np.exp(-dt / self.tau_r)
        self.r[:]  = target_r + (self.r - target_r) * r_decay

        dynamic_gain = self.base_gain + self.gain_scaling * np.abs(current)
        conductance  = dynamic_gain * self.r ** 2
        lam   = (1.0 / self.tau) + conductance
        drive = (self.v_rest / self.tau) + (current / self.tau) + conductance * self.v_reset
        decay = np.exp(-lam * dt)
        self.v[:] = np.where(lam > 1e-12,
                             self.v * decay + (drive / lam) * (1.0 - decay),
                             self.v + dt * drive)

        events = ((v_prev < self.event_threshold) & (self.v >= self.event_threshold)).astype(float)

        if self.activity_mode == "events":
            activity = events.copy()
        elif self.activity_mode == "gate":
            activity = np.clip(self.r, 0.0, 1.0)
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)

        return NeuronStepResult(activity=activity, events=events,
                                voltage=self.v.copy(), gate=self.r.copy())


class IzhikevichDirect(BaseDirectNeuron):
    """Izhikevich regular-spiking neuron (event-based activity)."""
    def __init__(self, n: int, a: float = 0.02, b: float = 0.2,
                 c: float = -65.0, d: float = 8.0, activity_mode: str = "events"):
        self.n = n
        self.a, self.b, self.c, self.d = a, b, c, d
        self.activity_mode = activity_mode
        self.v = np.full(n, c, dtype=float)
        self.u = self.b * self.v.copy()

    def reset(self) -> None:
        self.v[:] = self.c
        self.u[:] = self.b * self.v

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)
        dt_ms = dt * 1000.0
        dv = 0.04*self.v**2 + 5.0*self.v + 140.0 - self.u + current
        du = self.a * (self.b*self.v - self.u)
        self.v += dt_ms * dv
        self.u += dt_ms * du
        events = (self.v >= 30.0).astype(float)
        if np.any(events):
            idx = events > 0
            self.v[idx] = self.c
            self.u[idx] += self.d
        if self.activity_mode == "events":
            activity = events.copy()
        else:
            activity = np.clip((self.v + 80.0) / 110.0, 0.0, 1.0)
        return NeuronStepResult(activity=activity, events=events,
                                voltage=self.v.copy(), gate=np.zeros(self.n))


# ---- Presets ---------------------------------------------------------------

_CONTROL_SCALE_PARAMS = {
    "standard_lif":       dict(tau=0.05, v_thresh=1.0, v_reset=0.0),
    "hyperlif":           dict(tau=0.05, tau_r=0.005, reset_gain=120.0,
                               gamma=2.0, event_threshold=0.5),
    "adaptive_hyperlif":  dict(tau=0.05, tau_r=0.005, base_gain=120.0,
                               gain_scaling=30.0, gamma=2.0, event_threshold=0.5),
}


def make_direct_neuron(name: str, n: int,
                       activity_mode: str = "voltage",
                       scale: str = "paper") -> BaseDirectNeuron:
    """
    Factory for direct neuron models.
    scale="paper" uses original validation-scale parameters.
    scale="control" uses fast time constants appropriate for MuJoCo control loops.
    """
    name  = name.lower()
    extra = {} if scale == "paper" else _CONTROL_SCALE_PARAMS.get(name, {})

    if name in {"standard_lif", "lif", "direct_lif"}:
        return StandardLIFDirect(n=n, activity_mode=activity_mode, **extra)
    if name in {"hyperlif", "direct_hyperlif"}:
        return HyperLIFDirect(n=n, activity_mode=activity_mode, **extra)
    if name in {"adaptive_hyperlif", "adapthyperlif", "direct_adaptive_hyperlif"}:
        return AdaptiveHyperLIFDirect(n=n, activity_mode=activity_mode, **extra)
    if name in {"izhikevich", "izh", "direct_izhikevich"}:
        return IzhikevichDirect(n=n, activity_mode="events")
    raise ValueError(f"Unknown neuron type: '{name}'")
