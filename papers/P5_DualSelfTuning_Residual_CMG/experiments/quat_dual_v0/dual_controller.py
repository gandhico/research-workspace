"""Dual CMG controller: PES self-tuned PID gains (S) plus bounded CMG-PES residual (R).

Mathematics: docs/ARCHITECTURE_MATH.md (v0, 2026-09-12). The CMG units and the
residual augmentor are imported read-only from the ACC 2027 repository
(gra_control.gate), so both layers use exactly the canonical CMG dynamics.

Layout of the 9 tuner channels (S): index = gain * 3 + axis, gains ordered
(p, i, d), axes (x, y, z). Inputs use the same 9-slot layout: normalized
e_q, omega, and low-passed e_q.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gra_control.gate import CMGConfig, CoupledMembraneGateBank


@dataclass
class TunerConfig:
    beta_p: float = 0.5
    beta_i: float = 0.5
    beta_d: float = 0.5
    e_ref: float = 0.1        # rad
    w_ref: float = 1.0        # rad/s
    kappa_d: float = 1.0
    tau_lp: float = 1.0       # s
    learning_rate: float = 1e-4
    leak: float = 1e-6
    w_max: float = 6.0
    freeze_on_sat: bool = False   # v1 (st_pid_f/dual_f): retreat p,i targets to 0 while saturated
    v2_gating: bool = False       # v2: authority + local-validity gating, damping floor (PLAN v2)
    e_gate: float = 0.25


class PIDBase:
    """Quaternion PID with conditional-integration anti-windup.

    u0 = sat_l(-Kp e_q - Ki xi - Kd omega); xi integrates e_q only on axes whose
    command is unsaturated. The integral used in u0 is the pre-update value,
    matching run_mujoco_nef_pid.py (ACC 2027 baseline study).
    """

    def __init__(self, limits: np.ndarray):
        self.limits = np.asarray(limits, dtype=float)
        self.xi = np.zeros(3)
        self.frozen_steps = np.zeros(3, dtype=int)

    def command(self, eq, omega, kp, ki, kd, dt):
        u_unsat = -kp * eq - ki * self.xi - kd * omega
        u = np.clip(u_unsat, -self.limits, self.limits)
        free = np.isclose(u, u_unsat, rtol=0.0, atol=1e-12)
        self.last_free = free
        self.xi += np.where(free, eq, 0.0) * dt
        self.frozen_steps += (~free).astype(int)
        return u


class SelfTuner:
    """CMG population S whose PES-learned decoder outputs bounded gain multipliers."""

    def __init__(self, cfg: TunerConfig, cmg: CMGConfig | None = None,
                 adaptive_conductance: bool = True):
        self.cfg = cfg
        self.cmg = cmg or CMGConfig()
        self.units = CoupledMembraneGateBank(18, adaptive_conductance, self.cmg)
        self.W = np.zeros((9, 18))                       # sigma = 0 -> nominal PID at t = 0
        self.e_lp = np.zeros(3)
        self.beta = np.repeat([cfg.beta_p, cfg.beta_i, cfg.beta_d], 3)
        self.last_sigma = np.zeros(9)
        self.last_target = np.zeros(9)
        self.last_activity = np.zeros(18)

    def targets(self, eq: np.ndarray, omega: np.ndarray) -> np.ndarray:
        c = self.cfg
        y_p = np.tanh(np.abs(eq) / c.e_ref)
        y_i = np.tanh(np.abs(self.e_lp) / c.e_ref)
        y_d = np.clip(c.kappa_d * (eq / c.e_ref) * (omega / c.w_ref), -1.0, 1.0)
        return np.concatenate([y_p, y_i, y_d])

    def step(self, eq: np.ndarray, omega: np.ndarray, dt: float, saturated: np.ndarray | None = None,
             headroom: float | None = None):
        c, p = self.cfg, self.cmg
        self.e_lp += (dt / c.tau_lp) * (eq - self.e_lp)
        x = np.clip(np.concatenate([eq / c.e_ref, omega / c.w_ref, self.e_lp / c.e_ref]), -1.0, 1.0)
        current = np.concatenate([
            p.current_bias + p.current_gain * np.maximum(x, 0.0),
            p.current_bias + p.current_gain * np.maximum(-x, 0.0),
        ])
        gate = self.units.step(current, dt)
        a = np.clip(p.gate_gain * gate, 0.0, 1.0)
        sigma = np.clip(self.W @ a, -1.0, 1.0)            # pre-update decoder, as in R
        y = self.targets(eq, omega)
        if c.freeze_on_sat and saturated is not None:
            retreat = np.concatenate([saturated, saturated, np.zeros(3, dtype=bool)])
            y = np.where(retreat, 0.0, y)
        if c.v2_gating:
            h = 1.0 if headroom is None else float(headroom)
            g = h * (np.abs(eq) < c.e_gate)
            y = np.concatenate([y[0:3] * g, y[3:6] * g, np.clip(y[6:9], 0.0, 1.0) * h])
        self.W += c.learning_rate * np.outer(y - sigma, a) - c.leak * self.W
        np.clip(self.W, -c.w_max, c.w_max, out=self.W)
        if c.v2_gating:
            sigma = np.concatenate([sigma[0:6], np.maximum(sigma[6:9], 0.0)])   # damping floor m_d >= 1
        mult = 1.0 + self.beta * sigma
        self.last_sigma, self.last_target, self.last_activity = sigma, y, a
        return mult[0:3], mult[3:6], mult[6:9]


@dataclass
class STNConfig:
    """CMG analogue of STN-PID-PES (Olivares et al., NCA 38:192, 2026); docs §6a-6b."""
    bounded: bool = True
    mu_p: float = 5e-5            # per step; 0.1/s at unit normalized excitation
    mu_i: float = 5e-5
    mu_d: float = 5e-5
    e_ref: float = 0.1            # half-angle error units (e_q)
    w_ref: float = 1.0            # rad/s
    xi_ref: float = 0.1           # e_q integral units (rad s)
    tau_syn: float = 0.05         # synaptic tau for the (tau, 2 tau) derivative
    kappa_s: float = 1.0
    sens_learning_rate: float = 8e-4
    sens_leak: float = 1e-6
    du_deadband: float = 1e-3     # skip the singular set |du/l| < deadband
    m_min: float = 0.5
    m_max: float = 1.5
    leak_m: float = 5e-5          # per step toward m = 1 (10 s time constant)
    w_max: float = 6.0
    known_sign: bool = False      # post-smoke ablation: Yhat = +1 (open-loop torque->attitude sign)
    v2_gating: bool = False       # v2: authority + local-validity gating, damping floor (PLAN v2)
    e_gate: float = 0.25
    retreat_tau: float = 1.0      # s, p/i retreat to nominal while |e| >= e_gate
    dither_id: bool = False       # v3: sensitivity target from lock-in demodulated torque dither (§7.2)
    dither_amp: float = 0.02      # fraction of l
    dither_freq: tuple = (9.0, 11.0, 13.0)   # Hz, roll/pitch/yaw
    tau_demod: float = 0.5        # s


class STNSelfTuner:
    """MIT-rule gradient gain adaptation with a CMG-PES learned plant sensitivity.

    Paper-form error eps = -e_q (passive quaternion convention), derivative channel
    signal -omega, integral channel int(eps) = -xi. Gradients (normalized):
        dm_p = mu_p (eps/e_ref)^2 Yhat
        dm_d = mu_d (eps/e_ref)(-omega/w_ref) Yhat
        dm_i = mu_i (eps/e_ref)(int eps/xi_ref) Yhat
    Yhat ~ dtheta/du is learned by PES on six paired CMG units from X = du/l, with
    target Y = clip(kappa (omega_tau/w_ref)/(du/l)), du from synaptic (tau, 2 tau)
    filters as in the paper. bounded=False is the faithful unbounded law.
    """

    def __init__(self, cfg: STNConfig, limits: np.ndarray, cmg: CMGConfig | None = None,
                 inertia: np.ndarray | None = None):
        self.cfg = cfg
        self.cmg = cmg or CMGConfig()
        self.limits = np.asarray(limits, dtype=float)
        self.inertia = None if inertia is None else np.asarray(inertia, dtype=float)
        self.z_demod = np.zeros(3)
        self.last_s_hat = np.zeros(3)
        self.w_dither = 2.0 * np.pi * np.asarray(cfg.dither_freq, dtype=float)
        self.units = CoupledMembraneGateBank(6, True, self.cmg)
        self.Ws = np.zeros((3, 6))
        self.u_tau = np.zeros(3)
        self.u_2tau = np.zeros(3)
        self.w_tau = np.zeros(3)
        self.m = np.ones(9)
        self.last_yhat = np.zeros(3)
        self.valid_steps = np.zeros(3, dtype=int)
        self.blocked_steps = np.zeros(3, dtype=int)

    def dither(self, t: float) -> np.ndarray:
        """Torque dither d_i = a l_i sin(w_i t) (zero unless dither_id)."""
        if not self.cfg.dither_id:
            return np.zeros(3)
        return self.cfg.dither_amp * self.limits * np.sin(self.w_dither * t)

    def step(self, eq, omega, xi_int, u_prev, saturated, dt, headroom: float | None = None,
             t_now: float | None = None):
        c, p = self.cfg, self.cmg
        self.u_tau += (dt / c.tau_syn) * (u_prev - self.u_tau)
        self.u_2tau += (dt / (2.0 * c.tau_syn)) * (u_prev - self.u_2tau)
        self.w_tau += (dt / c.tau_syn) * (omega - self.w_tau)
        du_n = (self.u_tau - self.u_2tau) / c.tau_syn / self.limits

        x = np.clip(du_n, -1.0, 1.0)
        current = np.concatenate([
            p.current_bias + p.current_gain * np.maximum(x, 0.0),
            p.current_bias + p.current_gain * np.maximum(-x, 0.0),
        ])
        gate = self.units.step(current, dt)
        a = np.clip(p.gate_gain * gate, 0.0, 1.0)
        yhat = np.clip(self.Ws @ a, -1.0, 1.0)

        if c.dither_id:
            self.z_demod += (dt / c.tau_demod) * (omega * np.cos(self.w_dither * t_now) - self.z_demod)
            s_hat = -2.0 * self.inertia * self.w_dither * self.z_demod / (c.dither_amp * self.limits)
            self.last_s_hat = s_hat
            valid = np.ones(3, dtype=bool)
            target = np.clip(c.kappa_s * s_hat, -1.0, 1.0)
        else:
            valid = np.abs(du_n) > c.du_deadband
            ratio = np.divide(self.w_tau / c.w_ref, du_n, out=np.zeros(3), where=valid)
            target = np.clip(c.kappa_s * ratio, -1.0, 1.0)
        err = np.where(valid, target - yhat, 0.0)
        self.Ws += c.sens_learning_rate * np.outer(err, a) - c.sens_leak * self.Ws
        np.clip(self.Ws, -c.w_max, c.w_max, out=self.Ws)
        self.valid_steps += valid.astype(int)
        if c.known_sign:
            yhat = np.ones(3)

        eps = -eq
        g_p = (eps / c.e_ref) ** 2 * yhat
        g_i = (eps / c.e_ref) * ((-xi_int) / c.xi_ref) * yhat
        g_d = (eps / c.e_ref) * ((-omega) / c.w_ref) * yhat
        dm = np.concatenate([c.mu_p * g_p, c.mu_i * g_i, c.mu_d * g_d])
        if c.bounded:
            if saturated is not None:
                blocked = np.concatenate([saturated, saturated, np.zeros(3, dtype=bool)])
                self.blocked_steps += (saturated & ((dm[0:3] > 0) | (dm[3:6] > 0))).astype(int)
                dm = np.where(blocked, np.minimum(dm, 0.0), dm)
            if c.v2_gating:
                h = 1.0 if headroom is None else float(headroom)
                valid = np.abs(eq) < c.e_gate
                g = np.concatenate([h * valid, h * valid, np.full(3, h)])
                dm = np.where(dm > 0.0, dm * g, dm)
                large = np.concatenate([~valid, ~valid, np.zeros(3, dtype=bool)])
                dm = dm - np.where(large, (dt / c.retreat_tau) * (self.m - 1.0), 0.0)
            self.m += dm - c.leak_m * (self.m - 1.0)
            np.clip(self.m, c.m_min, c.m_max, out=self.m)
            if c.v2_gating:
                np.clip(self.m[6:9], 1.0, c.m_max, out=self.m[6:9])          # damping floor
        else:
            self.m += dm
        self.last_yhat = yhat
        return self.m[0:3].copy(), self.m[3:6].copy(), self.m[6:9].copy()


@dataclass
class IDGCConfig:
    """v4 identification-based gain correction (PLAN v4 declaration)."""
    dither_amp: float = 0.02      # fraction of l
    dither_freq: tuple = (9.0, 11.0, 13.0)   # Hz, roll/pitch/yaw
    tau_demod: float = 0.5        # s
    warmup_s: float = 3.0
    tau_id: float = 5.0           # s
    m_lo: float = 0.33
    m_hi: float = 3.0


class IDGainCorrector:
    """Per-axis gain multiplier m -> clip(1/s_hat) with s_hat = j_tune/J from the torque-dither lock-in (§7.2).

    s_hat = -2 j_tune w z / (a l), z = LPF(omega cos wt). All three PID gains share m (k_q, k_w, k_i ~ j).
    Increases are scaled by rotor headroom h; s_hat <= 0 (wrong sign, unconverged) holds m.
    """

    def __init__(self, cfg: IDGCConfig, limits: np.ndarray, inertia: np.ndarray):
        self.cfg = cfg
        self.limits = np.asarray(limits, dtype=float)
        self.inertia = np.asarray(inertia, dtype=float)
        self.w = 2.0 * np.pi * np.asarray(cfg.dither_freq, dtype=float)
        self.z = np.zeros(3)
        self.m = np.ones(3)
        self.last_s_hat = np.zeros(3)
        self.held_steps = np.zeros(3, dtype=int)

    def dither(self, t: float) -> np.ndarray:
        return self.cfg.dither_amp * self.limits * np.sin(self.w * t)

    def step(self, omega: np.ndarray, t: float, dt: float, headroom: float = 1.0) -> np.ndarray:
        c = self.cfg
        self.z += (dt / c.tau_demod) * (omega * np.cos(self.w * t) - self.z)
        s_hat = -2.0 * self.inertia * self.w * self.z / (c.dither_amp * self.limits)
        self.last_s_hat = s_hat
        if t >= c.warmup_s:
            ok = s_hat > 0.0
            target = np.clip(np.divide(1.0, s_hat, out=np.ones(3), where=ok), c.m_lo, c.m_hi)
            dm = np.where(ok, (dt / c.tau_id) * (target - self.m), 0.0)
            dm = np.where(dm > 0.0, float(headroom) * dm, dm)
            self.m = np.clip(self.m + dm, c.m_lo, c.m_hi)
            self.held_steps += (~ok).astype(int)
        return self.m.copy()
