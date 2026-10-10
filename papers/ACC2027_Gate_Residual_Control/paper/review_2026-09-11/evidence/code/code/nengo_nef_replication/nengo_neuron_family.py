"""Matched paired-current Nengo residuals for conventional neuron families."""
from __future__ import annotations

from dataclasses import dataclass
import warnings

import nengo
import numpy as np

from nengo_cmg import CoupledMembraneGate


FAMILIES = ("cmg", "lif", "alif", "izhikevich", "lifrate")


def neuron_type(family: str):
    family = family.lower()
    if family == "cmg":
        return CoupledMembraneGate(adaptive=True)
    if family == "lif":
        return nengo.LIF()
    if family == "alif":
        return nengo.AdaptiveLIF()
    if family == "izhikevich":
        return nengo.Izhikevich()
    if family == "lifrate":
        return nengo.LIFRate()
    raise ValueError(f"unknown neuron family: {family}")


@dataclass
class FamilyOutput:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    raw_output: np.ndarray


class NengoNeuronFamilyAugmentor:
    """Six signed units, normalized natural feature, and fixed or PES decoder.

    CMG exposes its continuous gate-derived output directly. LIF, ALIF, and
    Izhikevich expose a low-pass spike trace. LIFRate exposes its rate output
    through the same bandwidth-matching low-pass. All features are clipped to
    [0,1], so W0=[I,-I], beta, and the torque residual have identical meaning.
    """

    def __init__(
        self,
        family: str,
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
        self.channels = 3
        self.n_units = 6
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
        self.current_external = np.zeros(6)
        self.target_external = np.zeros(3)
        self.W0 = np.c_[np.eye(3), -np.eye(3)]
        # Conventional neuron outputs are rates/spikes in Hz. Folding the
        # calibration scale into W and eta makes the learned normalized decoder
        # obey Delta W_norm = eta * (target-y) * a_norm^T.
        self.nengo_learning_rate = (
            self.learning_rate * self.n_units / (self.dt * self.feature_scale)
        )

        self.network = nengo.Network(label=f"matched {family} {mode} residual", seed=seed)
        with self.network:
            drive = nengo.Node(
                lambda t: self.native_current_scale * self.current_external,
                size_out=6,
            )
            target = nengo.Node(lambda t: self.target_external, size_out=3)
            self.population = nengo.Ensemble(
                6,
                1,
                neuron_type=neuron_type(family),
                gain=np.ones(6),
                bias=np.zeros(6),
                encoders=np.ones((6, 1)),
                label=f"six signed {family} units",
            )
            nengo.Connection(drive, self.population.neurons, synapse=None)

            self.feature_node = nengo.Node(
                lambda t, x: x,
                size_in=6,
                size_out=6,
                label="normalized natural observable",
            )
            if family == "cmg":
                nengo.Connection(self.population.neurons, self.feature_node, synapse=None)
            else:
                nengo.Connection(
                    self.population.neurons,
                    self.feature_node,
                    transform=np.eye(6) / self.feature_scale,
                    synapse=nengo.Lowpass(self.feature_tau),
                )

            self.decoded_node = nengo.Node(size_in=3, label="raw normalized residual")
            learning_rule = None
            decoder_synapse = None if family == "cmg" else nengo.Lowpass(self.feature_tau)
            if mode == "pes":
                learning_rule = nengo.PES(
                    learning_rate=self.nengo_learning_rate,
                    pre_synapse=decoder_synapse,
                )
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="This learning rate is very high.*")
                self.decoder = nengo.Connection(
                    self.population.neurons,
                    self.decoded_node,
                    transform=self.W0 / self.feature_scale,
                    synapse=decoder_synapse,
                    learning_rule_type=learning_rule,
                )
            self.clipped_node = nengo.Node(
                lambda t, x: np.clip(x, -1.0, 1.0),
                size_in=3,
                size_out=3,
            )
            nengo.Connection(self.decoded_node, self.clipped_node, synapse=None)
            self.error_node = nengo.Node(
                lambda t, x: x[:3] - x[3:], size_in=6, size_out=3
            )
            nengo.Connection(self.clipped_node, self.error_node[:3], synapse=None)
            nengo.Connection(target, self.error_node[3:], synapse=None)
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
        state_signals = model.sig[self.population.neurons]
        self._states = {
            name: signals[value]
            for name, value in state_signals.items()
            if name not in ("in", "out") and np.asarray(signals[value]).shape == (6,)
        }
        self._last_target = np.zeros(3)
        self._last_weight_delta = np.zeros((3, 6))

    @property
    def W(self):
        return self.feature_scale * np.asarray(self._weights).copy()

    @property
    def activity(self):
        return np.asarray(self._feature).copy()

    @property
    def raw_output(self):
        return np.asarray(self._raw_output).copy()

    def diagnostics(self):
        payload = {
            "current": self.current_external.copy(),
            "native_current": self.native_current_scale * self.current_external,
            "raw_output": self.raw_output,
            "activity": self.activity,
            "states": {name: np.asarray(value).copy() for name, value in self._states.items()},
            "decoded_raw": np.asarray(self._decoded).copy(),
            "decoded_clipped": np.asarray(self._clipped).copy(),
            "target": self._last_target.copy(),
            "pes_error": np.asarray(self._error).copy(),
            "weights": self.W,
            "weight_delta": self._last_weight_delta.copy(),
        }
        if self.family == "cmg":
            neuron = self.population.neuron_type
            voltage = payload["states"]["voltage"]
            gate = payload["states"]["gate"]
            current = payload["native_current"]
            effective_threshold = neuron.v_threshold - neuron.gamma * gate
            gate_argument = np.clip(
                neuron.alpha * (voltage - effective_threshold), -60.0, 60.0
            )
            gate_target = 1.0 / (1.0 + np.exp(-gate_argument))
            conductance_gain = neuron.base_gain + neuron.gain_scaling * np.abs(current)
            conductance = conductance_gain * gate * gate
            payload.update({
                "voltage": voltage,
                "gate": gate,
                "effective_threshold": effective_threshold,
                "gate_argument": gate_argument,
                "gate_target": gate_target,
                "conductance_gain": conductance_gain,
                "conductance": conductance,
                "membrane_lambda": 1.0 / neuron.tau + conductance,
                "membrane_drive": neuron.v_rest / neuron.tau + current / neuron.tau + conductance * neuron.v_reset,
            })
        return payload

    def step(self, baseline: np.ndarray, target: np.ndarray) -> FamilyOutput:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        normalized = np.divide(u0, self.limits, out=np.zeros(3), where=self.limits > 1e-12)
        self.current_external[:] = np.r_[
            self.current_bias + self.current_gain * np.maximum(normalized, 0.0),
            self.current_bias + self.current_gain * np.maximum(-normalized, 0.0),
        ]
        self.target_external[:] = np.clip(target, -1.0, 1.0)
        self._last_target[:] = self.target_external
        before_actual = np.asarray(self._weights).copy()
        before = self.W
        self.sim.step()
        if self.mode == "pes":
            self._weights[:] -= self.leak * before_actual
            np.clip(
                self._weights,
                -6.0 / self.feature_scale,
                6.0 / self.feature_scale,
                out=self._weights,
            )
        self._last_weight_delta[:] = self.W - before
        signed = np.clip(np.asarray(self._clipped), -1.0, 1.0)
        requested = self.beta * signed * self.limits
        command = np.clip(u0 + requested, -self.limits, self.limits)
        return FamilyOutput(
            command=command,
            baseline=u0,
            residual=command - u0,
            activity=self.activity,
            raw_output=self.raw_output,
        )

    def close(self):
        self.sim.close()
