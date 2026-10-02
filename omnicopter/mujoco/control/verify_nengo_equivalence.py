"""Numerically verify direct and Nengo Omnicopter controller equivalence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mujoco
import numpy as np

from hover import make_sim, reset
from missions import MISSIONS, apply_reference, reference_kinematics
from nengo_controllers import NengoCMGPESController, NengoPDController
from residual import PESWrenchAugmentor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("--steps must be positive")
    mission = next(m for m in MISSIONS if m.name == "yaw_360_6s")
    model, data, controller = make_sim()
    reset(model, data, controller, False)
    q0 = controller.target_q.copy()
    nengo_pd = NengoPDController(controller, model.opt.timestep)
    direct_cmg = PESWrenchAugmentor(controller, beta=.05, learning_rate=8e-4, leak=1e-6)
    nengo_cmg = NengoCMGPESController(
        controller, model.opt.timestep, beta=.05, learning_rate=8e-4, leak=1e-6)
    maxima = {
        "pd_wrench_max_abs_error": 0., "pd_motor_max_abs_error_N": 0.,
        "cmg_motor_max_abs_error_N": 0., "cmg_residual_norm_max_abs_error": 0.,
    }
    try:
        for _ in range(args.steps):
            mujoco.mj_forward(model, data)
            p, v, a, q, omega, alpha, _ = reference_kinematics(mission, data.time, q0)
            apply_reference(controller, p, v, a, q, omega, alpha)
            direct_wrench, _ = controller.desired_wrench(data)
            nengo_wrench, _ = nengo_pd.desired_wrench(data)
            direct_motor, _ = controller.allocate(direct_wrench)
            nengo_motor, _ = controller.allocate(nengo_wrench)
            maxima["pd_wrench_max_abs_error"] = max(
                maxima["pd_wrench_max_abs_error"],
                float(np.max(np.abs(direct_wrench-nengo_wrench))))
            maxima["pd_motor_max_abs_error_N"] = max(
                maxima["pd_motor_max_abs_error_N"],
                float(np.max(np.abs(direct_motor-nengo_motor))))
            direct_out, direct_metrics = direct_cmg.command(data, model.opt.timestep)
            nengo_out, nengo_metrics = nengo_cmg.command(data, model.opt.timestep)
            maxima["cmg_motor_max_abs_error_N"] = max(
                maxima["cmg_motor_max_abs_error_N"],
                float(np.max(np.abs(direct_out-nengo_out))))
            maxima["cmg_residual_norm_max_abs_error"] = max(
                maxima["cmg_residual_norm_max_abs_error"],
                abs(direct_metrics["pes_residual_norm"]-nengo_metrics["pes_residual_norm"]))
            data.ctrl[:] = direct_motor
            mujoco.mj_step(model, data)
    finally:
        nengo_pd.close()
        nengo_cmg.close()
    thresholds = {
        "pd_wrench_max_abs_error": 1e-10,
        "pd_motor_max_abs_error_N": 1e-10,
        # Nengo schedules the teaching signal through its graph; the decoder
        # may differ by one PES increment while commands remain tightly matched.
        "cmg_motor_max_abs_error_N": 1e-4,
        "cmg_residual_norm_max_abs_error": 1e-4,
    }
    passed = all(maxima[key] <= limit for key, limit in thresholds.items())
    result = {
        "status": "pass" if passed else "fail", "steps": args.steps,
        "dt_s": float(model.opt.timestep), "mission_excitation": mission.name,
        "maxima": maxima, "thresholds": thresholds,
        "scope": "software backend equivalence; not physical validation",
    }
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not passed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
