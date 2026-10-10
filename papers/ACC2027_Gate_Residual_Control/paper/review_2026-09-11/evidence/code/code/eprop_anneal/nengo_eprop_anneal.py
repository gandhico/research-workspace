"""Nengo-native validation of eprop_anneal (annealed-eligibility online learning),
reusing the already-verified CoupledMembraneGate neuron type from
nengo_nef_replication_2026-08-29/nengo_cmg.py -- confirmed parameter-identical
to HyperLIFDirect's "control" scale (tau=0.05, tau_r=0.005, reset_gain=120.0,
gamma=2.0, alpha=50, v_thresh=1.0 all match exactly).

Nengo has no built-in annealed-eligibility-trace learning rule, so this keeps
nengo.PES on the decoder connection (proven signal-access pattern, learning
rate set to 0 so PES itself contributes nothing) and applies the exact
eprop_anneal update from learned_gate_experiment.py's LearnedGate._update
manually after each sim.step() -- same pattern NengoCMGPESAugmentor already
uses to apply leak+clip after PES's own update.
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import nengo
import numpy as np


# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import NENGO_NEF  # noqa: E402

sys.path.insert(0, str(NENGO_NEF))
from nengo_cmg import CoupledMembraneGate  # noqa: E402


@dataclass
class Output:
    command: np.ndarray
    residual: np.ndarray
    activity: np.ndarray


class NengoEpropAnnealAugmentor:
    def __init__(self, channels: int, limits: np.ndarray, dt: float, sim_time: float,
                 lr: float, k_err: float, k_rate: float, blend: float = 0.5,
                 current_bias: float = 0.75, current_gain: float = 1.25, seed: int = 1):
        self.channels = channels
        self.n_units = 2 * channels
        self.limits = np.asarray(limits, dtype=float)
        self.dt = float(dt)
        self.sim_time = float(sim_time)
        self.lr = float(lr)
        self.k_err = float(k_err)
        self.k_rate = float(k_rate)
        self.blend = float(blend)
        self.current_bias = current_bias
        self.current_gain = current_gain
        self.e_trace = np.zeros(self.n_units, dtype=float)
        self.W0 = np.concatenate([np.eye(channels), -np.eye(channels)], axis=1)

        self._current = np.zeros(self.n_units)

        self.network = nengo.Network(label="eprop_anneal CMG population", seed=seed)
        with self.network:
            drive = nengo.Node(lambda t: self._current, size_out=self.n_units)
            self.population = nengo.Ensemble(
                self.n_units, 1, neuron_type=CoupledMembraneGate(adaptive=False),
                gain=np.ones(self.n_units), bias=np.zeros(self.n_units),
                encoders=np.ones((self.n_units, 1)),
            )
            nengo.Connection(drive, self.population.neurons, synapse=None)
            decoded = nengo.Node(size_in=channels)
            self.decoded_node = decoded
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="This learning rate is very high.*")
                self.decoder = nengo.Connection(
                    self.population.neurons, decoded, transform=self.W0, synapse=None,
                    learning_rule_type=nengo.PES(learning_rate=0.0, pre_synapse=None),
                )
            dummy_target = nengo.Node(lambda t: np.zeros(channels), size_out=channels)
            err = nengo.Node(lambda t, x: np.zeros(channels), size_in=channels, size_out=channels)
            nengo.Connection(dummy_target, err, synapse=None)
            nengo.Connection(err, self.decoder.learning_rule, synapse=None)

        self.sim = nengo.Simulator(self.network, dt=self.dt, progress_bar=False)
        model, signals = self.sim.model, self.sim.signals
        self._activity = signals[model.sig[self.population.neurons]["out"]]
        self._weights = signals[model.sig[self.decoder]["weights"]]
        self._decoded = signals[model.sig[self.decoded_node]["out"]]

    def _lr_now(self, t):
        frac = np.clip(t / self.sim_time, 0.0, 1.0)
        return self.lr * (1.0 - 0.8 * frac)

    def _decay_now(self, t):
        frac = np.clip(t / self.sim_time, 0.0, 1.0)
        return 0.98 - 0.48 * frac

    def step(self, t: float, axis_error: np.ndarray, tau_pd: np.ndarray, omega: np.ndarray) -> Output:
        tau_norm = np.clip(np.divide(tau_pd, self.limits, out=np.zeros_like(tau_pd),
                                      where=np.abs(self.limits) > 1e-12), -1.0, 1.0)
        self._current[0:self.channels] = self.current_bias + self.current_gain * np.maximum(tau_norm, 0.0)
        self._current[self.channels:] = self.current_bias + self.current_gain * np.maximum(-tau_norm, 0.0)

        self.sim.step()

        activity = np.asarray(self._activity, dtype=float).copy()
        signed = np.clip(np.asarray(self._decoded, dtype=float), -1.0, 1.0)
        tau_neuron = signed * self.limits

        target = np.clip(-self.k_err * axis_error - self.k_rate * omega, -1.0, 1.0)
        e_dec = target - signed
        decay = self._decay_now(t)
        self.e_trace = decay * self.e_trace + (1.0 - decay) * activity
        self._weights[:] += self._lr_now(t) * np.outer(e_dec, self.e_trace)
        np.clip(self._weights, -6.0, 6.0, out=self._weights)

        tau = (1.0 - self.blend) * tau_pd + self.blend * tau_neuron
        tau = np.clip(tau, -self.limits, self.limits)
        return Output(command=tau, residual=tau - tau_pd, activity=activity)

    def close(self):
        self.sim.close()
