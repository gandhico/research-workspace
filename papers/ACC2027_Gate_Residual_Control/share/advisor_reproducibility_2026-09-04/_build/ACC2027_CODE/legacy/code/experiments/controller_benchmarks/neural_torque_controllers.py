from __future__ import annotations

from dataclasses import dataclass
import sys
from pathlib import Path
import numpy as np

from neuron_dynamics import make_direct_neuron


# Root path of the repository.
# This can be used later to build paths relative to the project folder,
# independent of where the script is executed from.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Standard output container returned by every controller.
# tau contains the commanded body torques, while info stores optional
# diagnostic data such as controller name, neural activity, or event counts.
@dataclass
class ControllerOutput:
    tau: np.ndarray
    info: dict


class ClassicalQuaternionPD:
    """
    Classical quaternion PD torque controller.

    tau = -KQ * axis_error - KW * omega
    """
    # Store the attitude gains, angular-rate damping gains, and torque limits.
    # All inputs are converted to NumPy arrays to guarantee vectorized operations.
    def __init__(self, kq: np.ndarray, kw: np.ndarray, tau_limit: np.ndarray):
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)


    # Reset controller internal state.
    # This classical PD controller has no memory, so there is nothing to reset.
    def reset(self) -> None:
        pass

    # Compute the body torque command from quaternion attitude error and angular velocity.
    # The control law applies proportional feedback on attitude error and damping feedback
    # on angular velocity, then clips the result to safe torque limits.
    def step(self, axis_error: np.ndarray, omega: np.ndarray, dt: float) -> ControllerOutput:
        tau = -self.kq * axis_error - self.kw * omega
        tau = np.clip(tau, -self.tau_limit, self.tau_limit)
        return ControllerOutput(tau=tau, info={"controller": "classical"})


class DirectNeuronTorqueController:
    """
    Paper-scale direct neuron torque controller.

    This controller keeps the classical PD law as a safe reference and passes
    the normalized desired torque through a pair-coded neuron layer.

    Pair coding:
        positive torque axis -> positive neuron
        negative torque axis -> negative neuron

    signed_activity = activity_pos - activity_neg

    tau_neuron = signed_activity * tau_limit

    Final torque:
        tau = (1 - blend) * tau_pd + blend * tau_neuron

    Use blend=0.0 to recover classical PD.
    Use small blend first, e.g. 0.10 to 0.30, for safe MuJoCo testing.
    """

    def __init__(
        self,
        neuron_name: str,
        kq: np.ndarray,
        kw: np.ndarray,
        tau_limit: np.ndarray,
        blend: float = 0.20,
        current_bias: float = 0.75,
        current_gain: float = 1.25,
        activity_mode: str = "voltage",
        direct_scale: str = "paper",
        direct_gate_gain: float = 1.0,
    ):
        # Store controller configuration and classical PD gains.
        # kq acts on quaternion-axis attitude error, kw acts on angular velocity,
        # and tau_limit defines the maximum safe torque for each body axis.
        self.neuron_name = neuron_name
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)


        # Store direct-neuron scaling parameters.
        # blend controls how much of the final torque comes from the neuron layer.
        # activity_mode selects which neuron signal is used as output activity.
        self.blend = float(blend)
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.activity_mode = activity_mode
        self.direct_scale = direct_scale
        self.direct_gate_gain = float(direct_gate_gain)

        # Create 6 neurons: positive and negative channels for each torque axis.
        # Channels 0:3 encode positive torque; channels 3:6 encode negative torque.
        self.neuron = make_direct_neuron(neuron_name, n=6, activity_mode=activity_mode, scale=direct_scale)

        # Store previous internal values for diagnostics and logging.
        self.last_tau_pd = np.zeros(3, dtype=float)
        self.last_tau_neuron = np.zeros(3, dtype=float)
        self.last_events = np.zeros(6, dtype=float)
        self.last_activity = np.zeros(6, dtype=float)

    def reset(self) -> None:
        # Reset neuron dynamics and clear stored diagnostic signals.
        self.neuron.reset()
        self.last_tau_pd[:] = 0.0
        self.last_tau_neuron[:] = 0.0
        self.last_events[:] = 0.0
        self.last_activity[:] = 0.0

    def step(self, axis_error: np.ndarray, omega: np.ndarray, dt: float) -> ControllerOutput:
        # Compute the safe classical PD torque command.
        # This is used both as a baseline and as the input target for the neuron layer.
        tau_pd = -self.kq * axis_error - self.kw * omega
        tau_pd = np.clip(tau_pd, -self.tau_limit, self.tau_limit)

        # Normalize torque into [-1, 1] so it can be encoded as neuron input current.
        # Division is protected against near-zero torque limits.
        tau_norm = np.divide(
            tau_pd,
            self.tau_limit,
            out=np.zeros_like(tau_pd),
            where=np.abs(self.tau_limit) > 1e-12,
        )
        tau_norm = np.clip(tau_norm, -1.0, 1.0)

        # Pair-coded current encoding.
        # Positive normalized torque activates the positive neuron channel.
        # Negative normalized torque activates the negative neuron channel.
        currents = np.zeros(6, dtype=float)
        currents[0:3] = self.current_bias + self.current_gain * np.maximum(tau_norm, 0.0)
        currents[3:6] = self.current_bias + self.current_gain * np.maximum(-tau_norm, 0.0)

        # Advance the direct neuron dynamics by one simulation step.
        result = self.neuron.step(currents, dt)

        # Copy neuron output activity so it can be optionally rescaled.
        activity = result.activity.copy()

        # Gate-mode activities can be numerically very small.
        # direct_gate_gain lets us test whether the gate signal is useful
        # after explicit scaling.
        if self.activity_mode == "gate":
            activity = np.clip(activity * self.direct_gate_gain, 0.0, 1.0)

        # Decode signed torque activity from positive-minus-negative channels.
        activity_pos = activity[0:3]
        activity_neg = activity[3:6]
        signed_activity = np.clip(activity_pos - activity_neg, -1.0, 1.0)
        
        # Convert decoded neural activity back into physical torque units.
        tau_neuron = signed_activity * self.tau_limit

        # Blend classical PD torque with neuron-generated torque.
        # blend=0 gives pure PD; blend=1 gives pure direct-neuron torque
        tau = (1.0 - self.blend) * tau_pd + self.blend * tau_neuron
        tau = np.clip(tau, -self.tau_limit, self.tau_limit)


        # Save diagnostic signals for later inspection or plotting
        self.last_tau_pd = tau_pd.copy()
        self.last_tau_neuron = tau_neuron.copy()
        self.last_events = result.events.copy()
        self.last_activity = activity.copy()


        # Return useful metadata for benchmark logging.
        info = {
            "controller": f"direct_{self.neuron_name}_{self.direct_scale}",
            "tau_pd": tau_pd.copy(),
            "tau_neuron": tau_neuron.copy(),
            "event_count_step": float(np.sum(result.events)),
            "activity_mean": float(np.mean(result.activity)),
            "activity_max": float(np.max(activity)),
            "raw_activity_mean": float(np.mean(result.activity)),
            "raw_activity_max": float(np.max(result.activity)),
            "direct_gate_gain": self.direct_gate_gain,
        }

        return ControllerOutput(tau=tau, info=info)


