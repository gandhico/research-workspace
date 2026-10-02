"""Tier-2 convolutional SNN (vision): a spiking conv feature extractor + a spiking FC readout layer.

Per timestep: conv -> neuron -> pool (x2), flatten -> FC -> readout neuron. Neuron states persist
across time (a true conv-SNN, not a per-frame CNN). Readout is taken on the final FC spiking layer,
so the same 6 readouts as the feedforward baseline apply. Neuron is swappable (LIF / HyperLIF / Adaptive)."""
from __future__ import annotations

import torch
import torch.nn as nn

from .common import READOUT_MULT, assemble, conductance, init_state, new_neuron, step


class ConvSNNNet(nn.Module):
    def __init__(self, sensor, n_classes, neuron="hyperlif", readout="hybrid_vr_conductance",
                 n_hidden=128, dt=1e-3, c1=16, c2=32, input_scale=8.0, cfg=None):
        super().__init__()
        self.P, self.H, self.W = sensor
        self.readout, self.n_hidden, self.dt = readout, n_hidden, dt
        self.conv1 = nn.Conv2d(self.P, c1, 3, padding=1)
        self.conv2 = nn.Conv2d(c1, c2, 3, padding=1)
        self.pool = nn.AvgPool2d(2)
        self.n1, self.g1 = new_neuron(neuron, dt, cfg=cfg)
        self.n2, self.g2 = new_neuron(neuron, dt, cfg=cfg)
        self.nh, self.gh = new_neuron(neuron, dt, cfg=cfg)
        flat = c2 * (self.H // 4) * (self.W // 4)
        self.fc = nn.Linear(flat, n_hidden)
        feat = n_hidden * READOUT_MULT[readout]
        self.norm = nn.BatchNorm1d(feat)
        self.head = nn.Linear(feat, n_classes)
        # firing-init: without this the spiking cascade never reaches threshold (see project-07 input_scale)
        for lin, fan in ((self.conv1, self.P * 9), (self.conv2, c1 * 9), (self.fc, flat)):
            nn.init.normal_(lin.weight, std=input_scale / max(fan, 1) ** 0.5)
            nn.init.zeros_(lin.bias)

    def forward(self, X):                        # X: [B, T, P*H*W]
        B, T, _ = X.shape
        xt = X.view(B, T, self.P, self.H, self.W)
        s1 = s2 = sh = None
        z = torch.zeros(B, self.n_hidden, device=X.device, dtype=X.dtype)
        vbar, rbar, gbar, spk_sum = z.clone(), z.clone(), z.clone(), z.clone()
        for t in range(T):
            a = self.conv1(xt[:, t])
            if s1 is None:
                s1 = init_state(self.n1, self.g1, a.shape, X.device, X.dtype)
            _, s1, _, act1 = step(self.n1, self.g1, a, s1)      # propagate natural output (spk/gate)
            h = self.pool(act1)
            b = self.conv2(h)
            if s2 is None:
                s2 = init_state(self.n2, self.g2, b.shape, X.device, X.dtype)
            _, s2, _, act2 = step(self.n2, self.g2, b, s2)
            h = self.pool(act2).flatten(1)
            cur = self.fc(h)
            if sh is None:
                sh = init_state(self.nh, self.gh, (B, self.n_hidden), X.device, X.dtype)
            spkh, sh, (v, r), _ = step(self.nh, self.gh, cur, sh)
            vbar, spk_sum = vbar + v, spk_sum + spkh
            if self.gh:
                rbar = rbar + r
                gbar = gbar + torch.tanh(conductance(self.nh, r, cur) / 20.0)
        vbar, rbar, gbar = vbar / T, rbar / T, gbar / T
        logits = self.head(self.norm(assemble(self.readout, vbar, rbar, gbar, spk_sum)))
        aux = {"events_per_sample": float(spk_sum.detach().sum(-1).mean()),
               "gate_mean": float(rbar.detach().mean())}
        return logits, aux
