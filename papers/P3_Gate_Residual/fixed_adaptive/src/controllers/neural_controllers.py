"""
Neural torque controllers: DirectNeuron (gate-state residual) and Nengo wrappers.

Key architecture for gate-state residual control:
    1. Classical PD computes tau_pd (safe baseline).
    2. tau_pd is normalized and encoded as pair-coded neuron current.
    3. HyperLIF / Adaptive HyperLIF neurons evolve their gate state r.
    4. The gate activity (r) is decoded as a signed residual torque.
    5. Final torque: tau = (1-blend)*tau_pd + blend*tau_neuron

For rotor-level residual (RotorResidualController):
    1. Classical PD → wrench_to_motors → u_nominal.
    2. HyperLIF gate state encodes rotor-level residual delta_u.
    3. Final: u = clip(u_nominal + delta_u, u_min, u_max).
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from quad.math_utils import quat_normalize, quat_mul, quat_conj
from controllers.neuron_dynamics import make_direct_neuron, NeuronStepResult


@dataclass
class ControllerOutput:
    tau: np.ndarray        # commanded body torque [Nm]
    q_err: np.ndarray      # quaternion error
    e_q: np.ndarray        # vector part
    info: dict


class DirectNeuronTorqueController:
    """
    Pair-coded direct-neuron torque controller.

    Encoding:
        currents[0:3] = bias + gain * max(tau_norm, 0)  (positive channels)
        currents[3:6] = bias + gain * max(-tau_norm, 0) (negative channels)

    Decoding:
        signed_activity = clip(activity_pos - activity_neg, -1, 1)
        tau_neuron = signed_activity * tau_limit

    Blend:
        tau = (1-blend)*tau_pd + blend*tau_neuron
    """

    def __init__(self, neuron_name: str, kq: np.ndarray, kw: np.ndarray,
                 tau_limit: np.ndarray, blend: float = 0.20,
                 current_bias: float = 0.75, current_gain: float = 1.25,
                 activity_mode: str = "voltage", scale: str = "paper",
                 gate_gain: float = 1.0):
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)
        self.blend = float(blend)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.activity_mode = activity_mode
        self.gate_gain = float(gate_gain)

        # 6 neurons: 3 positive + 3 negative channels for [τx, τy, τz]
        self.neuron = make_direct_neuron(neuron_name, n=6,
                                         activity_mode=activity_mode, scale=scale)
        self._name = f"direct_{neuron_name}_{scale}"

        self._last_result: NeuronStepResult | None = None
        self._last_tau_pd  = np.zeros(3)
        self._last_tau_neu = np.zeros(3)

    def reset(self) -> None:
        self.neuron.reset()
        self._last_result = None
        self._last_tau_pd[:] = 0.0
        self._last_tau_neu[:] = 0.0

    def step(self, q_ref: np.ndarray, q_meas: np.ndarray,
             omega: np.ndarray, dt: float) -> ControllerOutput:
        q_ref  = quat_normalize(q_ref)
        q_meas = quat_normalize(q_meas)

        q_err = quat_mul(q_ref, quat_conj(q_meas))
        q_err = quat_normalize(q_err)
        e_q   = q_err[1:].copy()
        if q_err[0] < 0.0:
            e_q = -e_q

        # Classical PD baseline
        tau_pd = -self.kq * e_q - self.kw * np.asarray(omega, dtype=float)
        tau_pd = np.clip(tau_pd, -self.tau_limit, self.tau_limit)

        # Normalize for neuron encoding
        tau_norm = np.divide(tau_pd, self.tau_limit,
                             out=np.zeros_like(tau_pd),
                             where=np.abs(self.tau_limit) > 1e-12)
        tau_norm = np.clip(tau_norm, -1.0, 1.0)

        currents = np.zeros(6, dtype=float)
        currents[0:3] = self.current_bias + self.current_gain * np.maximum(tau_norm, 0.0)
        currents[3:6] = self.current_bias + self.current_gain * np.maximum(-tau_norm, 0.0)

        result = self.neuron.step(currents, dt)
        self._last_result = result

        activity = result.activity.copy()
        if self.activity_mode == "gate":
            activity = np.clip(activity * self.gate_gain, 0.0, 1.0)

        signed_act = np.clip(activity[0:3] - activity[3:6], -1.0, 1.0)
        tau_neu    = signed_act * self.tau_limit

        tau = (1.0 - self.blend) * tau_pd + self.blend * tau_neu
        tau = np.clip(tau, -self.tau_limit, self.tau_limit)

        self._last_tau_pd  = tau_pd.copy()
        self._last_tau_neu = tau_neu.copy()

        info = {
            "controller":      self._name,
            "tau_pd":          tau_pd.copy(),
            "tau_neuron":      tau_neu.copy(),
            "residual":        tau_neu - tau_pd,
            "blend":           self.blend,
            "event_count":     float(np.sum(result.events)),
            "activity_mean":   float(np.mean(result.activity)),
            "activity_max":    float(np.max(result.activity)),
            "gate_mean":       float(np.mean(result.gate)),
            "gate_max":        float(np.max(result.gate)),
            "voltage_mean":    float(np.mean(result.voltage)),
        }
        return ControllerOutput(tau=tau, q_err=q_err, e_q=e_q, info=info)


class RotorResidualController:
    """
    Gate-state residual applied directly at rotor-command level (Skydio X2).

    Encodes the normalized quaternion-error torque direction projected into motor
    space as pair-coded currents.  At zero error the bias sits below v_thresh so
    the gate stays near 0 and delta_u = 0.  Under attitude error the gate fires
    on the appropriate motor channels, producing a signed per-motor residual.

    Architecture:
        tau_pd       = -kq*e_q - kw*omega
        tau_norm     = tau_pd / tau_limit              (in [-1,1])
        delta_dir    = B_inv @ [0, tau_norm]          (per-motor direction, [-1,1])
        currents+    = bias + gain * max(delta_dir, 0)
        currents-    = bias + gain * max(-delta_dir, 0)
        gate_diff    = clip(gate[0:4] - gate[4:8], -1, 1) * gate_gain
        u_final      = clip(u_nominal + residual_blend * gate_diff * u_scale, ...)
    """

    def __init__(self, neuron_name: str, kq: np.ndarray, kw: np.ndarray,
                 tau_limit: np.ndarray, mixer_B_inv: np.ndarray,
                 ctrl_min: np.ndarray, ctrl_max: np.ndarray,
                 residual_blend: float = 0.10,
                 current_bias: float = 0.75,
                 current_gain: float = 1.25,
                 activity_mode: str = "gate",
                 scale: str = "control",
                 gate_gain: float = 1.0,
                 u_scale: float | None = None):
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)
        self.B_inv = np.asarray(mixer_B_inv, dtype=float)
        self.ctrl_min = np.asarray(ctrl_min, dtype=float)
        self.ctrl_max = np.asarray(ctrl_max, dtype=float)
        self.residual_blend = float(residual_blend)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.gate_gain = float(gate_gain)
        self.u_scale = u_scale if u_scale is not None else float((ctrl_max[0] - ctrl_min[0]) * 0.15)

        # 8 neurons: 4 positive + 4 negative motor channels
        self.neuron = make_direct_neuron(neuron_name, n=8,
                                         activity_mode=activity_mode, scale=scale)
        self._name = f"rotor_residual_{neuron_name}_{scale}"
        self._last_result: NeuronStepResult | None = None

    def reset(self) -> None:
        self.neuron.reset()

    def step(self, q_ref: np.ndarray, q_meas: np.ndarray,
             omega: np.ndarray, T_collective: float, dt: float
             ) -> tuple[np.ndarray, np.ndarray, dict]:
        """
        Returns (u_final, u_nominal, info).
        u_final: clipped 4-motor command array.
        u_nominal: motor commands from classical PD alone.
        """
        q_ref  = quat_normalize(q_ref)
        q_meas = quat_normalize(q_meas)

        q_err = quat_mul(q_ref, quat_conj(q_meas))
        q_err = quat_normalize(q_err)
        e_q   = q_err[1:].copy()
        if q_err[0] < 0.0:
            e_q = -e_q

        tau_pd = -self.kq * e_q - self.kw * np.asarray(omega, dtype=float)
        tau_pd = np.clip(tau_pd, -self.tau_limit, self.tau_limit)

        wrench = np.array([T_collective, tau_pd[0], tau_pd[1], tau_pd[2]])
        u_nominal = np.clip(self.B_inv @ wrench, self.ctrl_min, self.ctrl_max)

        # Error-based pair encoding: zero error → all currents at bias (sub-threshold)
        tau_norm = np.divide(tau_pd, self.tau_limit,
                             out=np.zeros_like(tau_pd),
                             where=np.abs(self.tau_limit) > 1e-12)
        tau_norm = np.clip(tau_norm, -1.0, 1.0)
        wrench_norm = np.array([0.0, tau_norm[0], tau_norm[1], tau_norm[2]])
        delta_dir = self.B_inv @ wrench_norm
        max_dir = np.max(np.abs(delta_dir))
        if max_dir > 1e-12:
            delta_dir = delta_dir / max_dir

        currents = np.zeros(8, dtype=float)
        currents[0:4] = self.current_bias + self.current_gain * np.maximum(delta_dir, 0.0)
        currents[4:8] = self.current_bias + self.current_gain * np.maximum(-delta_dir, 0.0)

        result = self.neuron.step(currents, dt)
        self._last_result = result

        gate = np.clip(result.gate, 0.0, 1.0) * self.gate_gain
        # Signed residual per motor (positive - negative)
        delta_u_norm = np.clip(gate[0:4] - gate[4:8], -1.0, 1.0)
        delta_u = delta_u_norm * self.u_scale

        u_final = np.clip(u_nominal + self.residual_blend * delta_u,
                          self.ctrl_min, self.ctrl_max)

        info = {
            "controller":    self._name,
            "q_err":         q_err,
            "e_q":           e_q,
            "tau_pd":        tau_pd,
            "T_collective":  T_collective,
            "u_nominal":     u_nominal.copy(),
            "delta_u":       delta_u.copy(),
            "u_final":       u_final.copy(),
            "event_count":   float(np.sum(result.events)),
            "gate_mean":     float(np.mean(result.gate)),
            "gate_max":      float(np.max(result.gate)),
            "voltage_mean":  float(np.mean(result.voltage)),
            "residual_blend": self.residual_blend,
        }
        return u_final, u_nominal, info


class NengoTorqueController:
    """
    Nengo neural ensemble decoding the same PD torque law.
    Requires nengo to be installed.
    """

    def __init__(self, neuron_name: str, kq: np.ndarray, kw: np.ndarray,
                 tau_limit: np.ndarray, dt: float, n_neurons: int = 400,
                 radius: float = 1.5, synapse: float = 0.002, seed: int = 2,
                 max_rate_low: float = 100.0, max_rate_high: float = 200.0,
                 intercept_low: float = -0.8, intercept_high: float = 0.8):
        import nengo
        self.nengo = nengo
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)
        self.state  = np.zeros(6, dtype=float)
        self.output = np.zeros(3, dtype=float)

        def stim(t): return self.state
        def capture(t, x): self.output[:] = np.clip(x, -self.tau_limit, self.tau_limit)
        def func(x):
            return np.clip(-kq * x[:3] - kw * x[3:], -tau_limit, tau_limit)

        with nengo.Network(label=f"NengoTorque_{neuron_name}") as model:
            s   = nengo.Node(stim, size_out=6)
            ens = nengo.Ensemble(n_neurons=n_neurons, dimensions=6,
                                 neuron_type=self._nt(neuron_name),
                                 radius=radius,
                                 max_rates=nengo.dists.Uniform(max_rate_low, max_rate_high),
                                 intercepts=nengo.dists.Uniform(intercept_low, intercept_high),
                                 seed=seed)
            out = nengo.Node(capture, size_in=3)
            nengo.Connection(s, ens, synapse=None)
            nengo.Connection(ens, out, function=func, synapse=synapse)
        self.sim = nengo.Simulator(model, dt=dt, progress_bar=False)
        self._name = f"nengo_{neuron_name}"

    def _nt(self, name: str):
        n = self.nengo
        name = name.lower()
        if name in {"lif", "nengo_lif"}:       return n.LIF()
        if name in {"lifrate"}:                 return n.LIFRate()
        if name in {"rectified", "relu"}:       return n.RectifiedLinear()
        if name in {"adaptive_lif"}:            return n.AdaptiveLIF()
        raise ValueError(f"Unknown Nengo neuron: '{name}'")

    def reset(self) -> None:
        self.state[:] = 0.0; self.output[:] = 0.0

    def close(self) -> None:
        self.sim.close()

    def step(self, q_ref: np.ndarray, q_meas: np.ndarray,
             omega: np.ndarray, dt: float) -> ControllerOutput:
        from quad.math_utils import quat_mul, quat_conj, quat_normalize
        q_err = quat_mul(quat_normalize(q_ref), quat_conj(quat_normalize(q_meas)))
        q_err = quat_normalize(q_err)
        e_q   = q_err[1:].copy()
        if q_err[0] < 0.0: e_q = -e_q
        self.state[:] = np.concatenate([e_q, np.asarray(omega, dtype=float)])
        self.sim.step()
        tau = self.output.copy()
        return ControllerOutput(tau=tau, q_err=q_err, e_q=e_q,
                                info={"controller": self._name,
                                      "event_count": 0.0, "gate_mean": 0.0})
