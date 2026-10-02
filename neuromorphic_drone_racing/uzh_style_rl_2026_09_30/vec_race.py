"""Batched X2 racing simulator for UZH-style RL training (PyTorch, CPU). PyTorch only: no MuJoCo/SciPy import.

Physics and interface copy rl_cmg_2026_09_30/racing_env.py + the MuJoCo race world (parameters from
results/x2_params.json, extracted by extract_x2.py):
  action a in [-1,1]^4 -> collective thrust 0.5(a0+1) T_max and desired body rates a[1:] * rate_max
  every 2-ms plant step: tau = J (k_w (w_des - w)) + w x J w;  rotors f = B^-1 [T, tau], and when any rotor is out of
  bounds the weighted bounded least squares the MuJoCo env solves (yaw row weight 0.05), here by projected gradient;
  rigid body with MuJoCo's semi-implicit Euler (velocities first, then position/quaternion with the new velocities).
Gates: forward plane crossing inside the 1.5-m opening (race.GateJudge rule); collision = vehicle sphere of radius
half_span touching a frame bar or leg (MuJoCo uses the real geoms; validate_sim.py measures the difference).
Reward (Song et al., IROS 2021): progress along the segment from the previous to the next gate centre, body-rate and
command-smoothness penalties, crash penalty. Initialization: UZH "distributed initialization" along the race line.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
OBS_DIM = 31   # body velocity 3, rotation 9, rates 3, next two gates (relative position 3 + normal 3) x 2, previous action 4


def quat_to_R(q):
    w, x, y, z = q.unbind(-1)
    return torch.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
                        2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
                        2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1).reshape(q.shape[:-1] + (3, 3))


def R_to_quat(R):
    """Shepperd's method, batched."""
    m = R
    t = m[..., 0, 0] + m[..., 1, 1] + m[..., 2, 2]
    q = torch.zeros(R.shape[:-2] + (4,), dtype=R.dtype, device=R.device)
    c0 = t > 0
    s = torch.sqrt(torch.clamp(t + 1, min=1e-12)) * 2
    q0 = torch.stack([0.25 * s, (m[..., 2, 1] - m[..., 1, 2]) / s, (m[..., 0, 2] - m[..., 2, 0]) / s,
                      (m[..., 1, 0] - m[..., 0, 1]) / s], -1)
    s1 = torch.sqrt(torch.clamp(1 + m[..., 0, 0] - m[..., 1, 1] - m[..., 2, 2], min=1e-12)) * 2
    q1 = torch.stack([(m[..., 2, 1] - m[..., 1, 2]) / s1, 0.25 * s1, (m[..., 0, 1] + m[..., 1, 0]) / s1,
                      (m[..., 0, 2] + m[..., 2, 0]) / s1], -1)
    s2 = torch.sqrt(torch.clamp(1 + m[..., 1, 1] - m[..., 0, 0] - m[..., 2, 2], min=1e-12)) * 2
    q2 = torch.stack([(m[..., 0, 2] - m[..., 2, 0]) / s2, (m[..., 0, 1] + m[..., 1, 0]) / s2, 0.25 * s2,
                      (m[..., 1, 2] + m[..., 2, 1]) / s2], -1)
    s3 = torch.sqrt(torch.clamp(1 + m[..., 2, 2] - m[..., 0, 0] - m[..., 1, 1], min=1e-12)) * 2
    q3 = torch.stack([(m[..., 1, 0] - m[..., 0, 1]) / s3, (m[..., 0, 2] + m[..., 2, 0]) / s3,
                      (m[..., 1, 2] + m[..., 2, 1]) / s3, 0.25 * s3], -1)
    c1 = (~c0) & (m[..., 0, 0] > m[..., 1, 1]) & (m[..., 0, 0] > m[..., 2, 2])
    c2 = (~c0) & (~c1) & (m[..., 1, 1] > m[..., 2, 2])
    q = torch.where(c0[..., None], q0, torch.where(c1[..., None], q1, torch.where(c2[..., None], q2, q3)))
    return q / q.norm(dim=-1, keepdim=True)


