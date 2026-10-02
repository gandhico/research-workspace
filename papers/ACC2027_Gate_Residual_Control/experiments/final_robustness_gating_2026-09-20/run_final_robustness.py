"""Final matched robustness and saturation-gating experiment runner.

This runner intentionally fixes the nominal controller used by both arms to
the paper's strongest simple baseline:

    tau_0 = sat_l(-J (rho*wn_0)^2 (2 e_q)
                  -J 2*zeta*(rho*wn_0) (omega-omega_d)), rho = 3,

where ``omega_d`` is the verified quaternion-reference finite-difference
feedforward (``left-neg`` in the archived convention).  In the augmented arm,
the *same* ``tau_0`` drives the Nengo CMG population and is augmented by the
online-PES decoder.

The optional output-only gate is deliberately outside the neuron and learning
rule.  It suppresses a requested residual component only when that component
opposes a baseline torque component already at (or epsilon-close to) its torque
box.  PES continues to update on every step.  This distinction is logged and
is part of the saved provenance.

The script records true and corrupted-feedback errors separately, the full
torque/allocation path, neuron/decoder state, disturbance phase, saturation
masks, and deterministic source/configuration hashes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import mujoco
import nengo
import numpy as np


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
UPSTREAM = REPO / "experiments" / "nengo_nef_replication_2026-08-29"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(UPSTREAM))

from gra_control.math3d import (  # noqa: E402
    euler_to_quat,
    quat_angle,
    quat_conj,
    quat_error,
    quat_mul,
    reference_euler,
    reference_quat,
)
from gra_control.platforms.drone import (  # noqa: E402
    SPECS,
    _free_joint,
    _mixer,
    torque_limits,
)
from gra_control.provenance import manifest, write_json  # noqa: E402
from nengo_cmg import NengoCMGPESAugmentor  # noqa: E402
from run_mujoco_nef_baselines import AdvancedBaseline  # noqa: E402


CONTROLLERS = ("classical", "nengo-nef-pes")
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("hover", "roll", "full3", "hard45", "hardstep", "yaw360")
GATE_MODES = (
    "none",
    "torque-saturation-opposition",
    # exploratory (X2-only screen): also freeze the decoder rows of blocked axes
    "torque-saturation-opposition-freeze-pes",
)
FREEZE_MODE = "torque-saturation-opposition-freeze-pes"
AXES = ("x", "y", "z")
UNITS = ("+x", "+y", "+z", "-x", "-y", "-z")

# Frozen paper-facing baseline.  AdvancedBaseline with backstepping and
# --no-model-ff is algebraically PD + desired-rate feedforward.
BASE_WN_RAD_S = np.array([4.0, 4.0, 3.5])
BASELINE_RHO = 3.0
BASELINE_ZETA = 0.95
BASELINE_FAMILY = "backstepping"
BASELINE_RATE_FF = "left-neg"
BASELINE_MODEL_FF = False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _jsonable_args(args: argparse.Namespace, include_output: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in vars(args).items():
        if key == "output" and not include_output:
            continue
        out[key] = str(value) if isinstance(value, Path) else value
    return out


def _hash_json(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def disturbance_gain(t: float, args: argparse.Namespace) -> float:
    """Return the deterministic continuous or intermittent disturbance gain."""
    if args.disturbance_schedule == "continuous":
        return 1.0
    if t < args.disturbance_warmup:
        return 0.0
    phase = (t - args.disturbance_warmup) % (
        args.disturbance_on + args.disturbance_off
    )
    if phase >= args.disturbance_on:
        return 0.0
    ramp = args.disturbance_ramp
    if ramp <= 0.0:
        return 1.0
    if phase < ramp:
        return float(0.5 * (1.0 - np.cos(np.pi * phase / ramp)))
    if phase > args.disturbance_on - ramp:
        x = (args.disturbance_on - phase) / ramp
        return float(0.5 * (1.0 - np.cos(np.pi * x)))
    return 1.0


def _hardstep_metrics(
    time_s: np.ndarray,
    error_rad: np.ndarray,
    dt: float,
    slew_window_s: float,
    settled_window_s: float,
    threshold_deg: float = 5.0,
    hold_s: float = 0.1,
) -> dict[str, Any]:
    """Partition Hardstep into early-transient and late-settled windows.

    Each reference step lasts two seconds and starts at t=1,3,5,... .  The
    settling time is the first threshold crossing that remains below the
    threshold for ``hold_s``.  A missed crossing is conservatively assigned
    the complete 2 s step interval.
    """
    onsets = np.arange(1.0, max(float(time_s[-1]), 1.0), 2.0)
    slew_values: list[np.ndarray] = []
    settled_values: list[np.ndarray] = []
    settling_times: list[float] = []
    threshold = np.deg2rad(threshold_deg)
    hold_n = max(1, int(round(hold_s / dt)))
    retained_onsets: list[float] = []
    for onset in onsets:
        stop = min(onset + 2.0, float(time_s[-1]) + dt)
        if stop - onset < max(slew_window_s, settled_window_s):
            continue
        transient = (time_s >= onset) & (time_s < min(onset + slew_window_s, stop))
        settled = (time_s >= max(onset, stop - settled_window_s)) & (time_s < stop)
        interval = (time_s >= onset) & (time_s < stop)
        if not np.any(interval):
            continue
        retained_onsets.append(float(onset))
        slew_values.append(error_rad[transient])
        settled_values.append(error_rad[settled])
        local_error = error_rad[interval]
        local_time = time_s[interval] - onset
        below = (local_error < threshold).astype(np.int16)
        if below.size >= hold_n:
            sustained = np.convolve(below, np.ones(hold_n, dtype=np.int16), mode="valid")
            hits = np.flatnonzero(sustained == hold_n)
        else:
            hits = np.array([], dtype=int)
        settling_times.append(float(local_time[hits[0]]) if hits.size else float(stop - onset))

    slew = np.concatenate(slew_values) if slew_values else np.array([], dtype=float)
    settled = np.concatenate(settled_values) if settled_values else np.array([], dtype=float)
    return {
        "definition": {
            "step_period_s": 2.0,
            "first_step_s": 1.0,
            "slew_window_s": slew_window_s,
            "settled_window_s": settled_window_s,
            "settling_threshold_deg": threshold_deg,
            "settling_hold_s": hold_s,
        },
        "step_onsets_s": retained_onsets,
        "n_complete_steps": len(retained_onsets),
        "whole_mean_rad": float(np.mean(error_rad)),
        "whole_mean_deg": float(np.degrees(np.mean(error_rad))),
        "slew_mean_rad": float(np.mean(slew)) if slew.size else None,
        "slew_mean_deg": float(np.degrees(np.mean(slew))) if slew.size else None,
        "settled_mean_rad": float(np.mean(settled)) if settled.size else None,
        "settled_mean_deg": float(np.degrees(np.mean(settled))) if settled.size else None,
        "settling_time_5deg_s_per_step": settling_times,
        "settling_time_5deg_s_mean": (
            float(np.mean(settling_times)) if settling_times else None
        ),
    }


def _phase_metrics(
    error_rad: np.ndarray,
    gains: np.ndarray,
    time_s: np.ndarray,
    warmup_s: float,
) -> dict[str, Any]:
    active = gains >= 0.5
    quiet = (gains <= 1e-12) & (time_s >= warmup_s)
    warmup = time_s < warmup_s

    def stats(mask: np.ndarray) -> dict[str, float | None]:
        values = error_rad[mask]
        return {
            "mean_rad": float(np.mean(values)) if values.size else None,
            "mean_deg": float(np.degrees(np.mean(values))) if values.size else None,
            "max_rad": float(np.max(values)) if values.size else None,
            "max_deg": float(np.degrees(np.max(values))) if values.size else None,
            "sample_fraction": float(np.mean(mask)),
        }

    return {
        "active_definition": "disturbance_gain >= 0.5",
        "quiet_definition": "disturbance_gain == 0 after warmup",
        "warmup": stats(warmup),
        "active": stats(active),
        "quiet": stats(quiet),
    }


def _append(log: dict[str, list[Any]], name: str, value: Any) -> None:
    log.setdefault(name, []).append(np.asarray(value).copy())


def run(args: argparse.Namespace) -> dict[str, Any]:
    spec = SPECS[args.platform]
    model = mujoco.MjModel.from_xml_path(str(spec.model))
    model.opt.timestep = args.dt
    data = mujoco.MjData(model)
    _, body_id, qa, va = _free_joint(model)
    inertia = model.body_inertia[body_id].copy()
    mass = float(np.sum(model.body_mass))
    gravity = abs(float(model.opt.gravity[2]))
    limits = torque_limits(args.platform, inertia, model, args.torque_policy)

    # These fixed attributes make AdvancedBaseline exactly the archived tuned
    # PD+desired-rate-feedforward controller at rho=3.
    args.baseline = BASELINE_FAMILY
    args.bw_scale = BASELINE_RHO
    args.rate_ff = BASELINE_RATE_FF
    args.no_model_ff = not BASELINE_MODEL_FF
    args.baseline_rate_hz = 0.0
    baseline = AdvancedBaseline(args, inertia, limits, BASE_WN_RAD_S)

    augmentor = None
    if args.controller == "nengo-nef-pes":
        augmentor = NengoCMGPESAugmentor(
            3,
            limits,
            dt=args.dt,
            beta=args.beta,
            learning_rate=args.learning_rate,
            adaptive_conductance=True,
            seed=args.seed,
        )
    elif args.output_gate != "none":
        raise ValueError("The residual output gate requires --controller nengo-nef-pes")

    data.qpos[qa : qa + 3] = [0.0, 0.0, 1.0]
    initial_rad = np.deg2rad(args.initial_angle_deg)
    q_initial_body = euler_to_quat(
        initial_rad, -0.7 * initial_rad, 0.5 * initial_rad
    )
    data.qpos[qa + 3 : qa + 7] = quat_conj(q_initial_body)
    data.qvel[:] = 0.0
    data.ctrl[:] = 0.0
    mujoco.mj_forward(model, data)

    # Both paper platforms use four explicitly allocated rotor forces.
    act_ids, mixer, mixer_inv, ctrl_range = _mixer(model)
    if args.actuator_scale <= 0.0:
        raise ValueError("--actuator-scale must be positive")
    ctrl_range[:, 1] *= args.actuator_scale
    model.actuator_ctrlrange[act_ids, 1] = ctrl_range[:, 1]

    rows: list[dict[str, Any]] = []
    neural_log: dict[str, list[Any]] = {}
    rng = np.random.default_rng(args.seed)
    step_index = 0
    max_augmentor_consistency_error = 0.0

    metric_t: list[float] = []
    metric_qerr_true: list[float] = []
    metric_qerr_feedback: list[float] = []
    metric_raw_residual: list[np.ndarray] = []
    metric_gated_residual: list[np.ndarray] = []
    metric_realized_residual: list[np.ndarray] = []
    metric_tau0: list[np.ndarray] = []
    metric_tau_command: list[np.ndarray] = []
    metric_tau_realized: list[np.ndarray] = []
    metric_baseline_loaded: list[np.ndarray] = []
    metric_gate_blocked: list[np.ndarray] = []
    metric_torque_box_sat: list[np.ndarray] = []
    metric_rotor_sat: list[np.ndarray] = []
    metric_disturbance_gain: list[float] = []
    metric_z: list[float] = []

    gate_epsilon = args.gate_epsilon_fraction * limits + args.gate_epsilon_nm
    loaded_threshold = np.maximum(
        args.gate_load_threshold * limits - gate_epsilon, 0.0
    )

    try:
        while data.time < args.duration:
            t = float(data.time)
            q_true = quat_conj(
                np.asarray(data.qpos[qa + 3 : qa + 7], dtype=float).copy()
            )
            omega_true = np.asarray(
                data.qvel[va + 3 : va + 6], dtype=float
            ).copy()

            # The control arm receives corrupted feedback; the true plant state
            # is retained independently for the primary evaluation metric.
            q_feedback = q_true.copy()
            omega_feedback = omega_true.copy()
            if args.attitude_noise_std > 0.0:
                dq = euler_to_quat(
                    *rng.normal(0.0, args.attitude_noise_std, size=3)
                )
                q_feedback = quat_mul(dq, q_feedback)
            if args.rate_noise_std > 0.0:
                omega_feedback += rng.normal(0.0, args.rate_noise_std, size=3)

            ref_euler = reference_euler(t, args.mission, args.duration)
            q_ref = reference_quat(t, args.mission, args.duration)
            qe_true, eq_true = quat_error(q_ref, q_true)
            qe_feedback, eq_feedback = quat_error(q_ref, q_feedback)

            tau0 = baseline.torque(t, eq_feedback, omega_feedback, q_feedback)
            target = np.clip(
                -args.k_error * eq_feedback - args.k_rate * omega_feedback,
                -1.0,
                1.0,
            )

            diagnostics: dict[str, np.ndarray] = {}
            weights_before = np.zeros((3, 6))
            voltage = np.zeros(6)
            neural_gate = np.zeros(6)
            activity = np.zeros(6)
            weights = np.zeros((3, 6))
            pes_error = np.zeros(3)
            decoded_raw = np.zeros(3)
            decoded_clipped = np.zeros(3)
            raw_residual = np.zeros(3)

            if augmentor is not None:
                weights_before = augmentor.W
                native_out = augmentor.step(tau0, target)
                diagnostics = augmentor.diagnostics()
                voltage = diagnostics["voltage"].copy()
                neural_gate = diagnostics["gate"].copy()
                activity = diagnostics["activity"].copy()
                weights = diagnostics["weights"].copy()
                pes_error = diagnostics["pes_error"].copy()
                decoded_raw = diagnostics["decoded_raw"].copy()
                decoded_clipped = diagnostics["decoded_clipped"].copy()
                # Requested residual before the outer torque box.  The archived
                # augmentor returns only the post-clip residual, so this explicit
                # reconstruction is essential to audit gating and clipping.
                raw_residual = args.beta * limits * decoded_clipped
                reconstructed = np.clip(tau0 + raw_residual, -limits, limits)
                max_augmentor_consistency_error = max(
                    max_augmentor_consistency_error,
                    float(np.max(np.abs(reconstructed - native_out.command))),
                )

            baseline_loaded = np.abs(tau0) >= loaded_threshold
            opposing = baseline_loaded & (raw_residual * tau0 < 0.0)
            output_gate_mask = np.ones(3, dtype=float)
            if args.output_gate in ("torque-saturation-opposition", FREEZE_MODE):
                output_gate_mask[opposing] = 0.0
            if args.output_gate == FREEZE_MODE and augmentor is not None and np.any(opposing):
                # Anti-windup analogue: no decoder movement on an axis whose residual is blocked.
                # Neuron and gate states are untouched; only the pre-step weight rows are restored.
                augmentor._weights[opposing, :] = weights_before[opposing, :]
                weights = augmentor.W

            gated_residual = output_gate_mask * raw_residual
            tau_requested = tau0 + gated_residual
            tau_command = np.clip(tau_requested, -limits, limits)
            realized_residual = tau_command - tau0
            torque_box_sat = np.abs(tau_requested) >= limits - 1e-12

            rotation = np.asarray(data.xmat[body_id], dtype=float).reshape(3, 3)
            z = float(data.qpos[qa + 2])
            vz = float(data.qvel[va + 2])
            tilt = max(float(rotation[2, 2]), 0.35)
            collective_requested = mass * (
                gravity + 6.0 * (1.0 - z) - 4.0 * vz
            ) / tilt
            collective_requested = float(
                np.clip(
                    collective_requested,
                    0.0,
                    2.5 * mass * max(gravity, 1.0),
                )
            )

            actuator_requested = mixer_inv @ np.r_[collective_requested, tau_command]
            actuator_command = np.clip(
                actuator_requested, ctrl_range[:, 0], ctrl_range[:, 1]
            )
            rotor_sat_mask = (
                np.isclose(actuator_command, ctrl_range[:, 0], atol=1e-7)
                | np.isclose(actuator_command, ctrl_range[:, 1], atol=1e-7)
            )
            realized_wrench = mixer @ actuator_command
            collective_realized = float(realized_wrench[0])
            tau_realized = realized_wrench[1:4].copy()

            disturbance_scale = disturbance_gain(t, args)
            disturbance_body = np.zeros(3)
            if args.disturbance_torque > 0.0 and disturbance_scale > 0.0:
                disturbance_body = disturbance_scale * args.disturbance_torque * np.array(
                    [
                        np.sin(1.31 * t + 0.2),
                        0.8 * np.sin(1.73 * t + 1.1),
                        0.6 * np.sin(2.17 * t + 2.0),
                    ]
                )

            data.ctrl[:] = 0.0
            data.xfrc_applied[:] = 0.0
            data.ctrl[act_ids] = actuator_command
            data.xfrc_applied[body_id, 3:6] = rotation @ disturbance_body

            qerr_true = quat_angle(qe_true)
            qerr_feedback = quat_angle(qe_feedback)
            metric_t.append(t)
            metric_qerr_true.append(qerr_true)
            metric_qerr_feedback.append(qerr_feedback)
            metric_raw_residual.append(raw_residual.copy())
            metric_gated_residual.append(gated_residual.copy())
            metric_realized_residual.append(realized_residual.copy())
            metric_tau0.append(tau0.copy())
            metric_tau_command.append(tau_command.copy())
            metric_tau_realized.append(tau_realized.copy())
            metric_baseline_loaded.append(baseline_loaded.copy())
            metric_gate_blocked.append((output_gate_mask == 0.0).copy())
            metric_torque_box_sat.append(torque_box_sat.copy())
            metric_rotor_sat.append(rotor_sat_mask.copy())
            metric_disturbance_gain.append(disturbance_scale)
            metric_z.append(z)

            if step_index % args.log_every == 0:
                row: dict[str, Any] = {
                    "t": t,
                    "plant_step": step_index,
                    "qerr_true_rad": qerr_true,
                    "qerr_feedback_rad": qerr_feedback,
                    "qerr": qerr_true,
                    "qe_true_w": qe_true[0],
                    "qe_feedback_w": qe_feedback[0],
                    "ref_roll": ref_euler[0],
                    "ref_pitch": ref_euler[1],
                    "ref_yaw": ref_euler[2],
                    "z": z,
                    "collective_requested_N": collective_requested,
                    "collective_realized_N": collective_realized,
                    "disturbance_gain": disturbance_scale,
                    "rotor_saturated_any": int(np.any(rotor_sat_mask)),
                }
                for i, label in enumerate(("w", "x", "y", "z")):
                    row[f"qref_{label}"] = q_ref[i]
                    row[f"qtrue_{label}"] = q_true[i]
                    row[f"qfeedback_{label}"] = q_feedback[i]
                for i, axis in enumerate(AXES):
                    row[f"qe_true_{axis}"] = eq_true[i]
                    row[f"qe_feedback_{axis}"] = eq_feedback[i]
                    row[f"omega_true_{axis}"] = omega_true[i]
                    row[f"omega_feedback_{axis}"] = omega_feedback[i]
                    row[f"tau0_{axis}"] = tau0[i]
                    row[f"raw_residual_{axis}"] = raw_residual[i]
                    row[f"output_gate_mask_{axis}"] = output_gate_mask[i]
                    row[f"gated_residual_{axis}"] = gated_residual[i]
                    row[f"realized_residual_{axis}"] = realized_residual[i]
                    row[f"tau_requested_{axis}"] = tau_requested[i]
                    row[f"tau_command_{axis}"] = tau_command[i]
                    row[f"tau_realized_{axis}"] = tau_realized[i]
                    row[f"baseline_loaded_{axis}"] = int(baseline_loaded[i])
                    row[f"torque_box_saturated_{axis}"] = int(torque_box_sat[i])
                    row[f"target_{axis}"] = target[i]
                    row[f"decoder_raw_{axis}"] = decoded_raw[i]
                    row[f"decoder_clipped_{axis}"] = decoded_clipped[i]
                    row[f"pes_error_{axis}"] = pes_error[i]
                    row[f"disturbance_body_{axis}"] = disturbance_body[i]
                for i in range(6):
                    row[f"current_{i}"] = (
                        diagnostics["current"][i] if diagnostics else 0.0
                    )
                    row[f"voltage_{i}"] = voltage[i]
                    row[f"gate_{i}"] = neural_gate[i]
                    row[f"activity_{i}"] = activity[i]
                    row[f"gate_target_{i}"] = (
                        diagnostics["gate_target"][i] if diagnostics else 0.0
                    )
                    row[f"effective_threshold_{i}"] = (
                        diagnostics["effective_threshold"][i] if diagnostics else 0.0
                    )
                for i, value in enumerate(weights.ravel()):
                    row[f"decoder_w_{i}"] = value
                for i in range(4):
                    row[f"actuator_requested_{i}"] = actuator_requested[i]
                    row[f"actuator_command_{i}"] = actuator_command[i]
                    row[f"actuator_saturated_{i}"] = int(rotor_sat_mask[i])
                rows.append(row)

            if augmentor is not None and args.save_neural_archive:
                _append(neural_log, "t", t)
                _append(neural_log, "plant_step", step_index)
                _append(neural_log, "q_ref", q_ref)
                _append(neural_log, "q_true", q_true)
                _append(neural_log, "q_feedback", q_feedback)
                _append(neural_log, "qerr_true_rad", qerr_true)
                _append(neural_log, "qerr_feedback_rad", qerr_feedback)
                _append(neural_log, "omega_true", omega_true)
                _append(neural_log, "omega_feedback", omega_feedback)
                _append(neural_log, "baseline_tau", tau0)
                _append(neural_log, "target", target)
                _append(neural_log, "current", diagnostics["current"])
                _append(neural_log, "voltage", voltage)
                _append(neural_log, "gate", neural_gate)
                _append(neural_log, "activity", activity)
                for name in (
                    "effective_threshold",
                    "gate_argument",
                    "gate_target",
                    "conductance_gain",
                    "conductance",
                    "membrane_lambda",
                    "membrane_drive",
                    "decoded_raw",
                    "decoded_clipped",
                    "pes_error",
                    "weights",
                ):
                    _append(neural_log, name, diagnostics[name])
                _append(neural_log, "weight_delta", weights - weights_before)
                _append(neural_log, "raw_residual_torque", raw_residual)
                _append(neural_log, "output_gate_mask", output_gate_mask)
                _append(neural_log, "gated_residual_torque", gated_residual)
                _append(neural_log, "realized_residual_torque", realized_residual)
                _append(neural_log, "tau_requested", tau_requested)
                _append(neural_log, "tau_command", tau_command)
                _append(neural_log, "tau_realized", tau_realized)
                _append(neural_log, "baseline_loaded_mask", baseline_loaded)
                _append(neural_log, "torque_box_saturation_mask", torque_box_sat)
                _append(neural_log, "actuator_requested", actuator_requested)
                _append(neural_log, "actuator_command", actuator_command)
                _append(neural_log, "rotor_saturation_mask", rotor_sat_mask)
                _append(neural_log, "disturbance_gain", disturbance_scale)
                _append(neural_log, "disturbance_body", disturbance_body)

            step_index += 1
            mujoco.mj_step(model, data)
    finally:
        if augmentor is not None:
            augmentor.close()

    if not rows:
        raise RuntimeError("No trace rows were produced; check duration and log interval")

    args.output.mkdir(parents=True, exist_ok=True)
    trace_path = args.output / "trace.csv"
    with trace_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    neural_path: Path | None = None
    neural_schema_path: Path | None = None
    if neural_log:
        neural_path = args.output / "neural_trace_full_rate.npz"
        neural_arrays = {key: np.asarray(value) for key, value in neural_log.items()}
        np.savez_compressed(neural_path, **neural_arrays)
        neural_schema_path = args.output / "neural_trace_schema.json"
        schema = {
            "schema": 2,
            "sample_rate_hz": 1.0 / args.dt,
            "sample_period_s": args.dt,
            "axis_order": list(AXES),
            "unit_order": list(UNITS),
            "weight_shape_per_sample": [3, 6],
            "signals": {
                name: {"shape": list(values.shape), "dtype": str(values.dtype)}
                for name, values in neural_arrays.items()
            },
            "semantics": {
                "decoded_clipped": "clip(W @ activity,-1,1); PES input and raw residual source",
                "raw_residual_torque": "beta * torque_limit * decoded_clipped before outer gating/clipping",
                "output_gate_mask": "application-side mask; it does not mask PES updates (except in freeze-pes mode)",
                "gated_residual_torque": "output_gate_mask * raw_residual_torque",
                "realized_residual_torque": "tau_command - baseline_tau after torque-box clipping",
                "tau_realized": "torque reconstructed after rotor-force clipping/allocation",
                "weight_delta": "post-PES/leak decoder weights minus pre-step weights",
            },
        }
        write_json(neural_schema_path, schema)

    t_array = np.asarray(metric_t)
    qerr_true = np.asarray(metric_qerr_true)
    qerr_feedback = np.asarray(metric_qerr_feedback)
    raw_residual = np.asarray(metric_raw_residual)
    gated_residual = np.asarray(metric_gated_residual)
    realized_residual = np.asarray(metric_realized_residual)
    tau0_array = np.asarray(metric_tau0)
    tau_command_array = np.asarray(metric_tau_command)
    tau_realized_array = np.asarray(metric_tau_realized)
    baseline_loaded_array = np.asarray(metric_baseline_loaded, dtype=bool)
    gate_blocked_array = np.asarray(metric_gate_blocked, dtype=bool)
    torque_sat_array = np.asarray(metric_torque_box_sat, dtype=bool)
    rotor_sat_array = np.asarray(metric_rotor_sat, dtype=bool)
    disturbance_gains = np.asarray(metric_disturbance_gain)

    def normalized_rms(values: np.ndarray) -> float:
        return float(np.sqrt(np.mean((values / limits[None, :]) ** 2)))

    summary: dict[str, Any] = {
        "schema": 2,
        "experiment": "final_robustness_gating_2026-09-20",
        "platform": args.platform,
        "model_interface": spec.interface,
        "mission": args.mission,
        "duration_s": args.duration,
        "dt_s": args.dt,
        "controller": args.controller,
        "controller_backend": (
            "none" if augmentor is None else "Nengo built-in PES with CMG neuron"
        ),
        "baseline": {
            "name": "PD + desired-rate feedforward",
            "implementation": "AdvancedBaseline(backstepping, no model feedforward)",
            "rho": BASELINE_RHO,
            "base_wn_rad_s": BASE_WN_RAD_S.tolist(),
            "effective_wn_rad_s": (BASELINE_RHO * BASE_WN_RAD_S).tolist(),
            "zeta": BASELINE_ZETA,
            "reference_rate_convention": BASELINE_RATE_FF,
            "model_feedforward": BASELINE_MODEL_FF,
            "shared_by_classical_and_cmg": True,
            "stats": baseline.stats(),
        },
        "cmg_pes": {
            "beta": args.beta,
            "learning_rate_direct_equivalent": args.learning_rate,
            "nengo_pes_learning_rate": (
                args.learning_rate * 6.0 / args.dt if augmentor is not None else None
            ),
            "k_error": args.k_error,
            "k_rate": args.k_rate,
            "pes_learning_active_every_step": augmentor is not None,
            "max_native_vs_reconstructed_command_error_Nm": (
                max_augmentor_consistency_error if augmentor is not None else None
            ),
        },
        "output_gate": {
            "mode": args.output_gate,
            "location": "after decoder/residual scaling and before outer torque-box clip",
            "learning_semantics": (
                "output mask plus decoder rows restored (frozen) on blocked axes"
                if args.output_gate == FREEZE_MODE
                else "output-only; PES target/error/update are never masked"
            ),
            "epsilon_fraction_of_axis_limit": args.gate_epsilon_fraction,
            "epsilon_Nm": args.gate_epsilon_nm,
            "load_threshold_fraction_of_axis_limit": args.gate_load_threshold,
            "loaded_threshold_Nm": loaded_threshold.tolist(),
            "blocked_fraction_any_axis": float(np.mean(np.any(gate_blocked_array, axis=1))),
            "blocked_fraction_per_axis": np.mean(gate_blocked_array, axis=0).tolist(),
            "blocked_share_of_loaded_per_axis": (
                np.sum(gate_blocked_array, axis=0)
                / np.maximum(np.sum(baseline_loaded_array, axis=0), 1)
            ).tolist(),
        },
        "noise": {
            "attitude_std_rad_per_rotation_vector_component": args.attitude_noise_std,
            "rate_std_rad_s_per_axis": args.rate_noise_std,
            "seed": args.seed,
            "generator": "numpy.random.default_rng / PCG64",
            "primary_metric_uses_true_state": True,
        },
        "disturbance": {
            "amplitude_Nm": args.disturbance_torque,
            "schedule": args.disturbance_schedule,
            "warmup_s": args.disturbance_warmup,
            "on_s": args.disturbance_on,
            "off_s": args.disturbance_off,
            "raised_cosine_ramp_s": args.disturbance_ramp,
        },
        "actuation": {
            "torque_policy": args.torque_policy,
            "torque_limits_Nm": limits.tolist(),
            "actuator_scale": args.actuator_scale,
            "baseline_loaded_fraction_per_axis": np.mean(
                baseline_loaded_array, axis=0
            ).tolist(),
            "torque_box_saturation_fraction_any_axis": float(
                np.mean(np.any(torque_sat_array, axis=1))
            ),
            "torque_box_saturation_fraction_per_axis": np.mean(
                torque_sat_array, axis=0
            ).tolist(),
            "rotor_saturation_fraction_any_rotor": float(
                np.mean(np.any(rotor_sat_array, axis=1))
            ),
            "rotor_saturation_fraction_per_rotor": np.mean(
                rotor_sat_array, axis=0
            ).tolist(),
            "allocation_torque_error_normalized_rms": normalized_rms(
                tau_realized_array - tau_command_array
            ),
        },
        "metrics": {
            "qerr_true_mean_rad": float(np.mean(qerr_true)),
            "qerr_true_max_rad": float(np.max(qerr_true)),
            "qerr_true_rmse_rad": float(np.sqrt(np.mean(qerr_true**2))),
            "qerr_feedback_mean_rad": float(np.mean(qerr_feedback)),
            "qerr_feedback_max_rad": float(np.max(qerr_feedback)),
            "qerr_feedback_rmse_rad": float(np.sqrt(np.mean(qerr_feedback**2))),
            # Compatibility alias; unlike the archived noisy runner this is
            # explicitly the true-state metric.
            "qerr_mean_rad": float(np.mean(qerr_true)),
            "raw_residual_normalized_rms": normalized_rms(raw_residual),
            "gated_residual_normalized_rms": normalized_rms(gated_residual),
            "realized_residual_normalized_rms": normalized_rms(realized_residual),
            "tau0_normalized_rms": normalized_rms(tau0_array),
            "tau_command_normalized_rms": normalized_rms(tau_command_array),
            "tau_realized_normalized_rms": normalized_rms(tau_realized_array),
            "z_std_m": float(np.std(metric_z)),
        },
        "hardstep": (
            _hardstep_metrics(
                t_array,
                qerr_true,
                args.dt,
                args.hardstep_slew_window,
                args.hardstep_settled_window,
            )
            if args.mission == "hardstep"
            else None
        ),
        "disturbance_phase_metrics_true_state": _phase_metrics(
            qerr_true,
            disturbance_gains,
            t_array,
            args.disturbance_warmup,
        ),
        "n_steps": step_index,
        "logged_steps": len(rows),
        "log_every": args.log_every,
        "logged_dt_s": args.dt * args.log_every,
        "nengo_version": nengo.__version__,
        "files": {
            "trace": str(trace_path),
            "neural_trace_full_rate": str(neural_path) if neural_path else None,
            "neural_trace_schema": str(neural_schema_path) if neural_schema_path else None,
        },
    }

    source_paths = {
        "runner": Path(__file__).resolve(),
        "baseline_runner": UPSTREAM / "run_mujoco_nef_baselines.py",
        "nengo_cmg": UPSTREAM / "nengo_cmg.py",
        "gate_model": REPO / "src" / "gra_control" / "gate.py",
        "quaternion_and_reference": REPO / "src" / "gra_control" / "math3d.py",
        "platform_interface": REPO / "src" / "gra_control" / "platforms" / "drone.py",
        "mujoco_model": Path(spec.model),
    }
    source_hashes = {name: _sha256(path) for name, path in source_paths.items()}
    config = _jsonable_args(args)
    config["frozen_baseline"] = summary["baseline"]
    config_sha256 = _hash_json(config)
    run_id = _hash_json(
        {"configuration_sha256": config_sha256, "source_sha256": source_hashes}
    )[:20]
    summary["run_id"] = run_id
    summary["configuration_sha256"] = config_sha256

    summary_path = args.output / "summary.json"
    write_json(summary_path, summary)

    args_for_manifest = _jsonable_args(args, include_output=True)
    provenance = manifest(
        REPO,
        args.platform,
        args.controller,
        Path(spec.model),
        args_for_manifest,
    )
    provenance.update(
        {
            "schema": 2,
            "run_id": run_id,
            "configuration_sha256": config_sha256,
            "source_sha256": source_hashes,
            "noise_sequence_sha256": _hash_json(
                {
                    "seed": args.seed,
                    "dt": args.dt,
                    "duration": args.duration,
                    "attitude_noise_std": args.attitude_noise_std,
                    "rate_noise_std": args.rate_noise_std,
                    "generator": "numpy.default_rng.PCG64",
                }
            ),
            "output_sha256": {
                "trace.csv": _sha256(trace_path),
                "summary.json": _sha256(summary_path),
                **(
                    {"neural_trace_full_rate.npz": _sha256(neural_path)}
                    if neural_path
                    else {}
                ),
                **(
                    {"neural_trace_schema.json": _sha256(neural_schema_path)}
                    if neural_schema_path
                    else {}
                ),
            },
            "derived": {
                "body_inertia_kgm2": inertia.tolist(),
                "torque_limits_Nm": limits.tolist(),
                "baseline_effective_wn_rad_s": (
                    BASELINE_RHO * BASE_WN_RAD_S
                ).tolist(),
            },
        }
    )
    write_json(args.output / "manifest.json", provenance)
    return summary


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=PLATFORMS, required=True)
    parser.add_argument("--controller", choices=CONTROLLERS, required=True)
    parser.add_argument("--mission", choices=MISSIONS, default="hard45")
    parser.add_argument("--duration", type=float, default=45.0)
    parser.add_argument("--dt", type=float, default=5e-4)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=8.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument(
        "--torque-policy",
        choices=("model", "inertia", "legacy-learned"),
        default="model",
    )
    parser.add_argument("--actuator-scale", type=float, default=1.0)
    parser.add_argument("--initial-angle-deg", type=float, default=0.0)
    parser.add_argument("--attitude-noise-std", type=float, default=0.0)
    parser.add_argument("--rate-noise-std", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--disturbance-torque", type=float, default=0.0)
    parser.add_argument(
        "--disturbance-schedule",
        choices=("continuous", "intermittent"),
        default="continuous",
    )
    parser.add_argument("--disturbance-warmup", type=float, default=5.0)
    parser.add_argument("--disturbance-on", type=float, default=5.0)
    parser.add_argument("--disturbance-off", type=float, default=5.0)
    parser.add_argument("--disturbance-ramp", type=float, default=0.25)
    parser.add_argument(
        "--output-gate",
        choices=GATE_MODES,
        default="none",
        help="Optional application-side residual gate; PES always remains active.",
    )
    parser.add_argument(
        "--gate-load-threshold",
        type=float,
        default=1.0,
        help=(
            "Declare an axis loaded when |tau0_i| is at least this fraction "
            "of its limit. 1.0 is the frozen exact-saturation rule."
        ),
    )
    parser.add_argument(
        "--gate-epsilon-fraction",
        type=float,
        default=0.0,
        help="Optional tolerance subtracted from the declared load threshold.",
    )
    parser.add_argument(
        "--gate-epsilon-nm",
        type=float,
        default=1e-12,
        help="Additional absolute torque proximity threshold [N m].",
    )
    parser.add_argument("--hardstep-slew-window", type=float, default=0.5)
    parser.add_argument("--hardstep-settled-window", type=float, default=0.5)
    parser.add_argument("--log-every", type=int, default=10)
    parser.add_argument(
        "--no-neural-archive",
        dest="save_neural_archive",
        action="store_false",
        help="Disable the full-rate NPZ archive (decimated trace.csv remains).",
    )
    parser.set_defaults(save_neural_archive=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def _validate(args: argparse.Namespace) -> None:
    if args.duration <= 0.0 or args.dt <= 0.0:
        raise SystemExit("--duration and --dt must be positive")
    if args.log_every < 1:
        raise SystemExit("--log-every must be >= 1")
    if not (0.0 <= args.gate_epsilon_fraction < 1.0):
        raise SystemExit("--gate-epsilon-fraction must be in [0,1)")
    if not (0.0 < args.gate_load_threshold <= 1.0):
        raise SystemExit("--gate-load-threshold must be in (0,1]")
    if args.gate_epsilon_nm < 0.0:
        raise SystemExit("--gate-epsilon-nm must be nonnegative")
    if args.disturbance_on <= 0.0 or args.disturbance_off <= 0.0:
        raise SystemExit("disturbance on/off durations must be positive")
    if args.disturbance_warmup < 0.0 or args.disturbance_ramp < 0.0:
        raise SystemExit("disturbance warmup/ramp must be nonnegative")
    if args.disturbance_ramp > 0.5 * args.disturbance_on:
        raise SystemExit("--disturbance-ramp cannot exceed half --disturbance-on")
    for name in ("hardstep_slew_window", "hardstep_settled_window"):
        value = getattr(args, name)
        if not (0.0 < value <= 2.0):
            raise SystemExit(f"--{name.replace('_', '-')} must be in (0,2]")


if __name__ == "__main__":
    parsed = make_parser().parse_args()
    _validate(parsed)
    result = run(parsed)
    print(json.dumps(result, indent=2))
