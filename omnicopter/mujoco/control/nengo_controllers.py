"""Nengo realizations of the Omnicopter PD and CMG-PES controllers.

``NengoPDController`` executes the exact geometric PD/feedforward law as a
Nengo Node.  It is a backend-conformance comparator, not a neural
approximation. ``NengoCMGPESController`` adds a custom continuous CMG neuron
population and Nengo's built-in PES learning rule before the same bounded
MuJoCo rotor allocator.
"""
from __future__ import annotations

import warnings

import nengo
import numpy as np
from nengo.dists import Choice
from nengo.params import BoolParam, NumberParam

from hover import attitude_error


class CoupledMembraneGate(nengo.neurons.NeuronType):
    """Continuous, non-spiking coupled membrane--gate Nengo neuron."""

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

    def __init__(self, tau=.05, tau_r=.005, v_rest=0., v_reset=0.,
                 v_threshold=1., alpha=50., gamma=2., base_gain=120.,
                 gain_scaling=30., gate_gain=1e5, adaptive=True,
                 initial_state=None):
        super().__init__(initial_state=initial_state)
        self.tau, self.tau_r = tau, tau_r
        self.v_rest, self.v_reset = v_rest, v_reset
        self.v_threshold, self.alpha, self.gamma = v_threshold, alpha, gamma
        self.base_gain, self.gain_scaling = base_gain, gain_scaling
        self.gate_gain, self.adaptive = gate_gain, adaptive

    def step(self, dt, J, output, voltage, gate):
        argument = np.clip(
            self.alpha * (voltage - (self.v_threshold - self.gamma * gate)),
            -60., 60.)
        target = 1. / (1. + np.exp(-argument))
        gate += dt * (target - gate) / self.tau_r
        np.clip(gate, 0., 1., out=gate)
        gain = self.base_gain + (self.gain_scaling * np.abs(J) if self.adaptive else 0.)
        conductance = gain * gate * gate
        lam = 1. / self.tau + conductance
        drive = self.v_rest / self.tau + J / self.tau + conductance * self.v_reset
        decay = np.exp(-lam * dt)
        voltage[:] = voltage * decay + drive / np.maximum(lam, 1e-12) * (1. - decay)
        output[:] = np.clip(self.gate_gain * gate, 0., 1.)

    def max_rates_intercepts(self, gain, bias):
        gain = np.asarray(gain, dtype=float)
        return np.ones_like(gain), np.zeros_like(gain)


class NengoPDController:
    """Exact Omnicopter geometric PD law executed by a Nengo graph."""

    def __init__(self, controller, dt):
        self.controller = controller
        self.dt = float(dt)
        # R(9), omega, velocity_com, position error, velocity error,
        # attitude error, rate error, reference acceleration and angular accel.
        self.external = np.zeros(33, dtype=float)
        self.network = nengo.Network(label="Exact geometric PD + feedforward", seed=1)
        with self.network:
            self.state_node = nengo.Node(
                lambda t: self.external, size_out=33, label="measured/reference state")
            self.wrench_node = nengo.Node(size_in=6, label="body wrench")
            nengo.Connection(
                self.state_node, self.wrench_node, function=self._wrench,
                synapse=None)
        self.sim = nengo.Simulator(self.network, dt=self.dt, progress_bar=False)
        self._wrench_signal = self.sim.signals[
            self.sim.model.sig[self.wrench_node]["out"]]

    def _wrench(self, x):
        c = self.controller
        rotation = x[:9].reshape(3, 3)
        omega = x[9:12]
        force_world = c.mass * (
            x[27:30] + c.kp_position * x[15:18]
            + c.kd_position * x[18:21] - c.gravity)
        torque = c.inertia @ (
            x[30:33] + c.kp_attitude * x[21:24]
            + c.kd_attitude * x[24:27])
        torque += np.cross(omega, c.inertia @ omega)
        return np.r_[rotation.T @ force_world, torque]

    def desired_wrench(self, data):
        c = self.controller
        rotation = data.xmat[c.bid].reshape(3, 3)
        omega = data.qvel[3:6].copy()
        velocity_com = data.qvel[:3] + rotation @ np.cross(omega, c.com)
        error_p = c.target_com - data.xipos[c.bid]
        error_v = c.target_velocity_com - velocity_com
        error_r = attitude_error(data.qpos[3:7], c.target_q)
        error_omega = c.target_omega - omega
        self.external[:] = np.r_[
            rotation.ravel(), omega, velocity_com, error_p, error_v, error_r,
            error_omega, c.target_acceleration_com, c.target_alpha]
        self.sim.step()
        wrench = np.asarray(self._wrench_signal, dtype=float).copy()
        metrics = {
            "position_error_m": float(np.linalg.norm(data.qpos[:3] - c.target_origin)),
            "attitude_error_deg": float(np.rad2deg(np.linalg.norm(error_r))),
            "speed_com_m_s": float(np.linalg.norm(velocity_com)),
            "rate_rad_s": float(np.linalg.norm(omega)),
            "nengo_pd_wrench_norm": float(np.linalg.norm(wrench)),
        }
        return wrench, metrics

    def command(self, data, dt=None):
        wrench, metrics = self.desired_wrench(data)
        controls, allocation = self.controller.allocate(wrench)
        metrics.update(allocation)
        metrics["baseline_wrench"] = wrench.copy()
        metrics["commanded_wrench"] = wrench.copy()
        return controls, metrics

    def reset(self):
        self.sim.reset(seed=self.network.seed)

    def close(self):
        self.sim.close()

    def metadata(self):
        return {
            "implementation": "exact geometric PD/feedforward executed as a Nengo Node",
            "neural_approximation": False,
            "nengo_version": nengo.__version__,
            "dt_s": self.dt,
            "allocation": "shared bounded 6x8 allocator",
        }


