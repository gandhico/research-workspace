"""Pair-coded gate-state residual encoder (prototype of the embodied-control mechanism).

Faithful to the quad paper's encoding (`01_HyperLIF_Gate_Residual` / `07_ServoPendulum`):

    I_pos = bias + input_gain * max(+tau_norm, 0)     # positive-demand channel current
    I_neg = bias + input_gain * max(-tau_norm, 0)     # negative-demand channel current
    r_pos, r_neg  <- HyperLIF gate dynamics on each channel
    delta = clip(gate_gain * (r_pos - r_neg), -1, 1)  # normalized residual torque

`gate_gain` sweeps the residual from **graded** (low gate_gain -> delta proportional to the gate
*values*) to **binary** (high gate_gain -> delta = sign, only the threshold crossing matters). The
team's open question: at high gate_gain the gate saturates so Adaptive == HyperLIF (beta inert); is
there a graded regime where the adaptive conductance (beta) and the **origin** (gate-coupled AHP,
our novel addition) actually shape the residual? The gate run is gate_gain-independent, so we run
each neuron once and apply all gate_gains to the cached gates.
"""

from __future__ import annotations

import numpy as np
import torch

from ..neurons import HyperLIFConfig
from ..neurons.hyperlif_torch import hyperlif_step


@torch.no_grad()
def run_gates(tau_norm, cfg: HyperLIFConfig, dt, bias=0.75, input_gain=1.25):
    """Run the two-channel HyperLIF on a demand sequence.
    Returns (r_pos, r_neg, g_pos, g_neg) — gate states and effective conductances [T]."""
    tn = torch.as_tensor(np.asarray(tau_norm), dtype=torch.float64)
    I = torch.zeros((len(tn), 2), dtype=torch.float64)
    I[:, 0] = bias + input_gain * tn.clamp_min(0.0)
    I[:, 1] = bias + input_gain * (-tn).clamp_min(0.0)
    v = torch.full((2,), cfg.v_rest, dtype=torch.float64)
    r = torch.zeros(2, dtype=torch.float64)
    rp, rn, gp, gn = [], [], [], []
    for t in range(I.shape[0]):
        v, r, g, _ = hyperlif_step(v, r, I[t], cfg, dt)
        rp.append(r[0].item()); rn.append(r[1].item())
        gp.append(g[0].item()); gn.append(g[1].item())
    return np.array(rp), np.array(rn), np.array(gp), np.array(gn)


def residual_from_gates(r_pos, r_neg, gate_gain):
    """Gate-state residual: reads the gate values r."""
    return np.clip(gate_gain * (r_pos - r_neg), -1.0, 1.0)


def residual_from_conductance(g_pos, g_neg, gate_gain, g_scale=120.0):
    """Conductance residual: reads G_eff = (G_base + beta|I|)*r^2, so beta + demand appear directly."""
    return np.clip(gate_gain * (g_pos - g_neg) / g_scale, -1.0, 1.0)


def demand_profile(dt, t_total=6.0, base=0.06, pulses=((1.2, +0.75, 0.18), (2.6, -0.65, 0.15),
                                                       (4.0, +0.85, 0.20), (5.0, -0.55, 0.12))):
    """Low baseline demand (dormant regime) + signed high-demand pulses (disturbances).
    Each pulse = (center_time_s, signed_peak, width_s). Returns tau_norm[T] in ~[-1, 1]."""
    n = int(t_total / dt)
    t = np.arange(n) * dt
    tn = np.full(n, base, dtype=np.float64)
    for tc, amp, w in pulses:
        tn = tn + amp * np.exp(-0.5 * ((t - tc) / w) ** 2)
    return np.clip(tn, -1.0, 1.0)
