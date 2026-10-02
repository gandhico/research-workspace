"""
Controller factory.
Usage:
    ctrl = make_controller("classical",     params, dt)
    ctrl = make_controller("direct_hyperlif", params, dt, blend=0.20, gate_gain=100000)
    ctrl = make_controller("rotor_residual_adaptive_hyperlif", params, dt)
    ctrl = make_controller("nengo_lifrate",  params, dt)
"""
from __future__ import annotations

import numpy as np

from quad.models import DroneParams
from controllers.classical import ClassicalPD
from controllers.neural_controllers import (
    DirectNeuronTorqueController,
    RotorResidualController,
    NengoTorqueController,
)


def make_controller(
    name: str,
    params: DroneParams,
    dt: float,
    # --- Direct-neuron options ---
    blend: float = 0.20,
    activity_mode: str = "voltage",
    scale: str = "paper",
    gate_gain: float = 1.0,
    current_bias: float = 0.75,
    current_gain: float = 1.25,
    # --- Rotor-residual options ---
    residual_blend: float = 0.10,
    u_scale: float | None = None,
    # --- Nengo options ---
    n_neurons: int = 400,
    radius: float = 1.5,
    synapse: float = 0.002,
    seed: int = 2,
):
    """
    Return a controller instance appropriate for the given name and drone params.

    Supported names:
        "classical"
        "direct_lif"
        "direct_hyperlif"
        "direct_adaptive_hyperlif"
        "direct_izhikevich"
        "rotor_residual_hyperlif"
        "rotor_residual_adaptive_hyperlif"
        "nengo_lifrate"
        "nengo_lif"
        "nengo_rectified"
        "nengo_adaptive_lif"
    """
    kq = params.kq
    kw = params.kw
    tau_lim = params.tau_limit
    n = name.lower()

    if n == "classical":
        return ClassicalPD(kq, kw, tau_lim)

    # --- Direct-neuron body-torque residual ---
    _direct_map = {
        "direct_lif":                "standard_lif",
        "direct_hyperlif":           "hyperlif",
        "direct_adaptive_hyperlif":  "adaptive_hyperlif",
        "direct_izhikevich":         "izhikevich",
    }
    if n in _direct_map:
        nname = _direct_map[n]
        am    = "events" if nname == "izhikevich" else activity_mode
        cb    = 0.0 if nname == "izhikevich" else current_bias
        cg    = 20.0 if nname == "izhikevich" else current_gain
        return DirectNeuronTorqueController(
            neuron_name=nname, kq=kq, kw=kw, tau_limit=tau_lim,
            blend=blend, current_bias=cb, current_gain=cg,
            activity_mode=am, scale=scale, gate_gain=gate_gain,
        )

    # --- Rotor-level residual (Skydio X2 only) ---
    _rotor_map = {
        "rotor_residual_hyperlif":          "hyperlif",
        "rotor_residual_adaptive_hyperlif": "adaptive_hyperlif",
    }
    if n in _rotor_map:
        if params.actuator_mode != "rotor4":
            raise ValueError(
                f"Rotor-residual controllers require actuator_mode='rotor4', "
                f"but {params.name} uses '{params.actuator_mode}'."
            )
        nname = _rotor_map[n]
        return RotorResidualController(
            neuron_name=nname, kq=kq, kw=kw, tau_limit=tau_lim,
            mixer_B_inv=params.mixer_B_inv,
            ctrl_min=params.ctrl_min_vector(),
            ctrl_max=params.ctrl_max_vector(),
            residual_blend=residual_blend,
            activity_mode="gate",
            scale="control",
            gate_gain=gate_gain,
            u_scale=u_scale,
        )

    # --- Nengo ensemble controllers ---
    if n.startswith("nengo_"):
        nname = n.replace("nengo_", "", 1)
        return NengoTorqueController(
            neuron_name=nname, kq=kq, kw=kw, tau_limit=tau_lim,
            dt=dt, n_neurons=n_neurons, radius=radius,
            synapse=synapse, seed=seed,
        )

    raise ValueError(
        f"Unknown controller '{name}'.\n"
        "Supported: classical, direct_lif, direct_hyperlif, direct_adaptive_hyperlif, "
        "direct_izhikevich, rotor_residual_hyperlif, rotor_residual_adaptive_hyperlif, "
        "nengo_lifrate, nengo_lif, nengo_rectified, nengo_adaptive_lif."
    )
