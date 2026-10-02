"""Nengo-compatible HyperLIF and Adaptive HyperLIF neuron types."""

from __future__ import annotations

import numpy as np

from .hyperlif import sigmoid_switch, stable_voltage_update

try:
    from nengo.dists import Choice
    from nengo.neurons import NeuronType, settled_firingrate
    from nengo.params import NumberParam
except ImportError:  # pragma: no cover - exercised only without Nengo installed.
    Choice = None
    NeuronType = object
    NumberParam = None
    settled_firingrate = None


class _CurrentCalibrationMixin:
    """Shared current calibration for Nengo ensemble building."""

    def gain_bias(self, max_rates, intercepts):
        max_rates = np.asarray(np.atleast_1d(max_rates), dtype=float)
        intercepts = np.asarray(np.atleast_1d(intercepts), dtype=float)
        threshold_current = self.v_thresh - self.v_rest
        top_current = threshold_current + max_rates / self.rate_to_current
        gain = (threshold_current - top_current) / (intercepts - 1.0)
        bias = top_current - gain
        return gain, bias

    def max_rates_intercepts(self, gain, bias):
        gain = np.asarray(np.atleast_1d(gain), dtype=float)
        bias = np.asarray(np.atleast_1d(bias), dtype=float)
        threshold_current = self.v_thresh - self.v_rest
        intercepts = (threshold_current - bias) / gain
        top_current = gain + bias
        max_rates = np.maximum(0.0, top_current - threshold_current)
        return max_rates * self.rate_to_current, intercepts

    def make_state(self, n_neurons, rng=np.random, dtype=None):
        state = super().make_state(n_neurons, rng=rng, dtype=dtype)
        initial = {} if self.initial_state is None else self.initial_state
        if "voltage" not in initial:
            state["voltage"] = np.full(n_neurons, self.v_rest, dtype=state["voltage"].dtype)
        if "previous_voltage" in state and "previous_voltage" not in initial:
            state["previous_voltage"] = np.full(
                n_neurons, self.v_rest, dtype=state["previous_voltage"].dtype
            )
        return state


