# Direct neuron dynamics used by the MuJoCo torque controllers.
# Each neuron model receives an input current vector and returns:
#   activity: normalized output signal used by the controller
#   events: spike/event indicator for each neuron
#   voltage: internal membrane voltage/state for diagnostics
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

# Standard result container returned by every direct neuron model.
# This keeps the interface consistent across LIF, HyperLIF,
# Adaptive HyperLIF, and Izhikevich neurons.
@dataclass
class NeuronStepResult:
    activity: np.ndarray
    events: np.ndarray
    voltage: np.ndarray


# Abstract interface for all direct neuron models.
# Every direct neuron must implement step() and reset().
class BaseDirectNeuron:
    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError


# Direct implementation of a standard Leaky Integrate-and-Fire neuron.
# The membrane voltage integrates input current, emits an event when it crosses
# threshold, then resets. The controller can use either voltage activity or events.
class StandardLIFDirect(BaseDirectNeuron):
    """
    Paper-scale Standard LIF.

    Normalized voltage:
        dv/dt = (-(v - v_rest) + I) / tau

    Event/reset:
        if v >= v_thresh:
            event = 1
            v = v_reset

    This is a discrete-time approximation of the paper-scale LIF baseline.
    """

    def __init__(
        self,
        n: int,
        tau: float = 10.0,
        v_rest: float = 0.0,
        v_thresh: float = 1.0,
        v_reset: float = 0.0,
        activity_mode: str = "voltage",
    ):
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

        # Exact update for dv/dt = (v_rest + I - v)/tau
        target = self.v_rest + current
        decay = np.exp(-dt / self.tau)
        self.v[:] = target + (self.v - target) * decay

        events = (self.v >= self.v_thresh).astype(float)
        if np.any(events > 0.0):
            self.v[events > 0.0] = self.v_reset

        if self.activity_mode == "events":
            activity = events.copy()
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)

        return NeuronStepResult(activity=activity, events=events, voltage=self.v.copy())


# Direct implementation of HyperLIF.
# In addition to membrane voltage v, it uses a gate/reset state r that modifies
# the effective threshold and reset conductance, giving richer internal dynamics
# than standard LIF.
class HyperLIFDirect(BaseDirectNeuron):
    """
    Stable paper-scale HyperLIF.

    Continuous model:
        dv/dt = (-(v - v_rest) + I) / tau
                - reset_gain * r^2 * (v - v_reset)

        dr/dt = (sigmoid(alpha * (v - effective_thresh)) - r) / tau_r

        effective_thresh = v_thresh - gamma*r

    The voltage update uses the same stable exponential idea we used for Nengo.
    """

    def __init__(
        self,
        n: int,
        tau: float = 10.0,
        v_rest: float = 0.0,
        v_thresh: float = 1.0,
        v_reset: float = 0.0,
        alpha: float = 50.0,
        reset_gain: float = 800.0,
        tau_r: float = 0.2,
        gamma: float = 3.0,
        event_threshold: float = 0.5,
        activity_mode: str = "voltage",
    ):
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
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, -700.0, 700.0)
        return 1.0 / (1.0 + np.exp(-x))

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)
        v_prev = self.v.copy()

        effective_thresh = self.v_thresh - self.gamma * self.r
        target_r = self._sigmoid(self.alpha * (self.v - effective_thresh))

        r_decay = np.exp(-dt / self.tau_r)
        self.r[:] = target_r + (self.r - target_r) * r_decay

        conductance = self.reset_gain * self.r**2
        lam = (1.0 / self.tau) + conductance
        drive = (self.v_rest / self.tau) + (current / self.tau) + conductance * self.v_reset
        decay = np.exp(-lam * dt)

        self.v[:] = np.where(
            lam > 1e-12,
            self.v * decay + (drive / lam) * (1.0 - decay),
            self.v + dt * drive,
        )

        events = ((v_prev < self.event_threshold) & (self.v >= self.event_threshold)).astype(float)

        if self.activity_mode == "events":
            activity = events.copy()
        elif self.activity_mode == "gate":
            activity = np.clip(self.r, 0.0, 1.0)
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)

        return NeuronStepResult(activity=activity, events=events, voltage=self.v.copy())


# Direct implementation of Adaptive HyperLIF.
# This extends HyperLIF by making the reset/gate conductance depend on input
# current magnitude, allowing the neuron dynamics to adapt to stronger commands.
class AdaptiveHyperLIFDirect(BaseDirectNeuron):
    """
    Stable paper-scale Adaptive HyperLIF.

    Difference from HyperLIF:
        dynamic_gain = base_gain + gain_scaling * abs(I)
    """

    def __init__(
        self,
        n: int,
        tau: float = 10.0,
        v_rest: float = 0.0,
        v_thresh: float = 1.0,
        v_reset: float = 0.0,
        alpha: float = 50.0,
        base_gain: float = 800.0,
        gain_scaling: float = 100.0,
        tau_r: float = 0.2,
        gamma: float = 3.0,
        event_threshold: float = 0.5,
        activity_mode: str = "voltage",
    ):
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
    def _sigmoid(x: np.ndarray) -> np.ndarray:
        x = np.clip(x, -700.0, 700.0)
        return 1.0 / (1.0 + np.exp(-x))

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)
        v_prev = self.v.copy()

        effective_thresh = self.v_thresh - self.gamma * self.r
        target_r = self._sigmoid(self.alpha * (self.v - effective_thresh))

        r_decay = np.exp(-dt / self.tau_r)
        self.r[:] = target_r + (self.r - target_r) * r_decay

        dynamic_gain = self.base_gain + self.gain_scaling * np.abs(current)
        conductance = dynamic_gain * self.r**2

        lam = (1.0 / self.tau) + conductance
        drive = (self.v_rest / self.tau) + (current / self.tau) + conductance * self.v_reset
        decay = np.exp(-lam * dt)

        self.v[:] = np.where(
            lam > 1e-12,
            self.v * decay + (drive / lam) * (1.0 - decay),
            self.v + dt * drive,
        )

        events = ((v_prev < self.event_threshold) & (self.v >= self.event_threshold)).astype(float)

        if self.activity_mode == "events":
            activity = events.copy()
        elif self.activity_mode == "gate":
            activity = np.clip(self.r, 0.0, 1.0)
        else:
            activity = np.clip(self.v / max(self.v_thresh, 1e-12), 0.0, 1.0)

        return NeuronStepResult(activity=activity, events=events, voltage=self.v.copy())


