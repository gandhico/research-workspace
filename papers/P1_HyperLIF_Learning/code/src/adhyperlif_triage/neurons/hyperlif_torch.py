"""PyTorch neuron roster: LIF, ALIF, HyperLIF, Adaptive HyperLIF (+ origin, + adaptive theta).

Design contract
---------------
* The continuous ``(v, r)`` dynamics of HyperLIF / Adaptive HyperLIF use the **same** exact stable
  stepping as the validated reference (:mod:`reference_numpy`). In float64 with no autograd this
  reproduces the reference to machine precision -- the parity gate (``scripts/run_parity.py``).
  Nothing in this file changes that default path, so parity is preserved.
* The smooth ``v``/``r`` path is differentiable; the only non-differentiable piece is the
  event/threshold crossing, which gets a fast-sigmoid surrogate gradient (allowed for HyperLIF).
* Roster additions for the benchmark:
    - ``lif``   : surrogate-gradient LIF (the trainable standard baseline / honest "original").
    - ``alif``  : adaptive-threshold LIF (Bellec-style) -- the standard adaptive baseline.
    - adaptive ``theta_event`` overlay (thread 4): a homeostatic *readout* threshold that leaves
      the ``v``/``r`` dynamics untouched (so parity still holds). ``adaptive_theta=False`` default.
    - origin (idea 1): gate-coupled reset ``v_reset_eff = v_reset - delta_reset*r`` (``0`` => ref).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import torch
import torch.nn as nn


@dataclass
class HyperLIFConfig:
    model: str = "hyperlif"  # "lif" | "alif" | "hyperlif" | "adaptive_hyperlif"
    tau: float = 0.02
    v_rest: float = 0.0
    v_thresh: float = 1.0
    v_reset: float = 0.0
    alpha: float = 100.0
    reset_gain: float = 100.0      # HyperLIF fixed gain
    base_gain: float = 20.0        # Adaptive: G_base
    gain_scaling: float = 80.0     # Adaptive: beta
    tau_r: float = 0.002
    gamma: float = 0.2             # threshold hysteresis
    amplitude: float = 1.0
    min_voltage: float = 0.0
    event_threshold: float = 1.0
    tau_ref: float = 0.0
    lif_reset_mode: str = "subtract"   # "subtract" (default) | "to_reset" (origin-capable AHP)
    # --- idea 1: the origin (inert by default => exact reference) ---
    delta_reset: float = 0.0       # v_reset_eff = v_reset - delta_reset*r
    # --- ALIF baseline (adaptive spike threshold) ---
    tau_a: float = 0.2             # adaptation time constant
    beta_a: float = 1.6            # threshold increment scale
    # --- thread 4: adaptive event/readout threshold (overlay; dynamics untouched) ---
    adaptive_theta: bool = False
    theta_base: float = 0.99
    target_rate_hz: float = 60.0
    theta_error_gain: float = 0.002
    theta_spike: float = 0.0005
    tau_theta: float = 0.20
    activity_tau: float = 0.025
    theta_min: float = 0.90
    theta_max: float = 1.00
    # --- surrogate gradient slope for spike/event crossings ---
    surrogate_beta: float = 10.0

    def to_dict(self) -> dict:
        return asdict(self)


def _sigmoid(x: torch.Tensor) -> torch.Tensor:
    """Numerically stable logistic gate, clamped to the reference's [-700, 700] domain.

    ``torch.sigmoid`` matches the reference ``1/(1+exp(-x))`` forward to ~1e-15 (parity holds) but,
    unlike the literal form, is stable in backward (no ``0*inf -> nan`` in float32 at alpha=100).
    """
    return torch.sigmoid(torch.clamp(x, -700.0, 700.0))


class _SurrogateEvent(torch.autograd.Function):
    """Upward crossing ``[v_prev < thr <= v_next]``; fast-sigmoid surrogate grad wrt ``v_next``."""

    @staticmethod
    def forward(ctx, v_prev, v_next, threshold, beta):
        ctx.save_for_backward(v_next - threshold)
        ctx.beta = float(beta)
        crossed = (v_prev < threshold) & (v_next >= threshold)
        return crossed.to(v_next.dtype)

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        surr = ctx.beta / (1.0 + ctx.beta * x.abs()) ** 2
        return None, grad_out * surr, None, None


class _SpikeFn(torch.autograd.Function):
    """Heaviside ``[x >= 0]`` with a fast-sigmoid surrogate gradient (LIF / ALIF spikes)."""

    @staticmethod
    def forward(ctx, x, beta):
        ctx.save_for_backward(x)
        ctx.beta = float(beta)
        return (x >= 0).to(x.dtype)

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        surr = ctx.beta / (1.0 + ctx.beta * x.abs()) ** 2
        return grad_out * surr, None


# --------------------------------------------------------------------------------------------
# Single-step functions
# --------------------------------------------------------------------------------------------
def hyperlif_step(v, r, J, cfg: HyperLIFConfig, dt: float, event_threshold=None):
    """One exact stable HyperLIF / Adaptive HyperLIF step. ``event_threshold`` may be a tensor
    (adaptive theta); ``None`` uses the scalar ``cfg.event_threshold`` (the parity default)."""
    v_prev = v
    eff_thresh = cfg.v_thresh - cfg.gamma * r
    target = _sigmoid(cfg.alpha * (v - eff_thresh))
    gate_decay = math.exp(-dt / cfg.tau_r)
    r_next = torch.clamp(target + (r - target) * gate_decay, 0.0, 1.0)

    if cfg.model == "adaptive_hyperlif":
        g = (cfg.base_gain + cfg.gain_scaling * J.abs()) * r_next**2
    else:
        g = cfg.reset_gain * r_next**2

    v_reset_eff = cfg.v_reset - cfg.delta_reset * r_next
    lam = 1.0 / cfg.tau + g
    drive = cfg.v_rest / cfg.tau + J / cfg.tau + g * v_reset_eff
    decay = torch.exp(-lam * dt)
    v_next = torch.where(lam > 1e-12, v * decay + (drive / lam) * (1.0 - decay), v + dt * drive)
    if math.isfinite(cfg.min_voltage):
        v_next = torch.clamp_min(v_next, cfg.min_voltage)

    thr = cfg.event_threshold if event_threshold is None else event_threshold
    event = _SurrogateEvent.apply(v_prev, v_next, thr, cfg.surrogate_beta) * (cfg.amplitude / dt)
    return v_next, r_next, g, event


def lif_surrogate_step(v, J, cfg: HyperLIFConfig, dt: float):
    """Trainable surrogate-gradient LIF. ``lif_reset_mode``:
    ``"subtract"`` (default) subtracts the threshold; ``"to_reset"`` resets to ``v_reset`` --
    the origin-capable mode (set ``v_reset < v_rest`` for a hyperpolarizing after-hyperpolarization)."""
    decay_v = math.exp(-dt / cfg.tau)
    v_pre = decay_v * v + (1.0 - decay_v) * J
    z = _SpikeFn.apply(v_pre - cfg.v_thresh, cfg.surrogate_beta)
    if cfg.lif_reset_mode == "to_reset":
        v_next = v_pre * (1.0 - z) + cfg.v_reset * z
    else:
        v_next = v_pre - z * cfg.v_thresh
    if math.isfinite(cfg.min_voltage):
        v_next = torch.clamp_min(v_next, cfg.min_voltage)
    return v_next, z * (cfg.amplitude / dt)


def alif_step(v, a, J, cfg: HyperLIFConfig, dt: float):
    """Adaptive-LIF (Bellec-style): threshold ``v_thresh + beta_a*a`` rises after each spike."""
    decay_v = math.exp(-dt / cfg.tau)
    decay_a = math.exp(-dt / cfg.tau_a)
    theta = cfg.v_thresh + cfg.beta_a * a
    v_pre = decay_v * v + (1.0 - decay_v) * J
    z = _SpikeFn.apply(v_pre - theta, cfg.surrogate_beta)
    v_next = v_pre - z * theta
    if math.isfinite(cfg.min_voltage):
        v_next = torch.clamp_min(v_next, cfg.min_voltage)
    a_next = decay_a * a + z
    return v_next, a_next, z * (cfg.amplitude / dt), theta


def lif_step(v, J, refr, cfg: HyperLIFConfig, dt: float):
    """Hard-reset LIF (utility / reference; non-trainable). Benchmark uses ``lif_surrogate_step``."""
    target = cfg.v_rest + J
    v_free = target + (v - target) * math.exp(-dt / cfg.tau)
    active = (refr <= 0.0).to(v.dtype)
    v_next = active * v_free + (1.0 - active) * cfg.v_reset
    crossed = (v_next >= cfg.v_thresh) & (refr <= 0.0)
    event = crossed.to(v.dtype) * (cfg.amplitude / dt)
    v_next = torch.where(crossed, torch.full_like(v_next, cfg.v_reset), v_next)
    if math.isfinite(cfg.min_voltage):
        v_next = torch.clamp_min(v_next, cfg.min_voltage)
    refr_next = torch.where(crossed, torch.full_like(refr, cfg.tau_ref), torch.clamp_min(refr - dt, 0.0))
    return v_next, refr_next, event


# --------------------------------------------------------------------------------------------
# Sequence layer
# --------------------------------------------------------------------------------------------
class HyperLIFLayer(nn.Module):
    """Scan a current sequence ``J [T, ...]`` through the chosen neuron model.

    Returns a dict of ``[T, ...]`` traces: ``voltage``, ``reset_gate``, ``conductance``,
    ``dynamic_gain``, ``events`` (+ ``theta_event`` when ``adaptive_theta``). Pure function of the
    input; learnable parameters live in the encoder/readout, not here.
    """

    def __init__(self, cfg: HyperLIFConfig | None = None):
        super().__init__()
        self.cfg = cfg or HyperLIFConfig()

    def forward(self, J: torch.Tensor, dt: float) -> dict[str, torch.Tensor]:
        cfg = self.cfg
        shape = J.shape[1:]
        dtype, device = J.dtype, J.device
        zeros = lambda: torch.zeros(shape, dtype=dtype, device=device)  # noqa: E731
        v = torch.full(shape, cfg.v_rest, dtype=dtype, device=device)
        r, a, refr = zeros(), zeros(), zeros()
        theta = torch.full(shape, float(cfg.event_threshold), dtype=dtype, device=device)
        filt_act = zeros()
        use_adaptive_theta = cfg.adaptive_theta and cfg.model in ("hyperlif", "adaptive_hyperlif")

        rec = {k: [] for k in ("voltage", "reset_gate", "conductance", "dynamic_gain", "events", "theta_event")}
        for t in range(J.shape[0]):
            Jt = J[t]
            if cfg.model == "lif":
                v, e = lif_surrogate_step(v, Jt, cfg, dt)
                rec["voltage"].append(v); rec["reset_gate"].append(zeros()); rec["conductance"].append(zeros())
                rec["dynamic_gain"].append(zeros()); rec["events"].append(e); rec["theta_event"].append(theta)
            elif cfg.model == "alif":
                v_prev = v
                v, a, e, th = alif_step(v, a, Jt, cfg, dt)
                rec["voltage"].append(v); rec["reset_gate"].append(a); rec["conductance"].append(zeros())
                rec["dynamic_gain"].append(th); rec["events"].append(e); rec["theta_event"].append(th)
            else:  # hyperlif / adaptive_hyperlif
                v_prev = v
                thr = theta if use_adaptive_theta else None
                v, r, g, e = hyperlif_step(v, r, Jt, cfg, dt, event_threshold=thr)
                dyn = (cfg.base_gain + cfg.gain_scaling * Jt.abs()) if cfg.model == "adaptive_hyperlif" else zeros()
                rec["voltage"].append(v); rec["reset_gate"].append(r); rec["conductance"].append(g)
                rec["dynamic_gain"].append(dyn); rec["events"].append(e); rec["theta_event"].append(theta)
                if use_adaptive_theta:  # homeostatic readout-threshold controller (detached)
                    with torch.no_grad():
                        adec = math.exp(-dt / cfg.activity_tau)
                        hard = ((v_prev < theta) & (v >= theta)).to(dtype)
                        filt_act = filt_act * adec + hard * (1.0 - adec) / dt
                        theta = theta + dt * ((cfg.theta_base - theta) / cfg.tau_theta
                                              - cfg.theta_error_gain * (cfg.target_rate_hz - filt_act)) \
                                + cfg.theta_spike * hard
                        theta = torch.clamp(theta, cfg.theta_min, cfg.theta_max)
        out = {k: torch.stack(val, dim=0) for k, val in rec.items() if val}
        return out


@torch.no_grad()
def simulate_torch(current, cfg: HyperLIFConfig, dt: float, dtype=torch.float64, device="cpu"):
    """Run a 1-D current trace and return numpy arrays (used by the parity gate)."""
    J = torch.as_tensor(current, dtype=dtype, device=device).reshape(-1, 1)
    out = HyperLIFLayer(cfg).forward(J, dt)
    return {k: v.reshape(-1).cpu().numpy() for k, v in out.items()}
