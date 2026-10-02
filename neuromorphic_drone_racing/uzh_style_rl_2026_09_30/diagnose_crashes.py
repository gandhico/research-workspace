"""Why does every PPO episode end in failure? (1) does the teacher's clean MuJoCo flight trip the analytic crash
check? (2) for a trained policy: failure-type breakdown, time to failure, gates, distance to the next gate centre."""
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
from vec_race import VecRace  # noqa: E402
from train_ppo import ActorCritic, Features, RunningNorm, OBS_DIM, N_UNITS  # noqa: E402

torch.set_num_threads(4)
out = {}
rec = dict(np.load(HERE / "results" / "x2_reference_flight.npz"))
T = lambda x: torch.as_tensor(x, dtype=torch.float64)
gates = torch.as_tensor(rec["gates"])
ng = torch.cat([torch.zeros(1, dtype=torch.long), gates[:-1]]) % 7
sim = VecRace(1, dtype=torch.float64, episode_s=1e9)
crash_steps, ground_steps = [], []
for k in range(len(rec["action"])):
    sim.set_state(T(rec["p"][k:k + 1]), T(rec["v"][k:k + 1]), T(rec["R"][k:k + 1]), T(rec["w"][k:k + 1]), ng[k:k + 1])
    _, _, info = sim.step(T(rec["action"][k:k + 1]))
    if info["crashed"][0]: crash_steps.append(k)
    if info["ground"][0]: ground_steps.append(k)
out["teacher_forced"] = dict(crash_decisions=len(crash_steps), first=crash_steps[:10], ground_decisions=len(ground_steps),
                             start_z=float(rec["p"][0, 2]), half_span=sim.half_span)

for run in sys.argv[1:]:
    ck = torch.load(HERE / "results" / run / "policy.pt", weights_only=False)
    n = 2048
    sim = VecRace(n, seed=5)
    feat = Features(ck["arm"], n, ck["seed"])
    model = ActorCritic(OBS_DIM + N_UNITS, 0.0)
    model.load_state_dict(ck["model"])
    norm = RunningNorm(OBS_DIM + N_UNITS); norm.mean, norm.var = ck["norm_mean"], ck["norm_var"]
    kinds = dict(crashed=0, ground=0, outside=0, timeout=0)
    t_fail, g_fail, d_fail, speed = [], [], [], []
    alive = torch.ones(n, dtype=torch.bool)
    with torch.no_grad():
        for step in range(750):
            obs = sim.observe()
            a = torch.tanh(model.pi(norm(torch.cat([obs, feat(obs)], 1))))
            _, done, info = sim.step(a)
            new = done & alive
            for k in kinds:
                kinds[k] += int((info[k] & new).sum())
            if new.any():
                t_fail += [step * 0.02] * int(new.sum())
                g_fail += info["gates_passed"][new].tolist()
                d_fail += (sim.p[new] - sim.gc[sim.next_gate[new]]).norm(dim=1).tolist()
                speed += sim.v[new].norm(dim=1).tolist()
            alive &= ~done
            if not alive.any():
                break
    out[run] = dict(deterministic=True, n=n, failure_types=kinds, median_t_fail_s=float(np.median(t_fail)),
                    mean_gates=float(np.mean(g_fail)), median_dist_to_next_gate_m=float(np.median(d_fail)),
                    median_speed_at_fail=float(np.median(speed)))
print(json.dumps(out, indent=1))
