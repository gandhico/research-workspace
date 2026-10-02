"""Phase-1 model: input encoder -> spiking layer (neuron under test) -> readout -> linear head.

Feedforward architecture (the survey's conv / reservoir / WTA architectures are Phase 2). The
encoder is a trainable linear projection from input features to the hidden current ``J``; set
``fixed_encoder=True`` for a random-projection reservoir (train the head only).
"""

from __future__ import annotations

import torch
import torch.nn as nn

from ..neurons import HyperLIFConfig, HyperLIFLayer
from .readouts import READOUT_DIM, readout_features


class SNNClassifier(nn.Module):
    def __init__(
        self,
        n_in: int,
        n_hidden: int,
        n_classes: int,
        neuron_cfg: HyperLIFConfig,
        readout: str = "hybrid_vr_conductance",
        dt: float = 1e-3,
        input_scale: float = 1.0,
        fixed_encoder: bool = False,
    ):
        super().__init__()
        self.dt = dt
        self.readout = readout
        self.encoder = nn.Linear(n_in, n_hidden)
        nn.init.normal_(self.encoder.weight, std=input_scale / max(n_in, 1) ** 0.5)
        nn.init.zeros_(self.encoder.bias)
        if fixed_encoder:
            for p in self.encoder.parameters():
                p.requires_grad_(False)
        self.layer = HyperLIFLayer(neuron_cfg)
        feat_dim = n_hidden * READOUT_DIM[readout]
        self.norm = nn.BatchNorm1d(feat_dim)
        self.head = nn.Linear(feat_dim, n_classes)

    def forward(self, X: torch.Tensor):
        """X: ``[B, T, F]`` -> (logits ``[B, C]``, neuron output dict of ``[T, B, H]`` traces)."""
        Jt = self.encoder(X.transpose(0, 1))  # [T, B, H]
        out = self.layer(Jt, self.dt)
        feat = readout_features(out, self.readout, self.dt)
        feat = self.norm(feat)
        return self.head(feat), out
