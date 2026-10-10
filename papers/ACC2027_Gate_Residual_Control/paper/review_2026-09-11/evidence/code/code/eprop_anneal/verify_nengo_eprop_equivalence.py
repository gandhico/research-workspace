"""Verify NengoEpropAnnealAugmentor matches the frozen numpy LearnedGate
(elig=True, anneal=True) eligibility-trace update to high precision, on
random synthetic inputs, before trusting any closed-loop MuJoCo result.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


# --- portable paths (added for distribution) ---
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import LEGACY_P3  # noqa: E402

sys.path.insert(0, str(LEGACY_P3 / "experiments" / "controller_benchmarks"))
from neuron_dynamics import make_direct_neuron  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nengo_eprop_anneal import NengoEpropAnnealAugmentor  # noqa: E402

CHANNELS = 3
DT = 0.0005
SIM_TIME = 45.0
LR, K_ERR, K_RATE = 8e-4 * 2.0, 8.0, 0.0
STEPS = 3000
rng = np.random.default_rng(0)

limits = np.array([0.0005, 0.0006, 0.0004])  # ~ tau_limit scale used in the CF2 benchmark
W0 = np.concatenate([np.eye(CHANNELS), -np.eye(CHANNELS)], axis=1)

# --- numpy reference: exact copy of LearnedGate's encode+_update with elig+anneal ---
neuron = make_direct_neuron("hyperlif", n=6, activity_mode="gate", scale="control")
W = W0.copy()
e_trace = np.zeros(6)


def lr_now(t):
    return LR * (1.0 - 0.8 * np.clip(t / SIM_TIME, 0.0, 1.0))


def decay_now(t):
    return 0.98 - 0.48 * np.clip(t / SIM_TIME, 0.0, 1.0)


nengo_aug = NengoEpropAnnealAugmentor(CHANNELS, limits, DT, SIM_TIME, LR, K_ERR, K_RATE)

max_command_err, max_activity_err, max_weight_err = 0.0, 0.0, 0.0
for i in range(STEPS):
    t = i * DT
    axis_error = 0.6 * limits * np.sin(np.array([1.1, 1.7, 0.9]) * t + rng.normal(0, 0.02, 3))
    omega = 0.3 * np.sin(np.array([0.6, 1.2, 0.8]) * t)
    tau_pd = np.clip(-8.0 * axis_error - 0.0 * omega, -limits, limits)  # arbitrary PD-shaped input

    # numpy reference
    tau_norm = np.clip(np.divide(tau_pd, limits, out=np.zeros_like(tau_pd), where=np.abs(limits) > 1e-12), -1, 1)
    currents = np.zeros(6)
    currents[0:3] = 0.75 + 1.25 * np.maximum(tau_norm, 0.0)
    currents[3:6] = 0.75 + 1.25 * np.maximum(-tau_norm, 0.0)
    res = neuron.step(currents, DT)
    activity_np = np.clip(res.activity * 1e5, 0.0, 1.0)
    signed_np = np.clip(W @ activity_np, -1.0, 1.0)
    tau_neuron_np = signed_np * limits
    tau_np = np.clip(0.5 * tau_pd + 0.5 * tau_neuron_np, -limits, limits)

    target = np.clip(-K_ERR * axis_error - K_RATE * omega, -1.0, 1.0)
    e_dec = target - signed_np
    decay = decay_now(t)
    e_trace = decay * e_trace + (1.0 - decay) * activity_np
    W += lr_now(t) * np.outer(e_dec, e_trace)
    np.clip(W, -6.0, 6.0, out=W)

    # nengo
    out = nengo_aug.step(t, axis_error, tau_pd, omega)

    max_command_err = max(max_command_err, np.max(np.abs(tau_np - out.command)))
    max_activity_err = max(max_activity_err, np.max(np.abs(activity_np - out.activity)))
    max_weight_err = max(max_weight_err, np.max(np.abs(W - nengo_aug._weights)))

print(f"steps={STEPS}")
print(f"max |command_np - command_nengo|  = {max_command_err:.3e}  (limits scale ~{np.max(limits):.2e})")
print(f"max |activity_np - activity_nengo| = {max_activity_err:.3e}")
print(f"max |W_np - W_nengo| = {max_weight_err:.3e}")
rel = max_command_err / np.max(limits)
print(f"relative command error = {rel:.3e}  ({'PASS' if rel < 1e-4 else 'FAIL'} vs 1e-4 threshold)")
nengo_aug.close()
