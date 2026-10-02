"""Tier-1/2 recurrent SNN (audio + general): input projection + a recurrently-connected spiking
hidden layer + the shared readout. The recurrence (hidden spikes fed back through W_rec) is the
standard RSNN used for SHD/SSC. Neuron is swappable (LIF / HyperLIF / Adaptive)."""
from __future__ import annotations

import torch
import torch.nn as nn

from .common import READOUT_MULT, assemble, conductance, init_state, new_neuron, step


class RSNNNet(nn.Module):
    def __init__(self, n_in, n_classes, neuron="hyperlif", readout="hybrid_vr_conductance",
                 n_hidden=256, dt=1e-3, input_scale=16.0, cfg=None):
        super().__init__()
        self.readout, self.n_hidden, self.dt = readout, n_hidden, dt
        self.fc_in = nn.Linear(n_in, n_hidden)
        nn.init.normal_(self.fc_in.weight, std=input_scale / max(n_in, 1) ** 0.5)
        nn.init.zeros_(self.fc_in.bias)
        self.fc_rec = nn.Linear(n_hidden, n_hidden, bias=False)
        nn.init.orthogonal_(self.fc_rec.weight, gain=0.2)
        self.neuron, self.gated = new_neuron(neuron, dt, cfg=cfg)
        feat = n_hidden * READOUT_MULT[readout]
        self.norm = nn.BatchNorm1d(feat)
        self.head = nn.Linear(feat, n_classes)

    def forward(self, X):                        # X: [B, T, F]
        B, T, _ = X.shape
        H = self.n_hidden
        z = torch.zeros(B, H, device=X.device, dtype=X.dtype)
        vbar, rbar, gbar, spk_sum = z.clone(), z.clone(), z.clone(), z.clone()
        prev_spk = z.clone()
        s = init_state(self.neuron, self.gated, (B, H), X.device, X.dtype)
        for t in range(T):
            cur = self.fc_in(X[:, t]) + self.fc_rec(prev_spk)
            spk, s, (v, r), _ = step(self.neuron, self.gated, cur, s)
            prev_spk = spk
            vbar, spk_sum = vbar + v, spk_sum + spk
            if self.gated:
                rbar = rbar + r
                gbar = gbar + torch.tanh(conductance(self.neuron, r, cur) / 20.0)
        vbar, rbar, gbar = vbar / T, rbar / T, gbar / T
        logits = self.head(self.norm(assemble(self.readout, vbar, rbar, gbar, spk_sum)))
        aux = {"events_per_sample": float(spk_sum.detach().sum(-1).mean()),
               "gate_mean": float(rbar.detach().mean())}
        return logits, aux
