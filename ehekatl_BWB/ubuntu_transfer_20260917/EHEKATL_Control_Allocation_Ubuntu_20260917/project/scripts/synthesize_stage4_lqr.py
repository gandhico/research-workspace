#!/usr/bin/env python3
"""Synthesize and robustly audit delay-aware Stage-4 LQR controllers offline."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np


DT = 0.1
NOMINAL_DELAY = 3
COMMAND_LIMIT = 0.003
SLEW_PER_SAMPLE = 0.0005
ANGLE_SCALE_DEG = 2.0
RATE_SCALE_DEG_S = 2.0
INNER_RATE_SCALE_DEG_S = 1.0
DISTURBANCES = ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0), (1.0, 1.0), (-1.0, -1.0))


def c2d_rk4(a: np.ndarray, b: np.ndarray, dt: float = DT, substeps: int = 100):
    augmented = np.block([[a, b], [np.zeros((1, 3))]])
    transition = np.eye(3)
    h = dt / substeps
    for _ in range(substeps):
        k1 = augmented @ transition
        k2 = augmented @ (transition + 0.5 * h * k1)
        k3 = augmented @ (transition + 0.5 * h * k2)
        k4 = augmented @ (transition + h * k3)
        transition += h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return transition[:2, :2], transition[:2, 2:3]


def augment_delay(ad: np.ndarray, bd: np.ndarray, delay: int):
    aa = np.zeros((2 + delay, 2 + delay))
    ba = np.zeros((2 + delay, 1))
    aa[:2, :2] = ad
    aa[:2, -1:] = bd
    ba[2, 0] = 1.0
    for index in range(1, delay):
        aa[2 + index, 2 + index - 1] = 1.0
    return aa, ba


def augment_delay_mismatch(ad: np.ndarray, bd: np.ndarray, plant_delay: int, history_length: int = 4):
    """Common-state plant for comparing delay 2/3/4 under one nominal controller."""
    if not 1 <= plant_delay <= history_length:
        raise ValueError("plant delay must fit inside command history")
    aa = np.zeros((2 + history_length, 2 + history_length))
    ba = np.zeros((2 + history_length, 1))
    aa[:2, :2] = ad
    aa[:2, 2 + plant_delay - 1 : 2 + plant_delay] = bd
    ba[2, 0] = 1.0
    for index in range(1, history_length):
        aa[2 + index, 2 + index - 1] = 1.0
    return aa, ba


def solve_dare(a: np.ndarray, b: np.ndarray, q: np.ndarray, r: np.ndarray):
    p = q.copy()
    for _ in range(100000):
        next_p = a.T @ p @ a - a.T @ p @ b @ np.linalg.solve(r + b.T @ p @ b, b.T @ p @ a) + q
        if np.max(np.abs(next_p - p)) < 1e-10:
            p = next_p
            break
        p = next_p
    else:
        raise RuntimeError("DARE iteration failed to converge")
    k = np.linalg.solve(r + b.T @ p @ b, b.T @ p @ a)
    return k, p


def simulate(a: np.ndarray, b: np.ndarray, k: np.ndarray, initial, seconds: float = 20.0):
    state = np.zeros(a.shape[0])
    state[:2] = initial
    previous = 0.0
    angles, rates, commands = [], [], []
    for _ in range(round(seconds / DT)):
        requested = float(-(k @ state)[0])
        command = float(np.clip(requested, previous - SLEW_PER_SAMPLE, previous + SLEW_PER_SAMPLE))
        command = float(np.clip(command, -COMMAND_LIMIT, COMMAND_LIMIT))
        state = a @ state + b[:, 0] * command
        previous = command
        angles.append(state[0]); rates.append(state[1]); commands.append(command)
    return {
        "peak_angle_deg": float(np.max(np.abs(angles))),
        "peak_rate_deg_s": float(np.max(np.abs(rates))),
        "final_angle_deg": float(angles[-1]),
        "final_rate_deg_s": float(rates[-1]),
        "final_5s_max_angle_deg": float(np.max(np.abs(angles[-50:]))),
        "final_5s_max_rate_deg_s": float(np.max(np.abs(rates[-50:]))),
        "peak_command": float(np.max(np.abs(commands))),
        "command_saturation_fraction": float(np.mean(np.abs(commands) >= COMMAND_LIMIT - 1e-12)),
    }


def read_replay_states(path: Path, angle_column: str, rate_column: str):
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    t = np.asarray([float(row["t_s"]) for row in rows])
    angle = np.asarray([float(row[angle_column]) for row in rows])
    rate = np.asarray([float(row[rate_column]) for row in rows])
    baseline = t < 10.0
    active = (t >= 10.0) & (t <= 50.0)
    return angle[active] - angle[baseline].mean(), rate[active] - rate[baseline].mean()


def scalar_rate_design(a_rate: float, control_gain: float):
    ad = float(np.exp(a_rate * DT))
    bd = float(control_gain * (ad - 1.0) / a_rate) if abs(a_rate) > 1e-12 else control_gain * DT
    aa = np.zeros((1 + NOMINAL_DELAY, 1 + NOMINAL_DELAY))
    ba = np.zeros((1 + NOMINAL_DELAY, 1))
    aa[0, 0] = ad
    aa[0, -1] = bd
    ba[1, 0] = 1.0
    for index in range(1, NOMINAL_DELAY):
        aa[1 + index, index] = 1.0
    q = np.diag([1 / INNER_RATE_SCALE_DEG_S**2] + [0.0] * NOMINAL_DELAY)
    r = np.asarray([[1 / COMMAND_LIMIT**2]])
    gain, _ = solve_dare(aa, ba, q, r)
    return aa, ba, q, r, gain


def audit_rate_controller(source: dict, root: Path, columns):
    beta = np.asarray(source["beta"], dtype=float)
    stderr = np.asarray(source["stderr"], dtype=float)
    rate_a, rate_b, q, r, rate_gain = scalar_rate_design(beta[1], beta[2])
    full_gain = np.concatenate(([0.0, rate_gain[0, 0]], rate_gain[0, 1:]))[None, :]
    ac = np.asarray(source["A_continuous"], dtype=float)
    bc = np.asarray(source["B_continuous"], dtype=float)
    ad, bd = c2d_rk4(ac, bc)
    aa, ba = augment_delay(ad, bd, NOMINAL_DELAY)
    nominal_poles = np.linalg.eigvals(aa - ba @ full_gain)
    robustness = []
    for signs in itertools.product((-2.0, 0.0, 2.0), repeat=3):
        varied = beta + np.asarray(signs) * stderr
        vad, vbd = c2d_rk4(np.array([[0.0, 1.0], [varied[0], varied[1]]]), np.array([[0.0], [varied[2]]]))
        for delay in (2, 3, 4):
            va, vb = augment_delay_mismatch(vad, vbd, delay)
            applied_gain = np.pad(full_gain, ((0, 0), (0, 1)))
            radius = float(np.max(np.abs(np.linalg.eigvals(va - vb @ applied_gain))))
            robustness.append({"sigma_offsets": signs, "delay_samples": delay, "spectral_radius": radius})
    disturbances = [dict(initial=list(initial), **simulate(aa, ba, full_gain, initial)) for initial in DISTURBANCES]
    log_replay = []
    for filename in source["training_files"] + source["validation_files"]:
        _, rate = read_replay_states(root / "logs" / filename, *columns)
        history = np.zeros(NOMINAL_DELAY); previous = 0.0; commands = []
        for omega in rate:
            state = np.concatenate(([omega], history))
            requested = float(-(rate_gain @ state)[0])
            command = float(np.clip(requested, previous - SLEW_PER_SAMPLE, previous + SLEW_PER_SAMPLE))
            command = float(np.clip(command, -COMMAND_LIMIT, COMMAND_LIMIT))
            history = np.concatenate(([command], history[:-1])); previous = command; commands.append(command)
        log_replay.append({"file": filename, "peak_offline_command": float(np.max(np.abs(commands))),
                           "rms_offline_command": float(np.sqrt(np.mean(np.square(commands)))),
                           "saturation_fraction": float(np.mean(np.abs(commands) >= COMMAND_LIMIT - 1e-12))})
    return {
        "reduced_A_delay": rate_a, "reduced_B_delay": rate_b, "Q": q, "R": r,
        "K_rate_history": rate_gain, "K_full_state_mapping": full_gain,
        "nominal_closed_loop_poles_full_plant": nominal_poles,
        "nominal_spectral_radius_full_plant": float(np.max(np.abs(nominal_poles))),
        "robustness_cases": len(robustness),
        "worst_case_spectral_radius": max(item["spectral_radius"] for item in robustness),
        "unstable_robustness_cases": sum(item["spectral_radius"] >= 1.0 for item in robustness),
        "worst_case": max(robustness, key=lambda item: item["spectral_radius"]),
        "disturbance_replays_full_plant": disturbances, "saved_log_command_replay": log_replay,
    }


def audit_axis(name: str, source: dict, root: Path):
    ac = np.asarray(source["A_continuous"], dtype=float)
    bc = np.asarray(source["B_continuous"], dtype=float)
    stderr = np.asarray(source["stderr"], dtype=float)
    ad, bd = c2d_rk4(ac, bc)
    aa, ba = augment_delay(ad, bd, NOMINAL_DELAY)
    q = np.diag([1 / ANGLE_SCALE_DEG**2, 1 / RATE_SCALE_DEG_S**2] + [0.0] * NOMINAL_DELAY)
    r = np.asarray([[1 / COMMAND_LIMIT**2]])
    gain, _ = solve_dare(aa, ba, q, r)
    nominal_poles = np.linalg.eigvals(aa - ba @ gain)

    robustness = []
    for signs in itertools.product((-2.0, 0.0, 2.0), repeat=3):
        beta = np.asarray(source["beta"]) + np.asarray(signs) * stderr
        varied_ac = np.array([[0.0, 1.0], [beta[0], beta[1]]])
        varied_bc = np.array([[0.0], [beta[2]]])
        vad, vbd = c2d_rk4(varied_ac, varied_bc)
        for delay in (2, 3, 4):
            va, vb = augment_delay_mismatch(vad, vbd, delay)
            applied_gain = np.pad(gain, ((0, 0), (0, 1)))
            radius = float(np.max(np.abs(np.linalg.eigvals(va - vb @ applied_gain))))
            robustness.append({"sigma_offsets": signs, "delay_samples": delay, "spectral_radius": radius})

    disturbance_replays = [dict(initial=list(initial), **simulate(aa, ba, gain, initial)) for initial in DISTURBANCES]
    columns = ("roll_deg", "p_deg_s") if name == "roll" else ("pitch_deg", "q_deg_s")
    log_replay = []
    for filename in source["training_files"] + source["validation_files"]:
        angle, rate = read_replay_states(root / "logs" / filename, *columns)
        history = np.zeros(NOMINAL_DELAY)
        commands = []
        previous = 0.0
        for eta, omega in zip(angle, rate):
            state = np.concatenate(([eta, omega], history))
            requested = float(-(gain @ state)[0])
            command = float(np.clip(requested, previous - SLEW_PER_SAMPLE, previous + SLEW_PER_SAMPLE))
            command = float(np.clip(command, -COMMAND_LIMIT, COMMAND_LIMIT))
            history = np.concatenate(([command], history[:-1]))
            previous = command
            commands.append(command)
        log_replay.append({
            "file": filename,
            "peak_offline_command": float(np.max(np.abs(commands))),
            "rms_offline_command": float(np.sqrt(np.mean(np.square(commands)))),
            "saturation_fraction": float(np.mean(np.abs(commands) >= COMMAND_LIMIT - 1e-12)),
        })
    attitude = {
        "Ad": ad, "Bd": bd, "A_delay_augmented": aa, "B_delay_augmented": ba,
        "Q": q, "R": r, "K": gain, "nominal_closed_loop_poles": nominal_poles,
        "nominal_spectral_radius": float(np.max(np.abs(nominal_poles))),
        "robustness_cases": len(robustness),
        "worst_case_spectral_radius": max(item["spectral_radius"] for item in robustness),
        "unstable_robustness_cases": sum(item["spectral_radius"] >= 1.0 for item in robustness),
        "worst_case": max(robustness, key=lambda item: item["spectral_radius"]),
        "disturbance_replays": disturbance_replays,
        "saved_log_command_replay": log_replay,
    }
    attitude["inner_rate_controller"] = audit_rate_controller(source, root, columns)
    return attitude


def encode(value):
    if isinstance(value, np.ndarray): return encode(value.tolist())
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, complex): return {"real": value.real, "imag": value.imag}
    if isinstance(value, tuple): return [encode(item) for item in value]
    if isinstance(value, list): return [encode(item) for item in value]
    if isinstance(value, dict): return {key: encode(item) for key, item in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=Path("configs/stage3_models.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.models.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[1]
    result = {
        "dt_s": DT, "nominal_delay_samples": NOMINAL_DELAY,
        "command_limit": COMMAND_LIMIT, "slew_per_sample": SLEW_PER_SAMPLE,
        "bryson_scales": {"angle_deg": ANGLE_SCALE_DEG, "attitude_rate_deg_s": RATE_SCALE_DEG_S,
                           "inner_rate_deg_s": INNER_RATE_SCALE_DEG_S, "command": COMMAND_LIMIT},
        "controllers": {name: audit_axis(name, model, root) for name, model in source["models"].items()},
    }
    encoded = encode(result)
    args.out.write_text(json.dumps(encoded, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(encoded, indent=2))


if __name__ == "__main__":
    main()
