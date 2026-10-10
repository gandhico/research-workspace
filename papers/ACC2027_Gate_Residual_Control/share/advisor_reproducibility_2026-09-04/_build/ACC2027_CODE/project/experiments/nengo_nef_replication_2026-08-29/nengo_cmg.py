"""Nengo/NEF realization of the paper's paired CMG + online-PES residual.

The six neuron outputs are the continuous gate-derived activities used by the
existing NumPy controller.  A Nengo ``PES`` learning rule adapts the 3 x 6
decoder.  The small decoder leak and hard weight bound are applied after each
Nengo step to preserve the regularization used by the frozen controller.
"""
from __future__ import annotations

from dataclasses import dataclass
import warnings

import nengo
import numpy as np
from nengo.dists import Choice
from nengo.params import BoolParam, NumberParam


class CoupledMembraneGate(nengo.neurons.NeuronType):
    """Continuous, non-spiking coupled membrane--gate neuron for Nengo.

    ``output`` is ``clip(gate_gain * r, 0, 1)``.  Both internal states are
    probeable as ``voltage`` and ``gate``.  This is not an LIF spike/reset
    model; it is the continuous CMG dynamics used by the current paper code.
    """

    negative = False
    spiking = False
    state = {"voltage": Choice([0.0]), "gate": Choice([0.0])}

    tau = NumberParam("tau", low=0.0, low_open=True)
    tau_r = NumberParam("tau_r", low=0.0, low_open=True)
    v_rest = NumberParam("v_rest")
    v_reset = NumberParam("v_reset")
    v_threshold = NumberParam("v_threshold")
    alpha = NumberParam("alpha", low=0.0, low_open=True)
    gamma = NumberParam("gamma")
    base_gain = NumberParam("base_gain", low=0.0)
    gain_scaling = NumberParam("gain_scaling", low=0.0)
    gate_gain = NumberParam("gate_gain", low=0.0)
    adaptive = BoolParam("adaptive")

    def __init__(
        self,
        tau=0.05,
        tau_r=0.005,
        v_rest=0.0,
        v_reset=0.0,
        v_threshold=1.0,
        alpha=50.0,
        gamma=2.0,
        base_gain=120.0,
        gain_scaling=30.0,
        gate_gain=1.0e5,
        adaptive=True,
        initial_state=None,
    ):
        super().__init__(initial_state=initial_state)
        self.tau = tau
        self.tau_r = tau_r
        self.v_rest = v_rest
        self.v_reset = v_reset
        self.v_threshold = v_threshold
        self.alpha = alpha
        self.gamma = gamma
        self.base_gain = base_gain
        self.gain_scaling = gain_scaling
        self.gate_gain = gate_gain
        self.adaptive = adaptive

    def step(self, dt, J, output, voltage, gate):
        x = np.clip(
            self.alpha * (voltage - (self.v_threshold - self.gamma * gate)),
            -60.0,
            60.0,
        )
        gate_target = 1.0 / (1.0 + np.exp(-x))
        gate += dt * (gate_target - gate) / self.tau_r
        np.clip(gate, 0.0, 1.0, out=gate)

        gain = self.base_gain
        if self.adaptive:
            gain = gain + self.gain_scaling * np.abs(J)
        conductance = gain * gate * gate
        lam = 1.0 / self.tau + conductance
        drive = self.v_rest / self.tau + J / self.tau + conductance * self.v_reset
        decay = np.exp(-lam * dt)
        voltage[:] = voltage * decay + (drive / np.maximum(lam, 1e-12)) * (1.0 - decay)
        output[:] = np.clip(self.gate_gain * gate, 0.0, 1.0)

    def max_rates_intercepts(self, gain, bias):
        """Return metadata for a directly current-driven population.

        The experiment connects the six constructed currents directly to
        ``ensemble.neurons``; NEF gain/intercept fitting is intentionally not
        used.  These values satisfy Nengo's ensemble build metadata only.
        """
        gain = np.asarray(gain, dtype=float)
        return np.ones_like(gain), np.zeros_like(gain)


@dataclass
class NengoAugmentorOutput:
    command: np.ndarray
    baseline: np.ndarray
    residual: np.ndarray
    activity: np.ndarray
    gate: np.ndarray


class _ExternalSignals:
    def __init__(self, n_units: int, channels: int):
        self.current = np.zeros(n_units, dtype=float)
        self.target = np.zeros(channels, dtype=float)


