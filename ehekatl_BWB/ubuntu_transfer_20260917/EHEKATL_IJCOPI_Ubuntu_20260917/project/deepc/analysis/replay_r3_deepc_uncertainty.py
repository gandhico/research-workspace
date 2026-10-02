#!/usr/bin/env python3
"""Replay provisional DeePC on the frozen R3 cascade and 243-case uncertainty set."""

from __future__ import annotations

import csv
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from deepc.src.regularized_deepc import RegularizedDeePC  # noqa: E402
from lqr.discrete_cascade_roll_lqr import (  # noqa: E402
    COMMAND_LIMIT,
    K,
    SLEW_LIMIT,
)
from synthesize_rich_r3_roll_discrete_lqr import matrices  # noqa: E402


HZ = 35.0
DT = 1.0 / HZ
SECONDS = 30.0
PULSE_STARTS = (10.0, 12.0)
PULSE_DURATION = 0.2
PULSE_AMPLITUDE = 0.00005
TRAINING = ROOT / "logs/rich_R3_roll_dualrate_pilot_20260712_193416.csv"
OUTPUT = ROOT / "configs/rich_R3_deepc_uncertainty_replay.json"


def pulse(t: float) -> float:
    for index, start in enumerate(PULSE_STARTS):
        if start <= t <= start + PULSE_DURATION:
            sign = 1.0 if index % 2 == 0 else -1.0
            return sign * PULSE_AMPLITUDE * np.sin(np.pi * (t - start) / PULSE_DURATION)
    return 0.0


def load_deepc() -> tuple[RegularizedDeePC, np.ndarray, np.ndarray]:
    with TRAINING.open(newline="") as stream:
        raw = np.asarray(
            [
                [float(row[name]) for name in ["t_s", "yoke_roll_ratio", "p_deg_s"]]
                for row in csv.DictReader(stream)
            ]
        )
    library = raw[(raw[:, 0] >= 5.0) & (raw[:, 0] < 15.0), 1:]
    center = library.mean(axis=0)
    scale = library.std(axis=0, ddof=1)
    normalized = (library - center) / scale
    return RegularizedDeePC(normalized[:, 0], normalized[:, 1], 5, 5, 10.0), center, scale


def bounded(value: float, previous: float) -> float:
    value = float(np.clip(value, -COMMAND_LIMIT, COMMAND_LIMIT))
    return float(np.clip(value, previous - SLEW_LIMIT, previous + SLEW_LIMIT))


def simulate(a: np.ndarray, b: np.ndarray, mode: str, deepc, center, scale):
    state = np.zeros(3)
    phi = 0.0
    previous = 0.0
    u_history = [0.0] * 5
    p_history = [0.0] * 5
    p_values, angles, commands, sent_values, runtimes = [], [], [], [], []
    converged = True
    for sample in range(round(SECONDS * HZ)):
        t = sample * DT
        if mode == "lqr":
            requested = float(-K @ state)
        elif mode == "deepc":
            # The behavioral library uses absolute measured coordinates. The
            # cascade uses perturbations, so add/remove the training biases.
            u_ini = np.asarray(u_history) / scale[0]
            p_ini = (np.asarray(p_history) - center[1]) / scale[1]
            reference = np.full(5, (0.0 - center[1]) / scale[1])
            began = time.perf_counter()
            result = deepc.optimize(
                u_ini,
                p_ini,
                reference,
                COMMAND_LIMIT / scale[0],
                SLEW_LIMIT / scale[0],
                tolerance=1e-7,
                max_iterations=300,
            )
            runtimes.append((time.perf_counter() - began) * 1000.0)
            converged = converged and result.converged
            requested = float(result.future_u[0] * scale[0])
        else:
            raise ValueError(mode)
        command = bounded(requested, previous)
        disturbance = pulse(t)
        sent = command + disturbance
        state = a @ state + b[:, 0] * sent
        phi += DT * state[0]
        previous = command
        u_history = u_history[1:] + [command]
        p_history = p_history[1:] + [float(state[0])]
        p_values.append(state[0])
        angles.append(phi)
        commands.append(command)
        sent_values.append(sent)
    p_values = np.asarray(p_values)
    angles = np.asarray(angles)
    commands = np.asarray(commands)
    sent_values = np.asarray(sent_values)
    timeline = np.arange(len(p_values)) * DT
    active = (timeline >= 10.0) & (timeline < 18.0)
    final = timeline >= 25.0
    slew = np.diff(np.concatenate([[0.0], commands]))
    sent_slew = np.diff(np.concatenate([[0.0], sent_values]))
    return {
        "peak_abs_p_deg_s": float(np.max(np.abs(p_values[active]))),
        "integral_abs_p_deg": float(np.sum(np.abs(p_values[active])) * DT),
        "peak_abs_roll_deg": float(np.max(np.abs(angles))),
        "final_5s_max_abs_p_deg_s": float(np.max(np.abs(p_values[final]))),
        "final_5s_max_abs_roll_deg": float(np.max(np.abs(angles[final]))),
        "peak_abs_base_command": float(np.max(np.abs(commands))),
        "peak_abs_sent_command": float(np.max(np.abs(sent_values))),
        "maximum_base_slew": float(np.max(np.abs(slew))),
        "maximum_sent_slew": float(np.max(np.abs(sent_slew))),
        "base_limit_exceeded_samples": int(np.sum(np.abs(commands) > COMMAND_LIMIT + 1e-15)),
        "sent_limit_exceeded_samples": int(np.sum(np.abs(sent_values) > COMMAND_LIMIT + 1e-15)),
        "base_slew_exceeded_samples": int(np.sum(np.abs(slew) > SLEW_LIMIT + 1e-15)),
        "sent_slew_exceeded_samples": int(np.sum(np.abs(sent_slew) > SLEW_LIMIT + 1e-15)),
        "optimizer_converged": converged,
        "runtime_ms_median": float(np.median(runtimes)) if runtimes else 0.0,
        "runtime_ms_p95": float(np.percentile(runtimes, 95)) if runtimes else 0.0,
        "runtime_ms_max": float(np.max(runtimes)) if runtimes else 0.0,
    }