# Nengo-based neural torque controller.
# This controller builds a Nengo network that receives the current attitude error
# and angular velocity, then decodes the same PD torque law through a neural ensemble.
# Input:  [axis_error_x, axis_error_y, axis_error_z, omega_x, omega_y, omega_z]
# Output: [tau_x, tau_y, tau_z]
class NengoTorqueController:
    """
    Pure Python/Nengo torque decoder controller.

    This follows the same idea as your current MuJoCo Nengo controller:
        input  = [axis_error_x, axis_error_y, axis_error_z, wx, wy, wz]
        output = [tau_x, tau_y, tau_z]

    The decoded function is the same quaternion PD torque law.
    """

    def __init__(
        self,
        neuron_name: str,
        kq: np.ndarray,
        kw: np.ndarray,
        tau_limit: np.ndarray,
        dt: float,
        n_neurons: int = 400,
        radius: float = 1.5,
        synapse: float = 0.002,
        seed: int = 2,
        max_rate_low: float = 100.0,
        max_rate_high: float = 200.0,
        intercept_low: float = -0.8,
        intercept_high: float = 0.8,
    ):
        # Import Nengo only when this controller is used.
        # This avoids requiring Nengo for purely classical or direct-neuron runs.
        import nengo

        self.nengo = nengo
        self.neuron_name = neuron_name
        self.kq = np.asarray(kq, dtype=float)
        self.kw = np.asarray(kw, dtype=float)
        self.tau_limit = np.asarray(tau_limit, dtype=float)
        self.dt = float(dt)


        # State is the 6D input to the neural controller:
        # attitude-axis error plus angular velocity.
        # Output stores the decoded 3D body torque.
        self.state = np.zeros(6, dtype=float)
        self.output = np.zeros(3, dtype=float)


        # Nengo input node. At each simulation step, it provides the latest
        # controller state to the neural ensemble.
        def stim_func(_t: float) -> np.ndarray:
            return self.state


        # Nengo output node. It captures the decoded torque and clips it
        # to the physical torque limits.
        def capture_func(_t: float, x: np.ndarray) -> None:
            self.output[:] = np.clip(x, -self.tau_limit, self.tau_limit)


        # Function decoded by the neural ensemble.
        # It implements the same quaternion PD torque law used by the classical controller.
        def torque_func(x: np.ndarray) -> np.ndarray:
            axis_err = x[:3]
            omega = x[3:]
            tau = -self.kq * axis_err - self.kw * omega
            return np.clip(tau, -self.tau_limit, self.tau_limit)


        # Build the Nengo network:
        # input node -> neural ensemble -> decoded torque output node.
        with nengo.Network(label=f"Nengo torque controller {neuron_name}") as model:
            stim = nengo.Node(stim_func, size_out=6)

            ens = nengo.Ensemble(
                n_neurons=n_neurons,
                dimensions=6,
                neuron_type=self._neuron_type(neuron_name),
                radius=radius,
                max_rates=nengo.dists.Uniform(max_rate_low, max_rate_high),
                intercepts=nengo.dists.Uniform(intercept_low, intercept_high),
                seed=seed,
            )

            torque = nengo.Node(capture_func, size_in=3)

            nengo.Connection(stim, ens, synapse=None)
            nengo.Connection(ens, torque, function=torque_func, synapse=synapse)
            
        # Create the Nengo simulator using the same time step as the MuJoCo benchmark.
        self.sim = nengo.Simulator(model, dt=dt, progress_bar=False)

    def _neuron_type(self, name: str):
        nengo = self.nengo
        name = name.lower()

        if name in {"lif", "nengo_lif"}:
            return nengo.LIF()

        if name in {"lifrate", "nengo_lifrate"}:
            return nengo.LIFRate()

        if name in {"rectified", "relu", "nengo_rectified"}:
            return nengo.RectifiedLinear()

        if name in {"adaptive_lif", "nengo_adaptive_lif"}:
            return nengo.AdaptiveLIF()

        if name in {"izhikevich", "nengo_izhikevich"}:
            if hasattr(nengo, "Izhikevich"):
                return nengo.Izhikevich()
            if hasattr(nengo.neurons, "Izhikevich"):
                return nengo.neurons.Izhikevich()
            raise RuntimeError("This installed Nengo version does not expose Izhikevich.")

        raise ValueError(f"Unknown Nengo neuron type: {name}")

    def reset(self) -> None:
        # Nengo Simulator does not provide a simple full reset preserving the object.
        # For benchmark scripts, instantiate a new controller per run.
        self.state[:] = 0.0
        self.output[:] = 0.0

    def close(self) -> None:
        self.sim.close()

    def step(self, axis_error: np.ndarray, omega: np.ndarray, dt: float) -> ControllerOutput:
        self.state[:] = np.concatenate([axis_error, omega])
        self.sim.step()
        tau = self.output.copy()

        return ControllerOutput(
            tau=tau,
            info={
                "controller": f"nengo_{self.neuron_name}",
                "tau_neuron": tau.copy(),
                "event_count_step": 0.0,
            },
        )


