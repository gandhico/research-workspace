"""Baseline-recovery gate for the racing dual controller."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from dual_env import DualEnv

HERE = Path(__file__).resolve().parent


def run(vehicle, scenario, policy):
    env = DualEnv(vehicle, scenario, episode_s=12.0)
    env.reset()
    positions = []
    errors = []
    for _ in range(600):
        action = env.teacher_action()
        if policy == "direct_teacher":
            _, _, done, info = env.step(action, teacher=True)
        else:
            _, _, done, info = env.step_dual(np.zeros(7), "baseline")
        positions.append(info["position"])
        errors.append(info["position_error_m"])
        if done:
            break
    return np.asarray(positions), np.asarray(errors), info


def main():
    out = HERE / "results" / "parity"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for vehicle in ("x2", "cf2"):
        for scenario in ("nominal", "gust"):
            p0, e0, i0 = run(vehicle, scenario, "direct_teacher")
            p1, e1, i1 = run(vehicle, scenario, "zero_dual")
            assert len(p0) == len(p1), (vehicle, scenario, len(p0), len(p1))
            delta = float(np.max(np.abs(p0 - p1)))
            row = dict(vehicle=vehicle, scenario=scenario, samples=len(p0),
                       max_position_delta_m=delta,
                       direct_gates=i0["gates_in_order"], dual_zero_gates=i1["gates_in_order"],
                       direct_mean_error_m=float(e0.mean()), dual_zero_mean_error_m=float(e1.mean()),
                       direct_end=i0["termination_reason"], dual_zero_end=i1["termination_reason"])
            rows.append(row)
            print(row, flush=True)
            np.savez_compressed(out / f"{vehicle}_{scenario}.npz", direct_position=p0,
                                zero_dual_position=p1, direct_error=e0, zero_dual_error=e1)
    (out / "summary.json").write_text(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
