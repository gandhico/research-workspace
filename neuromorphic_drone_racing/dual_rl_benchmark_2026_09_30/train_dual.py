"""PPO trainer for the dual racing pilot (PyTorch only; MuJoCo runs in dual_worker.py subprocesses).

Reuses Codex's ppo_update from ../rl_cmg_2026_09_30/train_split.py unchanged. Differences from the direct pilot:
the action is the arm's slice of the 7-D dual latent, there is no behavior cloning, and the actor's mean head starts
at exactly zero so the deterministic initial policy is the geometric teacher. See PREREGISTRATION.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "rl_cmg_2026_09_30"
sys.path.insert(0, str(PARENT))
from train_split import DEFAULT_PYTHON, export_numpy, ppo_update  # noqa: E402

WORKER = HERE / "dual_worker.py"
ACT_DIM = {"self": 3, "residual": 4, "dual": 7}


class ActorCritic(nn.Module):
    def __init__(self, act_dim: int, log_std0: float):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(58, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh())
        self.mean = nn.Linear(64, act_dim)
        self.value_head = nn.Linear(64, 1)
        self.log_std = nn.Parameter(torch.full((act_dim,), log_std0))
        nn.init.zeros_(self.mean.weight)
        nn.init.zeros_(self.mean.bias)

    def forward(self, x):
        z = self.body(x)
        return self.mean(z), self.value_head(z).squeeze(-1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker(a, kind, arm, scenario, out, weights=None):
    cmd = [str(a.sim_python), str(WORKER), "--kind", kind, "--arm", arm, "--mode", a.mode, "--vehicle", a.vehicle,
           "--scenario", scenario, "--seed", str(a.seed), "--episode-s", str(a.episode_s),
           "--samples", str(a.samples), "--out", str(out)]
    if weights is not None:
        cmd += ["--weights", str(weights)]
    run = subprocess.run(cmd, text=True, capture_output=True, cwd=str(HERE))
    if run.returncode:
        raise RuntimeError(f"worker failed ({run.returncode})\n{run.stdout}\n{run.stderr}")
    print(run.stdout.strip(), flush=True)
    return dict(np.load(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=list(ACT_DIM), required=True)
    ap.add_argument("--mode", choices=["mlp", "graded"], required=True)
    ap.add_argument("--vehicle", choices=["x2", "cf2"], default="x2")
    ap.add_argument("--train-scenario", choices=["nominal", "gust"], default="gust")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--episode-s", type=float, default=12.0)
    ap.add_argument("--rollouts", type=int, default=10)
    ap.add_argument("--samples", type=int, default=600)
    ap.add_argument("--ppo-epochs", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--log-std0", type=float, default=-1.6)
    ap.add_argument("--sim-python", type=Path, default=DEFAULT_PYTHON)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    out = a.out or HERE / "results" / f"pilot_{a.vehicle}_{a.arm}_{a.mode}_seed{a.seed}"
    out.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(a.seed)
    begin = time.time()
    model = ActorCritic(ACT_DIM[a.arm], a.log_std0)
    optimizer = torch.optim.Adam(model.parameters(), lr=a.lr)
    training = []
    for k in range(a.rollouts):
        w = out / f"policy_before_{k:03d}.npz"
        export_numpy(model, w)
        trace = worker(a, "train", a.arm, a.train_scenario, out / f"train_{k:03d}.npz", w)
        loss = ppo_update(model, trace, optimizer, a.ppo_epochs)
        training.append(dict(rollout=k, samples=int(len(trace["t"])), episodes=int(trace["episode_id"][-1]) + 1,
                             return_sum=float(trace["reward"].sum()),
                             mean_position_error_m=float(trace["pos_error"].mean()),
                             collisions_last_episode=int(trace["collisions"][-1]), ppo_loss=loss,
                             log_std=model.log_std.detach().numpy().tolist()))
        print(f"rollout {k + 1}/{a.rollouts}: return={training[-1]['return_sum']:.2f} "
              f"pos_err={training[-1]['mean_position_error_m']:.4f} m", flush=True)
    final = out / "policy_final.npz"
    export_numpy(model, final)
    torch.save(model.state_dict(), out / "policy_final.pt")
    evaluation = {}
    for scenario in ("gust", "nominal"):
        worker(a, "eval", a.arm, scenario, out / f"eval_{scenario}.npz", final)
        evaluation[scenario] = json.loads((out / f"eval_{scenario}.json").read_text())
    summary = dict(arm=a.arm, mode=a.mode, vehicle=a.vehicle, seed=a.seed, train_scenario=a.train_scenario,
                   rollouts=a.rollouts, samples_per_rollout=a.samples,
                   mujoco_training_steps=a.rollouts * a.samples * 10, training=training, evaluation=evaluation,
                   wall_s=time.time() - begin, note="Exploratory dual racing pilot; see PREREGISTRATION.md")
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    (out / "manifest.json").write_text(json.dumps(dict(
        args={k: str(v) if isinstance(v, Path) else v for k, v in vars(a).items()},
        source_hashes={p.name: sha256(p) for p in (HERE / "dual_env.py", WORKER, Path(__file__).resolve(),
                                                    PARENT / "train_split.py", PARENT / "rollout_worker.py",
                                                    PARENT / "policy_basis.py", PARENT / "cmg_cells.py",
                                                    PARENT / "racing_env.py")},
        torch_version=torch.__version__, numpy_version=np.__version__,
        policy_parameter_count=sum(p.numel() for p in model.parameters())), indent=2))
    print(json.dumps({s: {k: evaluation[s][k] for k in ("gates", "collisions", "mean_position_error_m")}
                      for s in evaluation}, indent=2))


if __name__ == "__main__":
    main()