def main() -> None:
    deepc, center, scale = load_deepc()
    model = json.loads((ROOT / "configs/rich_R3_roll_discrete_cascade.json").read_text())
    yoke = model["yoke_to_total"]["selected"]["beta"]
    surface = model["surface_to_p"]["selected"]["beta"]
    gain = model["total_to_surface"]["static_gain"]
    cases = []
    began = time.perf_counter()
    for scales in itertools.product((0.75, 1.0, 1.25), repeat=5):
        a, b = matrices(
            yoke[0] * scales[0],
            yoke[1] * scales[1],
            yoke[2] * scales[2],
            gain,
            surface[0] * scales[3],
            surface[1] * scales[4],
        )
        lqr = simulate(a, b, "lqr", deepc, center, scale)
        candidate = simulate(a, b, "deepc", deepc, center, scale)
        cases.append(
            {
                "coefficient_scales": scales,
                "lqr": lqr,
                "deepc": candidate,
                "integral_ratio_deepc_to_lqr": candidate["integral_abs_p_deg"] / lqr["integral_abs_p_deg"],
                "peak_ratio_deepc_to_lqr": candidate["peak_abs_p_deg_s"] / lqr["peak_abs_p_deg_s"],
            }
        )
    all_deepc = [item["deepc"] for item in cases]
    summary = {
        "cases": len(cases),
        "wall_time_s": time.perf_counter() - began,
        "worst_integral_ratio_deepc_to_lqr": max(item["integral_ratio_deepc_to_lqr"] for item in cases),
        "median_integral_ratio_deepc_to_lqr": float(np.median([item["integral_ratio_deepc_to_lqr"] for item in cases])),
        "worst_peak_ratio_deepc_to_lqr": max(item["peak_ratio_deepc_to_lqr"] for item in cases),
        "maximum_sent_command": max(item["peak_abs_sent_command"] for item in all_deepc),
        "maximum_sent_slew": max(item["maximum_sent_slew"] for item in all_deepc),
        "sent_limit_exceeded_samples": sum(item["sent_limit_exceeded_samples"] for item in all_deepc),
        "sent_slew_exceeded_samples": sum(item["sent_slew_exceeded_samples"] for item in all_deepc),
        "optimizer_nonconverged_cases": sum(not item["optimizer_converged"] for item in all_deepc),
        "worst_runtime_ms": max(item["runtime_ms_max"] for item in all_deepc),
        "control_period_ms": 1000.0 / HZ,
    }
    gates = {
        "integral_ratio_deepc_to_lqr_max": 0.90,
        "peak_ratio_deepc_to_lqr_max": 1.10,
        "sent_command_abs_max": COMMAND_LIMIT,
        "sent_slew_max": SLEW_LIMIT,
        "runtime_ms_max": 1000.0 / HZ,
        "optimizer_nonconverged_cases_max": 0,
    }
    passed = (
        summary["worst_integral_ratio_deepc_to_lqr"] <= gates["integral_ratio_deepc_to_lqr_max"]
        and summary["worst_peak_ratio_deepc_to_lqr"] <= gates["peak_ratio_deepc_to_lqr_max"]
        and summary["maximum_sent_command"] <= COMMAND_LIMIT + 1e-15
        and summary["maximum_sent_slew"] <= SLEW_LIMIT + 1e-15
        and summary["sent_limit_exceeded_samples"] == 0
        and summary["sent_slew_exceeded_samples"] == 0
        and summary["optimizer_nonconverged_cases"] == 0
        and summary["worst_runtime_ms"] < 1000.0 / HZ
    )
    artifact = {
        "status": "pass" if passed else "fail",
        "training_file": str(TRAINING.relative_to(ROOT)),
        "held_out_response_files_opened": [],
        "plant": "frozen validated R3 discrete cascade",
        "disturbance": {"starts_s": PULSE_STARTS, "duration_s": PULSE_DURATION, "amplitude": PULSE_AMPLITUDE},
        "summary": summary,
        "prospective_offline_gates": gates,
        "cases": cases,
        "pass": passed,
        "claim_boundary": "Frozen-model uncertainty replay only; no X-Plane or superiority claim.",
    }
    OUTPUT.write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({"status": artifact["status"], "summary": summary, "gates": gates}, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()

