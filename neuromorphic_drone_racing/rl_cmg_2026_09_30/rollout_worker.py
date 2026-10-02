"""MuJoCo-only worker. No PyTorch import: avoids duplicate Intel OpenMP DLLs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np

from policy_basis import Basis
from racing_env import RacingEnv


def forward(weights, features):
    x = np.asarray(features, dtype=np.float64)
    for k in (0, 2):
        x = np.tanh(weights[f"body.{k}.weight"] @ x + weights[f"body.{k}.bias"])
    mean = weights["mean.weight"] @ x + weights["mean.bias"]
    value = float((weights["value_head.weight"] @ x + weights["value_head.bias"]).item())
    log_std = weights["log_std"]
    return mean, value, log_std


def cell_data(basis):
    if basis.cell is None:
        return dict(activity=np.zeros(basis.n), voltage=np.zeros(basis.n),
                    gate=np.zeros(basis.n), events=np.zeros(basis.n),
                    rate_hz=np.zeros(basis.n))
    d = basis.cell.diagnostics()
    return dict(activity=d["features"], voltage=d["voltage"], gate=d["gate"],
                events=d["event_count"], rate_hz=d["filtered_rate_hz"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["teacher", "oracle", "train", "eval"], required=True)
    ap.add_argument("--vehicle", choices=["x2", "cf2", "y6"], default="x2")
    ap.add_argument("--observation", choices=["reference", "gate_only"], default="reference")
    ap.add_argument("--mode", choices=["mlp", "graded", "crossing", "reset_gate", "reset_spike"], required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--episode-s", type=float, default=8.0)
    ap.add_argument("--policy-dt", type=float, default=0.02)
    ap.add_argument("--samples", type=int, default=0,
                    help="fixed policy-step budget for train rollouts; resets after terminal states")
    ap.add_argument("--weights", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.kind not in ("teacher", "oracle") and a.weights is None:
        ap.error("--weights required for train/eval")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    env = RacingEnv(a.vehicle, a.policy_dt, a.episode_s, a.seed, a.observation)
    basis = Basis(a.mode, a.seed, a.policy_dt)
    rng = np.random.default_rng(a.seed + (1000 if a.kind == "train" else 2000))
    weights = None if a.weights is None else dict(np.load(a.weights))
    obs = env.reset(); basis.reset()
    data = {k: [] for k in ("phi", "target", "raw", "logp", "value", "reward", "done", "done_reason", "episode_id",
                           "t", "gates", "collisions", "pos_error", "saturation",
                           "action", "position", "rotor", "obs", "current",
                           "activity", "voltage", "gate", "events", "rate_hz")}
    episode_id = 0
    requested = a.samples if a.kind == "train" and a.samples > 0 else round(a.episode_s / a.policy_dt)
    for step_i in range(requested):
        phi, current = basis.encode(obs)
        if a.kind in ("teacher", "oracle"):
            action = env.teacher_action()
            raw = np.arctanh(np.clip(action, -0.999, 0.999))
            logp = value = 0.0
        else:
            mean, value, log_std = forward(weights, phi)
            raw = mean + np.exp(log_std) * rng.normal(size=4) if a.kind == "train" else mean
            logp = float(-0.5 * np.sum(((raw - mean) / np.exp(log_std)) ** 2
                                         + 2 * log_std + np.log(2 * np.pi)))
            action = np.tanh(raw)
            # DAgger label at the *visited* state. Calling the teacher sets a
            # tentative rotor command, which env.step(policy) immediately
            # replaces before MuJoCo advances. No teacher action is executed.
            oracle_target = env.teacher_action()
        next_obs, reward, done, info = env.step(action, teacher=(a.kind == "teacher"))
        cell = cell_data(basis)
        for name, val in dict(phi=phi, target=action if a.kind in ("teacher", "oracle") else oracle_target,
                              raw=raw, logp=logp, value=value, reward=reward, done=done,
                              done_reason=info["termination_reason"], episode_id=episode_id,
                              t=info["time_s"], gates=info["gates_in_order"],
                              collisions=info["collisions"], pos_error=info["position_error_m"],
                              saturation=info["saturation_fraction"], action=action,
                              position=info["position"], rotor=info["rotor"], obs=obs,
                              current=current, **cell).items():
            data[name].append(val)
        obs = next_obs
        if done:
            if a.kind == "train" and step_i + 1 < requested:
                obs = env.reset(); basis.reset(); episode_id += 1
            else:
                break
    np.savez_compressed(a.out, **{k: np.asarray(v) for k, v in data.items()})
    summary = dict(kind=a.kind, vehicle=a.vehicle, mode=a.mode, seed=a.seed,
                   observation=a.observation,
                   episode_s=a.episode_s, samples=len(data["t"]),
                   return_sum=float(np.sum(data["reward"])), gates=int(data["gates"][-1]),
                   collisions=int(data["collisions"][-1]),
                   termination_reason=data["done_reason"][-1],
                   mean_position_error_m=float(np.mean(data["pos_error"])),
                   mean_saturation=float(np.mean(data["saturation"])),
                   episodes_started=episode_id + 1,
                   event_rate_hz=(np.asarray(data["events"][-1]) / (len(data["t"]) * a.policy_dt)).tolist()
                        if a.kind != "train" else None,
                   basis=basis.metadata(),
                   note="full MuJoCo vehicle, perfect-state observation; no DVS feedback")
    a.out.with_suffix(".json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ("kind", "mode", "samples", "gates", "collisions", "return_sum")}), flush=True)


if __name__ == "__main__":
    main()