def quat_mul(a, b):
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    return torch.stack([aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
                        aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw], -1)


class CMGBatch:
    """Batched copy of rl_cmg_2026_09_30/cmg_cells.CMGPopulation, policy preset, all four modes.

    graded       original continuous dynamics, gate readout            (non-spiking)
    crossing     original continuous dynamics, upward-crossing events  (spiking readout, no reset)
    reset_gate   NEW reset dynamics, gate readout                      (spiking dynamics, graded readout)
    reset_spike  NEW reset dynamics, filtered event-rate readout       (spiking)
    """

    MODES = ("graded", "crossing", "reset_gate", "reset_spike", "acc")

    def __init__(self, n_env, n_units, mode, dtype, device="cpu"):
        assert mode in self.MODES
        self.mode, self.shape, self.f = mode, (n_env, n_units), dict(dtype=dtype, device=device)
        self.alpha, self.gamma, self.base_gain, self.gain_scaling, self.gate_gain = 12.0, 0.35, 20.0, 10.0, 1.0
        self.v_th, self.tau, self.tau_r, self.event_th, self.filter_tau, self.scale_hz = 0.55, 0.05, 0.005, 0.48, 0.025, 80.0
        if mode == "acc":   # exact ACC 2027 CMG (paper Table I; src/gra_control/gate.py CMGConfig), gate readout a = clip(G r)
            self.alpha, self.gamma, self.base_gain, self.gain_scaling, self.gate_gain = 50.0, 2.0, 120.0, 30.0, 1.0e5
            self.v_th, self.tau, self.tau_r = 1.0, 0.05, 0.005
        self.reset(torch.ones(n_env, dtype=torch.bool, device=device))

    def reset(self, mask):
        if not hasattr(self, "v"):
            self.v = torch.zeros(self.shape, **self.f); self.r = torch.zeros(self.shape, **self.f)
            self.rate = torch.zeros(self.shape, **self.f); self.events = torch.zeros(self.shape, **self.f)
        for x in (self.v, self.r, self.rate):
            x[mask] = 0.0

    def step(self, j, dt):
        v_prev = self.v
        arg = (self.alpha * (self.v - (self.v_th - self.gamma * self.r))).clamp(-60, 60)
        self.r = (self.r + dt * (torch.sigmoid(arg) - self.r) / self.tau_r).clamp(0.0, 1.0)
        c = (self.base_gain + self.gain_scaling * j.abs()) * self.r * self.r
        lam = 1.0 / self.tau + c
        decay = torch.exp(-lam * dt)
        self.v = self.v * decay + (j / self.tau) / lam * (1.0 - decay)
        ev = ((v_prev < self.event_th) & (self.v >= self.event_th)).to(self.v.dtype)
        if self.mode in ("reset_gate", "reset_spike"):
            self.v = self.v - self.event_th * ev
        self.events = self.events + ev
        self.rate = self.rate + (-math.expm1(-dt / self.filter_tau)) * (ev / dt - self.rate)

    def features(self):
        if self.mode in ("graded", "reset_gate", "acc"):
            return (self.gate_gain * self.r).clamp(0.0, 1.0)
        return (self.rate / self.scale_hz).clamp(0.0, 1.0)


