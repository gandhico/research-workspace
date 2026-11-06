"""Seeded Omnicopter CMG cell-count study under synthetic model mismatch.

Controller forces always enter through data.ctrl.  xfrc_applied is used only to
represent an unmodelled external environment disturbance in this stress test.
The disturbance is deliberately synthetic; it is not an identified airflow
claim.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

RESEARCH = Path(__file__).resolve().parent
CONTROL = RESEARCH.parent
sys.path.insert(0, str(CONTROL))

from hover import XML, attitude_error, make_sim, reset, rotation  # noqa: E402
from missions import MISSIONS, apply_reference, reference_kinematics  # noqa: E402
from residual import PESWrenchAugmentor  # noqa: E402
from heterogeneous_cmg import HeadroomProjectedCMGPES  # noqa: E402

DEFAULT_MISSIONS = ("hover_push", "yaw_360_12s")


def unit_vector(rng):
    value = rng.normal(size=3)
    return value / np.linalg.norm(value)


def uncertainty(seed):
    rng = np.random.default_rng(seed)
    return {
        "mass_scale": float(rng.uniform(.90, 1.10)),
        "inertia_scale": rng.uniform(.85, 1.15, 3),
        "motor_gain": rng.uniform(.92, 1.08, 8),
        "motor_tau_s": rng.uniform(.025, .065, 8),
        "force_bias_world_N": unit_vector(rng)*rng.uniform(.4, 1.2),
        "force_wave_world_N": unit_vector(rng)*rng.uniform(.3, .8),
        "force_gust_world_N": unit_vector(rng)*rng.uniform(1.2, 2.5),
        "torque_bias_body_Nm": unit_vector(rng)*rng.uniform(.01, .035),
        "wave_frequency_hz": float(rng.uniform(.12, .35)),
        "wave_phase_rad": float(rng.uniform(-np.pi, np.pi)),
    }


def nominal_profile():
    return {
        "mass_scale": 1., "inertia_scale": np.ones(3),
        "motor_gain": np.ones(8), "motor_tau_s": np.full(8, 1e-6),
        "force_bias_world_N": np.zeros(3), "force_wave_world_N": np.zeros(3),
        "force_gust_world_N": np.zeros(3), "torque_bias_body_Nm": np.zeros(3),
        "wave_frequency_hz": 0., "wave_phase_rad": 0.,
    }


def disturbance(profile, t, duration):
    ramp = np.clip((t-.5)/1.0, 0., 1.)
    ramp = ramp*ramp*(3.-2.*ramp)
    phase = 2*np.pi*profile["wave_frequency_hz"]*t + profile["wave_phase_rad"]
    force = ramp*(profile["force_bias_world_N"] + profile["force_wave_world_N"]*np.sin(phase))
    gust_start = min(5., .45*duration)
    gust_length = 1.5
    u = (t-gust_start)/gust_length
    if 0. <= u <= 1.:
        force += profile["force_gust_world_N"]*np.sin(np.pi*u)**2
    torque = ramp*profile["torque_bias_body_Nm"]*(1.+.25*np.sin(.7*phase))
    return force, torque


def run_one(mission, controller_name, cells, seed, learning_rate, beta, timestep,
            nominal=False):
    profile = nominal_profile() if nominal else uncertainty(seed)
    model, data, controller = make_sim()
    model.opt.timestep = timestep
    reset(model, data, controller, False)
    q0 = controller.target_q.copy()

    # Freeze the controller's nominal copies, then perturb the actual plant.
    model.body_mass[controller.bid] *= profile["mass_scale"]
    model.body_inertia[controller.bid] *= profile["inertia_scale"]
    mujoco.mj_setConst(model, data)
    mujoco.mj_forward(model, data)

    augmentor = None
    if controller_name == "legacy_12":
        augmentor = PESWrenchAugmentor(controller, beta=.05, learning_rate=8e-4, leak=1e-6)
    elif controller_name.startswith("cmg_"):
        augmentor = HeadroomProjectedCMGPES(
            controller, cells=cells, seed=10_000+seed, learning_rate_per_s=learning_rate,
            beta=beta)

    p, v, a, q, omega, alpha, _ = reference_kinematics(mission, 0., q0)
    apply_reference(controller, p, v, a, q, omega, alpha)
    mujoco.mj_forward(model, data)
    motor_state = controller.command(data)[0].copy()

    dt = model.opt.timestep
    steps = int(round(mission.duration/dt))
    sum_position_sq = sum_attitude_sq = 0.
    peak_position = peak_attitude = peak_control = 0.
    saturated = contacts = samples = 0
    peak_decoder = peak_residual = 0.
    failed = None
    for step in range(steps+1):
        if mission.kick_s is not None and step == round(mission.kick_s/dt):
            data.qvel[:3] += [.30, -.20, .15]
            data.qvel[3:6] += [.35, -.25, .20]
        mujoco.mj_forward(model, data)
        p, v, a, q, omega, alpha, _ = reference_kinematics(mission, data.time, q0)
        apply_reference(controller, p, v, a, q, omega, alpha)
        if augmentor is None:
            requested, metrics = controller.command(data)
        else:
            requested, metrics = augmentor.command(data, dt)

        target_motor = np.clip(profile["motor_gain"]*requested,
                               controller.allocator.lower, controller.allocator.upper)
        motor_state += (1.-np.exp(-dt/profile["motor_tau_s"]))*(target_motor-motor_state)
        data.ctrl[:] = motor_state
        force_world, torque_body = disturbance(profile, data.time, mission.duration)
        data.xfrc_applied[:] = 0.
        data.xfrc_applied[controller.bid, :3] = force_world
        data.xfrc_applied[controller.bid, 3:] = rotation(data.qpos[3:7]) @ torque_body

        if data.time >= 2.-1e-9:
            ep = float(np.linalg.norm(data.qpos[:3]-p))
            er = float(np.rad2deg(np.linalg.norm(attitude_error(data.qpos[3:7], q))))
            sum_position_sq += ep*ep
            sum_attitude_sq += er*er
            peak_position = max(peak_position, ep)
            peak_attitude = max(peak_attitude, er)
            peak_control = max(peak_control, float(np.max(np.abs(motor_state))))
            saturated += int(np.any(np.isclose(motor_state, controller.allocator.lower, atol=1e-6))
                             or np.any(np.isclose(motor_state, controller.allocator.upper, atol=1e-6)))
            contacts += int(data.ncon > 0)
            samples += 1
            peak_decoder = max(peak_decoder, float(metrics.get("pes_decoder_norm", 0.)))
            peak_residual = max(peak_residual, float(metrics.get("pes_residual_norm", 0.)))
        if not np.all(np.isfinite(data.qpos)) or data.qpos[2] < .35:
            failed = "nonfinite_or_height"
            break
        if step < steps:
            mujoco.mj_step(model, data)

    return {
        "mission": mission.name, "controller": controller_name,
        "cells": cells if controller_name.startswith("cmg_") else (12 if controller_name == "legacy_12" else 0),
        "seed": seed, "status": "pass" if failed is None and contacts == 0 else "fail",
        "failure": failed, "samples": samples,
        "position_RMSE_m": float(np.sqrt(sum_position_sq/max(samples, 1))),
        "attitude_RMSE_deg": float(np.sqrt(sum_attitude_sq/max(samples, 1))),
        "peak_position_error_m": peak_position, "peak_attitude_error_deg": peak_attitude,
        "peak_abs_motor_N": peak_control, "saturation_fraction": saturated/max(samples, 1),
        "contact_steps": contacts, "peak_decoder_norm": peak_decoder,
        "peak_residual_wrench_norm": peak_residual,
        "mass_scale": profile["mass_scale"],
        "mean_motor_gain": float(np.mean(profile["motor_gain"])),
        "mean_motor_tau_s": float(np.mean(profile["motor_tau_s"])),
        "force_bias_N": float(np.linalg.norm(profile["force_bias_world_N"])),
        "gust_peak_N": float(np.linalg.norm(profile["force_gust_world_N"])),
    }


def aggregate(rows):
    grouped = {}
    for row in rows:
        key = (row["controller"], row["cells"])
        grouped.setdefault(key, []).append(row)
    output = []
    for (name, cells), group in grouped.items():
        output.append({
            "controller": name, "cells": cells, "runs": len(group),
            "passed": sum(r["status"] == "pass" for r in group),
            "mean_position_RMSE_m": float(np.mean([r["position_RMSE_m"] for r in group])),
            "std_position_RMSE_m": float(np.std([r["position_RMSE_m"] for r in group],
                                                  ddof=1 if len(group) > 1 else 0)),
            "mean_attitude_RMSE_deg": float(np.mean([r["attitude_RMSE_deg"] for r in group])),
            "std_attitude_RMSE_deg": float(np.std([r["attitude_RMSE_deg"] for r in group],
                                                    ddof=1 if len(group) > 1 else 0)),
            "worst_peak_position_m": max(r["peak_position_error_m"] for r in group),
            "worst_peak_attitude_deg": max(r["peak_attitude_error_deg"] for r in group),
            "max_motor_N": max(r["peak_abs_motor_N"] for r in group),
            "max_saturation_fraction": max(r["saturation_fraction"] for r in group),
            "mean_peak_residual_norm": float(np.mean([r["peak_residual_wrench_norm"] for r in group])),
        })
    return output


def write_table(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", nargs="+", type=int, default=[12, 24, 48, 96, 192])
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(5)))
    parser.add_argument("--missions", nargs="+", default=list(DEFAULT_MISSIONS))
    parser.add_argument("--learning-rate", type=float, default=8., help="PES rate per simulated second")
    parser.add_argument("--beta", type=float, default=.25)
    parser.add_argument("--timestep", type=float, default=.005,
                        help="Screening timestep; finalists must be rechecked at canonical 0.002 s")
    parser.add_argument("--skip-comparators", action="store_true",
                        help="Run only requested heterogeneous CMG variants")
    parser.add_argument("--nominal", action="store_true",
                        help="Disable all synthetic plant/environment mismatch")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    mission_map = {m.name: m for m in MISSIONS}
    selected = [mission_map[name] for name in args.missions]
    if any(c < 12 for c in args.cells):
        parser.error("cell counts must be at least 12")
    output = args.output or RESEARCH / "output" / datetime.now().strftime("cell_seed_%Y%m%d_%H%M%S")
    output.mkdir(parents=True, exist_ok=False)
    config = {
        "study": "Omnicopter heterogeneous CMG-PES seeded synthetic-mismatch screen",
        "model_xml": str(XML), "model_sha256": hashlib.sha256(XML.read_bytes()).hexdigest(),
        "hover_sha256": hashlib.sha256((CONTROL/"hover.py").read_bytes()).hexdigest(),
        "missions_sha256": hashlib.sha256((CONTROL/"missions.py").read_bytes()).hexdigest(),
        "research_controller_sha256": hashlib.sha256((RESEARCH/"heterogeneous_cmg.py").read_bytes()).hexdigest(),
        "cells": args.cells, "seeds": args.seeds, "missions": [asdict(m) for m in selected],
        "learning_rate_per_s": args.learning_rate, "beta": args.beta,
        "screening_timestep_s": args.timestep,
        "nominal_plant": args.nominal,
        "comparators": ["frozen PD", "current canonical 12-cell CMG-PES"],
        "important_scope": "Synthetic stress test, not identified aerodynamics or hardware qualification",
    }
    (output/"config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    rows = []
    variants = ([] if args.skip_comparators else [("pd", 0), ("legacy_12", 12)])
    variants += [(f"cmg_{c}", c) for c in args.cells]
    total = len(variants)*len(args.seeds)*len(selected)
    completed = 0
    for controller_name, cells in variants:
        for seed in args.seeds:
            for mission in selected:
                row = run_one(mission, controller_name, cells, seed, args.learning_rate,
                              args.beta, args.timestep, args.nominal)
                rows.append(row)
                completed += 1
                print(f"[{completed:3d}/{total}] {controller_name:10s} seed={seed:2d} "
                      f"{mission.name:15s} pos={row['position_RMSE_m']:.4f}m "
                      f"att={row['attitude_RMSE_deg']:.3f}deg {row['status']}", flush=True)
                (output/"runs.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    summary = aggregate(rows)
    write_table(output/"runs.csv", rows)
    write_table(output/"aggregate.csv", summary)
    (output/"aggregate.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# Omnicopter CMG cell/seed screening", "",
             "Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.", "",
             "| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summary:
        lines.append(f"| {row['controller']} | {row['cells']} | {row['passed']}/{row['runs']} | "
                     f"{row['mean_position_RMSE_m']:.5f} ± {row['std_position_RMSE_m']:.5f} | "
                     f"{row['mean_attitude_RMSE_deg']:.3f} ± {row['std_attitude_RMSE_deg']:.3f} | "
                     f"{row['worst_peak_position_m']:.3f} | {row['worst_peak_attitude_deg']:.2f} | {row['max_motor_N']:.2f} |")
    lines += ["", "This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance."]
    (output/"REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
