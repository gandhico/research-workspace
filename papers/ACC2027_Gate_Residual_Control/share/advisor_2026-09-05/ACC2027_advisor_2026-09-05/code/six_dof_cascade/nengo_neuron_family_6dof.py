"""Channel-general version of nengo_neuron_family.py's NengoNeuronFamilyAugmentor.

The original (nengo_nef_replication_2026-08-29/nengo_neuron_family.py) is
hardcoded to channels=3 -- kept as-is since it backs the published
NENGO_NEURON_FAMILY_BENCHMARK_2026-08-31.md results and must not change.
This is a straightforward generalization (3->channels, 6->2*channels)
of the exact same pattern, for the 6-channel (position+attitude) cascade.
Reuses FAMILIES/neuron_type from the original, not reimplemented.
"""
from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import nengo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"nengo_nef_replication_2026-08-29"))
from nengo_neuron_family import FAMILIES, neuron_type  # noqa: E402


@dataclass
class FamilyOutput:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    raw_output: np.ndarray


class NengoNeuronFamilyAugmentorND:
    """Same paired-current / natural-feature / PES-decoder pattern as
    NengoNeuronFamilyAugmentor, generalized to an arbitrary channel count."""

    def __init__(
        self,
        family: str,
        channels: int,
        limits: np.ndarray,
        dt: float,
        beta: float = 0.5,
        mode: str = "pes",
        learning_rate: float = 8e-4,
        leak: float = 1e-6,
        feature_tau: float = 0.005,
        feature_scale: float = 1.0,
        native_current_scale: float = 1.0,
        seed: int = 1,
        current_bias: float = 0.75,
        current_gain: float = 1.25,
    ):
        if family not in FAMILIES:
            raise ValueError(family)
        if mode not in ("fixed", "pes"):
            raise ValueError("mode must be fixed or pes")
        if feature_scale <= 0:
            raise ValueError("feature_scale must be positive")
        self.family = family
        self.mode = mode
        self.channels = int(channels)
        self.n_units = 2*self.channels
        self.limits = np.asarray(limits, dtype=float)
        self.dt = float(dt)
        self.beta = float(beta)
        self.learning_rate = float(learning_rate)
        self.leak = float(leak)
        self.feature_tau = float(feature_tau)
        self.feature_scale = float(feature_scale)
        self.native_current_scale = float(native_current_scale)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.current_external = np.zeros(self.n_units)
        self.target_external = np.zeros(self.channels)
        self.W0 = np.c_[np.eye(self.channels), -np.eye(self.channels)]
        self.nengo_learning_rate = (
            self.learning_rate*self.n_units/(self.dt*self.feature_scale)
        )

        self.network = nengo.Network(label=f"matched {family} {mode} residual ({channels}ch)", seed=seed)
        with self.network:
            drive = nengo.Node(
                lambda t: self.native_current_scale*self.current_external,
                size_out=self.n_units,
            )
            target = nengo.Node(lambda t: self.target_external, size_out=self.channels)
            self.population = nengo.Ensemble(
                self.n_units,
                1,
                neuron_type=neuron_type(family),
                gain=np.ones(self.n_units),
                bias=np.zeros(self.n_units),
                encoders=np.ones((self.n_units, 1)),
                label=f"{self.n_units} signed {family} units",
            )
            nengo.Connection(drive, self.population.neurons, synapse=None)

            self.feature_node = nengo.Node(
                lambda t, x: x, size_in=self.n_units, size_out=self.n_units,
                label="normalized natural observable",
            )
            if family == "cmg":
                nengo.Connection(self.population.neurons, self.feature_node, synapse=None)
            else:
                nengo.Connection(
                    self.population.neurons, self.feature_node,
                    transform=np.eye(self.n_units)/self.feature_scale,
                    synapse=nengo.Lowpass(self.feature_tau),
                )

            self.decoded_node = nengo.Node(size_in=self.channels, label="raw normalized residual")
            learning_rule = None
            decoder_synapse = None if family == "cmg" else nengo.Lowpass(self.feature_tau)
            if mode == "pes":
                learning_rule = nengo.PES(learning_rate=self.nengo_learning_rate, pre_synapse=decoder_synapse)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="This learning rate is very high.*")
                self.decoder = nengo.Connection(
                    self.population.neurons, self.decoded_node,
                    transform=self.W0/self.feature_scale,
                    synapse=decoder_synapse,
                    learning_rule_type=learning_rule,
                )
            self.clipped_node = nengo.Node(
                lambda t, x: np.clip(x, -1.0, 1.0), size_in=self.channels, size_out=self.channels,
            )
            nengo.Connection(self.decoded_node, self.clipped_node, synapse=None)
            self.error_node = nengo.Node(
                lambda t, x: x[:self.channels]-x[self.channels:],
                size_in=2*self.channels, size_out=self.channels,
            )
            nengo.Connection(self.clipped_node, self.error_node[:self.channels], synapse=None)
            nengo.Connection(target, self.error_node[self.channels:], synapse=None)
            if mode == "pes":
                nengo.Connection(self.error_node, self.decoder.learning_rule, synapse=None)

        self.sim = nengo.Simulator(self.network, dt=self.dt, progress_bar=False)
        model = self.sim.model
        signals = self.sim.signals
        self._raw_output = signals[model.sig[self.population.neurons]["out"]]
        self._feature = signals[model.sig[self.feature_node]["out"]]
        self._weights = signals[model.sig[self.decoder]["weights"]]
        self._decoded = signals[model.sig[self.decoded_node]["out"]]
        self._clipped = signals[model.sig[self.clipped_node]["out"]]
        self._error = signals[model.sig[self.error_node]["out"]]
        self._last_target = np.zeros(self.channels)

    @property
    def W(self):
        return self.feature_scale*np.asarray(self._weights).copy()

    @property
    def activity(self):
        return np.asarray(self._feature).copy()

    @property
    def raw_output(self):
        return np.asarray(self._raw_output).copy()

    def step(self, baseline: np.ndarray, target: np.ndarray) -> FamilyOutput:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        normalized = np.divide(u0, self.limits, out=np.zeros(self.channels), where=self.limits > 1e-12)
        self.current_external[:] = np.r_[
            self.current_bias+self.current_gain*np.maximum(normalized, 0.0),
            self.current_bias+self.current_gain*np.maximum(-normalized, 0.0),
        ]
        self.target_external[:] = np.clip(target, -1.0, 1.0)
        self._last_target[:] = self.target_external
        before_actual = np.asarray(self._weights).copy()
        self.sim.step()
        if self.mode == "pes":
            self._weights[:] -= self.leak*before_actual
            np.clip(self._weights, -6.0/self.feature_scale, 6.0/self.feature_scale, out=self._weights)
        signed = np.clip(np.asarray(self._clipped), -1.0, 1.0)
        requested = self.beta*signed*self.limits
        command = np.clip(u0+requested, -self.limits, self.limits)
        return FamilyOutput(
            command=command, baseline=u0, residual=command-u0,
            activity=self.activity, raw_output=self.raw_output,
        )

    def close(self):
        self.sim.close()