def make_controller(
    controller_name: str,
    kq: np.ndarray,
    kw: np.ndarray,
    tau_limit: np.ndarray,
    dt: float,
    direct_blend: float = 0.20,
    direct_activity_mode: str = "voltage",
    nengo_n_neurons: int = 400,
    nengo_radius: float = 1.5,
    nengo_synapse: float = 0.002,
    nengo_seed: int = 2,
    direct_scale: str = "paper",
    direct_gate_gain: float = 1.0,
):
    name = controller_name.lower()

    if name == "classical":
        return ClassicalQuaternionPD(kq, kw, tau_limit)

    if name in {"direct_lif", "direct_standard_lif"}:
        return DirectNeuronTorqueController(
            "standard_lif",
            kq,
            kw,
            tau_limit,
            blend=direct_blend,
            activity_mode=direct_activity_mode,
            direct_scale=direct_scale,
            direct_gate_gain=direct_gate_gain,
        )

    if name == "direct_hyperlif":
        return DirectNeuronTorqueController(
            "hyperlif",
            kq,
            kw,
            tau_limit,
            blend=direct_blend,
            activity_mode=direct_activity_mode,
            direct_scale=direct_scale,
            direct_gate_gain=direct_gate_gain,
        )

    if name in {"direct_adaptive_hyperlif", "direct_adapthyperlif"}:
        return DirectNeuronTorqueController(
            "adaptive_hyperlif",
            kq,
            kw,
            tau_limit,
            blend=direct_blend,
            activity_mode=direct_activity_mode,
            direct_scale=direct_scale,
            direct_gate_gain=direct_gate_gain,
        )

    if name == "direct_izhikevich":
        return DirectNeuronTorqueController(
            "izhikevich",
            kq,
            kw,
            tau_limit,
            blend=direct_blend,
            activity_mode="events",
            direct_scale=direct_scale,
            direct_gate_gain=direct_gate_gain,
            current_bias=0.0,
            current_gain=20.0,
        )

    if name.startswith("nengo_"):
        neuron_name = name.replace("nengo_", "")
        return NengoTorqueController(
            neuron_name=neuron_name,
            kq=kq,
            kw=kw,
            tau_limit=tau_limit,
            dt=dt,
            n_neurons=nengo_n_neurons,
            radius=nengo_radius,
            synapse=nengo_synapse,
            seed=nengo_seed,
        )

    raise ValueError(f"Unknown controller name: {controller_name}")