class NengoCMGPESAugmentor:
    """Step-wise Nengo controller that preserves the frozen CMG/PES equations."""

    def __init__(
        self,
        channels: int,
        limits: np.ndarray,
        dt: float,
        beta: float = 0.5,
        learning_rate: float = 8e-4,
        leak: float = 1e-6,
        adaptive_conductance: bool = True,
        seed: int = 1,
        current_bias: float = 0.75,
        current_gain: float = 1.25,
    ):
        self.channels = int(channels)
        self.n_units = 2 * self.channels
        self.limits = np.asarray(limits, dtype=float)
        self.dt = float(dt)
        self.beta = float(beta)
        self.learning_rate = float(learning_rate)
        self.leak = float(leak)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.external = _ExternalSignals(self.n_units, self.channels)
        self.W0 = np.concatenate(
            [np.eye(self.channels), -np.eye(self.channels)], axis=1
        )

        # Nengo's SimPES applies -eta_N * dt/n * e a^T.  This conversion makes
        # that increment equal to the frozen controller's
        # +eta_direct * (target-decoded) a^T.
        self.nengo_learning_rate = self.learning_rate * self.n_units / self.dt

        self.network = nengo.Network(label="CMG paired population + PES decoder", seed=seed)
        with self.network:
            drive = nengo.Node(
                lambda t: self.external.current,
                size_out=self.n_units,
                label="paired positive/negative currents",
            )
            target = nengo.Node(
                lambda t: self.external.target,
                size_out=self.channels,
                label="PES teaching target",
            )
            self.population = nengo.Ensemble(
                self.n_units,
                1,
                neuron_type=CoupledMembraneGate(adaptive=adaptive_conductance),
                gain=np.ones(self.n_units),
                bias=np.zeros(self.n_units),
                encoders=np.ones((self.n_units, 1)),
                label="six CMG units",
            )
            nengo.Connection(drive, self.population.neurons, synapse=None)

            decoded = nengo.Node(size_in=self.channels, label="decoded normalized residual")
            self.decoded_node = decoded
            decoded_clipped = nengo.Node(
                lambda t, x: np.clip(x, -1.0, 1.0),
                size_in=self.channels,
                size_out=self.channels,
                label="clipped decoder used by PES and residual",
            )
            self.decoded_clipped_node = decoded_clipped
            # Nengo warns for eta_N > 1.  Here 9.6 is analytically required to
            # cancel Nengo's dt/N factor and equals direct eta=8e-4; suppress
            # only that generic warning at construction.
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="This learning rate is very high.*"
                )
                self.decoder = nengo.Connection(
                    self.population.neurons,
                    decoded,
                    transform=self.W0,
                    synapse=None,
                    learning_rule_type=nengo.PES(
                        learning_rate=self.nengo_learning_rate,
                        pre_synapse=None,
                    ),
                )
            nengo.Connection(decoded, decoded_clipped, synapse=None)
            error = nengo.Node(
                lambda t, x: x[: self.channels] - x[self.channels :],
                size_in=2 * self.channels,
                size_out=self.channels,
                label="PES error = decoded - target",
            )
            self.error_node = error
            # The frozen direct controller computes PES from clip(Wa,-1,1).
            # Keeping the raw and clipped signals separate makes saturation
            # explicit and preserves exact controller semantics.
            nengo.Connection(decoded_clipped, error[: self.channels], synapse=None)
            nengo.Connection(target, error[self.channels :], synapse=None)
            nengo.Connection(error, self.decoder.learning_rule, synapse=None)

        self.sim = nengo.Simulator(self.network, dt=self.dt, progress_bar=False)
        model = self.sim.model
        signals = self.sim.signals
        self._activity = signals[model.sig[self.population.neurons]["out"]]
        self._voltage = signals[model.sig[self.population.neurons]["voltage"]]
        self._gate = signals[model.sig[self.population.neurons]["gate"]]
        self._weights = signals[model.sig[self.decoder]["weights"]]
        self._decoded = signals[model.sig[self.decoded_node]["out"]]
        self._decoded_clipped = signals[model.sig[self.decoded_clipped_node]["out"]]
        self._error = signals[model.sig[self.error_node]["out"]]
        self._last_decoded = np.zeros(self.channels, dtype=float)
        self._last_error = np.zeros(self.channels, dtype=float)
        self._last_target = np.zeros(self.channels, dtype=float)

    @property
    def v(self) -> np.ndarray:
        return np.asarray(self._voltage, dtype=float).copy()

    @property
    def r(self) -> np.ndarray:
        return np.asarray(self._gate, dtype=float).copy()

    @property
    def activity(self) -> np.ndarray:
        return np.asarray(self._activity, dtype=float).copy()

    @property
    def W(self) -> np.ndarray:
        return np.asarray(self._weights, dtype=float).copy()

    @property
    def current(self) -> np.ndarray:
        return self.external.current.copy()

    @property
    def target(self) -> np.ndarray:
        return self._last_target.copy()

    @property
    def decoded_raw(self) -> np.ndarray:
        return self._last_decoded.copy()

    @property
    def decoded_clipped(self) -> np.ndarray:
        return np.clip(self._last_decoded, -1.0, 1.0)

    @property
    def pes_error(self) -> np.ndarray:
        return self._last_error.copy()

    def reset(self) -> None:
        self.sim.reset(seed=self.network.seed)
        self._weights[:] = self.W0
        self._last_decoded.fill(0.0)
        self._last_error.fill(0.0)
        self._last_target.fill(0.0)

    def diagnostics(self) -> dict[str, np.ndarray]:
        """Return all CMG/PES states and algebraic quantities for logging."""
        neuron = self.population.neuron_type
        voltage = self.v
        gate = self.r
        current = self.current
        effective_threshold = neuron.v_threshold - neuron.gamma * gate
        gate_argument = np.clip(
            neuron.alpha * (voltage - effective_threshold), -60.0, 60.0
        )
        gate_target = 1.0 / (1.0 + np.exp(-gate_argument))
        gain = np.full_like(current, neuron.base_gain)
        if neuron.adaptive:
            gain += neuron.gain_scaling * np.abs(current)
        conductance = gain * gate * gate
        membrane_lambda = 1.0 / neuron.tau + conductance
        membrane_drive = (
            neuron.v_rest / neuron.tau
            + current / neuron.tau
            + conductance * neuron.v_reset
        )
        return {
            "current": current,
            "voltage": voltage,
            "gate": gate,
            "activity": self.activity,
            "effective_threshold": effective_threshold,
            "gate_argument": gate_argument,
            "gate_target": gate_target,
            "conductance_gain": gain,
            "conductance": conductance,
            "membrane_lambda": membrane_lambda,
            "membrane_drive": membrane_drive,
            "decoded_raw": self.decoded_raw,
            "decoded_clipped": self.decoded_clipped,
            "target": self.target,
            "pes_error": self.pes_error,
            "weights": self.W,
        }

    def step(
        self,
        baseline: np.ndarray,
        learning_target: np.ndarray,
    ) -> NengoAugmentorOutput:
        u0 = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        normalized = np.divide(
            u0,
            self.limits,
            out=np.zeros_like(u0),
            where=self.limits > 1e-12,
        )
        self.external.current[:] = np.concatenate(
            [
                self.current_bias + self.current_gain * np.maximum(normalized, 0.0),
                self.current_bias + self.current_gain * np.maximum(-normalized, 0.0),
            ]
        )
        self.external.target[:] = np.clip(
            np.asarray(learning_target, dtype=float), -1.0, 1.0
        )
        self._last_target[:] = self.external.target
        weights_before = self._weights.copy()
        self.sim.step()

        self._last_decoded[:] = np.asarray(self._decoded, dtype=float)
        self._last_error[:] = np.asarray(self._error, dtype=float)

        # Preserve the frozen controller's decoder regularization.  PES itself
        # is Nengo's built-in learning operator; only leak and safety clipping
        # are imposed here after its update.
        # Direct semantics are W_new = W_old + PES - leak*W_old.  Subtracting
        # from the pre-step value avoids scaling the just-computed PES update.
        self._weights[:] -= self.leak * weights_before
        np.clip(self._weights, -6.0, 6.0, out=self._weights)

        signed = np.clip(self._last_decoded, -1.0, 1.0)
        residual_requested = self.beta * signed * self.limits
        command = np.clip(u0 + residual_requested, -self.limits, self.limits)
        residual = command - u0
        return NengoAugmentorOutput(
            command=command.copy(),
            baseline=u0.copy(),
            residual=residual.copy(),
            activity=self.activity,
            gate=self.r,
        )

    def close(self) -> None:
        self.sim.close()
