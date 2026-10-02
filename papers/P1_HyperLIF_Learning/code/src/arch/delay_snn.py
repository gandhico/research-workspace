"""Tier-2 delay-SNN (audio, DCLS-style stub): a learnable per-channel temporal kernel over the
input current (learnable delays/weights across time lags) feeding a spiking hidden layer + readout.
The SHD/SSC SOTA route uses learnable synaptic delays; this is the minimal swappable prototype.
Neuron is swappable (LIF / HyperLIF / Adaptive)."""
from __future__ import annotations

import torch
import torch.nn as nn

from .common import READOUT_MULT, assemble, conductance, init_state, new_neuron, step


class DelaySNNNet(nn.Module):
    def __init__(self, n_in, n_classes, neuron="hyperlif", readout="hybrid_vr_conductance",
                 n_hidden=256, dt=1e-3, kernel=7, input_scale=16.0, cfg=None):
        super().__init__()
        self.readout, self.n_hidden, self.dt = readout, n_hidden, dt
        self.fc_in = nn.Linear(n_in, n_hidden)
        nn.init.normal_(self.fc_in.weight, std=input_scale / max(n_in, 1) ** 0.5)
        nn.init.zeros_(self.fc_in.bias)
        # depthwise temporal conv = learnable delays/weights per hidden channel; init as passthrough
        self.delay = nn.Conv1d(n_hidden, n_hidden, kernel, padding=kernel // 2, groups=n_hidden, bias=False)
        nn.init.zeros_(self.delay.weight)
        with torch.no_grad():
            self.delay.weight[:, :, kernel // 2] = 1.0
        self.neuron, self.gated = new_neuron(neuron, dt, cfg=cfg)
        feat = n_hidden * READOUT_MULT[readout]
        self.norm = nn.BatchNorm1d(feat)
        self.head = nn.Linear(feat, n_classes)

    def forward(self, X):                        # X: [B, T, F]
        B, T, _ = X.shape
        cur = self.fc_in(X).transpose(1, 2)      # [B, H, T]
        cur = self.delay(cur).transpose(1, 2)    # learnable temporal mixing -> [B, T, H]
        H = self.n_hidden
        z = torch.zeros(B, H, device=X.device, dtype=X.dtype)
        vbar, rbar, gbar, spk_sum = z.clone(), z.clone(), z.clone(), z.clone()
        s = init_state(self.neuron, self.gated, (B, H), X.device, X.dtype)
        for t in range(T):
            spk, s, (v, r), _ = step(self.neuron, self.gated, cur[:, t], s)
            vbar, spk_sum = vbar + v, spk_sum + spk
            if self.gated:
                rbar = rbar + r
                gbar = gbar + torch.tanh(conductance(self.neuron, r, cur[:, t]) / 20.0)
        vbar, rbar, gbar = vbar / T, rbar / T, gbar / T
        logits = self.head(self.norm(assemble(self.readout, vbar, rbar, gbar, spk_sum)))
        aux = {"events_per_sample": float(spk_sum.detach().sum(-1).mean()),
               "gate_mean": float(rbar.detach().mean())}
        return logits, aux
