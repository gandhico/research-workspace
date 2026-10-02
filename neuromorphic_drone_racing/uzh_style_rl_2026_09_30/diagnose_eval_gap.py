"""Train/eval gap check for a saved policy: gates per episode under four conditions, 512 episodes each (batched sim):
deterministic (mean action) vs stochastic (training noise), official start vs UZH distributed start.
Usage: python diagnose_eval_gap.py <run_dir_name> [more ...]  -> prints JSON, writes results/<run>/eval_gap.json"""
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
from vec_race import VecRace  # noqa: E402
from train_ppo import ActorCritic, Features, RunningNorm, OBS_DIM, N_UNITS  # noqa: E402

torch.set_num_threads(6)


def run(ck, stochastic, p_official, n=512, steps=750, seed=21):
    torch.manual_seed(seed)
    sim = VecRace(n, seed=seed, p_official_start=p_official, episode_s=steps * 0.02)
    feat = Features(ck["arm"], n, ck["seed"])
    model = ActorCritic(OBS_DIM + N_UNITS, 0.0); model.load_state_dict(ck["model"])
    norm = RunningNorm(OBS_DIM + N_UNITS); norm.mean, norm.var = ck["norm_mean"], ck["norm_var"]
    alive = torch.ones(n, dtype=torch.bool); gates = torch.zeros(n); crashed = torch.zeros(n, dtype=torch.bool)
    with torch.no_grad():
        for _ in range(steps):
            obs = sim.observe()
            x = norm(torch.cat([obs, feat(obs)], 1))
            a = torch.tanh(model.dist(x).sample() if stochastic else model.pi(x))
            _, done, info = sim.step(a)
            gates = torch.where(alive, info["gates_passed"].float(), gates)
            crashed |= alive & done & ~info["timeout"]
            alive &= ~done
            if not alive.any():
                break
    return {"gates_mean": round(float(gates.mean()), 2), "frac_full_lap": round(float((gates >= 7).float().mean()), 3),
            "crash_rate": round(float(crashed.float().mean()), 3)}


for name in sys.argv[1:]:
    ck = torch.load(HERE / "results" / name / "policy.pt", weights_only=False)
    out = {f"{'stoch' if s else 'det'}_{'official' if p == 1.0 else 'distributed'}": run(ck, s, p)
           for s in (False, True) for p in (1.0, 0.0)}
    (HERE / "results" / name / "eval_gap.json").write_text(json.dumps(out, indent=1))
    print(name, json.dumps(out))
