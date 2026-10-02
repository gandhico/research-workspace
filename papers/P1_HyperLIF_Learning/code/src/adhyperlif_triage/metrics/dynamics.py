"""Dynamics-specific metrics — the project's differentiator (not just accuracy).

These quantify *how* the neuron behaves: sparsity, gate engagement, conductance, and the
audit's dynamical-stability check (``outside_operating_fraction``). They take a layer output
dict (``voltage``/``reset_gate``/``conductance``/``events`` of shape ``[T, ...]``) and return
flat scalars suitable for the registry.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np


def _np(x):
    try:
        import torch

        if isinstance(x, torch.Tensor):
            return x.detach().cpu().numpy()
    except ImportError:
        pass
    return np.asarray(x)


def dynamics_metrics(
    out: Mapping[str, object],
    dt: float,
    *,
    operating_voltage_limit: float = 5.0,
    saturated_gate: float = 0.95,
    active_event_eps: float = 0.0,
) -> dict[str, float]:
    """Return sparsity / stability / gate-engagement metrics from a layer output.

    Shapes: ``[T]`` (single neuron) or ``[T, N]`` / ``[T, B, N]`` (population). Neuron axes are
    flattened; time is axis 0.
    """
    v = _np(out["voltage"])
    r = _np(out["reset_gate"])
    g = _np(out.get("conductance", np.zeros_like(v)))
    e = _np(out["events"])

    T = v.shape[0]
    duration = T * dt
    v2 = v.reshape(T, -1)
    r2 = r.reshape(T, -1)
    g2 = g.reshape(T, -1)
    e2 = (e.reshape(T, -1) > active_event_eps).astype(float)
    n_neurons = v2.shape[1]

    events_per_neuron = e2.sum(axis=0)            # [N]
    rate_hz = events_per_neuron / max(duration, 1e-12)
    mean_v = v2.mean(axis=0)                       # [N]
    gate_per_neuron_mean = r2.mean(axis=0)         # [N]

    active = (events_per_neuron > 0) | (r2.max(axis=0) > 0.05)
    return {
        "events_per_sample": float(events_per_neuron.sum() / max(n_neurons, 1)),
        "spike_rate_mean": float(rate_hz.mean()),
        "spike_rate_std": float(rate_hz.std()),
        "active_neuron_fraction": float(active.mean()),
        "dead_neuron_fraction": float((~active).mean()),
        "saturated_fraction": float((r2 > saturated_gate).mean()),
        "gate_mean": float(r2.mean()),
        "gate_std": float(r2.std()),
        "gate_neuron_mean_max": float(gate_per_neuron_mean.max()) if n_neurons else 0.0,
        "conductance_mean": float(g2.mean()),
        "voltage_min": float(v2.min()),
        "voltage_max": float(v2.max()),
        "voltage_range": float(v2.max() - v2.min()),
        # audit-style stability check: any neuron whose mean |v| left the operating window
        "outside_operating_fraction": float((np.abs(mean_v) >= operating_voltage_limit).mean()),
        "nan_count": int(np.isnan(v2).sum() + np.isnan(r2).sum()),
    }
