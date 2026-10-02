"""Deeper spiking conv-residual net (SEW-ResNet style) for the at-scale / SOTA-class runs.

Swappable neuron (lif/plif/alif/hyperlif/adaptive + cfg for theta_event/origin), all 6 readouts,
vision only.
Depth/width via base_ch and stage_blocks. Each conv layer carries its own (v,r) state across time;
residual blocks use SEW-ADD (element-wise add of neuron outputs).

INTER-LAYER PROPAGATION: every layer (LIF and HyperLIF alike) propagates its SURROGATE SPIKE, exactly
as SEW-ResNet is designed for. We validated that propagating HyperLIF's *graded gate r* trains in
shallow nets (ff/conv/rsnn/delay) but STALLS at chance through this deep residual stack — the steep
alpha=100 gate kills gradient flow across ~9 layers, while LIF (spike-propagating) trains to 1.0 on the
same net. HyperLIF's spike carries the same fast_sigmoid surrogate gradient as LIF, so spike propagation
trains through depth. The continuous gate r is retained as the HEAD readout feature (gate/hybrid
readouts, gate-state decoding) — it is a decodable readout, not the deep transport signal.
Report base_ch/stage_blocks/params in the paper for full reproducibility.
"""
from __future__ import annotations

import torch
import torch.nn as nn

from .common import READOUT_MULT, conductance, init_state, new_neuron, step

# BatchNorm normalizes activations to ~unit scale, below HyperLIF's firing drive (v_thresh=1). A
# post-BN drive scale restores firing-level input so deep HyperLIF is not starved. Report it in the
# paper; pair with cfg={"event_threshold":0.95} for denser output. Tune if activity is too high/low.
DRIVE_SCALE = 5.0


class SNNConv(nn.Module):
    """conv → BN → (×DRIVE_SCALE) → spiking neuron, carrying its own state across the time loop."""

    def __init__(self, cin, cout, neuron, dt, cfg, stride=1):
        super().__init__()
        self.conv = nn.Conv2d(cin, cout, 3, stride, 1, bias=False)
        self.bn = nn.BatchNorm2d(cout)
        self.neuron, self.exposes_second_state = new_neuron(neuron, dt, cfg=cfg)
        self.state = None

    def reset(self):
        self.state = None

    def forward(self, x):
        cur = self.bn(self.conv(x)) * DRIVE_SCALE
        if self.state is None:
            self.state = init_state(self.neuron, self.exposes_second_state, cur.shape, cur.device, cur.dtype)
        spk, self.state, _, _ = step(self.neuron, self.exposes_second_state, cur, self.state)
        return spk


class ResBlock(nn.Module):
    def __init__(self, ch, neuron, dt, cfg):
        super().__init__()
        self.c1 = SNNConv(ch, ch, neuron, dt, cfg)
        self.c2 = SNNConv(ch, ch, neuron, dt, cfg)

    def reset(self):
        self.c1.reset(); self.c2.reset()

    def forward(self, x):
        return self.c2(self.c1(x)) + x                 # SEW-ADD


class ConvResSNN(nn.Module):
    def __init__(self, sensor, n_classes, neuron="hyperlif", readout="membrane",
                 n_hidden=256, dt=1e-3, base_ch=64, stage_blocks=(2, 2, 2), cfg=None):
        super().__init__()
        self.P, self.H, self.W = sensor
        self.readout, self.dt, self.n_hidden = readout, dt, n_hidden
        self.stem = SNNConv(self.P, base_ch, neuron, dt, cfg)
        layers, ch = [], base_ch
        for si, nblk in enumerate(stage_blocks):
            if si > 0:
                layers.append(SNNConv(ch, ch * 2, neuron, dt, cfg, stride=2)); ch *= 2
            for _ in range(nblk):
                layers.append(ResBlock(ch, neuron, dt, cfg))
        self.layers = nn.ModuleList(layers)
        self.fc = nn.Linear(ch, n_hidden)
        # Drive the head neuron like the conv layers: global-avg-pool + fc shrinks the signal well below
        # threshold, starving the head's gate/spikes (all readouts are taken here). BN->unit variance
        # then xDRIVE_SCALE restores firing-level drive so gate/spike/hybrid readouts + the events metric
        # are valid, not just membrane. (Shallow ConvSNNNet achieves the same via firing-init on its fc.)
        self.fc_bn = nn.BatchNorm1d(n_hidden)
        self.head_neuron, self.head_exposes_second_state = new_neuron(neuron, dt, cfg=cfg)
        self.norm = nn.BatchNorm1d(n_hidden * READOUT_MULT[readout])
        self.head = nn.Linear(n_hidden * READOUT_MULT[readout], n_classes)

    def _cond(self, r, cur):
        if not self.head_exposes_second_state:
            return torch.zeros_like(r)
        return conductance(self.head_neuron, r, cur)

    def forward(self, X):
        B, T, F = X.shape
        x = X.view(B, T, self.P, self.H, self.W)
        self.stem.reset()
        for l in self.layers:
            l.reset()
        z = torch.zeros(B, self.n_hidden, dtype=X.dtype, device=X.device)
        vbar, rbar, gbar, spk_sum = z.clone(), z.clone(), z.clone(), z.clone()
        hv = None
        for t in range(T):
            h = self.stem(x[:, t])
            for l in self.layers:
                h = l(h)
            cur = self.fc_bn(self.fc(h.mean(dim=(-1, -2)))) * DRIVE_SCALE   # pool -> fc -> BN -> firing drive
            if hv is None:
                hv = init_state(self.head_neuron, self.head_exposes_second_state,
                                (B, self.n_hidden), X.device, X.dtype)
            spk, hv, (v, r), _ = step(self.head_neuron, self.head_exposes_second_state, cur, hv)
            vbar = vbar + v; spk_sum = spk_sum + spk
            if self.head_exposes_second_state:
                rbar = rbar + r
                gbar = gbar + torch.tanh(self._cond(r, cur) / 20.0)
        vbar, rbar, gbar = vbar / T, rbar / T, gbar / T
        if self.readout == "spike_count":
            feat = spk_sum
        elif self.readout == "membrane":
            feat = vbar
        elif self.readout == "gate":
            feat = rbar
        elif self.readout == "hybrid_gr":
            feat = torch.cat([rbar, gbar], -1)
        elif self.readout == "hybrid_vr":
            feat = torch.cat([vbar, rbar], -1)
        else:
            feat = torch.cat([vbar, rbar, gbar], -1)
        logits = self.head(self.norm(feat))
        aux = {"events_per_sample": float(spk_sum.detach().sum(-1).mean()),
               "gate_mean": float(rbar.detach().mean())}
        return logits, aux
