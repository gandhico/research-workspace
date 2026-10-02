"""MuJoCo-only rollout worker for the dual racing pilot (no PyTorch import; see ../rl_cmg_2026_09_30/README.md).

kind=train : stochastic actor, fixed number of policy steps, resets after terminal states
kind=eval  : deterministic actor, one episode
arm=baseline needs no weights: the latent is identically zero (exact teacher, see results/parity).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from dual_env import DualEnv  # also puts ../rl_cmg_2026_09_30 on sys.path
from policy_basis import Basis
from rollout_worker import cell_data, forward

SLOTS = {"baseline": [], "self": [4, 5, 6], "residual": [0, 1, 2, 3], "dual": list(range(7))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["train", "eval"], required=True)
    ap.add_argument("--arm", choices=list(SLOTS), required=True)
    ap.add_argument("--mode", choices=["mlp", "graded"], required=True)
    ap.add_argument("--vehicle", choices=["x2", "cf2"], default="x2")
    ap.add_argument("--scenario", choices=["nominal", "gust"], default="gust")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--episode-s", type=float, default=12.0)
    ap.add_argument("--samples", type=int, default=600)
    ap.add_argument("--weights", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    slots = SLOTS[a.arm]
    if slots and a.weights is None:
        ap.error("--weights required for a learning arm")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    env = DualEnv(a.vehicle, a.scenario, episode_s=a.episode_s, seed=a.seed)
    basis = Basis(a.mode, a.seed, env.policy_dt)
    rng = np.random.default_rng(a.seed + (1000 if a.kind == "train" else 2000))
    weights = None if a.weights is None else dict(np.load(a.weights))
    obs = env.reset(); basis.reset()
    keys = ("phi", "raw", "logp", "value", "reward", "done", "done_reason", "episode_id", "t", "gates", "collisions",
            "pos_error", "saturation", "z", "gain_scale", "wrench_delta", "position", "activity", "gate", "voltage")
    data = {k: [] for k in keys}
    episode = 0
    steps = a.samples if a.kind == "train" else round(a.episode_s / env.policy_dt)
    for i in range(steps):
        phi, _ = basis.encode(obs)
        z = np.zeros(7)
        raw, logp, value = np.zeros(len(slots)), 0.0, 0.0
        if slots:
            mean, value, log_std = forward(weights, phi)
            std = np.exp(log_std)
            raw = mean + std * rng.normal(size=len(slots)) if a.kind == "train" else mean
            logp = float(-0.5 * np.sum(((raw - mean) / std) ** 2 + 2 * log_std + np.log(2 * np.pi)))
            z[slots] = np.tanh(raw)
        next_obs, reward, done, info = env.step_dual(z, a.arm)
        cell = cell_data(basis)
        row = dict(phi=phi, raw=raw, logp=logp, value=value, reward=reward, done=done,
                   done_reason=info["termination_reason"], episode_id=episode, t=info["time_s"],
                   gates=info["gates_in_order"], collisions=info["collisions"], pos_error=info["position_error_m"],
                   saturation=info["saturation_fraction"], z=z, gain_scale=info["gain_scale"],
                   wrench_delta=info["wrench_delta"], position=info["position"],
                   activity=cell["activity"], gate=cell["gate"], voltage=cell["voltage"])
        for k, v in row.items():
            data[k].append(v)
        obs = next_obs
        if done:
            if a.kind == "train" and i + 1 < steps:
                obs = env.reset(); basis.reset(); episode += 1
            else:
                break
    np.savez_compressed(a.out, **{k: np.asarray(v) for k, v in data.items()})
    pe = np.asarray(data["pos_error"])
    zz = np.asarray(data["z"])
    summary = dict(kind=a.kind, arm=a.arm, mode=a.mode, vehicle=a.vehicle, scenario=a.scenario, seed=a.seed,
                   samples=len(pe), episodes=episode + 1, return_sum=float(np.sum(data["reward"])),
                   gates=int(data["gates"][-1]), collisions=int(data["collisions"][-1]),
                   termination_reason=str(data["done_reason"][-1]),
                   mean_position_error_m=float(pe.mean()), max_position_error_m=float(pe.max()),
                   mean_saturation=float(np.mean(data["saturation"])),
                   action_rms=float(np.sqrt(np.mean(zz[:, slots] ** 2))) if slots else 0.0,
                   gain_min=float(np.min(data["gain_scale"])), gain_max=float(np.max(data["gain_scale"])))
    a.out.with_suffix(".json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ("kind", "arm", "mode", "scenario", "samples", "gates", "collisions",
                                              "mean_position_error_m", "return_sum")}), flush=True)


if __name__ == "__main__":
    main()