class _ExternalCMGSignals:
    def __init__(self, units, channels):
        self.current = np.zeros(units)
        self.target = np.zeros(channels)


class NengoCMGPESBank:
    """Canonical paired CMG population with Nengo's native PES operator."""

    def __init__(self, channels, limits, dt, beta=.05, learning_rate=8e-4,
                 leak=1e-6, seed=1):
        self.channels, self.units = int(channels), 2 * int(channels)
        self.limits, self.dt = np.asarray(limits, dtype=float), float(dt)
        self.beta, self.learning_rate, self.leak = float(beta), float(learning_rate), float(leak)
        self.current_bias, self.current_gain = .75, 1.25
        self.external = _ExternalCMGSignals(self.units, self.channels)
        self.W0 = np.concatenate([np.eye(self.channels), -np.eye(self.channels)], axis=1)
        # Nengo SimPES applies -eta_N*dt/N*error*activity. This makes it
        # identical to the canonical direct per-step decoder update.
        self.nengo_learning_rate = self.learning_rate * self.units / self.dt
        self.network = nengo.Network(label="12-cell CMG + online PES", seed=seed)
        with self.network:
            drive = nengo.Node(lambda t: self.external.current, size_out=self.units)
            target = nengo.Node(lambda t: self.external.target, size_out=self.channels)
            self.population = nengo.Ensemble(
                self.units, 1, neuron_type=CoupledMembraneGate(),
                gain=np.ones(self.units), bias=np.zeros(self.units),
                encoders=np.ones((self.units, 1)), label="paired CMG cells")
            nengo.Connection(drive, self.population.neurons, synapse=None)
            decoded = nengo.Node(size_in=self.channels, label="decoded residual")
            clipped = nengo.Node(
                lambda t, x: np.clip(x, -1., 1.), size_in=self.channels,
                size_out=self.channels, label="bounded residual")
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="This learning rate is very high.*")
                self.decoder = nengo.Connection(
                    self.population.neurons, decoded, transform=self.W0,
                    synapse=None, learning_rule_type=nengo.PES(
                        learning_rate=self.nengo_learning_rate, pre_synapse=None))
            nengo.Connection(decoded, clipped, synapse=None)
            error = nengo.Node(
                lambda t, x: x[:self.channels] - x[self.channels:],
                size_in=2*self.channels, size_out=self.channels)
            nengo.Connection(clipped, error[:self.channels], synapse=None)
            nengo.Connection(target, error[self.channels:], synapse=None)
            nengo.Connection(error, self.decoder.learning_rule, synapse=None)
        self.sim = nengo.Simulator(self.network, dt=self.dt, progress_bar=False)
        model, signals = self.sim.model, self.sim.signals
        self._activity = signals[model.sig[self.population.neurons]["out"]]
        self._gate = signals[model.sig[self.population.neurons]["gate"]]
        self._weights = signals[model.sig[self.decoder]["weights"]]
        self._decoded = signals[model.sig[decoded]["out"]]

    def step(self, baseline, target):
        baseline = np.clip(np.asarray(baseline, dtype=float), -self.limits, self.limits)
        normalized = np.divide(
            baseline, self.limits, out=np.zeros_like(baseline), where=self.limits > 1e-12)
        self.external.current[:] = np.r_[
            self.current_bias + self.current_gain * np.maximum(normalized, 0.),
            self.current_bias + self.current_gain * np.maximum(-normalized, 0.)]
        self.external.target[:] = np.clip(target, -1., 1.)
        weights_before = self._weights.copy()
        self.sim.step()
        self._weights[:] -= self.leak * weights_before
        np.clip(self._weights, -6., 6., out=self._weights)
        decoded = np.clip(np.asarray(self._decoded, dtype=float), -1., 1.)
        command = np.clip(baseline + self.beta * decoded * self.limits,
                          -self.limits, self.limits)
        return command, baseline, command-baseline

    def reset(self):
        self.sim.reset(seed=self.network.seed)
        self._weights[:] = self.W0

    def close(self):
        self.sim.close()


