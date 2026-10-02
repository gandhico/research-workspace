"""Gate-state residual augmented controller — the MuJoCo-quadrotor architecture.

Faithful port of `experiments/hyperlif_aug_benchmark/hyperlif_aug_1d.py`
(SimpleCustomNeuron1D) to the 2-DOF Aero2. A classical PD provides the safe
command; a per-axis HyperLIF gate neuron sees the *error feature*
``x = error - K_OMEGA*omega`` and its **gate-state** output ``y = gate*sign(out)``
(the best MuJoCo setting) is folded back in one of two ways:

    residual (direction-safe):  u = u_pd + blend*scale*y*sign(u_pd)*V_MAX
    gain modulation:            u = clip(1 + blend*tanh(scale*|y|), 0.25, 4)*u_pd

`neuron="hyperlif"` = FIXED gains; `neuron="adaptive_hyperlif"` adds a slow
adaptation state `a` (ADAPTIVE gains). Reduces to pure PD at blend=0.

EXPERIMENTAL. The gate neuron here mirrors the validated 1D stand-in; the richer
`aero2.control.neuromorphic.neuron.HyperLIFDirect` can be swapped in later.
"""
from __future__ import annotations

import numpy as np

from aero2.config import hyperlif as cfg
from aero2.config import params
from aero2.control.base import BaseController, Reference
from aero2.control.linear.pd import PD2DOF


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


class _GateNeuron:
    """Per-axis HyperLIF gate neuron (fixed or adaptive), gate-state output."""

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.v = 0.0
        self.a = 0.0

    def reset(self) -> None:
        self.v = 0.0
        self.a = 0.0

    def step(self, x: float, dt: float):
        drive = np.tanh(cfg.GATE_RES_INPUT_GAIN * x)
        if self.kind == "adaptive_hyperlif":
            self.v += dt * (-self.v + drive - self.a) / cfg.GATE_RES_TAU_V
        else:  # "hyperlif" (fixed)
            self.v += dt * (-self.v + drive) / cfg.GATE_RES_TAU_V

        gate = _sigmoid(cfg.GATE_RES_GATE_ALPHA * (abs(self.v) - cfg.GATE_RES_GATE_THRESH))
        out = gate * np.tanh(cfg.GATE_RES_OUT_GAIN * self.v)

        if self.kind == "adaptive_hyperlif":
            self.a += dt * (-self.a + cfg.GATE_RES_A_GAIN * abs(out)) / cfg.GATE_RES_TAU_A

        y_gate = gate * np.sign(out + 1e-12)     # gate-state mode
        return float(y_gate), float(gate), float(out)


class GateResidualController(BaseController):
    name = "gate_residual"

    def __init__(self, base=None, neuron: str = cfg.GATE_RES_NEURON, aug: str = cfg.GATE_RES_AUG,
                 blend: float = cfg.GATE_RES_BLEND, scale: float = cfg.GATE_RES_SCALE,
                 k_omega: float = cfg.GATE_RES_K_OMEGA, voltage_limit: float = params.V_MAX) -> None:
        super().__init__()
        if neuron not in ("hyperlif", "adaptive_hyperlif"):
            raise ValueError(f"neuron must be 'hyperlif' or 'adaptive_hyperlif', got {neuron!r}")
        if aug not in ("residual", "gain"):
            raise ValueError(f"aug must be 'residual' or 'gain', got {aug!r}")
        self.base = base if base is not None else PD2DOF(voltage_limit=voltage_limit)
        self.neuron_kind = neuron
        self.aug = aug
        self.blend = float(blend)
        self.scale = float(scale)
        self.k_omega = float(k_omega)
        self.voltage_limit = abs(float(voltage_limit))
        self.n_pitch = _GateNeuron(neuron)
        self.n_yaw = _GateNeuron(neuron)
        self.name = f"gate_{aug}_{'adapt' if neuron == 'adaptive_hyperlif' else 'fixed'}"

    def reset(self) -> None:
        super().reset()
        self.base.reset()
        self.n_pitch.reset()
        self.n_yaw.reset()

    def compute(self, x_est: np.ndarray, ref: Reference, dt: float) -> np.ndarray:
        x = np.asarray(x_est, dtype=float).reshape(-1)
        theta, omega_p, psi, omega_y = float(x[0]), float(x[1]), float(x[2]), float(x[3])

        u_pd = np.asarray(self.base.compute(x_est, ref, dt), dtype=float).reshape(2)

        # per-axis error feature x = error - K_OMEGA * omega
        xp = (ref.theta - theta) - self.k_omega * omega_p
        xy = (ref.psi - psi) - self.k_omega * omega_y
        y_p, gate_p, out_p = self.n_pitch.step(xp, dt)
        y_y, gate_y, out_y = self.n_yaw.step(xy, dt)
        y = np.array([y_p, y_y])

        if self.aug == "residual":
            residual = self.scale * y * np.sign(u_pd + 1e-12) * self.voltage_limit
            u = u_pd + self.blend * residual
        else:  # gain modulation
            gain_mult = np.clip(1.0 + self.blend * np.tanh(self.scale * np.abs(y)), 0.25, 4.0)
            u = gain_mult * u_pd

        u = np.clip(u, -self.voltage_limit, self.voltage_limit)
        self.info = {
            "u_pd": u_pd, "u": u, "residual": u - u_pd,
            "gate": np.array([gate_p, gate_y]), "y": y,
            "adapt": np.array([self.n_pitch.a, self.n_yaw.a]),
        }
        return u


__all__ = ["GateResidualController"]
