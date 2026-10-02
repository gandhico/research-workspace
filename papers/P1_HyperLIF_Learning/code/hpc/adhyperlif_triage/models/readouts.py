"""Readout feature extractors (the readout axis of the matrix).

Each maps a neuron output dict of traces ``[T, B, H]`` to a feature vector ``[B, D]``. Event-
inclusive readouts (``*_event``, ``spike_count``, ``filtered_event``) are the only ones affected
by the event threshold ``theta_event`` -- voltage/gate/conductance readouts ignore it.
"""

from __future__ import annotations

import torch

# feature-dimension multiplier (xH) per readout, used to size the classifier head
READOUT_DIM = {
    "voltage": 1,
    "gate": 1,
    "spike_count": 1,
    "filtered_event": 1,
    "hybrid_vr": 2,
    "hybrid_vr_drdt": 3,
    "hybrid_vr_conductance": 3,
    "hybrid_vr_conductance_event": 4,
}


def _filtered(events: torch.Tensor, dt: float, tau_syn: float = 0.02) -> torch.Tensor:
    """Causal exponential filter of the event train, averaged over time -> [B, H]."""
    decay = float(torch.exp(torch.tensor(-dt / tau_syn)))
    tr = torch.zeros_like(events[0])
    acc = []
    for t in range(events.shape[0]):
        tr = decay * tr + events[t] * dt
        acc.append(tr)
    return torch.stack(acc, 0).mean(0)


def readout_features(out: dict, readout: str, dt: float) -> torch.Tensor:
    v, r = out["voltage"], out["reset_gate"]
    g, e = out["conductance"], out["events"]
    vbar, rbar = v.mean(0), r.mean(0)
    if readout == "voltage":
        return vbar
    if readout == "gate":
        return rbar
    if readout == "spike_count":
        return (e * dt).sum(0)
    if readout == "filtered_event":
        return _filtered(e, dt)
    if readout == "hybrid_vr":
        return torch.cat([vbar, rbar], dim=-1)
    if readout == "hybrid_vr_drdt":
        drdt = (r[1:] - r[:-1]).abs().mean(0) / dt if r.shape[0] > 1 else torch.zeros_like(rbar)
        return torch.cat([vbar, rbar, drdt], dim=-1)
    if readout == "hybrid_vr_conductance":
        return torch.cat([vbar, rbar, torch.tanh(g / 20.0).mean(0)], dim=-1)
    if readout == "hybrid_vr_conductance_event":
        return torch.cat([vbar, rbar, torch.tanh(g / 20.0).mean(0), (e * dt).sum(0)], dim=-1)
    raise ValueError(f"unknown readout: {readout!r}")
