"""Mechanism-control bases for the CMG-PES residual, with Nengo's exact PES ordering.

All analytic bases here share one decoder recursion, reverse-engineered from the
archived strict_exact Nengo CMG traces (``validate_ordering.py`` checks it to
machine precision).  At plant step k, with paired current J_k:

    a_k      = basis(J_k, internal state)                  # neuron/basis update
    W_pes    = W_{k-1} + eta (y*_{k-1} - s_{k-1}) a_{k-1}^T # Nengo PES: previous step
    s_k      = clip(W_pes a_k, -1, 1)                      # decoder read
    W_k      = clip(W_pes - leak W_{k-1}, -6, 6)           # frozen leak/projection

This differs from the NumPy ``constant-one``/``paired-current`` adapters of
neuron_basis_decisive_2026-09-24, which update W from the *same* step.  Using
Nengo's ordering here makes every new arm differ from CMG only in the basis.

Bases
-----
cmg-numpy      Exact NumPy restatement of nengo_cmg.CoupledMembraneGate (validation only).
lpf-logistic   a = clip(G sigma(alpha (LPF_tau(J) - v_th)), 0, 1): CMG minus gate dynamics,
               gate feedback (gamma) and conductance; same tau, alpha, v_th, G, clip.
constant-rest  a = a_rest (CMG resting readout at the bias current) on all six units.
latch-replay   a_j = a_rest before unit j's archived CMG latch time, 1 afterwards.
constant-one-nengo-order  a = 1 with this ordering (ordering-effect check only).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

BASES = ("cmg-numpy", "lpf-logistic", "constant-rest", "latch-replay", "constant-one-nengo-order")

# nengo_cmg.CoupledMembraneGate defaults (paper Table I).
CMG_PARAMS = dict(
    tau=0.05, tau_r=0.005, v_rest=0.0, v_reset=0.0, v_threshold=1.0,
    alpha=50.0, gamma=2.0, base_gain=120.0, gain_scaling=30.0, gate_gain=1.0e5,
)


def cmg_step(p: dict, adaptive: bool, dt: float, J: np.ndarray, v: np.ndarray, r: np.ndarray):
    """One CoupledMembraneGate.step, in the same operation order; updates v, r in place."""
    x = np.clip(p["alpha"] * (v - (p["v_threshold"] - p["gamma"] * r)), -60.0, 60.0)
    gate_target = 1.0 / (1.0 + np.exp(-x))
    r += dt * (gate_target - r) / p["tau_r"]
    np.clip(r, 0.0, 1.0, out=r)
    gain = p["base_gain"]
    if adaptive:
        gain = gain + p["gain_scaling"] * np.abs(J)
    conductance = gain * r * r
    lam = 1.0 / p["tau"] + conductance
    drive = p["v_rest"] / p["tau"] + J / p["tau"] + conductance * p["v_reset"]
    decay = np.exp(-lam * dt)
    v[:] = v * decay + (drive / np.maximum(lam, 1e-12)) * (1.0 - decay)
    return np.clip(p["gate_gain"] * r, 0.0, 1.0)


def cmg_rest_activity(dt: float = 5e-4, current: float = 0.75, seconds: float = 20.0) -> float:
    """Resting readout of the canonical CMG unit at constant bias current."""
    v = np.zeros(1)
    r = np.zeros(1)
    J = np.full(1, current)
    a = np.zeros(1)
    for _ in range(int(round(seconds / dt))):
        a = cmg_step(CMG_PARAMS, True, dt, J, v, r)
    return float(a[0])


@dataclass
class _Output:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    raw_output: np.ndarray


class NengoOrderBasisAdapter:
    """Six-feature basis + PES decoder behind the final runner's augmentor interface."""

    family = "mechanism-control"

    def __init__(
        self,
        basis: str,
        limits: np.ndarray,
        dt: float,
        beta: float,
        learning_rate: float,
        seed: int,
        *,
        latch_times_s: list[float | None] | None = None,
        rest_activity: float | None = None,
        adaptive: bool = True,
        leak: float = 1e-6,
        current_bias: float = 0.75,
        current_gain: float = 1.25,
    ):
        del seed  # deterministic; kept for interface parity
        if basis not in BASES:
            raise ValueError(f"Unsupported basis: {basis}")
        if basis == "latch-replay" and latch_times_s is None:
            raise ValueError("latch-replay needs latch_times_s")
        self.basis = basis
        self.p = dict(CMG_PARAMS)
        self.adaptive = bool(adaptive)
        self.limits = np.asarray(limits, dtype=float)
        self.dt = float(dt)
        self.beta = float(beta)
        self.learning_rate = float(learning_rate)
        self.leak = float(leak)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.rest_activity = float(cmg_rest_activity(self.dt) if rest_activity is None else rest_activity)
        self.latch_steps = (
            None if latch_times_s is None
            else np.array([np.inf if t is None else round(t / self.dt) for t in latch_times_s])
        )
        self.nengo_learning_rate = self.learning_rate * 6 / self.dt  # equivalent Nengo eta_N, for metadata
        self._k = 0
        self._v = np.zeros(6)
        self._r = np.zeros(6)
        self._weights = np.c_[np.eye(3), -np.eye(3)].astype(float)
        self._current = np.zeros(6)
        self._activity = np.zeros(6)
        self._gate_target = np.zeros(6)
        self._effective_threshold = np.zeros(6)
        self._decoded_raw = np.zeros(3)
        self._decoded_clipped = np.zeros(3)
        self._target = np.zeros(3)
        self._pes_error = np.zeros(3)
        self._prev_activity = np.zeros(6)
        self._prev_target = np.zeros(3)
        self._prev_decoded = np.zeros(3)

    @property
    def W(self) -> np.ndarray:
        return self._weights.copy()

    def _basis(self, J: np.ndarray) -> np.ndarray:
        p = self.p
        if self.basis == "cmg-numpy":
            a = cmg_step(p, self.adaptive, self.dt, J, self._v, self._r)
            # Post-step algebraic quantities, as nengo_cmg.NengoCMGPESAugmentor.diagnostics reports them.
            self._effective_threshold = p["v_threshold"] - p["gamma"] * self._r
            self._gate_target = 1.0 / (1.0 + np.exp(-np.clip(p["alpha"] * (self._v - self._effective_threshold), -60.0, 60.0)))
            return a
        if self.basis == "lpf-logistic":
            # Instantaneous gate from the pre-update membrane (same sample alignment as CMG,
            # whose gate also reads the pre-update v), no gate feedback, no conductance.
            x = np.clip(p["alpha"] * (self._v - p["v_threshold"]), -60.0, 60.0)
            self._r[:] = 1.0 / (1.0 + np.exp(-x))
            self._gate_target[:] = self._r
            self._effective_threshold[:] = p["v_threshold"]
            lam = 1.0 / p["tau"]
            decay = np.exp(-lam * self.dt)
            self._v[:] = self._v * decay + (p["v_rest"] + J) * (1.0 - decay)
            return np.clip(p["gate_gain"] * self._r, 0.0, 1.0)
        if self.basis == "constant-rest":
            return np.full(6, self.rest_activity)
        if self.basis == "latch-replay":
            return np.where(self._k >= self.latch_steps, 1.0, self.rest_activity)
        return np.ones(6)  # constant-one-nengo-order

    def step(self, baseline: np.ndarray, target: np.ndarray) -> _Output:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        n = np.divide(u0, self.limits, out=np.zeros(3), where=self.limits > 1e-12)
        self._current[:] = np.r_[
            self.current_bias + self.current_gain * np.maximum(n, 0.0),
            self.current_bias + self.current_gain * np.maximum(-n, 0.0),
        ]
        self._target[:] = np.clip(np.asarray(target, dtype=float), -1.0, 1.0)
        self._activity[:] = self._basis(self._current)

        weights_before = self._weights.copy()
        w_pes = weights_before + self.learning_rate * np.outer(
            self._prev_target - self._prev_decoded, self._prev_activity
        )
        self._decoded_raw[:] = w_pes @ self._activity
        self._decoded_clipped[:] = np.clip(self._decoded_raw, -1.0, 1.0)
        self._pes_error[:] = self._decoded_clipped - self._target
        self._weights[:] = np.clip(w_pes - self.leak * weights_before, -6.0, 6.0)

        self._prev_activity[:] = self._activity
        self._prev_target[:] = self._target
        self._prev_decoded[:] = self._decoded_clipped
        self._k += 1

        command = np.clip(u0 + self.beta * self.limits * self._decoded_clipped, -self.limits, self.limits)
        return _Output(command.copy(), u0.copy(), (command - u0).copy(),
                       self._activity.copy(), self._activity.copy())

    def diagnostics(self) -> dict:
        p = self.p
        conductance_gain = p["base_gain"] + (p["gain_scaling"] * np.abs(self._current) if self.adaptive else 0.0)
        has_conductance = self.basis == "cmg-numpy"
        conductance = conductance_gain * self._r * self._r if has_conductance else np.zeros(6)
        lam = 1.0 / p["tau"] + conductance
        return {
            "current": self._current.copy(),
            "native_current": self._current.copy(),
            "raw_output": self._activity.copy(),
            "activity": self._activity.copy(),
            "states": {},
            "voltage": self._v.copy(),
            "gate": self._r.copy(),
            "effective_threshold": np.asarray(self._effective_threshold, dtype=float).copy(),
            "gate_argument": np.clip(p["alpha"] * (self._v - np.asarray(self._effective_threshold)), -60, 60),
            "gate_target": np.asarray(self._gate_target, dtype=float).copy(),
            "conductance_gain": np.broadcast_to(conductance_gain, (6,)).astype(float).copy() if has_conductance else np.zeros(6),
            "conductance": conductance,
            "membrane_lambda": lam if self.basis in ("cmg-numpy", "lpf-logistic") else np.zeros(6),
            "membrane_drive": (p["v_rest"] / p["tau"] + self._current / p["tau"] + conductance * p["v_reset"])
                              if self.basis in ("cmg-numpy", "lpf-logistic") else np.zeros(6),
            "decoded_raw": self._decoded_raw.copy(),
            "decoded_clipped": self._decoded_clipped.copy(),
            "target": self._target.copy(),
            "pes_error": self._pes_error.copy(),
            "weights": self._weights.copy(),
        }

    def close(self) -> None:
        return None
