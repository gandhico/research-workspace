"""HyperLIF / Adaptive HyperLIF as snnTorch neurons (Line B: event-vision, HPC-bound).

An independent re-implementation inside the snnTorch framework — subclasses ``snntorch.SpikingNeuron``
so it interoperates with snnTorch pipelines/utilities and uses an snnTorch surrogate for threshold
occupancy.  The forward observable is ``1[v >= threshold]``, not an upward-crossing detector.
HyperLIF has a *continuous* gate-controlled reset (no hard reset), so we fully override ``forward``
with the validated stable step and carry two states ``(v, r)``. Parity-checked to machine precision
against the same reference as the native PyTorch neuron (``scripts/run_parity_snntorch.py``).

The lightweight PLIF and ALIF cells below are not part of the HyperLIF parity path. They provide
reviewer-facing contemporary baselines for the same snnTorch/HPC architecture harness.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
from snntorch import SpikingNeuron, surrogate


class HyperLIFsnn(SpikingNeuron):
    def __init__(self, model="hyperlif", dt=1e-3, tau=0.02, tau_r=0.002, alpha=100.0, gamma=0.2,
                 v_rest=0.0, v_thresh=1.0, v_reset=0.0, reset_gain=100.0, base_gain=20.0,
                 gain_scaling=80.0, min_voltage=0.0, event_threshold=1.0, amplitude=1.0,
                 delta_reset=0.0, spike_grad=None):
        super().__init__(threshold=event_threshold,
                         spike_grad=spike_grad or surrogate.fast_sigmoid(slope=25.0),
                         reset_mechanism="subtract")  # stored only; forward overrides reset
        self.model = model
        self.dt = float(dt)
        self.tau, self.tau_r, self.alpha, self.gamma = tau, tau_r, alpha, gamma
        self.v_rest, self.v_thresh, self.v_reset = v_rest, v_thresh, v_reset
        self.reset_gain, self.base_gain, self.gain_scaling = reset_gain, base_gain, gain_scaling
        self.min_voltage, self.amplitude, self.delta_reset = min_voltage, amplitude, delta_reset
        self.gate_decay = math.exp(-self.dt / tau_r)

    def init_hyperlif(self, shape, device="cpu", dtype=torch.float32):
        return (torch.full(tuple(shape), self.v_rest, dtype=dtype, device=device),
                torch.zeros(tuple(shape), dtype=dtype, device=device))

    def forward(self, input_, v, r):
        eff = self.v_thresh - self.gamma * r
        target = torch.sigmoid(torch.clamp(self.alpha * (v - eff), -700.0, 700.0))
        r = torch.clamp(target + (r - target) * self.gate_decay, 0.0, 1.0)
        if self.model == "adaptive_hyperlif":
            g = (self.base_gain + self.gain_scaling * input_.abs()) * r**2
        else:
            g = self.reset_gain * r**2
        v_reset_eff = self.v_reset - self.delta_reset * r
        lam = 1.0 / self.tau + g
        drive = self.v_rest / self.tau + input_ / self.tau + g * v_reset_eff
        decay = torch.exp(-lam * self.dt)
        v = v * decay + (drive / lam) * (1.0 - decay)
        if math.isfinite(self.min_voltage):
            v = torch.clamp_min(v, self.min_voltage)
        # Historical architecture semantics: threshold occupancy at each time
        # sample.  This can remain one for consecutive samples and therefore
        # must not be interpreted as an upward-crossing spike count.
        spk = self.spike_grad(v - self.threshold)
        return spk, v, r


class PLIFsnn(SpikingNeuron):
    """Parametric LIF baseline with a learned membrane decay ``beta``.

    This keeps the snnTorch current scaling used by ``snntorch.Leaky`` while adding the standard
    learnable-time-constant control requested by modern SNN baseline comparisons.
    """

    def __init__(self, beta=0.95, threshold=1.0, beta_min=0.50, beta_max=0.995, spike_grad=None):
        super().__init__(threshold=threshold,
                         spike_grad=spike_grad or surrogate.fast_sigmoid(slope=25.0),
                         reset_mechanism="subtract")
        self.model = "plif"
        self.beta_min = float(beta_min)
        self.beta_max = float(beta_max)
        beta = min(max(float(beta), self.beta_min + 1e-6), self.beta_max - 1e-6)
        scaled = (beta - self.beta_min) / (self.beta_max - self.beta_min)
        self.logit_beta = nn.Parameter(torch.logit(torch.tensor(scaled, dtype=torch.float32)))

    @property
    def beta(self):
        return self.beta_min + (self.beta_max - self.beta_min) * torch.sigmoid(self.logit_beta)

    def init_plif(self, shape, device="cpu", dtype=torch.float32):
        return torch.zeros(tuple(shape), dtype=dtype, device=device)

    def forward(self, input_, mem):
        beta = self.beta.to(dtype=input_.dtype, device=input_.device)
        mem_pre = beta * mem + input_
        spk = self.spike_grad(mem_pre - self.threshold)
        mem = mem_pre - spk * self.threshold
        return spk, mem


class ALIFsnn(SpikingNeuron):
    """Adaptive-threshold LIF / LSNN-style baseline for the snnTorch architecture harness."""

    def __init__(self, dt=1e-3, beta=0.95, threshold=1.0, tau_a=0.2, beta_a=1.6,
                 spike_grad=None):
        super().__init__(threshold=threshold,
                         spike_grad=spike_grad or surrogate.fast_sigmoid(slope=25.0),
                         reset_mechanism="subtract")
        self.model = "alif"
        self.dt = float(dt)
        self.beta = float(beta)
        self.tau_a = float(tau_a)
        self.beta_a = float(beta_a)
        self.adapt_decay = math.exp(-self.dt / self.tau_a)

    def init_alif(self, shape, device="cpu", dtype=torch.float32):
        z = torch.zeros(tuple(shape), dtype=dtype, device=device)
        return z.clone(), z.clone()

    def forward(self, input_, mem, adapt):
        theta = self.threshold + self.beta_a * adapt
        mem_pre = self.beta * mem + input_
        spk = self.spike_grad(mem_pre - theta)
        mem = mem_pre - spk * theta
        adapt = self.adapt_decay * adapt + spk
        return spk, mem, adapt


@torch.no_grad()
def simulate_snntorch(current, dt, *, model="hyperlif", dtype=torch.float64, **kw):
    """Run a 1-D current trace through the snnTorch HyperLIF; returns numpy v/r/events (parity)."""
    neuron = HyperLIFsnn(model=model, dt=dt, **kw)
    J = torch.as_tensor(current, dtype=dtype).reshape(-1, 1)
    v, r = neuron.init_hyperlif((1,), dtype=dtype)
    vs, rs, es = [], [], []
    thr = neuron.threshold if not torch.is_tensor(neuron.threshold) else float(neuron.threshold)
    v_prev = v.clone()
    for t in range(J.shape[0]):
        _, v, r = neuron(J[t], v, r)
        crossed = (v_prev < thr) & (v >= thr)
        es.append(float(crossed.item()) * (neuron.amplitude / dt))
        vs.append(v.item()); rs.append(r.item())
        v_prev = v.clone()
    import numpy as np
    return {"voltage": np.array(vs), "reset_gate": np.array(rs), "events": np.array(es)}
