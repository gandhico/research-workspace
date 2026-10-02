"""Exploratory CMG observables for reward-driven *racing* policies.

The default membrane/gate step is algebraically the same as the Nengo
CoupledMembraneGate.step in the ACC project.  It is not an LIF spike/reset
    cell.  ``crossing`` adds the historical upward-crossing *observable* without
    changing (v,r). ``reset_gate`` and ``reset_spike`` are NEW models: an event subtracts threshold
from voltage, allowing repeated events. Never call its results ACC-CMG parity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class CMGParams:
    tau: float = 0.05
    tau_r: float = 0.005
    v_rest: float = 0.0
    v_reset: float = 0.0
    v_threshold: float = 1.0
    alpha: float = 50.0
    gamma: float = 2.0
    base_gain: float = 120.0
    gain_scaling: float = 30.0
    gate_gain: float = 1.0e5
    adaptive: bool = True
    event_threshold: float = 0.5
    event_filter_tau: float = 0.025
    event_scale_hz: float = 80.0

    def asdict(self):
        return asdict(self)


class CMGPopulation:
    """Direct-current-driven population; no hidden Nengo gain/intercept fit."""

    MODES = ("graded", "crossing", "reset_gate", "reset_spike")

    def __init__(self, n: int, mode: str, params: CMGParams | None = None):
        if mode not in self.MODES:
            raise ValueError(f"unknown CMG mode {mode!r}")
        self.n = int(n)
        self.mode = mode
        self.p = params or CMGParams()
        self.reset()

    def reset(self):
        self.v = np.full(self.n, self.p.v_rest, dtype=np.float64)
        self.r = np.zeros(self.n, dtype=np.float64)
        self.filtered_rate_hz = np.zeros(self.n, dtype=np.float64)
        self.last_events = np.zeros(self.n, dtype=np.float64)
        self.event_total = np.zeros(self.n, dtype=np.int64)
        self.time_s = 0.0

    def step(self, current: np.ndarray, dt: float) -> np.ndarray:
        """One substep. Events are binary per cell/substep, never occupancy."""
        p = self.p
        j = np.asarray(current, dtype=np.float64)
        if j.shape != (self.n,):
            raise ValueError(f"expected current shape {(self.n,)}, got {j.shape}")
        v_previous = self.v.copy()
        arg = np.clip(p.alpha * (self.v - (p.v_threshold - p.gamma * self.r)), -60, 60)
        target = 1.0 / (1.0 + np.exp(-arg))
        self.r += dt * (target - self.r) / p.tau_r
        np.clip(self.r, 0.0, 1.0, out=self.r)
        gain = p.base_gain + p.gain_scaling * np.abs(j) if p.adaptive else p.base_gain
        conductance = gain * self.r * self.r
        lam = 1.0 / p.tau + conductance
        drive = p.v_rest / p.tau + j / p.tau + conductance * p.v_reset
        decay = np.exp(-lam * dt)
        self.v[:] = self.v * decay + (drive / lam) * (1.0 - decay)

        events = (v_previous < p.event_threshold) & (self.v >= p.event_threshold)
        if self.mode in ("reset_gate", "reset_spike"):
            # Explicitly new hybrid CMG-LIF dynamics; the gate state is retained.
            self.v[events] -= p.event_threshold
        self.last_events[:] = events.astype(float)
        self.event_total += events.astype(np.int64)
        self.filtered_rate_hz += -np.expm1(-dt / p.event_filter_tau) * (
            self.last_events / dt - self.filtered_rate_hz
        )
        self.time_s += dt
        return self.features()

    def advance(self, current: np.ndarray, duration: float, neural_dt: float) -> np.ndarray:
        n = round(duration / neural_dt)
        if n < 1 or not np.isclose(n * neural_dt, duration, atol=1e-9):
            raise ValueError("duration must be a positive integer number of neural substeps")
        for _ in range(n):
            self.step(current, neural_dt)
        return self.features()

    def features(self) -> np.ndarray:
        if self.mode in ("graded", "reset_gate"):
            return np.clip(self.p.gate_gain * self.r, 0.0, 1.0)
        return np.clip(self.filtered_rate_hz / self.p.event_scale_hz, 0.0, 1.0)

    def diagnostics(self) -> dict:
        return {
            "voltage": self.v.copy(), "gate": self.r.copy(),
            "features": self.features().copy(), "filtered_rate_hz": self.filtered_rate_hz.copy(),
            "event_count": self.event_total.copy(), "event_rate_hz": self.event_total / max(self.time_s, 1e-12),
            "time_s": self.time_s,
        }


def policy_preset(mode: str) -> CMGParams:
    """Predeclared policy presets; not tuned on held-out race outcomes.

    Graded mode lowers the gate readout gain from 1e5 to 1 and softens the
    sigmoid. Spike modes share the same continuous cell parameters; only the
    event/reset rule differs. This does NOT match the ACC frozen cell.
    """
    if mode not in CMGPopulation.MODES:
        raise ValueError(mode)
    return CMGParams(alpha=12.0, gamma=0.35, base_gain=20.0,
                     gain_scaling=10.0, gate_gain=1.0,
                     v_threshold=0.55, event_threshold=0.48,
                     event_filter_tau=0.025, event_scale_hz=80.0)
