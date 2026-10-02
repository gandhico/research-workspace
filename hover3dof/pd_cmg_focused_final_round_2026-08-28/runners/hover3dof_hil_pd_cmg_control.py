r"""Explicit-PD and torque-space CMG/PES control for the Quanser 3DOF Hover.

THIS IS A NEW, SEPARATE EXPERIMENTAL RUNNER. It does not modify or overwrite the
frozen LQR/CMG results. Read PD_HARDWARE_RUNBOOK.md before using --armed.

Default baseline signal path (MuJoCo-matched, yaw/pitch/roll coordinates):
    qe, eq = quat_error(q_ref, q_meas)
    tau_pd = clip(Kq*eq - Kw*omega_body, +/- inertia-policy limits)
    delta_v_pd = G^T (G G^T)^-1 tau_pd
    v_pd_raw = V_bias + delta_v_pd
    v_pd = allocator(v_pd_raw, tau_pd)

Kq, Kw, wn=[4,4,3.5], and the inertia-policy torque limits reproduce canonical
MuJoCo drone.py after a declared coordinate-sign/order transform. The optional
--pd-profile lqr-equivalent retains the exact vendor-LQR bridge check but is not
the default PD experiment.

PD-CMG signal path:
    tau_pd -> 3-channel CMG bank (6 +/- units) -> requested delta_tau
    requested delta_tau -> minimum-norm four-motor delta_v
    delta_v -> per-motor magnitude AND applied-signal slew limit
    command = allocator(v_pd_raw + bounded_delta_v, tau_pd + delta_tau)

The default ``fixed-bias`` allocator reproduces the original experiment. The
optional, explicitly reported ``stability-priority`` Hover allocator uses the
common-mode nullspace to keep every motor above a declared floor and reduces
yaw before pitch/roll when the requested torque is infeasible. It is intended
for the Yaw360/Hardstep failure investigation and must be applied identically to
PD and PD-CMG runs.

The module is disarmed by default. Armed use requires BOTH --armed and
--confirm-pd-review. Any normal Python exception or Ctrl-C zeros all four analog
outputs in finally. This software behavior is not a substitute for a configured
hardware watchdog and E-stop.
"""
from __future__ import annotations

import argparse
import array as arr
import csv
import sys
import time
from pathlib import Path

import numpy as np
from quanser.hardware import HIL, HILError

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
HOVER_ROOT = Path(r"C:\Research\hover3dof")
ACC_ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
sys.path.insert(0, str(EXPERIMENT_ROOT / "src"))

from pd_baseline import (  # noqa: E402
    VendorPlant,
    allocate_stability_priority_torque,
    euler_rates_ypr_to_body_omega_ypr,
    limit_and_slew_motor_residual,
    mujoco_pd_parameters_ypr,
    mujoco_pes_target_ypr,
    mujoco_quaternion_pd_torque_ypr,
    pd_torque,
    realized_torque,
    torque_to_motor_differential,
)
from gra_control.gate import CMGResidualAugmentor  # noqa: E402
from gra_control.math3d import euler_to_quat, quat_angle, quat_error, reference_euler  # noqa: E402
from gra_control.provenance import manifest, write_json  # noqa: E402


PLANT = VendorPlant()
K_AMP = 3.0
V_MAX_DAC = 10.0
K_EC_PITCH = 2.0 * np.pi / (8 * 1024)
K_EC_ROLL = 2.0 * np.pi / (8 * 1024)
K_EC_YAW = -2.0 * np.pi / (8 * 1024)
WCF = 2.0 * np.pi * 20.0
ZETAF = 0.8
CHANNELS = ("Vf", "Vb", "Vl", "Vr")
AXES = ("yaw", "pitch", "roll")
HARDSTEP_TARGETS_RPY = np.array([
    [0.75, -0.45, 0.55],
    [-0.65, 0.55, -0.70],
    [0.50, 0.50, 0.90],
    [-0.80, -0.35, 0.20],
])


