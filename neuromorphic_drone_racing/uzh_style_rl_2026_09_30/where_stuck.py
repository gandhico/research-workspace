"""Deterministic official-start flight of a saved policy: gate times, then where the drone is after its last gate."""
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
from vec_race import VecRace  # noqa: E402
from train_ppo import ActorCritic, Features, RunningNorm, OBS_DIM, N_UNITS  # noqa: E402

torch.set_num_threads(2)
ck = torch.load(HERE / "results" / sys.argv[1] / "policy.pt", weights_only=False)
sim = VecRace(1, seed=ck["seed"] + 99, episode_s=40.0, p_official_start=1.0)
feat = Features(ck["arm"], 1, ck["seed"])
model = ActorCritic(OBS_DIM + N_UNITS, 0.0); model.load_state_dict(ck["model"])
norm = RunningNorm(OBS_DIM + N_UNITS); norm.mean, norm.var = ck["norm_mean"], ck["norm_var"]
gates, trace = [], []
with torch.no_grad():
    for k in range(2000):
        obs = sim.observe()
        _, done, info = sim.step(torch.tanh(model.pi(norm(torch.cat([obs, feat(obs)], 1)))))
        t = (k + 1) * 0.02
        if info["passed"][0]: gates.append(round(t, 2))
        if k % 50 == 49 or done[0]:
            g = int(sim.next_gate[0])
            trace.append(dict(t=round(t, 1), next_gate=g, p=[round(x, 2) for x in sim.p[0].tolist()],
                              speed=round(float(sim.v[0].norm()), 2),
                              dist_to_gate=round(float((sim.p[0] - sim.gc[g]).norm()), 2)))
        if done[0]:
            trace.append(dict(end="timeout" if info["timeout"][0] else
                              [k for k in ("crashed", "ground", "outside") if info[k][0]]))
            break
print(json.dumps(dict(gate_times=gates, gate_centres=sim.gc.tolist(), trace=trace), indent=0))
