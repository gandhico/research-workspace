"""Spiking controller for the pendulum probe.

A neuron population (optional fixed reservoir) reads the state-error features and a *trained
per-step linear readout* outputs the torque. The reservoir is fixed; the readout is fit by
closed-form ridge to imitate a PD demonstrator (fast, convex). Then the controller is run
closed-loop on the plant and compared across neurons at low vs high drive.

Note on timescale: the control loop runs at the plant dt (~0.02 s), so neuron time constants are
set to the *control* timescale (tau~0.1, tau_r~0.02) rather than the perception-scale reference
(dt~1e-4) — otherwise the fast gate fully equilibrates each step and carries no dynamics. The
parity-gate-validated equations are unchanged; only the time constants are task-appropriate.
"""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn

from ..neurons import HyperLIFConfig
from ..neurons.hyperlif_torch import alif_step, hyperlif_step, lif_surrogate_step


class ControlNet(nn.Module):
    def __init__(self, neuron_cfg: HyperLIFConfig, n_in=2, n_res=64, dt=0.02, input_scale=3.0,
                 spectral_radius=0.6, rec_density=0.2, fb_tau=0.05, seed=0):
        super().__init__()
        self.cfg, self.dt, self.n_res = neuron_cfg, dt, n_res
        g = torch.Generator().manual_seed(seed)
        W_in = torch.randn(n_in, n_res, generator=g) * input_scale
        W_rec = torch.randn(n_res, n_res, generator=g)
        W_rec *= (torch.rand(n_res, n_res, generator=g) < rec_density).float()
        with torch.no_grad():
            try:
                sr = torch.linalg.eigvals(W_rec).abs().max().item()
                W_rec *= spectral_radius / sr if sr > 1e-6 else 1.0
            except Exception:
                W_rec *= spectral_radius / max((n_res * rec_density) ** 0.5, 1e-6)
        self.register_buffer("W_in", W_in.float())
        self.register_buffer("W_rec", W_rec.float())
        self.fb_decay = math.exp(-dt / fb_tau)
        self.readout = nn.Linear(n_res * 3, 1)

    def _step(self, v, r, a, J):
        cfg = self.cfg
        if cfg.model == "lif":
            v, e = lif_surrogate_step(v, J, cfg, self.dt); gg, rr = torch.zeros_like(v), torch.zeros_like(v)
        elif cfg.model == "alif":
            v, a, e, _ = alif_step(v, a, J, cfg, self.dt); gg, rr = torch.zeros_like(v), a
        else:
            v, r, gg, e = hyperlif_step(v, r, J, cfg, self.dt); rr = r
        return v, r, a, rr, gg, e

    @staticmethod
    def _feat(v, r, gg):
        return torch.cat([v, r, torch.tanh(gg / 20.0)], dim=-1)

    @torch.no_grad()
    def features_seq(self, state_seq):  # [B,T,2] -> [B,T,3*n_res]
        B, dev, dt = state_seq.shape[0], state_seq.device, state_seq.dtype
        z = lambda: torch.zeros((B, self.n_res), dtype=dt, device=dev)  # noqa: E731
        v = torch.full((B, self.n_res), self.cfg.v_rest, dtype=dt, device=dev); r, a, fb = z(), z(), z()
        out = []
        for t in range(state_seq.shape[1]):
            J = state_seq[:, t] @ self.W_in + fb @ self.W_rec
            v, r, a, rr, gg, e = self._step(v, r, a, J)
            out.append(self._feat(v, rr, gg))
            fb = self.fb_decay * fb + (e * self.dt / self.cfg.amplitude)
        return torch.stack(out, 1)

    @torch.no_grad()
    def rollout(self, plant, ref):
        """Closed-loop: the controller drives the plant. Returns angles[T], torques[T], diverged."""
        z = lambda: torch.zeros((1, self.n_res))  # noqa: E731
        v = torch.full((1, self.n_res), self.cfg.v_rest); r, a, fb = z(), z(), z()
        state = np.array([0.0, 0.0], dtype=np.float32)
        T = len(ref); angles = np.zeros(T); torques = np.zeros(T); diverged = False
        for t in range(T):
            sf = torch.tensor([[ref[t] - state[0], state[1]]], dtype=torch.float32)
            J = sf @ self.W_in + fb @ self.W_rec
            v, r, a, rr, gg, e = self._step(v, r, a, J)
            u = float(self.readout(self._feat(v, rr, gg)).item())
            angles[t] = state[0]
            state, u_app = plant.step(state, u)
            torques[t] = u_app
            fb = self.fb_decay * fb + (e * self.dt / self.cfg.amplitude)
            if not np.isfinite(state).all() or abs(state[0]) > 50:
                diverged = True; break
        return angles, torques, diverged


@torch.no_grad()
def fit_readout_ridge(net: ControlNet, feats, targets, lam=1.0):
    """Closed-form ridge fit of the per-step torque readout on the fixed reservoir features."""
    F = net.features_seq(torch.tensor(np.asarray(feats), dtype=torch.float32))
    n, T, D = F.shape
    Fm = F.reshape(n * T, D)
    ym = torch.tensor(np.asarray(targets), dtype=torch.float32).reshape(n * T, 1)
    W = torch.linalg.solve(Fm.T @ Fm + lam * torch.eye(D), Fm.T @ ym)
    net.readout.weight.copy_(W.T)
    net.readout.bias.zero_()
    return float(((Fm @ W - ym) ** 2).mean())
