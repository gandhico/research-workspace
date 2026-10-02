"""Per-episode reward decomposition of a saved policy (stochastic, as in training): progress, rate, smoothness, fail."""
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
from vec_race import VecRace  # noqa: E402
from train_ppo import ActorCritic, Features, RunningNorm, OBS_DIM, N_UNITS  # noqa: E402

torch.set_num_threads(4)
run = sys.argv[1]
ck = torch.load(HERE / "results" / run / "policy.pt", weights_only=False)
n = 1024
sim = VecRace(n, seed=11)
feat = Features(ck["arm"], n, ck["seed"])
model = ActorCritic(OBS_DIM + N_UNITS, 0.0); model.load_state_dict(ck["model"])
norm = RunningNorm(OBS_DIM + N_UNITS); norm.mean, norm.var = ck["norm_mean"], ck["norm_var"]
acc = {k: torch.zeros(n) for k in ("progress", "rate", "smooth", "fail", "steps")}
alive = torch.ones(n, dtype=torch.bool)
with torch.no_grad():
    for _ in range(750):
        obs = sim.observe()
        a = torch.tanh(model.dist(norm(torch.cat([obs, feat(obs)], 1))).sample())
        prev = sim.prev_action.clone()
        _, done, info = sim.step(a)
        m = alive.float()
        acc["progress"] += m * info["progress"].clamp(-1, 1)
        acc["rate"] -= m * sim.w_rate * (sim.w ** 2).sum(1)
        acc["smooth"] -= m * sim.w_smooth * ((a - prev) ** 2).sum(1)
        acc["fail"] -= m * sim.crash_penalty * (done & ~info["timeout"]).float()
        acc["steps"] += m
        alive &= ~done
        if not alive.any():
            break
print(json.dumps({k: round(float(v.mean()), 3) for k, v in acc.items()}, indent=1))
