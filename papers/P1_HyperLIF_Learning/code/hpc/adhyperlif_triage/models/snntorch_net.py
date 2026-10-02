"""Configurable snnTorch classifier for the HPC event-vision benchmark.

Neuron in {lif (snntorch.Leaky), hyperlif, adaptive (HyperLIFsnn)}; readout in
{spike_count, membrane, gate, hybrid_gr, hybrid_vr, hybrid_vr_conductance}. The gate/hybrid readouts
read the HyperLIF gate (r) and conductance (G) state (LIF has no gate -> those channels are zero,
which is the honest baseline). hybrid_gr=[r,G], hybrid_vr=[v,r], hybrid_vr_conductance=[v,r,G].
Returns (logits, aux) where aux carries activity/stability stats for the dynamics metrics.
"""

from __future__ import annotations

import torch
import torch.nn as nn

import snntorch
from snntorch import surrogate

from ..neurons.snntorch_hyperlif import HyperLIFsnn

READOUT_MULT = {"spike_count": 1, "membrane": 1, "gate": 1,
                "hybrid_gr": 2, "hybrid_vr": 2, "hybrid_vr_conductance": 3}


class SNNTorchNet(nn.Module):
    def __init__(self, n_in, n_hidden, n_classes, neuron="hyperlif",
                 readout="hybrid_vr_conductance", dt=1e-3, input_scale=16.0, beta=0.95):
        super().__init__()
        self.kind, self.readout, self.n_hidden, self.dt = neuron, readout, n_hidden, dt
        self.fc1 = nn.Linear(n_in, n_hidden)
        nn.init.normal_(self.fc1.weight, std=input_scale / max(n_in, 1) ** 0.5)
        nn.init.zeros_(self.fc1.bias)
        if neuron == "lif":
            self.neuron = snntorch.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid(slope=25.0))
            self._has_gate = False
        else:
            self.neuron = HyperLIFsnn(model=("adaptive_hyperlif" if neuron == "adaptive" else "hyperlif"), dt=dt)
            self._has_gate = True
        feat_dim = n_hidden * READOUT_MULT[readout]
        self.norm = nn.BatchNorm1d(feat_dim)
        self.head = nn.Linear(feat_dim, n_classes)

    def _conductance(self, r, cur):
        nu = self.neuron
        if hasattr(nu, "reset_gain") and nu.model == "hyperlif":
            return nu.reset_gain * r**2
        return (nu.base_gain + nu.gain_scaling * cur.abs()) * r**2

    def forward(self, X):  # [B, T, F]
        cur = self.fc1(X)  # [B, T, H]
        T = X.shape[1]
        z = torch.zeros(X.shape[0], self.n_hidden, dtype=X.dtype, device=X.device)
        vbar, rbar, gbar, spk_sum = z.clone(), z.clone(), z.clone(), z.clone()

        if self.kind == "lif":
            mem = self.neuron.init_leaky()
            for t in range(T):
                spk, mem = self.neuron(cur[:, t], mem)
                vbar = vbar + mem
                spk_sum = spk_sum + spk
            vbar = vbar / T
        else:
            v, r = self.neuron.init_hyperlif((X.shape[0], self.n_hidden), device=X.device, dtype=X.dtype)
            for t in range(T):
                spk, v, r = self.neuron(cur[:, t], v, r)
                vbar = vbar + v
                rbar = rbar + r
                gbar = gbar + torch.tanh(self._conductance(r, cur[:, t]) / 20.0)
                spk_sum = spk_sum + spk
            vbar, rbar, gbar = vbar / T, rbar / T, gbar / T

        if self.readout == "spike_count":
            feat = spk_sum
        elif self.readout == "membrane":
            feat = vbar
        elif self.readout == "gate":
            feat = rbar
        elif self.readout == "hybrid_gr":
            feat = torch.cat([rbar, gbar], dim=-1)
        elif self.readout == "hybrid_vr":
            feat = torch.cat([vbar, rbar], dim=-1)
        else:  # hybrid_vr_conductance
            feat = torch.cat([vbar, rbar, gbar], dim=-1)

        logits = self.head(self.norm(feat))
        aux = {
            "events_per_sample": float(spk_sum.detach().sum(-1).mean()),
            "gate_mean": float(rbar.detach().mean()),
            "active_neuron_fraction": float((spk_sum.detach() > 0).float().mean()),
            "voltage_max": float(vbar.detach().abs().max()),
        }
        return logits, aux
