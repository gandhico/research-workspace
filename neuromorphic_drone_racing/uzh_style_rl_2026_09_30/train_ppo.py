"""UZH-style PPO for the X2 race in the batched simulator (PyTorch only).

Recipe (Song et al., IROS 2021): progress reward, distributed initialization along the track, z-scored observations,
2 x 128 tanh actor and critic, PPO. Arms share everything except the policy input (32 extra slots):
  mlp             observation only + 32 zeros                              (no neuron)
  cmg             original continuous CMG, gate readout                    (NON-SPIKING line)
  cmg_crossing    original continuous CMG, filtered upward-crossing events (spiking readout, no reset)
  cmg_reset_gate  NEW reset CMG dynamics, gate readout                     (spiking dynamics, graded readout)
  cmg_spike       NEW reset CMG dynamics, filtered event rate              (SPIKING line)
The CMG current encoder is a fixed random map of the observation (frozen); CMG cells advance every 0.5 ms.
Writes results/<run>/{metrics.csv, policy.pt, config.json}.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import torch
from torch import nn

from vec_race import OBS_DIM, CMGBatch, HyperLIFBatch, VecRace

HERE = Path(__file__).resolve().parent
N_UNITS = 32
ARM_MODE = {"mlp": None, "cmg": "graded", "cmg_crossing": "crossing", "cmg_reset_gate": "reset_gate",
            "cmg_spike": "reset_spike", "hyperlif_spike": "hyperlif_spike", "hyperlif_gate": "hyperlif_gate",
            "cmg_acc": "acc"}
# Exact ACC 2027 CMG (gate.py CoupledMembraneGateBank, parity 1e-14 in check_cmg_acc.py): ACC paired currents
# J+- = 0.75 + 1.25 max(+-z, 0) on 16 projections z = tanh(E o) -> 32 cells, readout clip(1e5 r).
# Established spiking HyperLIF (P2_HyperLIF_Nengo): P2 parameters and P2's validated step dt = 1e-4 (at 5e-4 the
# spiking window and depolarization-block onset shift). Currents span silent -> spiking -> just below the block.
HL_DT, HL_J = 1e-4, (1.0, 2.25)


class RunningNorm:
    def __init__(self, dim, floor=None):
        self.n, self.mean, self.var = 1e-4, torch.zeros(dim), torch.ones(dim)
        self.floor = torch.zeros(dim) if floor is None else floor   # variance floor (v4: neuron features)

    def effective_var(self):
        return torch.maximum(self.var, self.floor)

    def update(self, x):
        b = x.shape[0]; bm = x.mean(0); bv = x.var(0, unbiased=False)
        d = bm - self.mean; tot = self.n + b
        self.mean = self.mean + d * b / tot
        self.var = (self.var * self.n + bv * b + d ** 2 * self.n * b / tot) / tot
        self.n = tot

    def __call__(self, x):
        return ((x - self.mean) / torch.sqrt(self.effective_var() + 1e-8)).clamp(-5, 5)


class Features:
    """Fixed encoder + CMG population (or zeros for the MLP arm)."""

    def __init__(self, arm, n_env, seed):
        self.arm = arm
        g = torch.Generator().manual_seed(seed + 8001)
        self.enc = torch.randn(N_UNITS, OBS_DIM, generator=g) / math.sqrt(OBS_DIM)
        self.off = (torch.rand(N_UNITS, generator=g) - 0.5) * 0.6
        mode = ARM_MODE[arm]
        self.hyperlif = mode is not None and mode.startswith("hyperlif")
        if mode is None:
            self.cmg = None
        elif self.hyperlif:
            self.cmg = HyperLIFBatch(n_env, N_UNITS, torch.float32)
            self.cmg.gate_readout = mode == "hyperlif_gate"
        else:
            self.cmg = CMGBatch(n_env, N_UNITS, mode, torch.float32)
        self.n_env = n_env

    def reset(self, mask):
        if self.cmg is not None:
            self.cmg.reset(mask)

    def __call__(self, obs):
        if self.cmg is None:
            return torch.zeros(obs.shape[0], N_UNITS)
        if self.hyperlif:
            lo, hi = HL_J
            j = lo + (hi - lo) * 0.5 * (1.0 + torch.tanh(obs @ self.enc.T + self.off))
            for _ in range(round(0.02 / HL_DT)):   # 20 ms decision / 0.1 ms neural step
                self.cmg.step(j, HL_DT)
            return self.cmg.r.clamp(0, 1) if self.cmg.gate_readout else self.cmg.features()
        if self.arm == "cmg_acc":
            z = torch.tanh(obs @ self.enc[: N_UNITS // 2].T)
            j = torch.cat([0.75 + 1.25 * z.clamp(min=0), 0.75 + 1.25 * (-z).clamp(min=0)], 1)
        else:
            j = (0.85 + self.off + 0.95 * torch.tanh(obs @ self.enc.T)).clamp(0.05, 2.2)
        for _ in range(40):                      # 20 ms decision / 0.5 ms neural step
            self.cmg.step(j, 0.0005)
        return self.cmg.features()


class ActorCritic(nn.Module):
    def __init__(self, in_dim, hover_action, log_std0=-0.5):
        super().__init__()
        self.pi = nn.Sequential(nn.Linear(in_dim, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 4))
        self.vf = nn.Sequential(nn.Linear(in_dim, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 1))
        self.log_std = nn.Parameter(torch.full((4,), log_std0))
        nn.init.orthogonal_(self.pi[-1].weight, 0.01); nn.init.zeros_(self.pi[-1].bias)
        with torch.no_grad():                      # start near hover: tanh(bias) = hover thrust command
            self.pi[-1].bias[0] = math.atanh(hover_action)

    def dist(self, x):
        return torch.distributions.Normal(self.pi(x), self.log_std.exp())

    def value(self, x):
        return self.vf(x).squeeze(-1)


def evaluate(model, norm, arm, seed, laps=2, time_s=40.0):
    """Deterministic flight from the official start: gates in order, crash, lap time."""
    sim = VecRace(1, seed=seed + 99, episode_s=time_s, p_official_start=1.0)
    feat = Features(arm, 1, seed)
    gate_t, t, crashed = [], 0.0, False
    with torch.no_grad():
        for _ in range(round(time_s / 0.02)):
            obs = sim.observe()
            x = norm(torch.cat([obs, feat(obs)], 1))
            a = torch.tanh(model.pi(x))
            _, done, info = sim.step(a)
            t += 0.02
            if info["passed"][0]:
                gate_t.append(round(t, 2))
            if done[0]:
                crashed = bool(~info["timeout"][0])
                break
            if len(gate_t) >= 7 * laps:
                break
    lap = gate_t[6] if len(gate_t) >= 7 else None
    return dict(gates=len(gate_t), crashed=crashed, first_lap_s=lap, gate_times=gate_t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=list(ARM_MODE), required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--n-env", type=int, default=1024)
    ap.add_argument("--horizon", type=int, default=64)
    ap.add_argument("--total-steps", type=float, default=20e6)
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--minibatch", type=int, default=8192)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--gamma", type=float, default=0.99)
    ap.add_argument("--lam", type=float, default=0.95)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--pass-bonus", type=float, default=0.0)
    ap.add_argument("--crash-penalty", type=float, default=10.0)
    ap.add_argument("--w-smooth", type=float, default=0.01)
    ap.add_argument("--w-rate", type=float, default=0.002)
    ap.add_argument("--stall-s", type=float, default=0.0)
    ap.add_argument("--feat-var-floor", type=float, default=0.0)
    a = ap.parse_args()
    torch.set_num_threads(a.threads)
    torch.manual_seed(a.seed)
    out = a.out or HERE / "results" / f"ppo_x2_{a.arm}_seed{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps({k: str(v) for k, v in vars(a).items()}, indent=1))
    sim = VecRace(a.n_env, seed=a.seed, pass_bonus=a.pass_bonus, crash_penalty=a.crash_penalty,
                  w_smooth=a.w_smooth, w_rate=a.w_rate, stall_s=a.stall_s)
    feat = Features(a.arm, a.n_env, a.seed)
    in_dim = OBS_DIM + N_UNITS
    model = ActorCritic(in_dim, hover_action=2.0 * sim.mass * 9.81 / sim.tmax - 1.0)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    norm = RunningNorm(in_dim, torch.cat([torch.zeros(OBS_DIM), torch.full((N_UNITS,), a.feat_var_floor)]))
    N, H = a.n_env, a.horizon
    updates = int(a.total_steps // (N * H))
    obs = sim.observe(); x_raw = torch.cat([obs, feat(obs)], 1)
    log = open(out / "metrics.csv", "w", newline="")
    writer = None
    begin = time.time()
    ep_ret, ep_gates = torch.zeros(N), torch.zeros(N)
    for u in range(updates):
        X, A, LP, V, Rw, D = [], [], [], [], [], []
        fin_ret, fin_gates, fin_crash = [], [], []
        ev_snap = feat.cmg.events.clone() if feat.cmg is not None else None
        f_sum = f_hi = f_lo = 0.0
        with torch.no_grad():
            for _ in range(H):
                fx = x_raw[:, OBS_DIM:]
                f_sum += float(fx.mean()); f_hi += float((fx > 0.99).float().mean()); f_lo += float((fx < 0.01).float().mean())
                norm.update(x_raw)
                x = norm(x_raw)
                d = model.dist(x)
                raw = d.sample()
                lp = d.log_prob(raw).sum(-1)
                v = model.value(x)
                r, done, info = sim.step(torch.tanh(raw))
                obs = sim.observe()
                x_next_raw = torch.cat([obs, feat(obs)], 1)
                to = info["timeout"]
                if to.any():                                        # bootstrap truncated episodes
                    r = r + a.gamma * to.float() * model.value(norm(x_next_raw))
                ep_ret += r; ep_gates = info["gates_passed"].float()
                if done.any():
                    fin_ret.append(ep_ret[done]); fin_gates.append(ep_gates[done])
                    fin_crash.append((~info["timeout"][done]).float())
                    ep_ret[done] = 0
                    sim.reset(done); feat.reset(done)
                    obs = sim.observe()
                    x_next_raw = torch.cat([obs, feat(obs)], 1) if feat.cmg is None else \
                        torch.where(done[:, None], torch.cat([obs, feat.cmg.features()], 1), x_next_raw)
                X.append(x); A.append(raw); LP.append(lp); V.append(v); Rw.append(r); D.append(done.float())
                x_raw = x_next_raw
            last_v = model.value(norm(x_raw))
        X, A, LP, V, Rw, D = map(torch.stack, (X, A, LP, V, Rw, D))
        adv = torch.zeros_like(Rw); gae = torch.zeros(N)
        for t in reversed(range(H)):
            nv = last_v if t == H - 1 else V[t + 1]
            delta = Rw[t] + a.gamma * nv * (1 - D[t]) - V[t]
            gae = delta + a.gamma * a.lam * (1 - D[t]) * gae
            adv[t] = gae
        ret = adv + V
        X, A, LP, adv, ret = (z.reshape(N * H, -1).squeeze(-1) for z in (X, A, LP, adv, ret))
        adv = (adv - adv.mean()) / (adv.std() + 1e-8)
        for _ in range(a.epochs):
            perm = torch.randperm(N * H)
            for i in range(0, N * H, a.minibatch):
                b = perm[i:i + a.minibatch]
                d = model.dist(X[b])
                ratio = torch.exp(d.log_prob(A[b]).sum(-1) - LP[b])
                pl = -torch.minimum(ratio * adv[b], ratio.clamp(0.8, 1.2) * adv[b]).mean()
                vl = ((model.value(X[b]) - ret[b]) ** 2).mean()
                loss = pl + 0.5 * vl
                opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 0.5); opt.step()
        steps = (u + 1) * N * H
        row = dict(update=u + 1, env_steps=steps, wall_s=round(time.time() - begin, 1),
                   episodes=int(sum(len(x) for x in fin_ret)),
                   ep_return=float(torch.cat(fin_ret).mean()) if fin_ret else float("nan"),
                   ep_gates=float(torch.cat(fin_gates).mean()) if fin_gates else float("nan"),
                   crash_rate=float(torch.cat(fin_crash).mean()) if fin_crash else float("nan"),
                   log_std=float(model.log_std.mean()),
                   feature_mean=f_sum / H, feature_frac_saturated=f_hi / H, feature_frac_silent=f_lo / H)
        if ev_snap is not None:
            inc = feat.cmg.events - ev_snap
            row.update(event_rate_hz=float(inc.mean()) / (H * 0.02), active_unit_frac=float((inc > 0).float().mean()))
        if (u + 1) % 10 == 0 or u == updates - 1:
            row.update({f"eval_{k}": v for k, v in evaluate(model, norm, a.arm, a.seed).items() if k != "gate_times"})
            torch.save(dict(model=model.state_dict(), norm_mean=norm.mean, norm_var=norm.effective_var(), arm=a.arm, seed=a.seed,
                            enc=feat.enc, off=feat.off), out / "policy.pt")
        if writer is None:
            keys = list(row) + [k for k in ("event_rate_hz", "active_unit_frac", "eval_gates", "eval_crashed",
                                            "eval_first_lap_s") if k not in row]
            writer = csv.DictWriter(log, fieldnames=keys); writer.writeheader()
        writer.writerow(row); log.flush()
        print(json.dumps(row), flush=True)
    final = evaluate(model, norm, a.arm, a.seed)
    (out / "final_eval.json").write_text(json.dumps(final, indent=1))
    print("FINAL", json.dumps(final))


if __name__ == "__main__":
    main()
