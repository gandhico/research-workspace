"""HyperLIF gate-state residual controller (control) — PD + neuromorphic residual.

Realizes the brief's "PD + neuromorphic residual" (§14) and the gate-residual
architecture from `01_HyperLIF_Gate_Residual` (published +7.35% vs classical PD on
a quadrotor). A classical base controller (default PD2DOF) provides the safe
command; its 2-axis output is pair-coded into 4 HyperLIF currents whose gate state
decodes a signed residual that is blended back in:

    u_pd   = base.compute(...)                       # [u_p, u_y], clipped +/-V_MAX
    u_norm = clip(u_pd / V_MAX, -1, 1)
    I_pos  = bias + gain*max(u_norm, 0)              # 2 channels
    I_neg  = bias + gain*max(-u_norm, 0)             # 2 channels
    gate   = neuron.step([I_pos, I_neg]).gate
    signed = clip(gate_pos - gate_neg, -1, 1)
    u      = clip((1-blend)*u_pd + blend*signed*V_MAX, +/-V_MAX)

EXPERIMENTAL: fixed-weight neurons (the "adaptive" is input-dependent conductance,
not synaptic plasticity). No Aero2 HyperLIF results exist yet. `blend=0` reduces
exactly to the base controller.
"""
from __future__ import annotations

import numpy as np

from aero2.config import hyperlif as cfg
from aero2.config import params
from aero2.control.base import BaseController, Reference
from aero2.control.linear.pd import PD2DOF
from aero2.control.neuromorphic.neuron import make_direct_neuron


class HyperLIFResidualController(BaseController):
    name = "hyperlif"

    def __init__(self, base=None, neuron_name=cfg.RESIDUAL_NEURON, blend=cfg.RESIDUAL_BLEND,
                 gate_gain=cfg.RESIDUAL_GATE_GAIN, activity_mode=cfg.RESIDUAL_ACTIVITY_MODE,
                 scale=cfg.RESIDUAL_SCALE, current_bias=cfg.RESIDUAL_CURRENT_BIAS,
                 current_gain=cfg.RESIDUAL_CURRENT_GAIN, voltage_limit=params.V_MAX):
        super().__init__()
        self.base = base if base is not None else PD2DOF(voltage_limit=voltage_limit)
        self.neuron = make_direct_neuron(neuron_name, n=4, activity_mode=activity_mode, scale=scale)
        self.blend = float(blend)
        self.gate_gain = float(gate_gain)
        self.activity_mode = activity_mode
        self.current_bias = float(current_bias)
        self.current_gain = float(current_gain)
        self.voltage_limit = abs(float(voltage_limit))
        self._name = f"hyperlif_{neuron_name}_{activity_mode}"

    def reset(self):
        super().reset()
        self.base.reset()
        self.neuron.reset()

    def compute(self, x_est, ref: Reference, dt):
        u_pd = np.asarray(self.base.compute(x_est, ref, dt), dtype=float).reshape(2)

        u_norm = np.clip(u_pd / self.voltage_limit, -1.0, 1.0)
        currents = np.zeros(4)
        currents[0:2] = self.current_bias + self.current_gain * np.maximum(u_norm, 0.0)
        currents[2:4] = self.current_bias + self.current_gain * np.maximum(-u_norm, 0.0)

        result = self.neuron.step(currents, dt)
        activity = result.activity
        if self.activity_mode == "gate":
            activity = np.clip(activity * self.gate_gain, 0.0, 1.0)
        signed = np.clip(activity[0:2] - activity[2:4], -1.0, 1.0)
        u_neural = signed * self.voltage_limit

        u = np.clip((1.0 - self.blend) * u_pd + self.blend * u_neural,
                    -self.voltage_limit, self.voltage_limit)
        self.info = {
            "u_pd": u_pd, "u_neural": u_neural, "residual": u_neural - u_pd,
            "gate_mean": float(np.mean(result.gate)), "blend": self.blend,
        }
        return u


__all__ = ["HyperLIFResidualController"]
