"""Single-axis attitude-control prototype of the embodied-control residual architecture.

Mirrors the per-axis pair-coded residual of `01_HyperLIF_Gate_Residual` / `07_ServoPendulum`:
a classical PD is the stability anchor; a HyperLIF residual is *blended* in. We test three residual
readouts — **gate** (`r`, the team's mechanism), **conductance** (`G_eff`, our novel readout where
beta+demand appear), and **hybrid** — across {HyperLIF, Adaptive, +origin}. Lightweight (no MuJoCo)
so it runs foreground; the validated winner ports to the real quad sim.

    I*thetaddot = tau - b*thetadot          (single rotational axis)
    tau_pd  = -kq*(theta-theta_ref) - kw*thetadot      (clipped to tau_limit)
    tau_final = (1-blend)*tau_pd + blend*delta*tau_limit
"""

from __future__ import annotations

import math

import numpy as np
import torch

from ..neurons import HyperLIFConfig
from ..neurons.hyperlif_torch import hyperlif_step


class Attitude1D:
    def __init__(self, I=0.05, b=0.10, dt=5e-4, tau_limit=1.5):
        self.I, self.b, self.dt, self.tau_limit = I, b, dt, tau_limit

    def step(self, state, tau, dist=0.0):
        theta, omega = float(state[0]), float(state[1])
        tau = float(np.clip(tau, -self.tau_limit, self.tau_limit))
        domega = (tau + dist - self.b * omega) / self.I  # dist = unmodeled disturbance torque
        omega += self.dt * domega
        theta += self.dt * omega
        return np.array([theta, omega], dtype=np.float64), tau


def pd_gains(I, wn=15.0, zeta=0.9, alpha_max=30.0):
    return dict(kq=2 * I * wn**2, kw=2 * zeta * wn * I, tau_limit=I * alpha_max)


def reference(n, dt, drive=1.0):
    t = np.arange(n) * dt
    a, f = 0.06 * drive, 1.0 * drive
    return (a * np.sin(2 * np.pi * f * t) + 0.4 * a * np.sin(2 * np.pi * 2.1 * f * t + 0.4)).astype(np.float64)


class ResidualController:
    """PD + HyperLIF residual. ``mode`` in {none, gate, conductance, hybrid}."""

    def __init__(self, cfg: HyperLIFConfig, dt, *, mode="gate", blend=0.5, gate_gain=100000.0,
                 bias=0.75, input_gain=1.25, g_scale=120.0, hybrid_w=0.5):
        self.cfg, self.dt, self.mode = cfg, dt, mode
        self.blend, self.gate_gain = blend, gate_gain
        self.bias, self.input_gain, self.g_scale, self.hybrid_w = bias, input_gain, g_scale, hybrid_w
        self.reset()

    def reset(self):
        self.v = torch.full((2,), self.cfg.v_rest, dtype=torch.float64)
        self.r = torch.zeros(2, dtype=torch.float64)

    @torch.no_grad()
    def __call__(self, state, theta_ref, kq, kw, tau_limit):
        tau_pd = -kq * (state[0] - theta_ref) - kw * state[1]
        if self.mode == "none":
            return float(np.clip(tau_pd, -tau_limit, tau_limit)), 0.0, 0.0
        tau_norm = float(np.clip(tau_pd / tau_limit, -1.0, 1.0))
        I = torch.tensor([self.bias + self.input_gain * max(tau_norm, 0.0),
                          self.bias + self.input_gain * max(-tau_norm, 0.0)], dtype=torch.float64)
        self.v, self.r, g, _ = hyperlif_step(self.v, self.r, I, self.cfg, self.dt)
        rp, rn = float(self.r[0]), float(self.r[1])
        gp, gn = float(g[0]), float(g[1])
        gate = rp - rn
        cond = (gp - gn) / self.g_scale
        if self.mode == "gate":
            d = gate
        elif self.mode == "conductance":
            d = cond
        else:  # hybrid
            d = (1 - self.hybrid_w) * gate + self.hybrid_w * cond
        delta = float(np.clip(self.gate_gain * d, -1.0, 1.0))
        tau_final = (1 - self.blend) * tau_pd + self.blend * delta * tau_limit
        return float(np.clip(tau_final, -tau_limit, tau_limit)), delta, tau_norm


def disturbance_profile(n, dt, amp):
    """Unmodeled disturbance torque: low-freq drift + impulses (PD alone tracks it poorly)."""
    t = np.arange(n) * dt
    d = amp * (0.6 * np.sin(2 * np.pi * 0.6 * t) + 0.4 * np.sin(2 * np.pi * 1.7 * t + 0.7))
    for tc, w, a in [(1.5, 0.08, 1.2), (3.2, 0.06, -1.4), (4.6, 0.07, 1.0)]:
        d = d + amp * a * np.exp(-0.5 * ((t - tc) / w) ** 2)
    return d


def run_episode(plant: Attitude1D, ctrl: ResidualController, ref, gains, disturbance=None):
    ctrl.reset()
    state = np.array([0.0, 0.0])
    n = len(ref)
    err = np.zeros(n); tau = np.zeros(n); act = np.zeros(n)
    for k in range(n):
        u, delta, _ = ctrl(state, ref[k], gains["kq"], gains["kw"], gains["tau_limit"])
        err[k] = state[0] - ref[k]
        act[k] = abs(delta)
        d = 0.0 if disturbance is None else float(disturbance[k])
        state, u_app = plant.step(state, u, dist=d)
        tau[k] = u_app
        if not np.isfinite(state).all():
            return None
    return dict(rmse=float(np.sqrt(np.mean(err**2))), emax=float(np.max(np.abs(err))),
                effort=float(np.mean(np.abs(tau))), activity=float(np.mean(act)))
