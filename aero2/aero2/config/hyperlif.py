"""Adaptive HyperLIF constants (survey: docs/10_neuromorphic_hyperlif.md).

Neuron presets are the control-scale parameters from the gate-residual repo
(`neuron_dynamics.py` _CONTROL_SCALE_PARAMS). Residual defaults are the published
best gate-mode configuration. These are EXPERIMENTAL (no Aero2 HyperLIF results
exist yet); the classical pipeline is unaffected.
"""
from __future__ import annotations

# --- neuron model (Adaptive HyperLIF paper; control-scale presets) ---------
NEURON_ALPHA: float = 50.0          # gate sigmoid steepness
NEURON_V_THRESH: float = 1.0
NEURON_V_RESET: float = 0.0
NEURON_V_REST: float = 0.0

#: scale="control" overrides (fast loops); scale="paper" uses class defaults
NEURON_PRESETS = {
    "standard_lif":      dict(tau=0.05, v_thresh=1.0, v_reset=0.0),
    "hyperlif":          dict(tau=0.05, tau_r=0.005, reset_gain=120.0, gamma=2.0, event_threshold=0.5),
    "adaptive_hyperlif": dict(tau=0.05, tau_r=0.005, base_gain=120.0, gain_scaling=30.0, gamma=2.0, event_threshold=0.5),
}

# --- PD + gate-state residual controller (published-best gate config) -------
RESIDUAL_NEURON: str = "adaptive_hyperlif"
RESIDUAL_BLEND: float = 0.5          # tau = (1-blend)*u_pd + blend*u_neural
RESIDUAL_GATE_GAIN: float = 1.0e5    # gate-mode amplification
RESIDUAL_ACTIVITY_MODE: str = "gate"
RESIDUAL_SCALE: str = "control"
RESIDUAL_CURRENT_BIAS: float = 0.75
RESIDUAL_CURRENT_GAIN: float = 1.25

# --- Gate-state residual augmented controller (MuJoCo-quadrotor architecture) --
# Faithful port of experiments/hyperlif_aug_benchmark/hyperlif_aug_1d.py
# (SimpleCustomNeuron1D). Per-axis gate neuron sees the error feature
# x = error - K_OMEGA*omega; gate-state output y = gate*sign(out) is added as a
# DIRECTION-SAFE residual (or modulates the PD gain). `adaptive` adds a slow
# adaptation state `a` (adaptive gains); `fixed` omits it.
GATE_RES_TAU_V: float = 0.02        # membrane time constant [s]
GATE_RES_TAU_A: float = 0.20        # adaptation time constant [s] (adaptive only)
GATE_RES_A_GAIN: float = 0.25       # adaptation drive from |output|
GATE_RES_INPUT_GAIN: float = 4.0    # tanh(INPUT_GAIN * x) membrane drive
GATE_RES_GATE_ALPHA: float = 20.0   # gate sigmoid steepness on |v|
GATE_RES_GATE_THRESH: float = 0.03  # gate threshold on |v|
GATE_RES_OUT_GAIN: float = 5.0      # tanh(OUT_GAIN * v) output
GATE_RES_K_OMEGA: float = 0.05      # error feature: x = error - K_OMEGA*omega
GATE_RES_BLEND: float = 0.10        # residual/gain blend weight
GATE_RES_SCALE: float = 1.0         # residual/gain scale
GATE_RES_NEURON: str = "adaptive_hyperlif"   # "hyperlif" (fixed) | "adaptive_hyperlif"
GATE_RES_AUG: str = "residual"      # "residual" | "gain"

# --- neuromorphic identifier (HyperLIF reservoir + linear readout) ----------
# Reservoir-computing baseline (fully Python); full e-prop/APEX learning is Julia (future).
ID_RESERVOIR_SIZE: int = 120
ID_RESERVOIR_NEURON: str = "adaptive_hyperlif"
ID_INPUT_GAIN: float = 0.8
ID_INPUT_BIAS: float = 1.0
ID_RIDGE: float = 1e-2               # ridge regularization for the readout
ID_SEED: int = 0

# --- e-prop training (Python replica of the Julia gate-eligibility learning) ---
# Paper-scale neuron (AdaptiveHyperLIF/.../METHODS.md default_params).
EPROP_TAU: float = 10.0
EPROP_TAU_R: float = 0.2
EPROP_ALPHA: float = 50.0            # gate steepness (sharp; gate_exact factor)
EPROP_GAMMA: float = 3.0
EPROP_G_BASE: float = 800.0
EPROP_BETA: float = 100.0            # adaptive gain (DB-stability rule)
EPROP_DT: float = 0.5
EPROP_TAU_TRACE: float = 5.0         # pre-synaptic eligibility trace
EPROP_ALPHA_SURROGATE: float = 2.0   # wide heuristic surrogate (alpha_learn)

__all__ = [
    "NEURON_ALPHA", "NEURON_V_THRESH", "NEURON_V_RESET", "NEURON_V_REST", "NEURON_PRESETS",
    "RESIDUAL_NEURON", "RESIDUAL_BLEND", "RESIDUAL_GATE_GAIN", "RESIDUAL_ACTIVITY_MODE",
    "RESIDUAL_SCALE", "RESIDUAL_CURRENT_BIAS", "RESIDUAL_CURRENT_GAIN",
    "ID_RESERVOIR_SIZE", "ID_RESERVOIR_NEURON", "ID_INPUT_GAIN", "ID_INPUT_BIAS", "ID_RIDGE", "ID_SEED",
]