# Direct Izhikevich neuron model for benchmarking.
# This model uses voltage and recovery variables with spike-reset dynamics.
# Its voltage scale is different from the normalized LIF-family models, so it is
# usually safest to use event-based activity.
class IzhikevichDirect(BaseDirectNeuron):
    """
    Direct Izhikevich regular-spiking model.

    This is included for controller benchmarking, but its raw voltage scale is
    different from the normalized LIF-family models.
    """

    def __init__(
        self,
        n: int,
        a: float = 0.02,
        b: float = 0.2,
        c: float = -65.0,
        d: float = 8.0,
        activity_mode: str = "events",
    ):
        self.n = n
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.activity_mode = activity_mode

        self.v = np.full(n, c, dtype=float)
        self.u = self.b * self.v

    def reset(self) -> None:
        self.v[:] = self.c
        self.u[:] = self.b * self.v

    def step(self, current: np.ndarray, dt: float) -> NeuronStepResult:
        current = np.asarray(current, dtype=float)

        # Izhikevich equations are usually written in ms.
        # Convert seconds dt to ms-like integration step.
        dt_ms = dt * 1000.0

        dv = 0.04 * self.v**2 + 5.0 * self.v + 140.0 - self.u + current
        du = self.a * (self.b * self.v - self.u)

        self.v += dt_ms * dv
        self.u += dt_ms * du

        events = (self.v >= 30.0).astype(float)

        if np.any(events > 0.0):
            idx = events > 0.0
            self.v[idx] = self.c
            self.u[idx] += self.d

        if self.activity_mode == "events":
            activity = events.copy()
        else:
            # Normalize approximate voltage range [-80, 30] to [0, 1].
            activity = np.clip((self.v + 80.0) / 110.0, 0.0, 1.0)

        return NeuronStepResult(activity=activity, events=events, voltage=self.v.copy())



# Return parameter presets for the selected direct-neuron scale.
# "paper" keeps the original validation-scale parameters.
# "control" uses faster time constants so neuron dynamics are visible and useful
# at the MuJoCo control timestep.
def _scale_kwargs(name: str, scale: str) -> dict:
    """
    Parameter presets for direct neuron controllers.

    paper:
        Uses the paper-scale time constants used in the neuron validation stage.
        This is scientifically consistent but slow for MuJoCo control.

    control:
        Time-rescaled parameters for fast MuJoCo / Quanser-style control loops.
        This is the mode we use to make the neuron dynamics visible at dt=0.0005.
    """
    name = name.lower()
    scale = scale.lower()

    if scale == "paper":
        return {}

    if scale != "control":
        raise ValueError(f"Unknown direct neuron scale: {scale}")

    if name in {"standard_lif", "lif", "direct_lif"}:
        return dict(
            tau=0.05,
            v_thresh=1.0,
            v_reset=0.0,
        )

    if name in {"hyperlif", "direct_hyperlif"}:
        return dict(
            tau=0.05,
            tau_r=0.005,
            reset_gain=120.0,
            gamma=2.0,
            event_threshold=0.5,
        )

    if name in {"adaptive_hyperlif", "adapthyperlif", "direct_adaptive_hyperlif"}:
        return dict(
            tau=0.05,
            tau_r=0.005,
            base_gain=120.0,
            gain_scaling=30.0,
            gamma=2.0,
            event_threshold=0.5,
        )

    if name in {"izhikevich", "izh", "direct_izhikevich"}:
        return {}

    return {}


# Factory function for direct neuron models.
# Creates the requested neuron type with the selected activity mode and scale.
# This keeps controller code simple because it can request a neuron by name
def make_direct_neuron(
    name: str,
    n: int,
    activity_mode: str = "voltage",
    scale: str = "paper",
) -> BaseDirectNeuron:
    name = name.lower()
    kwargs = _scale_kwargs(name, scale)

    if name in {"standard_lif", "lif", "direct_lif"}:
        return StandardLIFDirect(n=n, activity_mode=activity_mode, **kwargs)

    if name in {"hyperlif", "direct_hyperlif"}:
        return HyperLIFDirect(n=n, activity_mode=activity_mode, **kwargs)

    if name in {"adaptive_hyperlif", "adapthyperlif", "direct_adaptive_hyperlif"}:
        return AdaptiveHyperLIFDirect(n=n, activity_mode=activity_mode, **kwargs)

    if name in {"izhikevich", "izh", "direct_izhikevich"}:
        return IzhikevichDirect(n=n, activity_mode="events", **kwargs)

    raise ValueError(f"Unknown direct neuron type: {name}")

