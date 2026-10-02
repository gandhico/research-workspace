"""Shared pieces for the architecture zoo — reuses the parity-validated neuron from project 07.

A neuron is a snnTorch module; we wrap LIF (snntorch.Leaky, 1 state) and HyperLIF/Adaptive
(HyperLIFsnn, 2 states v,r) behind a uniform (init_state, step) interface so any topology can swap
the neuron. PLIF and ALIF are reviewer-facing contemporary baselines; HyperLIFsnn remains the
parity-validated path. Readout assembly matches project 07 exactly (same 6 readouts, same feature
dims)."""
from __future__ import annotations

import sys
from pathlib import Path

import torch

# reuse the validated neuron from 07_AdHyperLIF_Triage (single source of truth)
_SEVEN = Path(__file__).resolve().parents[3] / "07_AdHyperLIF_Triage" / "src"
if _SEVEN.is_dir() and str(_SEVEN) not in sys.path:
    sys.path.insert(0, str(_SEVEN))

import snntorch  # noqa: E402
from snntorch import surrogate  # noqa: E402

from adhyperlif_triage.neurons.snntorch_hyperlif import ALIFsnn, HyperLIFsnn, PLIFsnn  # noqa: E402

READOUT_MULT = {"spike_count": 1, "membrane": 1, "gate": 1,
                "hybrid_gr": 2, "hybrid_vr": 2, "hybrid_vr_conductance": 3}
READOUTS = list(READOUT_MULT)
NEURONS = ["lif", "plif", "alif", "hyperlif", "adaptive"]

# Validated neuron variants (mirror project-07's roster). theta-event lowers the sampled occupancy
# threshold in this snnTorch architecture path
# -> denser firing (the fix for deep-HyperLIF starvation); origin lowers the reset anchor
# (static AHP v_reset<0, gate-coupled AHP delta_reset>0) with min_voltage=-2.0 so the hyperpolarizing
# reset is not clipped. cfg overrides HyperLIFsnn params.
NEURON_VARIANTS = {
    "lif":             ("lif", {}),
    "plif":            ("plif", {}),
    "alif":            ("alif", {}),
    "hyperlif":        ("hyperlif", {}),
    "hyperlif_t0.95":  ("hyperlif", dict(event_threshold=0.95)),
    "adaptive":        ("adaptive", {}),
    "adaptive_t0.95":  ("adaptive", dict(event_threshold=0.95)),
    "adaptive_origin": ("adaptive", dict(v_reset=-0.6, min_voltage=-2.0)),
    "adaptive_dreset": ("adaptive", dict(delta_reset=0.3, min_voltage=-2.0)),
}

# F -> (P, H, W) for the known vision caches (used by conv-SNN)
KNOWN_SENSOR = {2312: (2, 34, 34), 2048: (2, 32, 32), 4608: (2, 48, 48), 128: (2, 8, 8)}


def new_neuron(kind, dt=1e-3, beta=0.95, cfg=None):
    """Return (neuron_module, exposes_second_state).

    ``exposes_second_state`` marks neurons with a useful readout state in addition to voltage:
    HyperLIF/Adaptive expose the reset gate ``r`` and ALIF exposes its adaptive threshold state.
    cfg passes cell params — notably HyperLIF event_threshold/origin settings and ALIF adaptation
    constants. PLIF is one-state and uses a learnable membrane decay.
    """
    cfg = cfg or {}
    if kind == "lif":
        return snntorch.Leaky(beta=beta, spike_grad=surrogate.fast_sigmoid(slope=25.0)), False
    if kind == "plif":
        return PLIFsnn(beta=beta, **cfg), False
    if kind == "alif":
        return ALIFsnn(dt=dt, beta=beta, **cfg), True
    model = "adaptive_hyperlif" if kind == "adaptive" else "hyperlif"
    return HyperLIFsnn(model=model, dt=dt, **cfg), True


def init_state(neuron, exposes_second_state, shape, device, dtype):
    if getattr(neuron, "model", "") == "alif":
        return neuron.init_alif(shape, device, dtype)               # (mem, adapt)
    if getattr(neuron, "model", "") == "plif":
        return (neuron.init_plif(shape, device, dtype),)            # (mem,)
    if exposes_second_state:
        return neuron.init_hyperlif(shape, device, dtype)          # (v, r)
    return (torch.zeros(tuple(shape), device=device, dtype=dtype),)  # (mem,)


def step(neuron, exposes_second_state, cur, state):
    """One timestep. Returns spk, new_state, (v, second_state), act.

    ``act`` is the signal to PROPAGATE to a downstream layer: the hard spike for LIF, but the graded
    gate ``r`` for HyperLIF. HyperLIF's continuous gate is its natural output — its hard spikes are
    deliberately sparse and starve deep cascades, so propagating ``r`` uses each neuron as designed.
    (For HyperLIF, ``spk`` is historical threshold occupancy rather than an
    upward-crossing count; energy/event claims require a recomputed crossing
    observable.)"""
    if getattr(neuron, "model", "") == "alif":
        mem, adapt = state
        spk, mem, adapt = neuron(cur, mem, adapt)
        return spk, (mem, adapt), (mem, adapt), spk
    if exposes_second_state:
        v, r = state
        spk, v, r = neuron(cur, v, r)
        return spk, (v, r), (v, r), r
    (mem,) = state
    spk, mem = neuron(cur, mem)
    return spk, (mem,), (mem, torch.zeros_like(mem)), spk


def conductance(neuron, r, cur):
    if getattr(neuron, "model", "") == "alif":
        return torch.zeros_like(r)
    if getattr(neuron, "model", "") == "hyperlif":
        return neuron.reset_gain * r**2
    return (neuron.base_gain + neuron.gain_scaling * cur.abs()) * r**2


def assemble(readout, vbar, rbar, gbar, spk_sum):
    if readout == "spike_count":
        return spk_sum
    if readout == "membrane":
        return vbar
    if readout == "gate":
        return rbar
    if readout == "hybrid_gr":
        return torch.cat([rbar, gbar], dim=-1)
    if readout == "hybrid_vr":
        return torch.cat([vbar, rbar], dim=-1)
    return torch.cat([vbar, rbar, gbar], dim=-1)  # hybrid_vr_conductance
