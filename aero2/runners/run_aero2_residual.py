"""Aero2 2-DOF residual-augmentation runner (classical anchor + bounded gate-state residual).

Ports the hardware-validated Qube residual ablation to Aero2. The CLASSICAL controller
(smc / backstepping / nmpc) remains the stability anchor; a bounded HyperLIF / Adaptive
HyperLIF gate-state residual is optionally added at the VIRTUAL pitch/yaw level and re-mapped
to motor channels via the existing output_mapping (the controller structure is NOT bypassed).

Reuses the working hardware code from aero2_clean WITHOUT modifying it (imported via sys.path).
Outputs go under 04_Aero2_SNNs/results/residual/.

Modes: none | shadow_gate | gate | always_on | shuffled_gate
  none/shadow_gate  -> motor command == classical (residual applied = 0).
  gate/always_on/shuffled_gate -> residual applied ONLY in active control, capped, double-clipped.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

# --- reuse the working Aero2 hardware code from aero2_clean (do not modify it) ----------
AERO2_CLEAN = Path(os.environ.get("AERO2_CLEAN", r"C:\02_Research\01_Robotics_Quanser\01_Aero2\aero2_clean"))
QUANSER_PY = Path(os.environ.get("QUANSER_PYTHON", r"C:\Quanser\0_libraries\python"))
for _p in (str(AERO2_CLEAN), str(QUANSER_PY)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from M7_Aero2_Linear_Controllers.src.M7_aero2_simulink_2dof_pd_replicate import (  # noqa: E402
    DirectHilAero2IO, PalAero2IO, SimulinkSecondOrderDerivative, clamp, output_mapping, simulink_square,
)
from M8_Aero2_Nonlinear_Controllers.src.controllers.backstepping import Backstepping2DOFController  # noqa: E402
from M8_Aero2_Nonlinear_Controllers.src.controllers.sliding_modes import SlidingMode2DOFController  # noqa: E402
from M8_Aero2_Nonlinear_Controllers.src.controllers.nmpc import NMPC2DOFController  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from aero2_residual.residual_gate import Aero2GateResidual, ShuffleSource, str2bool, make_inrun_shuffle_buffer  # noqa: E402

# constants mirrored from aero2_clean (kept in sync; clean ref is the source of truth)
VOLTAGE_LIMIT = 24.0
THETA_SAFE_LIMIT = 0.90
PSI_SAFE_LIMIT = 1.40
MAX_ABS_GYRO_Y = 8.0
MAX_ABS_GYRO_Z = 8.0
MAX_SAMPLE_OVERRUN_FRACTION = 0.35
GYRO_BIAS_Y = -0.01797350
GYRO_BIAS_Z = -0.00718040
FILTER_WN = 100.0
FILTER_DAMPING = 1.0

RESIDUAL_APPLIED_MODES = frozenset({"gate", "always_on", "shuffled_gate"})
RESIDUAL_MODES = ("none", "shadow_gate", "gate", "always_on", "shuffled_gate")
RESIDUAL_CHANNELS = ("pitch", "yaw", "pitch_yaw", "motor_pair")


def make_controller(name, voltage_limit, variant="nominal"):
    if name == "backstepping":
        if variant == "yawboost":
            return Backstepping2DOFController(k1_pitch=2.0, k2_pitch=3.0, k1_yaw=4.0, k2_yaw=3.5, voltage_limit=voltage_limit)
        return Backstepping2DOFController(voltage_limit=voltage_limit)
    if name == "smc":
        if variant == "yawboost":
            return SlidingMode2DOFController(lambda_pitch=2.5, eta_pitch=0.7, phi_pitch=0.10, lambda_yaw=4.0, eta_yaw=3.0, phi_yaw=0.25, voltage_limit=voltage_limit)
        return SlidingMode2DOFController(voltage_limit=voltage_limit)
    if name == "nmpc":
        if variant == "realtime":
            return NMPC2DOFController(prediction_dt=0.06, horizon=5, q_diag=(80.0, 2.5, 50.0, 1.5), r_diag=(0.10, 0.10), terminal_scale=1.5, offset_grid=(-2.5, 0.0, 2.5), voltage_limit=voltage_limit)
        return NMPC2DOFController(voltage_limit=voltage_limit)
    raise ValueError(f"unknown controller: {name}")


def parse_args():
    p = argparse.ArgumentParser(description="Aero2 residual-augmentation runner (classical + bounded gate residual).")
    # classical controller / hardware (mirrors aero2_clean M8 runner)
    p.add_argument("--controller", choices=["smc", "backstepping", "nmpc"], default="smc")
    p.add_argument("--variant", choices=["nominal", "yawboost", "realtime"], default="yawboost")
    p.add_argument("--backend", choices=["hil", "pal"], default="hil")
    p.add_argument("--output-mode", choices=["direct", "mixed", "mixed-reversed"], default="direct")
    p.add_argument("--frequency", type=float, default=500.0)
    p.add_argument("--run-time", type=float, default=30.0)
    p.add_argument("--filter-wn", type=float, default=FILTER_WN)
    p.add_argument("--filter-damping", type=float, default=FILTER_DAMPING)
    p.add_argument("--filter-dt-mode", choices=["actual", "fixed"], default="actual")
    # mission / references
    p.add_argument("--mission", choices=["tracking", "equilibrium"], default="tracking",
                   help="tracking=square-wave pitch/yaw; equilibrium=zero references (hold + manual perturb).")
    p.add_argument("--pitch-freq", type=float, default=0.05)
    p.add_argument("--yaw-freq", type=float, default=0.04)
    p.add_argument("--pitch-amp-deg", type=float, default=20.0)
    p.add_argument("--yaw-amp-deg", type=float, default=45.0)
    p.add_argument("--voltage-limit", type=float, default=VOLTAGE_LIMIT)
    p.add_argument("--theta-safe-limit", type=float, default=THETA_SAFE_LIMIT)
    p.add_argument("--psi-safe-limit", type=float, default=PSI_SAFE_LIMIT)
    p.add_argument("--max-abs-gyro-y", type=float, default=MAX_ABS_GYRO_Y)
    p.add_argument("--max-abs-gyro-z", type=float, default=MAX_ABS_GYRO_Z)
    p.add_argument("--no-safety", action="store_true")
    p.add_argument("--plot-live", action="store_true")
    p.add_argument("--plot-every", type=int, default=100)
    p.add_argument("--ask-save-plots", action="store_true")
    p.add_argument("--tag", default=None)
    # residual
    p.add_argument("--residual-mode", choices=list(RESIDUAL_MODES), default="none")
    p.add_argument("--residual-channel", choices=list(RESIDUAL_CHANNELS), default="pitch")
    p.add_argument("--residual-scale", type=float, default=1.0)
    p.add_argument("--residual-max-voltage", type=float, default=0.5, help="Hard cap on |applied residual| per channel (V).")
    p.add_argument("--residual-neuron", choices=["hyperlif", "adaptive_hyperlif"], default="adaptive_hyperlif")
    p.add_argument("--residual-threshold", type=float, default=0.15)
    p.add_argument("--residual-demand-threshold", type=float, default=0.20)
    p.add_argument("--residual-sign", type=float, default=1.0)
    p.add_argument("--residual-apply-active-only", type=str, default="true",
                   help="true/false. Active-control-only application (ENFORCED for safety regardless).")
    p.add_argument("--residual-settle-s", type=float, default=1.0, help="No residual during the first N s (startup).")
    p.add_argument("--residual-shuffle-offset-s", type=float, default=5.0)
    p.add_argument("--residual-shuffle-source", type=Path, default=None)
    p.add_argument("--residual-log-prefix", type=str, default=None)
    # scripted REFERENCE perturbations (repeatable; applied to the reference only, not the motor)
    p.add_argument("--perturbation-profile",
                   choices=["none", "pitch_pulse_train", "yaw_pulse_train", "pitch_yaw_pulse_train"],
                   default="none")
    p.add_argument("--perturbation-amplitude-pitch", type=float, default=0.08, help="A (rad) for pitch pulses.")
    p.add_argument("--perturbation-amplitude-yaw", type=float, default=0.08, help="A (rad) for yaw pulses.")
    p.add_argument("--perturbation-width-s", type=float, default=3.0)
    p.add_argument("--perturbation-times", type=str, default="10,20,30,40", help="comma list of window start times (s).")
    p.add_argument("--perturbation-alternating-sign", type=str, default="true", help="true/false: alternate +/- per window.")
    return p.parse_args()


def _parse_times(spec):
    return [float(x) for x in str(spec).split(",") if x.strip() != ""]


def perturbation_reference(profile, t, times, width, amp_pitch, amp_yaw, alternating):
    """Repeatable scripted REFERENCE perturbation. Returns (theta_pert, psi_pert, active).

    Window i (start times[i], duration `width`): sign alternates +,-,+,- (if `alternating`)
    and magnitude escalates 1.0x for the first half of the windows, 1.5x for the second half
    (so the default times/width/A reproduce: +A, -A, +1.5A, -1.5A). Reference-only; never
    touches motor voltage.
    """
    if profile == "none" or not times:
        return 0.0, 0.0, False
    n = len(times)
    for i, t0 in enumerate(times):
        if t0 <= t < t0 + width:
            scale = 1.0 if i < n / 2.0 else 1.5
            sgn = (1.0 if i % 2 == 0 else -1.0) if alternating else 1.0
            vp = sgn * scale * amp_pitch
            vy = sgn * scale * amp_yaw
            if profile == "pitch_pulse_train":
                return vp, 0.0, True
            if profile == "yaw_pulse_train":
                return 0.0, vy, True
            if profile == "pitch_yaw_pulse_train":
                return vp, vy, True
    return 0.0, 0.0, False


def main():
    args = parse_args()
    if args.backend == "pal" and args.voltage_limit > 15.0:
        print("Warning: PAL clips to +/-15 V; lowering voltage limit to 15 V.")
        args.voltage_limit = 15.0
    if args.backend == "hil" and args.voltage_limit > 24.0:
        raise ValueError("Refusing voltage-limit above +/-24 V.")

    residual_mode = args.residual_mode
    residual_applied_mode = residual_mode in RESIDUAL_APPLIED_MODES
    apply_active_only = str2bool(args.residual_apply_active_only)
    sign = float(args.residual_sign)
    scale = float(args.residual_scale)
    vmax = float(args.residual_max_voltage)
    vlim = float(args.voltage_limit)

    if args.mission == "equilibrium":
        args.pitch_amp_deg = 0.0
        args.yaw_amp_deg = 0.0

    perturbation_profile = args.perturbation_profile
    perturbation_times = _parse_times(args.perturbation_times)
    perturbation_alternating = str2bool(args.perturbation_alternating_sign)

    sample_time = 1.0 / args.frequency
    pitch_amp = math.radians(args.pitch_amp_deg)
    yaw_amp = math.radians(args.yaw_amp_deg)
    out_dir = PROJECT_ROOT / "results" / "residual"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = args.residual_log_prefix or f"aero2_{args.controller}_{residual_mode}_{args.mission}"
    stem = f"{prefix}_{args.backend}_{timestamp}"
    csv_path = out_dir / f"{stem}.csv"

    controller = make_controller(args.controller, vlim, args.variant)
    residual_gate = Aero2GateResidual(args.residual_neuron, sample_time, args.residual_threshold,
                                      args.residual_demand_threshold, vmax)
    shuffle_source = None
    if residual_mode == "shuffled_gate" and args.residual_shuffle_source:
        shuffle_source = ShuffleSource(args.residual_shuffle_source, args.residual_shuffle_offset_s)
    shuffle_buf = make_inrun_shuffle_buffer(args.residual_shuffle_offset_s, args.frequency)

    print("=" * 72)
    print(f"Aero2 RESIDUAL runner | controller={args.controller}/{args.variant} backend={args.backend} "
          f"output_mode={args.output_mode}")
    print(f"mission={args.mission} (pitch_amp={args.pitch_amp_deg} deg, yaw_amp={args.yaw_amp_deg} deg) "
          f"run_time={args.run_time}s freq={args.frequency}Hz")
    print(f"RESIDUAL MODE: {residual_mode} | channel={args.residual_channel} | neuron={args.residual_neuron}")
    if residual_applied_mode:
        print(f"RESIDUAL APPLIED TO MOTORS: *** YES *** (active control only; |residual| <= {vmax:.3f} V/chan; "
              f"total clipped to +/-{vlim:.1f} V)")
    elif residual_mode == "shadow_gate":
        print("RESIDUAL APPLIED TO MOTORS: NO  (SHADOW: computed + logged only; u_total = u0)")
    else:
        print("RESIDUAL APPLIED TO MOTORS: NO  (classical controller only)")
    print(f"  scale={scale} sign={sign} max_voltage={vmax} V apply_active_only={apply_active_only} "
          f"settle={args.residual_settle_s}s thr={args.residual_threshold} demand_thr={args.residual_demand_threshold}")
    if perturbation_profile != "none":
        print(f"PERTURBATION (reference-only): {perturbation_profile} A_pitch={args.perturbation_amplitude_pitch} "
              f"A_yaw={args.perturbation_amplitude_yaw} width={args.perturbation_width_s}s "
              f"times={perturbation_times} alternating={perturbation_alternating}")
    else:
        print("PERTURBATION: none")
    print(f"CSV: {csv_path}")
    print("Press Ctrl+C to stop safely.")
    print("=" * 72)

    live_plot = None
    if args.plot_live:
        from aero2_common.live_plot import Aero2LivePlotter
        live_plot = Aero2LivePlotter(title=f"Aero2 {args.controller} residual={residual_mode}", update_every=args.plot_every)

    pitch_filter = SimulinkSecondOrderDerivative(args.filter_wn, args.filter_damping)
    yaw_filter = SimulinkSecondOrderDerivative(args.filter_wn, args.filter_damping)
    io = PalAero2IO(args.frequency) if args.backend == "pal" else DirectHilAero2IO(args.frequency)

    rows = []
    start = time.time()
    stop_reason = "completed"
    overrun_count = 0
    k = 0
    last_loop_start = None

    try:
        while True:
            loop_start = time.time()
            t = loop_start - start
            dt_actual = sample_time if last_loop_start is None else max(1e-6, loop_start - last_loop_start)
            filter_dt = dt_actual if args.filter_dt_mode == "actual" else sample_time
            if t >= args.run_time:
                break

            sample = io.read()
            theta = sample.theta
            psi = sample.psi
            gyro_y_corr = sample.gyro_y - GYRO_BIAS_Y
            gyro_z_corr = sample.gyro_z - GYRO_BIAS_Z

            # ---- safety (UNCHANGED from clean reference) ----
            safety_tripped = False
            if not args.no_safety:
                if abs(theta) > args.theta_safe_limit:
                    stop_reason = f"safety theta {theta:+.4f} rad"; safety_tripped = True
                elif abs(psi) > args.psi_safe_limit:
                    stop_reason = f"safety psi {psi:+.4f} rad"; safety_tripped = True
                elif abs(gyro_y_corr) > args.max_abs_gyro_y:
                    stop_reason = f"safety gyro_y {gyro_y_corr:+.4f}"; safety_tripped = True
                elif abs(gyro_z_corr) > args.max_abs_gyro_z:
                    stop_reason = f"safety gyro_z {gyro_z_corr:+.4f}"; safety_tripped = True
            if safety_tripped:
                print(f"Safety stop: {stop_reason}", flush=True)
                break

            # reference = base (square wave / 0) + scripted perturbation (reference-only)
            theta_ref_base = simulink_square(t, args.pitch_freq, pitch_amp)
            psi_ref_base = simulink_square(t, args.yaw_freq, yaw_amp)
            theta_ref_pert, psi_ref_pert, perturbation_active = perturbation_reference(
                perturbation_profile, t, perturbation_times, args.perturbation_width_s,
                args.perturbation_amplitude_pitch, args.perturbation_amplitude_yaw, perturbation_alternating)
            theta_ref = theta_ref_base + theta_ref_pert
            psi_ref = psi_ref_base + psi_ref_pert
            theta_rate_f = pitch_filter.filtered_rate
            psi_rate_f = yaw_filter.filtered_rate
            x = np.array([theta, theta_rate_f, psi, psi_rate_f])
            u_virtual, aux = controller.step(x, theta_ref, psi_ref, filter_dt)
            u_pitch, u_yaw = float(u_virtual[0]), float(u_virtual[1])

            pitch_error = theta_ref - theta
            yaw_error = psi_ref - psi
            sensors_valid = all(math.isfinite(v) for v in (theta, psi, theta_rate_f, psi_rate_f, u_pitch, u_yaw))
            control_mode = ("startup" if t < args.residual_settle_s else
                            ("invalid_sensor" if not sensors_valid else "active"))
            is_active = (control_mode == "active")

            # ---- base (classical) motor channels ----
            b0_raw, b1_raw = output_mapping(args.output_mode, u_pitch, u_yaw)
            base_left = clamp(b0_raw, -vlim, vlim)
            base_right = clamp(b1_raw, -vlim, vlim)

            # ---- residual (computed for shadow + applied modes; never for none) ----
            pd = yd = cd = sat = 0.0
            gs = cs = ev = af = 0.0
            pitch_cand = yaw_cand = left_cand = right_cand = 0.0
            pitch_res = yaw_res = left_res = right_res = 0.0
            total_left, total_right = base_left, base_right
            try:
                if residual_mode != "none":
                    pd, yd, cd, sat = residual_gate.demand_scores(
                        pitch_error, theta_rate_f, yaw_error, psi_rate_f, u_pitch, u_yaw, vlim)
                    g = residual_gate.step_gate(cd)
                    gs, cs, ev, af = g["gate_state"], g["conductance_state"], g["event_activity"], g["residual_active_flag"]
                    pitch_cand, yaw_cand, corr_p, corr_y = residual_gate.candidates(gs, cd, pitch_error, yaw_error)
                    left_cand, right_cand = output_mapping(args.output_mode, pitch_cand, yaw_cand)

                    # time-misaligned gate/demand for shuffled_gate
                    g_shuf, d_shuf = 0.0, 0.0
                    if residual_mode == "shuffled_gate":
                        if shuffle_source is not None:
                            g_shuf, d_shuf = shuffle_source.sample(t)
                        else:
                            if len(shuffle_buf) == shuffle_buf.maxlen:
                                g_shuf, d_shuf = shuffle_buf[0]
                            shuffle_buf.append((gs, cd))

                    # virtual applied per mode (before channel routing / cap)
                    if residual_applied_mode and is_active:
                        if residual_mode == "gate":
                            vp, vy = sign * scale * pitch_cand, sign * scale * yaw_cand
                        elif residual_mode == "always_on":
                            vp, vy = sign * scale * vmax * corr_p, sign * scale * vmax * corr_y
                        else:  # shuffled_gate
                            vp = sign * scale * vmax * corr_p * g_shuf * d_shuf
                            vy = sign * scale * vmax * corr_y * g_shuf * d_shuf
                        # channel routing
                        if args.residual_channel == "pitch":
                            vy = 0.0
                        elif args.residual_channel == "yaw":
                            vp = 0.0
                        if args.residual_channel == "motor_pair":
                            la, ra = output_mapping(args.output_mode, vp, vy)
                            left_res = clamp(la, -vmax, vmax)
                            right_res = clamp(ra, -vmax, vmax)
                            total_left = clamp(base_left + left_res, -vlim, vlim)
                            total_right = clamp(base_right + right_res, -vlim, vlim)
                            pitch_res, yaw_res = 0.0, 0.0
                        else:
                            pitch_res = clamp(vp, -vmax, vmax)
                            yaw_res = clamp(vy, -vmax, vmax)
                            t0_raw, t1_raw = output_mapping(args.output_mode, u_pitch + pitch_res, u_yaw + yaw_res)
                            total_left = clamp(t0_raw, -vlim, vlim)
                            total_right = clamp(t1_raw, -vlim, vlim)
            except Exception:
                # any residual error -> classical command only (never crash, never unsafe)
                total_left, total_right = base_left, base_right
                pitch_res = yaw_res = left_res = right_res = 0.0

            io.write(total_left, total_right)
            pitch_filter.update(theta, filter_dt)
            yaw_filter.update(psi, filter_dt)

            # effective channel-level residual actually applied
            left_applied_eff = total_left - base_left
            right_applied_eff = total_right - base_right
            applied_energy = (left_applied_eff ** 2 + right_applied_eff ** 2) * dt_actual
            applied_active = 1.0 if max(abs(left_applied_eff), abs(right_applied_eff)) > 1.0e-3 else 0.0

            loop_elapsed = time.time() - loop_start
            if loop_elapsed > sample_time:
                overrun_count += 1
                if not args.no_safety and k > int(args.frequency) and overrun_count / max(1, k + 1) > MAX_SAMPLE_OVERRUN_FRACTION:
                    stop_reason = "safety sample overrun fraction"
                    print(f"Safety stop: {stop_reason}", flush=True)
                    break

            rows.append({
                "k": k, "t": t, "controller": args.controller, "control_mode": control_mode,
                "dt_actual": dt_actual,
                "theta": theta, "theta_ref": theta_ref, "pitch_error": pitch_error, "theta_rate": theta_rate_f,
                "psi": psi, "psi_ref": psi_ref, "yaw_error": yaw_error, "psi_rate": psi_rate_f,
                # scripted reference perturbation (reference-only; motor voltages untouched)
                "perturbation_profile": perturbation_profile,
                "perturbation_active_flag": int(perturbation_active),
                "theta_ref_base": theta_ref_base, "psi_ref_base": psi_ref_base,
                "theta_ref_perturbation": theta_ref_pert, "psi_ref_perturbation": psi_ref_pert,
                "theta_ref_total": theta_ref, "psi_ref_total": psi_ref,
                "u_pitch": u_pitch, "u_yaw": u_yaw,
                "base_left_voltage": base_left, "base_right_voltage": base_right,
                "total_left_voltage": total_left, "total_right_voltage": total_right,
                "left_motor_voltage": total_left, "right_motor_voltage": total_right,
                # residual block
                "residual_mode": residual_mode, "residual_channel": args.residual_channel,
                "residual_scale": scale, "residual_max_voltage": vmax, "residual_sign": sign,
                "residual_neuron": args.residual_neuron, "residual_threshold": args.residual_threshold,
                "residual_apply_active_only": int(apply_active_only),
                "pitch_demand_score": pd, "yaw_demand_score": yd, "combined_demand_score": cd,
                "gate_state": gs, "conductance_state": cs, "event_activity": ev, "residual_active_flag": af,
                "pitch_residual_candidate": pitch_cand, "yaw_residual_candidate": yaw_cand,
                "left_residual_candidate": left_cand, "right_residual_candidate": right_cand,
                "pitch_residual_applied": pitch_res, "yaw_residual_applied": yaw_res,
                "left_residual_applied": left_applied_eff, "right_residual_applied": right_applied_eff,
                "saturation_proximity": sat,
                "applied_residual_energy": applied_energy, "applied_residual_active_flag": applied_active,
                "channel_saturated": int(abs(total_left) >= vlim - 1e-9 or abs(total_right) >= vlim - 1e-9),
                "gyro_y_corr": gyro_y_corr, "gyro_z_corr": gyro_z_corr,
                "motor0_current": sample.motor0_current, "motor1_current": sample.motor1_current,
            })

            if live_plot is not None:
                live_plot.sample(k, t, theta_ref, theta, psi_ref, psi, u_pitch, u_yaw)
            if k % max(1, int(args.frequency)) == 0:
                print(f"t={t:6.2f} th={theta:+.3f}/{theta_ref:+.3f} ps={psi:+.3f}/{psi_ref:+.3f} "
                      f"u=({u_pitch:+.2f},{u_yaw:+.2f}) ch=({total_left:+.2f},{total_right:+.2f}) "
                      f"dmd={cd:.2f} gate={gs:.2f} res=({pitch_res:+.3f},{yaw_res:+.3f}) [{control_mode}]", flush=True)
            k += 1
            last_loop_start = loop_start
            time.sleep(max(0.0, sample_time - (time.time() - loop_start)))

    except KeyboardInterrupt:
        stop_reason = "user interrupted"
        print("\nUser interrupted.", flush=True)
    finally:
        print("Stopping outputs and closing hardware...", flush=True)
        try:
            io.write(0.0, 0.0); time.sleep(0.3)
        except Exception as exc:
            print(f"Warning: could not write zero voltage: {exc}", flush=True)
        try:
            io.terminate()
        except Exception as exc:
            print(f"Warning: could not terminate cleanly: {exc}", flush=True)
        if rows:
            with open(csv_path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)
            print(f"Saved CSV: {csv_path}  ({len(rows)} rows, stop_reason={stop_reason}, overruns={overrun_count})")
        else:
            print("No data collected.")
        if live_plot is not None:
            should_save = False
            if args.ask_save_plots:
                should_save = input("Save live plot? [y/N]: ").strip().lower() in {"y", "yes"}
            if should_save:
                live_plot.save(out_dir / f"{stem}_live.png")
            live_plot.close()
        print("Done.")


if __name__ == "__main__":
    main()
