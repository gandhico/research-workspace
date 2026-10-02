"""Extract the X2 race-world parameters from MuJoCo and record a reference flight for simulator validation.

Writes results/x2_params.json (everything the batched trainer needs) and results/x2_reference_flight.npz:
the geometric controller's commands projected onto the policy's thrust/body-rate interface and executed through
RacingEnv.step (the same path a learned policy uses), 600 decisions = 12 s, with the full state at every decision.
Run with the hyperlif environment (MuJoCo + SciPy; no PyTorch).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rl_cmg_2026_09_30"))
sys.path.insert(0, str(HERE.parent))
from racing_env import RacingEnv  # noqa: E402
import track  # noqa: E402
from race import HALF_SPAN  # noqa: E402


def main():
    env = RacingEnv("x2", policy_dt=0.02, episode_s=12.0, seed=1, observation="reference")
    c, m = env.teacher, env.m
    p0, v0, R0, w0 = c.state(env.d)
    params = dict(
        vehicle="x2", plant_dt=float(m.opt.timestep), policy_dt=env.policy_dt, substeps=env.substeps,
        integrator=int(m.opt.integrator), gravity=m.opt.gravity.tolist(),
        mass=c.mass, J=c.J.tolist(), B_full=c.B.tolist(), Bs=c.Bs.tolist(), Bpinv=c.Bpinv.tolist(),
        rotor_lo=c.lo.tolist(), rotor_hi=c.hi.tolist(), tmax=float(env.tmax), rate_max=env.rate_max.tolist(),
        rate_gain=env.rate_gain.tolist(), alloc_weights=[1.0, 1.0, 1.0, 0.05], half_span=HALF_SPAN["x2"],
        thrust_to_weight=float(c.tw),
        start=dict(p=p0.tolist(), v=v0.tolist(), R=R0.tolist(), w=w0.tolist(), time=env.start_time),
        gates=[dict(name=n, centre=list(cc), yaw_deg=float(y)) for n, cc, y in track.GATES],
        gate_inner=track.GATE_INNER, gate_border=track.GATE_BORDER, gate_depth=track.GATE_DEPTH, leg_radius=0.04,
    )
    line = track.RaceLine()
    u = np.linspace(0.0, len(track.GATES), 7 * 200, endpoint=False)          # segment k = gate k -> gate k+1
    d1 = line._eval(u, 1)
    params["race_line"] = dict(u=u.tolist(), p=line._eval(u, 0).tolist(),
                               tangent=(d1 / np.linalg.norm(d1, axis=1, keepdims=True)).tolist(),
                               next_gate=((np.floor(u).astype(int) + 1) % len(track.GATES)).tolist(),
                               length_m=line.length)
    (HERE / "results" / "x2_params.json").write_text(json.dumps(params, indent=1))

    env.reset()
    rec = {k: [] for k in ("t", "p", "v", "R", "w", "action", "rotor", "gates", "collisions", "sat")}
    for _ in range(600):
        p, v, R, w = c.state(env.d)
        a = env.teacher_action()
        rec["t"].append(float(env.d.time)); rec["p"].append(p); rec["v"].append(v); rec["R"].append(R.copy())
        rec["w"].append(w); rec["action"].append(a)
        _, _, done, info = env.step(a)
        rec["rotor"].append(info["rotor"]); rec["gates"].append(info["gates_in_order"])
        rec["collisions"].append(info["collisions"]); rec["sat"].append(info["saturation_fraction"])
        if done:
            break
    p, v, R, w = c.state(env.d)
    rec["t"].append(float(env.d.time)); rec["p"].append(p); rec["v"].append(v); rec["R"].append(R.copy()); rec["w"].append(w)
    np.savez_compressed(HERE / "results" / "x2_reference_flight.npz", **{k: np.asarray(x) for k, x in rec.items()})
    print(json.dumps(dict(decisions=len(rec["action"]), gates=rec["gates"][-1], collisions=rec["collisions"][-1],
                          end=info["termination_reason"], mean_saturation=float(np.mean(rec["sat"])),
                          mass=c.mass, tmax=env.tmax, integrator=int(m.opt.integrator)), indent=1))


if __name__ == "__main__":
    main()