if Choice is not None:

    class HyperLIFNengo(_CurrentCalibrationMixin, NeuronType):
        """Stable Nengo port of the Julia HyperLIF equations."""

        spiking = True
        probeable = ("output", "voltage", "reset_gate", "previous_voltage")
        state = {
            "voltage": Choice([0.0]),
            "reset_gate": Choice([0.0]),
            "previous_voltage": Choice([0.0]),
        }

        tau = NumberParam("tau", low=0, low_open=True)
        v_rest = NumberParam("v_rest")
        v_thresh = NumberParam("v_thresh")
        v_reset = NumberParam("v_reset")
        alpha = NumberParam("alpha", low=0, low_open=True)
        reset_gain = NumberParam("reset_gain", low=0)
        tau_r = NumberParam("tau_r", low=0, low_open=True)
        gamma = NumberParam("gamma", low=0)
        amplitude = NumberParam("amplitude", low=0, low_open=True)
        min_voltage = NumberParam("min_voltage")
        event_threshold = NumberParam("event_threshold")
        rate_to_current = NumberParam("rate_to_current", low=0, low_open=True)

        def __init__(
            self,
            tau=0.02,
            v_rest=0.0,
            v_thresh=1.0,
            v_reset=0.0,
            alpha=100.0,
            reset_gain=100.0,
            tau_r=0.002,
            gamma=0.2,
            amplitude=1.0,
            min_voltage=0.0,
            event_threshold=1.0,
            rate_to_current=100.0,
            initial_state=None,
        ):
            super().__init__(initial_state=initial_state)
            self.tau = tau
            self.v_rest = v_rest
            self.v_thresh = v_thresh
            self.v_reset = v_reset
            self.alpha = alpha
            self.reset_gain = reset_gain
            self.tau_r = tau_r
            self.gamma = gamma
            self.amplitude = amplitude
            self.min_voltage = min_voltage
            self.event_threshold = event_threshold
            self.rate_to_current = rate_to_current

        def rates(self, x, gain, bias):
            J = self.current(x, gain, bias)
            return settled_firingrate(
                self.step,
                J,
                state={
                    "output": np.zeros_like(J),
                    "voltage": np.full_like(J, self.v_rest),
                    "reset_gate": np.zeros_like(J),
                    "previous_voltage": np.full_like(J, self.v_rest),
                },
            )

        def step(self, dt, J, output, voltage, reset_gate, previous_voltage):
            previous_voltage[...] = voltage
            effective_thresh = self.v_thresh - self.gamma * reset_gate
            target_gate = sigmoid_switch(self.alpha * (voltage - effective_thresh))
            gate_decay = np.exp(-dt / self.tau_r)
            reset_gate[...] = np.clip(
                target_gate + (reset_gate - target_gate) * gate_decay,
                0.0,
                1.0,
            )

            conductance = self.reset_gain * reset_gate**2
            voltage[...] = stable_voltage_update(
                voltage,
                J,
                conductance,
                dt,
                self.tau,
                self.v_rest,
                self.v_reset,
            )

            if np.isfinite(self.min_voltage):
                voltage[...] = np.maximum(voltage, self.min_voltage)

            crossed = (previous_voltage < self.event_threshold) & (
                voltage >= self.event_threshold
            )
            output[...] = np.where(crossed, self.amplitude / dt, 0.0)


    class AdaptiveHyperLIFNengo(_CurrentCalibrationMixin, NeuronType):
        """Stable Nengo port of the Julia Adaptive HyperLIF equations."""

        spiking = True
        probeable = (
            "output",
            "voltage",
            "reset_gate",
            "previous_voltage",
            "dynamic_gain",
        )
        state = {
            "voltage": Choice([0.0]),
            "reset_gate": Choice([0.0]),
            "previous_voltage": Choice([0.0]),
            "dynamic_gain": Choice([0.0]),
        }

        tau = NumberParam("tau", low=0, low_open=True)
        v_rest = NumberParam("v_rest")
        v_thresh = NumberParam("v_thresh")
        v_reset = NumberParam("v_reset")
        alpha = NumberParam("alpha", low=0, low_open=True)
        base_gain = NumberParam("base_gain", low=0)
        gain_scaling = NumberParam("gain_scaling", low=0)
        tau_r = NumberParam("tau_r", low=0, low_open=True)
        gamma = NumberParam("gamma", low=0)
        amplitude = NumberParam("amplitude", low=0, low_open=True)
        min_voltage = NumberParam("min_voltage")
        event_threshold = NumberParam("event_threshold")
        rate_to_current = NumberParam("rate_to_current", low=0, low_open=True)

        def __init__(
            self,
            tau=0.02,
            v_rest=0.0,
            v_thresh=1.0,
            v_reset=0.0,
            alpha=100.0,
            base_gain=20.0,
            gain_scaling=80.0,
            tau_r=0.002,
            gamma=0.2,
            amplitude=1.0,
            min_voltage=0.0,
            event_threshold=1.0,
            rate_to_current=15.0,
            initial_state=None,
        ):
            super().__init__(initial_state=initial_state)
            self.tau = tau
            self.v_rest = v_rest
            self.v_thresh = v_thresh
            self.v_reset = v_reset
            self.alpha = alpha
            self.base_gain = base_gain
            self.gain_scaling = gain_scaling
            self.tau_r = tau_r
            self.gamma = gamma
            self.amplitude = amplitude
            self.min_voltage = min_voltage
            self.event_threshold = event_threshold
            self.rate_to_current = rate_to_current

        def rates(self, x, gain, bias):
            J = self.current(x, gain, bias)
            return settled_firingrate(
                self.step,
                J,
                state={
                    "output": np.zeros_like(J),
                    "voltage": np.full_like(J, self.v_rest),
                    "reset_gate": np.zeros_like(J),
                    "previous_voltage": np.full_like(J, self.v_rest),
                    "dynamic_gain": np.zeros_like(J),
                },
            )

        def step(
            self,
            dt,
            J,
            output,
            voltage,
            reset_gate,
            previous_voltage,
            dynamic_gain,
        ):
            previous_voltage[...] = voltage
            effective_thresh = self.v_thresh - self.gamma * reset_gate
            target_gate = sigmoid_switch(self.alpha * (voltage - effective_thresh))
            gate_decay = np.exp(-dt / self.tau_r)
            reset_gate[...] = np.clip(
                target_gate + (reset_gate - target_gate) * gate_decay,
                0.0,
                1.0,
            )

            dynamic_gain[...] = self.base_gain + self.gain_scaling * np.abs(J)
            conductance = dynamic_gain * reset_gate**2
            voltage[...] = stable_voltage_update(
                voltage,
                J,
                conductance,
                dt,
                self.tau,
                self.v_rest,
                self.v_reset,
            )

            if np.isfinite(self.min_voltage):
                voltage[...] = np.maximum(voltage, self.min_voltage)

            crossed = (previous_voltage < self.event_threshold) & (
                voltage >= self.event_threshold
            )
            output[...] = np.where(crossed, self.amplitude / dt, 0.0)

else:

    class HyperLIFNengo:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("Nengo is required for HyperLIFNengo.")


    class AdaptiveHyperLIFNengo:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("Nengo is required for AdaptiveHyperLIFNengo.")