class HyperLIFBatch:
    """The established spiking HyperLIF, batched: P2_HyperLIF_Nengo/src/neurons/nengo_hyperlif.HyperLIFNengo.step
    with P2's default parameters. Spikes come from the gate's own reset conductance (no hard reset):
        r <- clip(r* + (r - r*) exp(-dt/tau_r), 0, 1),   r* = sigmoid(alpha (v - (v_th - gamma r)))
        v <- exact step of dv/dt = (-(v - v_rest) + J)/tau - G r^2 (v - v_reset);  v <- max(v, v_min)
        spike when v crosses event_threshold upward.
    P2 result (dt 1e-4): silent for J < 1.6, ~62-73 Hz for 1.6 <= J <= 2.2, depolarization block from J = 2.4.
    Readout: spike train low-passed with tau_syn (Nengo-style synapse), divided by rate_scale_hz.
    """

    def __init__(self, n_env, n_units, dtype, tau_syn=0.02, rate_scale_hz=75.0, device="cpu"):
        self.shape, self.f = (n_env, n_units), dict(dtype=dtype, device=device)
        self.tau, self.v_rest, self.v_th, self.v_reset = 0.02, 0.0, 1.0, 0.0
        self.alpha, self.G, self.tau_r, self.gamma, self.v_min, self.event_th = 100.0, 100.0, 0.002, 0.2, 0.0, 1.0
        self.tau_syn, self.scale_hz = tau_syn, rate_scale_hz
        self.reset(torch.ones(n_env, dtype=torch.bool, device=device))

    def reset(self, mask):
        if not hasattr(self, "v"):
            self.v = torch.zeros(self.shape, **self.f); self.r = torch.zeros(self.shape, **self.f)
            self.rate = torch.zeros(self.shape, **self.f); self.events = torch.zeros(self.shape, **self.f)
        for x in (self.v, self.r, self.rate):
            x[mask] = 0.0

    def step(self, j, dt):
        v_prev = self.v
        target = torch.sigmoid((self.alpha * (self.v - (self.v_th - self.gamma * self.r))).clamp(-700, 700))
        self.r = (target + (self.r - target) * math.exp(-dt / self.tau_r)).clamp(0.0, 1.0)
        c = self.G * self.r * self.r
        lam = 1.0 / self.tau + c
        drive = self.v_rest / self.tau + j / self.tau + c * self.v_reset
        decay = torch.exp(-lam * dt)
        self.v = (self.v * decay + drive / lam * (1.0 - decay)).clamp(min=self.v_min)
        ev = ((v_prev < self.event_th) & (self.v >= self.event_th)).to(self.v.dtype)
        self.events = self.events + ev
        self.rate = self.rate + (-math.expm1(-dt / self.tau_syn)) * (ev / dt - self.rate)

    def features(self):
        return (self.rate / self.scale_hz).clamp(0.0, 1.0)