class NengoCMGPESController:
    """Nengo-executed PD plus custom CMG neurons and native online PES."""

    def __init__(self, controller, dt, beta=.05, learning_rate=8e-4, leak=1e-6):
        self.controller = controller
        self.pd = NengoPDController(controller, dt)
        row_authority = np.sum(
            np.abs(controller.matrix) * controller.allocator.upper[None, :], axis=1)
        self.limits = np.minimum(row_authority, np.array([45., 40., 40., 2., 2., 2.]))
        self.cmg = NengoCMGPESBank(
            6, self.limits, dt, beta=beta, learning_rate=learning_rate, leak=leak)
        self.beta, self.learning_rate, self.leak = beta, learning_rate, leak
        self.position_scale_m, self.velocity_scale_m_s = .15, .75
        self.attitude_scale_rad, self.rate_scale_rad_s = np.deg2rad(15.), 1.5

    def learning_target(self, data):
        c = self.controller
        rotation = data.xmat[c.bid].reshape(3, 3)
        omega = data.qvel[3:6].copy()
        velocity_com = data.qvel[:3] + rotation @ np.cross(omega, c.com)
        position = ((c.target_com-data.xipos[c.bid])/self.position_scale_m
                    + (c.target_velocity_com-velocity_com)/self.velocity_scale_m_s)
        attitude = (attitude_error(data.qpos[3:7], c.target_q)/self.attitude_scale_rad
                    + (c.target_omega-omega)/self.rate_scale_rad_s)
        return np.clip(np.r_[rotation.T @ position, attitude], -1., 1.)

    def command(self, data, dt=None):
        baseline, metrics = self.pd.desired_wrench(data)
        target = self.learning_target(data)
        requested, baseline_clipped, residual = self.cmg.step(baseline, target)
        controls, allocation = self.controller.allocate(requested)
        metrics.update(allocation)
        metrics.update({
            "baseline_wrench": baseline_clipped.copy(),
            "commanded_wrench": requested.copy(),
            "pes_residual_wrench": residual.copy(),
            "pes_learning_target": target.copy(),
            "pes_activity_mean": float(np.mean(self.cmg._activity)),
            "pes_gate_mean": float(np.mean(self.cmg._gate)),
            "pes_decoder_norm": float(np.linalg.norm(self.cmg._weights)),
            "pes_residual_norm": float(np.linalg.norm(residual)),
        })
        return controls, metrics

    def reset(self):
        self.pd.reset()
        self.cmg.reset()

    def close(self):
        self.pd.close()
        self.cmg.close()

    def metadata(self):
        return {
            "implementation": "Nengo exact PD Node + custom continuous CMG NeuronType + native PES",
            "nengo_version": nengo.__version__, "channels": 6, "paired_units": 12,
            "wrench_limits": self.limits.tolist(), "beta": self.beta,
            "learning_rate": self.learning_rate, "leak": self.leak,
            "allocation": "shared bounded 6x8 allocator",
            "actuation_path": "Nengo wrench -> bounded allocator -> data.ctrl",
        }
