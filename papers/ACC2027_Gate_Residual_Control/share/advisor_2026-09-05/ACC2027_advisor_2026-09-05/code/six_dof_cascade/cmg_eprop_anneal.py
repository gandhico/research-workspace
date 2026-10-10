"""CMG residual augmentor with the eprop_anneal (annealed-eligibility online)
learning rule, generalized to an arbitrary channel count -- for the 6-channel
(3 position + 3 attitude) X2 cascade.

Reuses CoupledMembraneGateBank/CMGConfig from gra_control.gate UNMODIFIED
(canonical, never touched). This is a new sibling class, not a variant of
CMGResidualAugmentor -- it swaps that class's online-PES rule for the exact
eligibility-trace + annealed-rate update verified this session against the
P3_Gate_Residual/learned codebase (see eprop_anneal_reproduction/), matched
there to 6 decimal places (isolated) and 0.03% relative (closed-loop, Nengo).
Same formula, generalized from 3 to N channels:

    target       = clip(learning_target, -1, 1)
    e_dec        = target - signed
    decay(t)     = 0.98 - 0.48 * clip(t/sim_time, 0, 1)
    e_trace      = decay*e_trace + (1-decay)*activity
    lr(t)        = lr0 * (1 - 0.8*clip(t/sim_time, 0, 1))
    W           += lr(t) * outer(e_dec, e_trace) - leak*W
    W            = clip(W, -6, 6)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gra_control.gate import CMGConfig, CoupledMembraneGateBank


@dataclass
class EpropOutput:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    gate: np.ndarray


class CMGEpropAnnealAugmentor:
    def __init__(self, channels: int, limits: np.ndarray, sim_time: float,
                 beta: float = 0.5, learning_rate: float = 0.0016,
                 leak: float = 1e-6, adaptive_conductance: bool = True,
                 cfg: CMGConfig | None = None):
        self.channels = int(channels)
        self.limits = np.asarray(limits, dtype=float)
        self.sim_time = float(sim_time)
        self.beta = float(beta)
        self.lr0 = float(learning_rate)
        self.leak = float(leak)
        self.cfg = cfg or CMGConfig()
        self.units = CoupledMembraneGateBank(2 * self.channels, adaptive_conductance, self.cfg)
        self.W = np.concatenate([np.eye(self.channels), -np.eye(self.channels)], axis=1)
        self.e_trace = np.zeros(2 * self.channels, dtype=float)

    def reset(self) -> None:
        self.units.reset()
        self.W[:] = np.concatenate([np.eye(self.channels), -np.eye(self.channels)], axis=1)
        self.e_trace[:] = 0.0

    def _lr_now(self, t: float) -> float:
        return self.lr0 * (1.0 - 0.8 * np.clip(t / self.sim_time, 0.0, 1.0))

    def _decay_now(self, t: float) -> float:
        return 0.98 - 0.48 * np.clip(t / self.sim_time, 0.0, 1.0)

    def step(self, baseline: np.ndarray, dt: float, t: float,
              learning_target: np.ndarray) -> EpropOutput:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        normalized = np.divide(u0, self.limits, out=np.zeros_like(u0), where=self.limits > 1e-12)
        current = np.concatenate([
            self.cfg.current_bias + self.cfg.current_gain * np.maximum(normalized, 0.0),
            self.cfg.current_bias + self.cfg.current_gain * np.maximum(-normalized, 0.0),
        ])
        gate = self.units.step(current, dt)
        activity = np.clip(self.cfg.gate_gain * gate, 0.0, 1.0)
        signed = np.clip(self.W @ activity, -1.0, 1.0)

        target = np.clip(np.asarray(learning_target, dtype=float), -1.0, 1.0)
        e_dec = target - signed
        decay = self._decay_now(t)
        self.e_trace[:] = decay * self.e_trace + (1.0 - decay) * activity
        self.W += self._lr_now(t) * np.outer(e_dec, self.e_trace) - self.leak * self.W
        self.W[:] = np.clip(self.W, -6.0, 6.0)

        neural = signed * self.limits
        residual = self.beta * neural
        command = np.clip(u0 + residual, -self.limits, self.limits)
        residual = command - u0
        return EpropOutput(command, u0, residual, activity, gate)
