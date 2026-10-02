"""PyTorch-only PPO trainer orchestrating separate MuJoCo rollout workers.

Use this entry point on Windows. A single-process prototype was discarded
because conda's duplicate Intel OpenMP runtimes make combined MuJoCo/SciPy
and PyTorch execution unsafe.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.distributions import Normal

HERE = Path(__file__).resolve().parent
WORKER = HERE / "rollout_worker.py"
DEFAULT_PYTHON = Path(r"C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe")
torch.set_num_threads(1)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class ActorCritic(nn.Module):
    def __init__(self):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(58, 64), nn.Tanh(),
                                  nn.Linear(64, 64), nn.Tanh())
        self.mean = nn.Linear(64, 4)
        self.value_head = nn.Linear(64, 1)
        self.log_std = nn.Parameter(torch.full((4,), -1.5))

    def forward(self, x):
        z = self.body(x)
        return self.mean(z), self.value_head(z).squeeze(-1)


def export_numpy(model, path):
    np.savez(path, **{k: v.detach().numpy() for k, v in model.state_dict().items()})


def worker(a, kind, output, weights=None):
    cmd = [str(a.sim_python), str(WORKER), "--kind", kind,
           "--vehicle", a.vehicle, "--mode", a.mode,
           "--observation", a.observation,
           "--seed", str(a.seed), "--episode-s", str(a.episode_s),
           "--policy-dt", str(a.policy_dt), "--out", str(output)]
    if kind == "train":
        cmd += ["--samples", str(a.ppo_samples)]
    if weights is not None:
        cmd += ["--weights", str(weights)]
    run = subprocess.run(cmd, text=True, capture_output=True)
    if run.returncode:
        raise RuntimeError(f"MuJoCo worker failed ({run.returncode})\n{run.stdout}\n{run.stderr}")
    print(run.stdout.strip(), flush=True)
    return dict(np.load(output))


def behavior_clone(model, phi, target, epochs, seed):
    if epochs == 0:
        return None
    rng = np.random.default_rng(seed)
    x = torch.as_tensor(phi, dtype=torch.float32)
    y = torch.as_tensor(target, dtype=torch.float32)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss = None
    for _ in range(epochs):
        for ids in np.array_split(rng.permutation(len(x)), max(1, int(np.ceil(len(x) / 128)))):
            mu, _ = model(x[ids])
            loss = ((mu.tanh() - y[ids]) ** 2).mean()
            optimizer.zero_grad(); loss.backward(); optimizer.step()
    return float(loss.detach())


def ppo_update(model, data, optimizer, epochs, batch_size=128):
    x = torch.as_tensor(data["phi"], dtype=torch.float32)
    raw = torch.as_tensor(data["raw"], dtype=torch.float32)
    old_logp = torch.as_tensor(data["logp"], dtype=torch.float32)
    old_value = np.asarray(data["value"], dtype=float)
    reward = np.asarray(data["reward"], dtype=float)
    done = np.asarray(data["done"], dtype=bool)
    advantage = np.zeros(len(reward)); carry = 0.0
    for t in reversed(range(len(reward))):
        next_value = 0.0 if t == len(reward) - 1 else old_value[t + 1]
        nonterminal = 0.0 if done[t] else 1.0
        delta = reward[t] + 0.99 * next_value * nonterminal - old_value[t]
        carry = delta + 0.99 * 0.95 * nonterminal * carry
        advantage[t] = carry
    returns = torch.as_tensor(advantage + old_value, dtype=torch.float32)
    adv = torch.as_tensor(advantage, dtype=torch.float32)
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    rng = np.random.default_rng(1129)
    losses = []
    for _ in range(epochs):
        for ids in np.array_split(rng.permutation(len(reward)), max(1, int(np.ceil(len(reward) / batch_size)))):
            mu, value = model(x[ids])
            dist = Normal(mu, model.log_std.exp())
            ratio = torch.exp(dist.log_prob(raw[ids]).sum(-1) - old_logp[ids])
            policy = -torch.minimum(ratio * adv[ids],
                                    ratio.clamp(0.8, 1.2) * adv[ids]).mean()
            value_loss = ((value - returns[ids]) ** 2).mean()
            loss = policy + 0.5 * value_loss - 0.001 * dist.entropy().sum(-1).mean()
            optimizer.zero_grad(); loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(loss.detach()))
    return float(np.mean(losses))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vehicle", choices=["x2", "cf2", "y6"], default="x2")
    ap.add_argument("--observation", choices=["reference", "gate_only"], default="reference")
    ap.add_argument("--mode", choices=["mlp", "graded", "crossing", "reset_gate", "reset_spike"], required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--episode-s", type=float, default=8.0)
    ap.add_argument("--policy-dt", type=float, default=0.02)
    ap.add_argument("--bc-epochs", type=int, default=20)
    ap.add_argument("--dagger-rounds", type=int, default=0)
    ap.add_argument("--dagger-epochs", type=int, default=30)
    ap.add_argument("--ppo-rollouts", type=int, default=2)
    ap.add_argument("--ppo-samples", type=int, default=600,
                    help="exact policy steps in each PPO rollout for matched budgets")
    ap.add_argument("--ppo-epochs", type=int, default=4)
    ap.add_argument("--sim-python", type=Path, default=DEFAULT_PYTHON)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if not a.sim_python.is_file():
        ap.error(f"simulator Python not found: {a.sim_python}")
    out = a.out or HERE / "results" / f"pilot_{a.vehicle}_{a.observation}_{a.mode}_seed{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(a.seed)
    begin = time.time()
    teacher = worker(a, "teacher", out / "teacher.npz")
    model = ActorCritic()
    bc_loss = behavior_clone(model, teacher["phi"], teacher["target"], a.bc_epochs, a.seed)
    dagger = []
    training_phi = teacher["phi"].copy()
    training_target = teacher["target"].copy()
    for k in range(a.dagger_rounds):
        weights = out / f"dagger_policy_{k:03d}.npz"
        export_numpy(model, weights)
        visited = worker(a, "eval", out / f"dagger_{k:03d}.npz", weights)
        training_phi = np.concatenate([training_phi, visited["phi"]])
        training_target = np.concatenate([training_target, visited["target"]])
        loss = behavior_clone(model, training_phi, training_target, a.dagger_epochs, a.seed + k + 1)
        dagger.append(dict(round=k, visited=len(visited["t"]),
                           gates=int(visited["gates"][-1]),
                           collisions=int(visited["collisions"][-1]),
                           total_labeled=len(training_phi), bc_loss=loss))
        print(f"DAgger {k+1}/{a.dagger_rounds}: gates={dagger[-1]['gates']} "
              f"collision={dagger[-1]['collisions']} labeled={len(training_phi)}", flush=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-4)
    training = []
    for k in range(a.ppo_rollouts):
        weights = out / f"policy_before_{k:03d}.npz"
        export_numpy(model, weights)
        trace = worker(a, "train", out / f"train_{k:03d}.npz", weights)
        loss = ppo_update(model, trace, optimizer, a.ppo_epochs)
        training.append(dict(rollout=k, samples=len(trace["t"]),
                             simulator_steps=round(len(trace["t"]) * a.policy_dt / 0.002),
                             return_sum=float(trace["reward"].sum()),
                             gates=int(trace["gates"][-1]), collisions=int(trace["collisions"][-1]),
                             ppo_loss=loss))
        print(f"PPO {k+1}/{a.ppo_rollouts}: gates={training[-1]['gates']} "
              f"collisions={training[-1]['collisions']} return={training[-1]['return_sum']:.3f}", flush=True)
    weights = out / "policy_final.npz"
    export_numpy(model, weights)
    torch.save(model.state_dict(), out / "policy_final.pt")
    evaluation = worker(a, "eval", out / "eval.npz", weights)
    summary = dict(vehicle=a.vehicle, mode=a.mode, seed=a.seed,
                   observation=a.observation,
                   episode_s=a.episode_s, policy_dt=a.policy_dt,
                   bc_samples=len(teacher["t"]), bc_epochs=a.bc_epochs, bc_final_loss=bc_loss,
                   dagger_rounds=a.dagger_rounds, dagger_epochs=a.dagger_epochs,
                   dagger_training=dagger,
                   ppo_rollouts=a.ppo_rollouts, ppo_epochs=a.ppo_epochs, training=training,
                   eval_samples=len(evaluation["t"]), eval_return=float(evaluation["reward"].sum()),
                   eval_gates=int(evaluation["gates"][-1]), eval_collisions=int(evaluation["collisions"][-1]),
                   eval_termination_reason=str(evaluation["done_reason"][-1]),
                   eval_position_error_mean_m=float(evaluation["pos_error"].mean()),
                   eval_saturation_mean=float(evaluation["saturation"].mean()),
                   eval_spikes_per_unit_hz=(evaluation["events"][-1] /
                                            (len(evaluation["t"]) * a.policy_dt)).tolist(),
                   teacher_gates=int(teacher["gates"][-1]),
                   teacher_position_error_mean_m=float(teacher["pos_error"].mean()),
                   wall_s=time.time() - begin,
                   note="Exploratory trajectory-conditioned BC+PPO; no ACC paper or Swift equivalence claim")
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    (out / "manifest.json").write_text(json.dumps(dict(
        args={k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
        source_hashes={x: sha256(HERE / x) for x in
                       ("cmg_cells.py", "policy_basis.py", "racing_env.py", "rollout_worker.py", "train_split.py")},
        race_source_hashes={x: sha256(HERE.parent / x) for x in
                            ("build_scene.py", "controller.py", "race.py", "track.py")},
        vehicle_xml_hash=sha256(HERE / "results" / f"race_world_{a.vehicle}.xml"),
        torch_version=torch.__version__, numpy_version=np.__version__,
        policy_parameter_count=sum(p.numel() for p in model.parameters()),
        separation="MuJoCo/SciPy worker and PyTorch trainer are distinct processes"), indent=2))
    print(json.dumps({k: summary[k] for k in ("mode", "eval_gates", "eval_collisions",
                    "eval_position_error_mean_m", "eval_return", "wall_s")}, indent=2))
    print(out)


if __name__ == "__main__":
    main()
