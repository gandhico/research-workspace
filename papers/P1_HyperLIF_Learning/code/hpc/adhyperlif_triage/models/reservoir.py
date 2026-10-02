"""Reservoir / Liquid-State-Machine architecture (Phase 2, survey idea 3).

A *fixed* random recurrent spiking layer (the "liquid") driven by the input; only a linear
readout is trained. The research question: does HyperLIF's richer ``(v, r, G_eff)`` state make a
better reservoir than LIF — i.e. do the same fixed dynamics carry more decodable information?

The reservoir weights (W_in, W_rec) are buffers (untrained). Recurrent feedback is a low-pass
filtered spike train (LSM-style), so the comparison across neurons is fair (all emit events);
the readout then reads whatever rich state each neuron exposes.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn

from ..neurons import HyperLIFConfig
from ..neurons.hyperlif_torch import alif_step, hyperlif_step, lif_surrogate_step
from .readouts import READOUT_DIM, readout_features


class ReservoirSNNClassifier(nn.Module):
    def __init__(
        self,
        n_in: int,
        n_res: int,
        n_classes: int,
        neuron_cfg: HyperLIFConfig,
        readout: str = "hybrid_vr_conductance",
        dt: float = 1e-3,
        input_scale: float = 16.0,
        spectral_radius: float = 0.9,
        rec_density: float = 0.15,
        fb_tau: float = 0.02,
        seed: int = 0,
    ):
        super().__init__()
        self.cfg = neuron_cfg
        self.readout = readout
        self.dt = dt
        self.n_res = n_res
        g = torch.Generator().manual_seed(seed)

        W_in = torch.randn(n_in, n_res, generator=g) * (input_scale / max(n_in, 1) ** 0.5)
        W_rec = torch.randn(n_res, n_res, generator=g)
        W_rec *= (torch.rand(n_res, n_res, generator=g) < rec_density).float()
        with torch.no_grad():  # scale to target spectral radius (echo-state-style)
            try:
                sr = torch.linalg.eigvals(W_rec).abs().max().item()
                W_rec *= spectral_radius / sr if sr > 1e-6 else 1.0
            except Exception:
                W_rec *= spectral_radius / max((n_res * rec_density) ** 0.5, 1e-6)
        self.register_buffer("W_in", W_in)
        self.register_buffer("W_rec", W_rec)
        self.fb_decay = math.exp(-dt / fb_tau)

        feat_dim = n_res * READOUT_DIM[readout]
        self.norm = nn.BatchNorm1d(feat_dim)
        self.head = nn.Linear(feat_dim, n_classes)  # the ONLY trained component

    def forward(self, X: torch.Tensor):
        """X: ``[B, T, F]`` -> (logits, reservoir trace dict)."""
        cfg, dt = self.cfg, self.dt
        B, dev, dtype = X.shape[0], X.device, X.dtype
        z = lambda: torch.zeros((B, self.n_res), dtype=dtype, device=dev)  # noqa: E731
        v = torch.full((B, self.n_res), cfg.v_rest, dtype=dtype, device=dev)
        r, a, fb = z(), z(), z()
        rec = {k: [] for k in ("voltage", "reset_gate", "conductance", "events")}
        for t in range(X.shape[1]):
            J = X[:, t] @ self.W_in + fb @ self.W_rec
            if cfg.model == "lif":
                v, e = lif_surrogate_step(v, J, cfg, dt)
                gg, rr = z(), z()
            elif cfg.model == "alif":
                v, a, e, _ = alif_step(v, a, J, cfg, dt)
                gg, rr = z(), a
            else:
                v, r, gg, e = hyperlif_step(v, r, J, cfg, dt)
                rr = r
            rec["voltage"].append(v); rec["reset_gate"].append(rr)
            rec["conductance"].append(gg); rec["events"].append(e)
            fb = self.fb_decay * fb + (e * dt / cfg.amplitude)  # filtered spike feedback
        out = {k: torch.stack(val, 0) for k, val in rec.items()}
        feat = readout_features(out, self.readout, dt)
        return self.head(self.norm(feat)), out