class VecRace:
    def __init__(self, n_env, seed=1, dtype=torch.float32, episode_s=15.0, p_official_start=0.25,
                 init_speed=(0.0, 3.0), w_rate=0.002, w_smooth=0.01, crash_penalty=10.0, device="cpu",
                 progress_mode="gate_distance", pass_bonus=0.0, stall_s=0.0):
        # stall_s > 0 (v4): no gate passed for stall_s seconds -> failure (hovering is no safer than trying)
        self.progress_mode, self.pass_bonus = progress_mode, pass_bonus
        self.stall_steps = round(stall_s / 0.02) if stall_s > 0 else 0
        P = json.loads((HERE / "results" / "x2_params.json").read_text())
        self.P, self.n, self.f = P, n_env, dict(dtype=dtype, device=device)
        t = lambda x: torch.as_tensor(x, **self.f)
        self.dt, self.sub = P["plant_dt"], P["substeps"]
        self.mass, self.J, self.Jinv = P["mass"], t(P["J"]), torch.linalg.inv(t(P["J"]))
        self.B6, self.Bs, self.Bpinv = t(P["B_full"]), t(P["Bs"]), t(P["Bpinv"])
        self.lo, self.hi = t(P["rotor_lo"]), t(P["rotor_hi"])
        Wsq = t(P["alloc_weights"]) ** 2
        self.BtW2 = self.Bs.T * Wsq
        self.alloc_step = 1.0 / torch.linalg.eigvalsh(self.Bs.T @ (Wsq[:, None] * self.Bs)).max()
        self.tmax, self.rate_max, self.k_w = P["tmax"], t(P["rate_max"]), t(P["rate_gain"])
        self.g = t(P["gravity"])
        self.half_span = P["half_span"]
        self.gc = t([g["centre"] for g in P["gates"]])
        yaw = torch.deg2rad(t([g["yaw_deg"] for g in P["gates"]]))
        self.gn = torch.stack([torch.cos(yaw), torch.sin(yaw), torch.zeros_like(yaw)], -1)
        self.gy = torch.stack([-torch.sin(yaw), torch.cos(yaw), torch.zeros_like(yaw)], -1)   # gate-local y
        self.n_gates = len(P["gates"])
        h, w, d = P["gate_inner"] / 2, P["gate_border"], P["gate_depth"] / 2
        self.bar_c = t([[0, 0, h + w / 2], [0, 0, -(h + w / 2)], [0, h + w / 2, 0], [0, -(h + w / 2), 0]])
        self.bar_h = t([[d, h + w, w / 2], [d, h + w, w / 2], [d, w / 2, h + w], [d, w / 2, h + w]])
        self.leg_y, self.leg_top, self.leg_r = h + w / 2, -(h + w), P["leg_radius"]
        self.leg_bot = (h + w) - self.gc[:, 2]                    # build_scene.add_gate: local z = -z0
        L = P["race_line"]
        self.line_p, self.line_t, self.line_next = t(L["p"]), t(L["tangent"]), torch.as_tensor(L["next_gate"])
        S = P["start"]
        self.start = dict(p=t(S["p"]), v=t(S["v"]), q=R_to_quat(t(S["R"])), w=t(S["w"]))
        self.episode_steps = round(episode_s / P["policy_dt"])
        self.p_official, self.init_speed = p_official_start, init_speed
        self.w_rate, self.w_smooth, self.crash_penalty = w_rate, w_smooth, crash_penalty
        self.gen = torch.Generator().manual_seed(seed)
        z = lambda *s: torch.zeros(*s, **self.f)
        self.p, self.v, self.w = z(n_env, 3), z(n_env, 3), z(n_env, 3)
        self.q = torch.zeros(n_env, 4, **self.f); self.q[:, 0] = 1
        self.next_gate = torch.zeros(n_env, dtype=torch.long)
        self.prev_action, self.steps = z(n_env, 4), torch.zeros(n_env, dtype=torch.long)
        self.gates_passed = torch.zeros(n_env, dtype=torch.long)
        self.since_gate = torch.zeros(n_env, dtype=torch.long)
        self.reset(torch.ones(n_env, dtype=torch.bool))

    # ------------------------------------------------------------------ initialization
    def reset(self, mask):
        idx = mask.nonzero().flatten()
        k = len(idx)
        if k == 0:
            return
        r = lambda *s: torch.rand(*s, generator=self.gen).to(**self.f)
        official = r(k) < self.p_official
        j = torch.randint(0, len(self.line_p), (k,), generator=self.gen)
        tan = self.line_t[j]
        yaw = torch.atan2(tan[:, 1], tan[:, 0])
        cy, sy = torch.cos(yaw / 2), torch.sin(yaw / 2)
        qyaw = torch.stack([cy, torch.zeros_like(cy), torch.zeros_like(cy), sy], -1)
        tilt = 0.1 * torch.randn(k, 2, generator=self.gen).to(**self.f)
        half = tilt.norm(dim=1, keepdim=True).clamp(min=1e-9) / 2
        axis = torch.cat([tilt, torch.zeros(k, 1, **self.f)], 1) / (2 * half)
        qtilt = torch.cat([torch.cos(half), torch.sin(half) * axis], 1)
        lo, hi = self.init_speed
        p = self.line_p[j] + 0.3 * torch.randn(k, 3, generator=self.gen).to(**self.f)
        v = tan * (lo + (hi - lo) * r(k))[:, None]
        q = quat_mul(qyaw, qtilt)
        ng = self.line_next[j]
        S = self.start
        o = official[:, None]
        self.p[idx] = torch.where(o, S["p"].expand(k, 3), p)
        self.v[idx] = torch.where(o, S["v"].expand(k, 3), v)
        self.q[idx] = torch.where(o, S["q"].expand(k, 4), q)
        self.w[idx] = torch.where(o, S["w"].expand(k, 3), torch.zeros(k, 3, **self.f))
        self.next_gate[idx] = torch.where(official, torch.zeros_like(ng), ng)
        self.prev_action[idx] = 0.0
        self.steps[idx] = 0
        self.gates_passed[idx] = 0
        self.since_gate[idx] = 0

    def set_state(self, p, v, R, w, next_gate):
        self.p, self.v, self.q, self.w = p.clone(), v.clone(), R_to_quat(R), w.clone()
        self.next_gate = next_gate.clone()

    # ------------------------------------------------------------------ observation
    def observe(self):
        R = quat_to_R(self.q)
        Rt = R.transpose(1, 2)
        bm = lambda x: (Rt @ x[..., None])[..., 0]
        g1, g2 = self.next_gate, (self.next_gate + 1) % self.n_gates
        obs = torch.cat([bm(self.v) / 10.0, R.reshape(self.n, 9), self.w / 10.0,
                         bm(self.gc[g1] - self.p) / 15.0, bm(self.gn[g1]),
                         bm(self.gc[g2] - self.p) / 15.0, bm(self.gn[g2]), self.prev_action], 1)
        return obs.clamp(-3, 3)

    # ------------------------------------------------------------------ physics
    def _allocate(self, wrench):
        u = wrench @ self.Bpinv.T
        sat = ((u < self.lo - 1e-9) | (u > self.hi + 1e-9)).any(1)
        if sat.any():
            us, ws = u[sat].clamp(self.lo, self.hi), wrench[sat]
            for _ in range(40):
                grad = (us @ self.Bs.T - ws) @ self.BtW2.T
                us = (us - self.alloc_step * grad).clamp(self.lo, self.hi)
            u = u.clone(); u[sat] = us
        return u, sat

    def _substep(self, thrust, w_des):
        Jw = self.w @ self.J.T
        tau = (self.k_w * (w_des - self.w)) @ self.J.T + torch.cross(self.w, Jw, dim=1)
        u, sat = self._allocate(torch.cat([thrust[:, None], tau], 1))
        wr = u @ self.B6.T
        R = quat_to_R(self.q)
        self.w = self.w + self.dt * ((wr[:, 3:] - torch.cross(self.w, Jw, dim=1)) @ self.Jinv.T)
        self.v = self.v + self.dt * ((R @ wr[:, :3, None])[..., 0] / self.mass + self.g)
        p_prev = self.p
        self.p = self.p + self.dt * self.v
        ang = self.w.norm(dim=1, keepdim=True)
        half = 0.5 * self.dt * ang
        axis = self.w / ang.clamp(min=1e-12)
        dq = torch.cat([torch.cos(half), torch.sin(half) * axis], 1)
        self.q = quat_mul(self.q, dq)
        self.q = self.q / self.q.norm(dim=1, keepdim=True)
        return p_prev, sat

    def _gate_events(self, p_prev):
        """Forward crossings of the next gate's plane inside the opening -> pass; any frame/leg contact -> crash."""
        i = self.next_gate
        c, n, gy = self.gc[i], self.gn[i], self.gy[i]
        a, b = ((p_prev - c) * n).sum(1), ((self.p - c) * n).sum(1)
        lat = self.p - c
        off_y, off_z = (lat * gy).sum(1).abs(), lat[:, 2].abs()
        passed = (a < 0) & (b >= 0) & (torch.maximum(off_y, off_z) < self.P["gate_inner"] / 2)
        # distance from the CoM to every gate's bars and legs (gate-local frame)
        rel = self.p[:, None, :] - self.gc[None]                                     # [n, G, 3]
        loc = torch.stack([(rel * self.gn).sum(-1), (rel * self.gy).sum(-1), rel[..., 2]], -1)
        dbar = ((loc[:, :, None, :] - self.bar_c).abs() - self.bar_h).clamp(min=0).norm(dim=-1).amin(-1)
        dleg = []
        for s in (-1.0, 1.0):
            zc = loc[..., 2].clamp(min=torch.minimum(self.leg_bot, torch.full_like(self.leg_bot, self.leg_top)),
                                   max=torch.maximum(self.leg_bot, torch.full_like(self.leg_bot, self.leg_top)))
            dleg.append(torch.sqrt(loc[..., 0] ** 2 + (loc[..., 1] - s * self.leg_y) ** 2 + (loc[..., 2] - zc) ** 2)
                        - self.leg_r)
        dist = torch.minimum(dbar, torch.minimum(dleg[0], dleg[1])).amin(1)
        crashed = dist < self.half_span
        return passed, crashed

    def progress_coordinate(self):
        """v2 (default): minus the distance to the next gate centre (Swift-style progress, from memory - check before
        citing). Bounded: no reward for flying past a gate outside its opening. v1 'segment' (projection on the
        gate-to-gate line, Song 2021 style) let PPO dash at ~40 m/s out of the arena (diagnose_crashes.py)."""
        if self.progress_mode == "gate_distance":
            return -(self.p - self.gc[self.next_gate]).norm(dim=1)
        i = self.next_gate
        prev = (i - 1) % self.n_gates
        seg = self.gc[i] - self.gc[prev]
        return ((self.p - self.gc[prev]) * seg).sum(1) / seg.norm(dim=1)

    def step(self, action):
        a = action.clamp(-1, 1)
        thrust = 0.5 * (a[:, 0] + 1.0) * self.tmax
        w_des = a[:, 1:] * self.rate_max
        s0 = self.progress_coordinate()
        progress = torch.zeros(self.n, **self.f)
        passed_any = torch.zeros(self.n, dtype=torch.bool)
        crashed = torch.zeros(self.n, dtype=torch.bool)
        sat_count = torch.zeros(self.n, **self.f)
        for _ in range(self.sub):
            p_prev, sat = self._substep(thrust, w_des)
            sat_count += sat.to(sat_count.dtype)
            passed, crash = self._gate_events(p_prev)
            crashed |= crash
            if passed.any():
                progress = torch.where(passed, progress + self.progress_coordinate() - s0, progress)
                self.next_gate = torch.where(passed, (self.next_gate + 1) % self.n_gates, self.next_gate)
                self.gates_passed += passed.long()
                s0 = torch.where(passed, self.progress_coordinate(), s0)
                passed_any |= passed
        progress = progress + self.progress_coordinate() - s0
        ground = self.p[:, 2] < 0.15
        outside = self.p[:, :2].norm(dim=1) > 30.0
        invalid = ~torch.isfinite(self.p).all(1)
        self.steps += 1
        timeout = self.steps >= self.episode_steps
        self.since_gate = torch.where(passed_any, torch.zeros_like(self.since_gate), self.since_gate + 1)
        stall = (self.since_gate >= self.stall_steps) if self.stall_steps else torch.zeros_like(crashed)
        fail = crashed | ground | outside | invalid | stall
        reward = (progress.clamp(-1, 1) + self.pass_bonus * passed_any.to(progress.dtype) - self.w_rate * (self.w ** 2).sum(1)
                  - self.w_smooth * ((a - self.prev_action) ** 2).sum(1) - self.crash_penalty * fail.to(progress.dtype))
        self.prev_action = a.clone()
        done = fail | timeout
        info = dict(passed=passed_any, crashed=crashed, ground=ground, outside=outside, stall=stall, timeout=timeout & ~fail,
                    gates_passed=self.gates_passed.clone(), sat_fraction=sat_count / self.sub, progress=progress)
        reward = torch.nan_to_num(reward, nan=-self.crash_penalty)
        return reward, done, info