def experiment_reference_euler(
    t: float,
    mission: str,
    duration: float,
    reference_scale: float,
    hardstep_transition_s: float,
) -> np.ndarray:
    """Return canonical reference or the declared actuator-feasible Hardstep.

    ``transition=0`` reproduces ``gra_control.math3d.reference_euler`` exactly.
    A positive transition applies cubic smoothstep interpolation after each
    two-second Hardstep target change. Scaling and shaping are logged mission
    adaptations and must match between PD and PD-CMG.
    """
    if mission != "hardstep" or hardstep_transition_s <= 0.0:
        return reference_scale * reference_euler(t, mission, duration)
    if t < 1.0:
        return np.zeros(3)
    phase_number = int((t - 1.0) // 2.0)
    phase = phase_number % len(HARDSTEP_TARGETS_RPY)
    current = HARDSTEP_TARGETS_RPY[phase]
    previous = np.zeros(3) if phase_number == 0 else HARDSTEP_TARGETS_RPY[(phase - 1) % len(HARDSTEP_TARGETS_RPY)]
    phase_start = 1.0 + 2.0 * phase_number
    fraction = np.clip((t - phase_start) / hardstep_transition_s, 0.0, 1.0)
    smooth = fraction * fraction * (3.0 - 2.0 * fraction)
    return reference_scale * ((1.0 - smooth) * previous + smooth * current)


class RateFilter:
    """Vendor 20 Hz, zeta=.8 band-limited differentiator."""

    def __init__(self, n: int):
        self.x1 = np.zeros(n)
        self.x2 = np.zeros(n)

    def step(self, angle: np.ndarray, dt: float) -> np.ndarray:
        x1_dot = self.x2
        x2_dot = -WCF * WCF * self.x1 - 2.0 * ZETAF * WCF * self.x2 + angle
        self.x1 = self.x1 + dt * x1_dot
        self.x2 = self.x2 + dt * x2_dot
        return WCF * WCF * self.x2


def read_angles(card: HIL, encoder_channels: arr.array, counts: arr.array) -> np.ndarray:
    card.read_encoder(encoder_channels, 3, counts)
    return np.array([
        counts[2] * K_EC_YAW,
        counts[0] * K_EC_PITCH,
        counts[1] * K_EC_ROLL,
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--armed", action="store_true", help="Permit nonzero Q8 output.")
    parser.add_argument(
        "--confirm-pd-review", action="store_true",
        help="Second explicit acknowledgement required with --armed after completing the runbook.",
    )
    parser.add_argument("--controller", choices=["pd", "pd-cmg"], default="pd")
    parser.add_argument(
        "--pd-profile", choices=["mujoco", "lqr-equivalent"], default="mujoco",
        help="mujoco reproduces drone.py's quaternion-PD law; lqr-equivalent is retained only as a labeled bridge check.",
    )
    parser.add_argument("--mission", choices=["hover", "roll", "full3", "hard45", "hardstep", "yaw360"], default="hover")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument(
        "--stop-after", type=float,
        help="Optional shorter qualification segment while retaining the full mission reference duration (especially Yaw360).",
    )
    parser.add_argument("--rate-hz", type=float, default=200.0)
    parser.add_argument(
        "--reference-scale", type=float, default=1.0,
        help="Logged mission-amplitude scale. Use below 1 only as a separately reported hardware-feasible mission variant.",
    )
    parser.add_argument(
        "--hardstep-transition-s", type=float, default=0.0,
        help="Cubic transition time for Hardstep targets; 0 reproduces the canonical discontinuous mission.",
    )
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument(
        "--motor-residual-cap-volts", type=float, default=1.2,
        help="Post-allocation per-motor safety projection. This is a declared Hover-only change; MuJoCo has XML rotor bounds instead.",
    )
    parser.add_argument("--learning-rate", type=float, default=8e-4)
    parser.add_argument("--k-error", type=float, default=8.0)
    parser.add_argument("--k-rate", type=float, default=0.0)
    parser.add_argument("--residual-slew-v-per-s", type=float, default=4.0)
    parser.add_argument(
        "--allocation-policy", choices=["fixed-bias", "stability-priority"],
        default="fixed-bias",
        help="Hover motor allocator. stability-priority keeps motors active and preserves pitch/roll before yaw; report it as a hardware adaptation.",
    )
    parser.add_argument(
        "--motor-floor-volts", type=float, default=2.0,
        help="Minimum commanded motor-equivalent voltage under stability-priority allocation.",
    )
    parser.add_argument(
        "--neural-substeps", type=int, default=10,
        help="CMG/PES updates per 5-ms hardware step. Default 10 reproduces the MuJoCo paper dt=0.0005 s under zero-order-held measurements.",
    )
    parser.add_argument("--max-abs-pitch-deg", type=float, default=55.0)
    parser.add_argument("--max-abs-roll-deg", type=float, default=55.0)
    parser.add_argument(
        "--expected-raw-home-yaw-deg", type=float,
        help="Optional accumulated encoder yaw required before tare; protects matched yaw pairs from cable/history contamination.",
    )
    parser.add_argument(
        "--raw-home-yaw-tolerance-deg", type=float, default=5.0,
        help="Maximum absolute difference from --expected-raw-home-yaw-deg before the run is refused with zero output.",
    )
    parser.add_argument("--max-consecutive-deadline-misses", type=int, default=20)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.armed and not args.confirm_pd_review:
        raise SystemExit("--armed requires --confirm-pd-review after completing PD_HARDWARE_RUNBOOK.md")
    duration_limit = 60.0 if args.mission == "yaw360" else 30.0
    if not (0.0 < args.duration <= duration_limit):
        raise SystemExit(f"duration must be in (0, {duration_limit:g}] seconds for mission {args.mission}")
    if args.stop_after is not None and not (0.0 < args.stop_after <= args.duration):
        raise SystemExit("stop-after must be in (0, duration]")
    if args.rate_hz != 200.0:
        raise SystemExit("This first PD experiment is frozen at 200 Hz for LQR comparability")
    if not (0.0 < args.reference_scale <= 1.0):
        raise SystemExit("reference-scale must be in (0, 1]")
    if not (0.0 <= args.hardstep_transition_s < 2.0):
        raise SystemExit("hardstep-transition-s must be in [0, 2)")
    if args.mission != "hardstep" and args.hardstep_transition_s != 0.0:
        raise SystemExit("hardstep-transition-s is only valid for mission hardstep")
    if not (0.0 <= args.beta <= 1.0):
        raise SystemExit("beta must be in [0, 1]")
    if args.motor_residual_cap_volts <= 0.0:
        raise SystemExit("motor-residual-cap-volts must be positive")
    if args.neural_substeps < 1 or args.neural_substeps > 10:
        raise SystemExit("neural-substeps must be 1..10")
    if args.residual_slew_v_per_s < 0.0:
        raise SystemExit("residual-slew-v-per-s must be nonnegative")
    if not (PLANT.minimum_voltage <= args.motor_floor_volts < PLANT.maximum_voltage):
        raise SystemExit("motor-floor-volts must be inside [0, 24)")
    if args.max_consecutive_deadline_misses < 1:
        raise SystemExit("max-consecutive-deadline-misses must be at least 1")
    if args.max_abs_pitch_deg <= 0.0 or args.max_abs_roll_deg <= 0.0:
        raise SystemExit("mechanical safety angles must be positive")
    if args.raw_home_yaw_tolerance_deg <= 0.0:
        raise SystemExit("raw-home-yaw-tolerance-deg must be positive")
    if args.controller == "pd-cmg" and args.pd_profile != "mujoco":
        raise SystemExit("pd-cmg is intentionally restricted to --pd-profile mujoco; use lqr-equivalent only for baseline bridge validation")


def main() -> None:
    args = parse_args()
    validate_args(args)

    dt = 1.0 / args.rate_hz
    planned_run_duration = args.stop_after if args.stop_after is not None else args.duration
    n_steps = int(round(planned_run_duration * args.rate_hz))
    mujoco_kq, mujoco_kw, cmg_torque_limits = mujoco_pd_parameters_ypr(PLANT)
    effective_beta = args.beta if args.controller == "pd-cmg" else 0.0
    actual_motor_residual_limit = args.motor_residual_cap_volts if args.controller == "pd-cmg" else 0.0

    augmentor = None
    if args.controller == "pd-cmg":
        augmentor = CMGResidualAugmentor(
            channels=3,
            limits=cmg_torque_limits,
            mode="online_pes",
            adaptive_conductance=True,
            beta=args.beta,
            learning_rate=args.learning_rate,
        )

    card = HIL()
    card.open("q8_usb", "0")
    ao_channels = arr.array("i", [0, 1, 2, 3])
    encoder_channels = arr.array("i", [0, 1, 2])
    zero = arr.array("d", [0.0] * 4)
    counts = arr.array("i", [0, 0, 0])

    # Establish zero output before any encoder/tare operation. If startup sensing
    # fails, close the card explicitly because the main loop's finally has not
    # been entered yet.
    card.write_analog(ao_channels, 4, zero)
    try:
        angle_home = read_angles(card, encoder_channels, counts)
    except Exception:
        card.write_analog(ao_channels, 4, zero)
        card.close()
        raise
    raw_home_ypr_deg = np.rad2deg(angle_home)
    if args.expected_raw_home_yaw_deg is not None:
        raw_home_yaw_error_deg = float(raw_home_ypr_deg[0] - args.expected_raw_home_yaw_deg)
        if abs(raw_home_yaw_error_deg) > args.raw_home_yaw_tolerance_deg:
            card.write_analog(ao_channels, 4, zero)
            card.close()
            raise SystemExit(
                "Raw yaw home mismatch: measured "
                f"{raw_home_ypr_deg[0]:.3f} deg, expected {args.expected_raw_home_yaw_deg:.3f} deg, "
                f"difference {raw_home_yaw_error_deg:+.3f} deg exceeds "
                f"+/-{args.raw_home_yaw_tolerance_deg:.3f} deg. Outputs remained zero."
            )
    rate_filter = RateFilter(3)
    previous_motor_residual = np.zeros(4)
    rows: list[dict] = []
    abort_reason = ""
    mission_completed = False
    consecutive_deadline_misses = 0
    session_clock = time.perf_counter()

    print(f"Tared at startup: raw home = {raw_home_ypr_deg} deg")
    print(
        f"armed={args.armed} controller={args.controller} mission={args.mission} "
        f"reference_duration={args.duration}s run_duration={planned_run_duration}s "
        f"pd_profile={args.pd_profile} beta={effective_beta} "
        f"actual per-motor residual cap={actual_motor_residual_limit}V neural_dt={dt/args.neural_substeps:.7f}s"
    )
    print("Ctrl-C or any raised safety condition forces all four outputs to zero in finally.")

    try:
        card.write_analog(ao_channels, 4, zero)
        for k in range(n_steps):
            loop_start = time.perf_counter()
            scheduled_t = k * dt
            wall_t = loop_start - session_clock

            angles = read_angles(card, encoder_channels, counts) - angle_home
            rates = rate_filter.step(angles, dt)
            pitch_deg = float(np.rad2deg(angles[1]))
            roll_deg = float(np.rad2deg(angles[2]))
            if abs(pitch_deg) > args.max_abs_pitch_deg:
                abort_reason = f"pitch safety limit exceeded: {pitch_deg:.3f} deg"
                raise RuntimeError(abort_reason)
            if abs(roll_deg) > args.max_abs_roll_deg:
                abort_reason = f"roll safety limit exceeded: {roll_deg:.3f} deg"
                raise RuntimeError(abort_reason)

            ref_rpy = experiment_reference_euler(
                scheduled_t,
                args.mission,
                args.duration,
                args.reference_scale,
                args.hardstep_transition_s,
            )
            setpoint = np.array([ref_rpy[2], ref_rpy[1], ref_rpy[0]])
            angle_error = setpoint - angles
            angle_error_wrapped = angle_error.copy()
            angle_error_wrapped[0] = np.arctan2(np.sin(angle_error[0]), np.cos(angle_error[0]))
            q_ref = euler_to_quat(*ref_rpy)
            q_meas = euler_to_quat(angles[2], angles[1], angles[0])
            qe, eq_xyz = quat_error(q_ref, q_meas)
            eq_ypr = eq_xyz[[2, 1, 0]]
            body_omega_ypr = euler_rates_ypr_to_body_omega_ypr(angles, rates)
            if args.pd_profile == "mujoco":
                tau_baseline = mujoco_quaternion_pd_torque_ypr(eq_ypr, body_omega_ypr, PLANT)
            else:
                tau_baseline = pd_torque(setpoint, angles, rates, PLANT)
            baseline_raw = PLANT.bias_voltage + torque_to_motor_differential(tau_baseline, PLANT)
            baseline_clipped = np.clip(baseline_raw, PLANT.minimum_voltage, PLANT.maximum_voltage)

            requested_delta_tau = np.zeros(3)
            requested_delta_v = np.zeros(4)
            applied_delta_v = np.zeros(4)
            gate_mean = 0.0
            learning_target = np.zeros(3)
            neuron_v = neuron_r = neuron_activity = neuron_current = decoder_w = None

            if augmentor is not None:
                # Exact canonical architecture up to the declared Hover coordinate
                # transform: torque baseline directly drives CMG, and the independent
                # quaternion-error target supervises PES.
                gate_drive = tau_baseline
                learning_target = mujoco_pes_target_ypr(
                    eq_ypr, body_omega_ypr, args.k_error, args.k_rate
                )
                sub_dt = dt / args.neural_substeps
                out = None
                for _ in range(args.neural_substeps):
                    out = augmentor.step(gate_drive, sub_dt, learning_target)
                assert out is not None
                requested_delta_tau = out.residual
                requested_delta_v = torque_to_motor_differential(requested_delta_tau, PLANT)
                applied_delta_v = limit_and_slew_motor_residual(
                    requested_delta_v,
                    previous_motor_residual,
                    actual_motor_residual_limit,
                    args.residual_slew_v_per_s,
                    dt,
                )
                previous_motor_residual = applied_delta_v.copy()
                gate_mean = float(np.mean(out.gate))
                neuron_v = augmentor.units.v.copy()
                neuron_r = augmentor.units.r.copy()
                neuron_activity = out.activity.copy()
                normalized_gate_drive = np.divide(
                    tau_baseline, cmg_torque_limits,
                    out=np.zeros_like(tau_baseline), where=cmg_torque_limits > 1e-12,
                )
                neuron_current = np.concatenate([
                    augmentor.cfg.current_bias + augmentor.cfg.current_gain * np.maximum(normalized_gate_drive, 0.0),
                    augmentor.cfg.current_bias + augmentor.cfg.current_gain * np.maximum(-normalized_gate_drive, 0.0),
                ])
                decoder_w = augmentor.W.copy().ravel()

            command_preclip = baseline_raw + applied_delta_v
            requested_applied_delta_tau = realized_torque(applied_delta_v, PLANT)
            requested_total_tau = tau_baseline + requested_applied_delta_tau
            if args.allocation_policy == "stability-priority":
                baseline_allocation = allocate_stability_priority_torque(
                    tau_baseline, PLANT, args.motor_floor_volts
                )
                total_allocation = allocate_stability_priority_torque(
                    requested_total_tau, PLANT, args.motor_floor_volts
                )
                baseline_clipped = baseline_allocation.voltage_fblr
                command_computed = total_allocation.voltage_fblr
                realized_baseline_tau = baseline_allocation.realized_torque_ypr
                realized_command_tau = total_allocation.realized_torque_ypr
                allocator_yaw_scale = total_allocation.yaw_scale
                allocator_pitch_roll_scale = total_allocation.pitch_roll_scale
                allocator_common_mode = total_allocation.common_mode_voltage
            else:
                command_computed = np.clip(command_preclip, PLANT.minimum_voltage, PLANT.maximum_voltage)
                realized_baseline_tau = realized_torque(baseline_clipped, PLANT)
                realized_command_tau = realized_torque(command_computed, PLANT)
                allocator_yaw_scale = np.nan
                allocator_pitch_roll_scale = np.nan
                allocator_common_mode = PLANT.bias_voltage
            command_written = command_computed if args.armed else np.zeros(4)
            dac = np.clip(command_written / K_AMP, 0.0, V_MAX_DAC)
            card.write_analog(ao_channels, 4, arr.array("d", dac.tolist()))

            realized_delta_tau = realized_command_tau - realized_baseline_tau
            lower_sat = command_preclip < PLANT.minimum_voltage
            upper_sat = command_preclip > PLANT.maximum_voltage

            row = {
                "t": scheduled_t,
                "wall_t": wall_t,
                "yaw_deg": np.rad2deg(angles[0]),
                "pitch_deg": pitch_deg,
                "roll_deg": roll_deg,
                "yaw_ref_deg": np.rad2deg(setpoint[0]),
                "pitch_ref_deg": np.rad2deg(setpoint[1]),
                "roll_ref_deg": np.rad2deg(setpoint[2]),
                "raw_yaw_deg": np.rad2deg(angles[0] + angle_home[0]),
                "raw_pitch_deg": np.rad2deg(angles[1] + angle_home[1]),
                "raw_roll_deg": np.rad2deg(angles[2] + angle_home[2]),
                "yaw_error_wrapped_deg": np.rad2deg(angle_error_wrapped[0]),
                "pitch_error_deg": np.rad2deg(angle_error_wrapped[1]),
                "roll_error_deg": np.rad2deg(angle_error_wrapped[2]),
                "wrapped_euler_error_norm_deg": np.linalg.norm(np.rad2deg(angle_error_wrapped)),
                "allocator_yaw_scale": allocator_yaw_scale,
                "allocator_pitch_roll_scale": allocator_pitch_roll_scale,
                "allocator_common_mode_V": allocator_common_mode,
                "allocator_motor_floor_V": args.motor_floor_volts if args.allocation_policy == "stability-priority" else 0.0,
                "yaw_rate_dps": np.rad2deg(rates[0]),
                "pitch_rate_dps": np.rad2deg(rates[1]),
                "roll_rate_dps": np.rad2deg(rates[2]),
                "qerr_rad": quat_angle(qe),
                "gate_mean": gate_mean,
                "requested_residual_torque_norm": float(np.linalg.norm(requested_delta_tau)),
                "realized_residual_torque_norm": float(np.linalg.norm(realized_delta_tau)),
            }
            for i, axis in enumerate(AXES):
                row[f"tau0_{axis}"] = tau_baseline[i]
                row[f"quaternion_error_vector_{axis}"] = eq_ypr[i]
                row[f"body_omega_{axis}_rad_s"] = body_omega_ypr[i]
                row[f"learning_target_{axis}"] = learning_target[i]
                row[f"requested_delta_tau_{axis}"] = requested_delta_tau[i]
                row[f"realized_delta_tau_{axis}"] = realized_delta_tau[i]
            for i, channel in enumerate(CHANNELS):
                row[channel] = command_written[i]
                row[f"{channel}_computed"] = command_computed[i]
                row[f"{channel}_baseline_raw"] = baseline_raw[i]
                row[f"{channel}_baseline_clipped"] = baseline_clipped[i]
                row[f"{channel}_delta_requested"] = requested_delta_v[i]
                row[f"{channel}_delta_applied"] = applied_delta_v[i]
                row[f"{channel}_lower_sat"] = int(lower_sat[i])
                row[f"{channel}_upper_sat"] = int(upper_sat[i])
            if neuron_v is not None:
                for i, (value_v, value_r, value_a, value_i) in enumerate(zip(neuron_v, neuron_r, neuron_activity, neuron_current)):
                    row[f"neuron_v_{i}"] = value_v
                    row[f"neuron_r_{i}"] = value_r
                    row[f"neuron_activity_{i}"] = value_a
                    row[f"neuron_current_{i}"] = value_i
                for i, weight in enumerate(decoder_w):
                    row[f"decoder_w_{i}"] = weight

            elapsed = time.perf_counter() - loop_start
            row["loop_elapsed_s"] = elapsed
            row["deadline_miss"] = int(elapsed > dt)
            rows.append(row)

            if elapsed > dt:
                consecutive_deadline_misses += 1
            else:
                consecutive_deadline_misses = 0
                time.sleep(dt - elapsed)
            if consecutive_deadline_misses >= args.max_consecutive_deadline_misses:
                abort_reason = f"{consecutive_deadline_misses} consecutive 200-Hz deadline misses"
                raise RuntimeError(abort_reason)

            if k % int(args.rate_hz) == 0:
                print(
                    f"t={scheduled_t:5.2f}s ypr={np.round(np.rad2deg(angles), 2)} "
                    f"computed_V={np.round(command_computed, 2)} "
                    f"delta_V={np.round(applied_delta_v, 3)} gate={gate_mean:.3f} "
                    f"alloc_pr={allocator_pitch_roll_scale:.3f} alloc_yaw={allocator_yaw_scale:.3f}"
                )
        mission_completed = True
        completion_label = "MISSION COMPLETE" if planned_run_duration == args.duration else "QUALIFICATION SEGMENT COMPLETE"
        print(f"{completion_label}: {args.mission} finished all {n_steps} samples.")
    except KeyboardInterrupt:
        abort_reason = "KeyboardInterrupt"
        print("Interrupted by operator.")
    except Exception as ex:
        if not abort_reason:
            abort_reason = f"{type(ex).__name__}: {ex}"
        print(f"ABORT: {abort_reason}")
        raise
    finally:
        card.write_analog(ao_channels, 4, zero)
        card.close()
        print("All four Q8 analog outputs forced to zero. Card closed.")

        if rows:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            armed_tag = "armed" if args.armed else "dryrun"
            output = EXPERIMENT_ROOT / "results" / "hardware" / f"{args.controller}_{armed_tag}_{timestamp}"
            output.mkdir(parents=True, exist_ok=True)
            csv_path = output / "trace.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)

            error_ypr = np.array([[
                r["yaw_error_wrapped_deg"], r["pitch_error_deg"], r["roll_error_deg"]
            ] for r in rows])
            error_magnitude = np.linalg.norm(error_ypr, axis=1)
            qerr = np.array([r["qerr_rad"] for r in rows])
            summary = {
                "platform": "hover3dof_hardware_pd_track",
                "hardware": True,
                "controller": args.controller,
                "pd_profile": args.pd_profile,
                "armed": args.armed,
                "mission": args.mission,
                "duration": args.duration,
                "planned_run_duration_s": planned_run_duration,
                "rate_hz": args.rate_hz,
                "reference_scale": args.reference_scale,
                "hardstep_transition_s": args.hardstep_transition_s,
                "beta": effective_beta,
                "actual_motor_residual_cap_volts": actual_motor_residual_limit,
                "mujoco_kq_ypr_Nm": mujoco_kq.tolist(),
                "mujoco_kw_ypr_Nm_s": mujoco_kw.tolist(),
                "cmg_torque_limits_ypr_Nm": cmg_torque_limits.tolist(),
                "learning_rate": args.learning_rate,
                "k_error": args.k_error,
                "k_rate": args.k_rate,
                "residual_slew_v_per_s": args.residual_slew_v_per_s,
                "allocation_policy": args.allocation_policy,
                "motor_floor_volts": args.motor_floor_volts if args.allocation_policy == "stability-priority" else 0.0,
                "neural_substeps": args.neural_substeps,
                "neural_dt_s": dt / args.neural_substeps,
                "raw_home_ypr_deg": raw_home_ypr_deg.tolist(),
                "expected_raw_home_yaw_deg": args.expected_raw_home_yaw_deg,
                "raw_home_yaw_tolerance_deg": args.raw_home_yaw_tolerance_deg,
                "run_completed": bool(mission_completed and len(rows) == n_steps and not abort_reason),
                "full_mission_completed": bool(
                    mission_completed and planned_run_duration == args.duration
                    and len(rows) == n_steps and not abort_reason
                ),
                "angle_err_mean_deg": float(np.mean(error_magnitude)),
                "angle_err_max_deg": float(np.max(error_magnitude)),
                "axis_error_mae_deg": dict(zip(AXES, np.mean(np.abs(error_ypr), axis=0).tolist())),
                "axis_error_rmse_deg": dict(zip(AXES, np.sqrt(np.mean(error_ypr**2, axis=0)).tolist())),
                "qerr_mean_rad": float(np.mean(qerr)),
                "qerr_max_rad": float(np.max(qerr)),
                "neuron_columns": {
                    "membrane": "neuron_v_0..5",
                    "gate": "neuron_r_0..5",
                    "decoder_activity": "neuron_activity_0..5",
                    "input_current": "neuron_current_0..5",
                    "decoder_weights": "decoder_w_0..17"
                },
                "lower_saturation_fraction": float(np.mean([[r[f"{c}_lower_sat"] for c in CHANNELS] for r in rows])),
                "upper_saturation_fraction": float(np.mean([[r[f"{c}_upper_sat"] for c in CHANNELS] for r in rows])),
                "deadline_miss_fraction": float(np.mean([r["deadline_miss"] for r in rows])),
                "allocator_yaw_scale_min": float(np.nanmin([r["allocator_yaw_scale"] for r in rows])) if args.allocation_policy == "stability-priority" else None,
                "allocator_yaw_scale_mean": float(np.nanmean([r["allocator_yaw_scale"] for r in rows])) if args.allocation_policy == "stability-priority" else None,
                "allocator_pitch_roll_scale_min": float(np.nanmin([r["allocator_pitch_roll_scale"] for r in rows])) if args.allocation_policy == "stability-priority" else None,
                "allocator_pitch_roll_scale_mean": float(np.nanmean([r["allocator_pitch_roll_scale"] for r in rows])) if args.allocation_policy == "stability-priority" else None,
                "abort_reason": abort_reason,
                "n_steps_logged": len(rows),
                "trace": str(csv_path),
            }
            args_dict = vars(args).copy()
            try:
                provenance = manifest(ACC_ROOT, "hover3dof_hardware_pd_track", args.controller, Path(__file__), args_dict)
                write_json(output / "manifest.json", provenance)
            except Exception as ex:
                print(f"(manifest write skipped: {ex})")
            write_json(output / "summary.json", summary)
            print(
                f"angle_err_mean_deg={summary['angle_err_mean_deg']:.3f} "
                f"angle_err_max_deg={summary['angle_err_max_deg']:.3f} results={output}"
            )


if __name__ == "__main__":
    try:
        main()
    except HILError as ex:
        print(f"HIL error: {ex.get_error_message()}")
        raise
