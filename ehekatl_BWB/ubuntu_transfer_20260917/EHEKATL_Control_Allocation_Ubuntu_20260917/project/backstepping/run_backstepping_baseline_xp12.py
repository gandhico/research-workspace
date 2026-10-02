#!/usr/bin/env python3
"""Instrumented Stage-1 runner for the unchanged original backstepping law.

The default is observe-only: commands are calculated and logged but never sent.
Pass --engage only after the logger/routing evidence has been reviewed.
"""

import argparse
import csv
import math
import time
from pathlib import Path

import Backstepping
import xpc


MEASUREMENTS = (
    ("p_deg_s", "sim/flightmodel/position/P", 0),
    ("q_deg_s", "sim/flightmodel/position/Q", 0),
    ("r_deg_s", "sim/flightmodel/position/R", 0),
    ("p_dot_deg_s2", "sim/flightmodel/position/P_dot", 0),
    ("q_dot_deg_s2", "sim/flightmodel/position/Q_dot", 0),
    ("r_dot_deg_s2", "sim/flightmodel/position/R_dot", 0),
    ("ias_kts", "sim/flightmodel/position/indicated_airspeed", 0),
    ("tas_m_s", "sim/flightmodel/position/true_airspeed", 0),
    ("groundspeed_m_s", "sim/flightmodel/position/groundspeed", 0),
    ("vvi_m_s", "sim/flightmodel/position/vh_ind", 0),
    ("agl_m", "sim/flightmodel/position/y_agl", 0),
    ("alpha_deg", "sim/flightmodel/position/alpha", 0),
    ("beta_deg", "sim/flightmodel/position/beta", 0),
    ("flight_path_deg", "sim/flightmodel/position/vpath", 0),
    ("track_deg", "sim/flightmodel/position/hpath", 0),
    ("local_vx_m_s", "sim/flightmodel/position/local_vx", 0),
    ("local_vy_m_s", "sim/flightmodel/position/local_vy", 0),
    ("local_vz_m_s", "sim/flightmodel/position/local_vz", 0),
    ("local_ax_m_s2", "sim/flightmodel/position/local_ax", 0),
    ("local_ay_m_s2", "sim/flightmodel/position/local_ay", 0),
    ("local_az_m_s2", "sim/flightmodel/position/local_az", 0),
    ("body_vx_m_s", "sim/flightmodel/forces/vx_acf_axis", 0),
    ("body_vy_m_s", "sim/flightmodel/forces/vy_acf_axis", 0),
    ("body_vz_m_s", "sim/flightmodel/forces/vz_acf_axis", 0),
    ("g_axial", "sim/flightmodel/forces/g_axil", 0),
    ("g_side", "sim/flightmodel/forces/g_side", 0),
    ("g_normal", "sim/flightmodel/forces/g_nrml", 0),
    ("roll_moment_n_m", "sim/flightmodel/forces/L_total", 0),
    ("pitch_moment_n_m", "sim/flightmodel/forces/M_total", 0),
    ("yaw_moment_n_m", "sim/flightmodel/forces/N_total", 0),
    ("mass_total_kg", "sim/flightmodel/weight/m_total", 0),
    ("fuel_total_kg", "sim/flightmodel/weight/m_fuel_total", 0),
    ("mach", "sim/flightmodel/misc/machno", 0),
    ("air_density_kg_m3", "sim/weather/rho", 0),
    ("yoke_pitch_ratio", "sim/joystick/yoke_pitch_ratio", 0),
    ("yoke_roll_ratio", "sim/joystick/yoke_roll_ratio", 0),
    ("yoke_yaw_ratio", "sim/joystick/yoke_heading_ratio", 0),
    ("total_pitch_ratio", "sim/cockpit2/controls/total_pitch_ratio", 0),
    ("total_roll_ratio", "sim/cockpit2/controls/total_roll_ratio", 0),
    ("total_yaw_ratio", "sim/cockpit2/controls/total_heading_ratio", 0),
    ("pitch_trim_ratio", "sim/cockpit2/controls/elevator_trim", 0),
    ("roll_trim_ratio", "sim/cockpit2/controls/aileron_trim", 0),
    ("yaw_trim_ratio", "sim/cockpit2/controls/rudder_trim", 0),
    ("flap_ratio", "sim/cockpit2/controls/flap_system_deploy_ratio", 0),
    ("speedbrake_ratio", "sim/cockpit2/controls/speedbrake_ratio", 0),
    ("throttle_engine_0", "sim/flightmodel/engine/ENGN_thro", 0),
    ("throttle_engine_1", "sim/flightmodel/engine/ENGN_thro", 1),
    ("autopilot_on", "sim/cockpit2/autopilot/autopilot_on", 0),
    ("autopilot_servos_on", "sim/cockpit2/autopilot/servos_on", 0),
    ("autothrottle_on", "sim/cockpit2/autopilot/autothrottle_on", 0),
    ("sim_paused", "sim/time/paused", 0),
    ("sim_speed", "sim/time/sim_speed", 0),
    ("replay_mode", "sim/operation/prefs/replay_mode", 0),
    ("art_stab_on", "sim/cockpit/switches/art_stab_on", 0),
    ("elevator_deflection_time_s", "sim/aircraft/controls/acf_elev_def_time", 0),
    ("aileron_deflection_time_s", "sim/aircraft/controls/acf_ailn_def_time", 0),
    ("rudder_deflection_time_s", "sim/aircraft/controls/acf_rudd_def_time", 0),
    ("left_aileron_1_def_deg", "sim/flightmodel/controls/lail1def", 0),
    ("right_aileron_1_def_deg", "sim/flightmodel/controls/rail1def", 0),
    ("left_elevator_1_def_deg", "sim/flightmodel/controls/hstab1_elv1def", 0),
    ("right_elevator_1_def_deg", "sim/flightmodel/controls/hstab1_elv2def", 0),
    ("left_rudder_1_def_deg", "sim/flightmodel/controls/vstab1_rud1def", 0),
    ("right_rudder_1_def_deg", "sim/flightmodel/controls/vstab1_rud2def", 0),
    ("distributed_elv1_wing2l_deg", "sim/flightmodel/controls/elv1_def", 8),
    ("distributed_elv1_wing2r_deg", "sim/flightmodel/controls/elv1_def", 9),
    ("distributed_elv1_wing3l_deg", "sim/flightmodel/controls/elv1_def", 10),
    ("distributed_elv1_wing3r_deg", "sim/flightmodel/controls/elv1_def", 11),
    ("distributed_elv1_outer_l_deg", "sim/flightmodel/controls/elv1_def", 25),
    ("distributed_elv1_outer_r_deg", "sim/flightmodel/controls/elv1_def", 35),
    ("distributed_elv2_wing2l_deg", "sim/flightmodel/controls/elv2_def", 8),
    ("distributed_elv2_wing2r_deg", "sim/flightmodel/controls/elv2_def", 9),
    ("distributed_ail1_wing2l_deg", "sim/flightmodel/controls/ail1_def", 8),
    ("distributed_ail1_wing2r_deg", "sim/flightmodel/controls/ail1_def", 9),
    ("override_joystick", "sim/operation/override/override_joystick", 0),
    ("override_roll", "sim/operation/override/override_joystick_roll", 0),
    ("override_pitch", "sim/operation/override/override_joystick_pitch", 0),
    ("override_flightcontrol", "sim/operation/override/override_flightcontrol", 0),
    ("override_surfaces", "sim/operation/override/override_control_surfaces", 0),
)

ROLL_OVERRIDE_DREF = "sim/operation/override/override_joystick_roll"
ROLL_YOKE_DREF = "sim/joystick/yoke_roll_ratio"
PITCH_OVERRIDE_DREF = "sim/operation/override/override_joystick_pitch"
PITCH_YOKE_DREF = "sim/joystick/yoke_pitch_ratio"


def scalar(value, index=0):
    while isinstance(value, (list, tuple)):
        if not value:
            raise ValueError("empty X-Plane dataref value")
        value = value[min(index, len(value) - 1)]
        index = 0
    return float(value)


def clamp(value, limit):
    if limit <= 0:
        return float(value)
    return max(-limit, min(limit, float(value)))


def read_measurements(client):
    datarefs = list(dict.fromkeys(dataref for _, dataref, _ in MEASUREMENTS))
    values = client.getDREFs(datarefs)
    by_dataref = dict(zip(datarefs, values))
    measurements = {
        field: scalar(by_dataref[dataref], index)
        for field, dataref, index in MEASUREMENTS
    }
    measurements["dynamic_pressure_pa"] = (
        0.5 * measurements["air_density_kg_m3"] * measurements["tas_m_s"] ** 2
    )
    return measurements


def calculate_command(
    roll_ctrl, pitch_ctrl, roll, pitch, ctrl, routing, clip, rudder, throttle,
    control_trim=None,
):
    """Calculate exactly the original controller outputs and wrapper routing."""
    if control_trim is None:
        roll_ctrl_value, pitch_ctrl_value = ctrl[0], ctrl[1]
        trim0 = trim1 = 0.0
    else:
        pitch_index, roll_index = (0, 1) if routing == "legacy" else (1, 0)
        roll_ctrl_value = ctrl[roll_index] - control_trim[roll_index]
        pitch_ctrl_value = ctrl[pitch_index] - control_trim[pitch_index]
        trim0, trim1 = control_trim[0], control_trim[1]
    roll_ctrl.update(roll, roll_ctrl_value)
    pitch_ctrl.update(pitch, pitch_ctrl_value)
    roll_out, pitch_out = roll_ctrl.output, pitch_ctrl.output
    raw0, raw1 = (pitch_out, roll_out) if routing == "legacy" else (roll_out, pitch_out)
    raw0 += trim0
    raw1 += trim1
    sent0, sent1 = clamp(raw0, clip), clamp(raw1, clip)
    sent2 = clamp(rudder, clip)
    return {
        "raw_roll_output": roll_out,
        "raw_pitch_output": pitch_out,
        "sent_ctrl_0": sent0,
        "sent_ctrl_1": sent1,
        "sent_ctrl_2": sent2,
        "sent_ctrl_3": throttle,
        "ctrl_0_saturated": abs(raw0) > clip if clip > 0 else False,
        "ctrl_1_saturated": abs(raw1) > clip if clip > 0 else False,
    }


def send_control(client, command, routing, direct_roll_axis=False, direct_pitch_axis=False):
    """Send CTRL and persist whichever attitude axes this runner explicitly owns."""
    client.sendCTRL(command)
    pitch_index, roll_index = (0, 1) if routing == "legacy" else (1, 0)
    if direct_roll_axis:
        client.sendDREF(ROLL_YOKE_DREF, command[roll_index])
    if direct_pitch_axis:
        client.sendDREF(PITCH_YOKE_DREF, command[pitch_index])


def start_block_reasons(args, altitude_m, pitch_deg, roll_deg, measurements):
    """Return every reason an engaged baseline is not allowed to start."""
    reasons = []
    checks = (
        (abs(altitude_m - args.target_altitude_m) > args.altitude_tolerance_m, "altitude outside start envelope"),
        (abs(measurements["ias_kts"] - args.target_ias_kts) > args.ias_tolerance_kts, "IAS outside start envelope"),
        (abs(pitch_deg - args.pitch_sp) > args.max_start_pitch_error_deg, "pitch outside start envelope"),
        (abs(roll_deg - args.roll_sp) > args.max_start_roll_error_deg, "roll outside start envelope"),
        (max(abs(measurements[name]) for name in ("p_deg_s", "q_deg_s", "r_deg_s")) > args.max_start_rate_deg_s, "body rate outside start envelope"),
        (abs(measurements["throttle_engine_0"] - args.target_throttle) > args.throttle_tolerance, "engine 0 throttle outside start envelope"),
        (abs(measurements["throttle_engine_1"] - args.target_throttle) > args.throttle_tolerance, "engine 1 throttle outside start envelope"),
        (measurements["autopilot_on"] != 0.0, "autopilot is on"),
        (measurements["autopilot_servos_on"] != 0.0, "autopilot servos are on"),
        (measurements["autothrottle_on"] != 0.0, "autothrottle is on"),
        (measurements["sim_paused"] != 0.0, "simulator is paused"),
        (measurements["sim_speed"] <= 0.0, "simulation speed is zero"),
        (measurements["replay_mode"] != 0.0, "simulator is in replay mode"),
    )
    return [reason for failed, reason in checks if failed]


def smooth_recovery_pulse(elapsed_s, start_s, duration_s, amplitude):
    """Single half-sine pulse with zero endpoints; returns zero outside its window."""
    if duration_s <= 0 or elapsed_s < start_s or elapsed_s > start_s + duration_s:
        return 0.0
    phase = (elapsed_s - start_s) / duration_s
    return float(amplitude) * math.sin(math.pi * phase)


def recovery_abort_reason(args, pitch_deg, roll_deg, measurements):
    if abs(pitch_deg) > args.recovery_max_abs_pitch_deg:
        return "recovery pitch envelope exceeded"
    if abs(roll_deg) > args.recovery_max_abs_roll_deg:
        return "recovery roll envelope exceeded"
    if max(abs(measurements[name]) for name in ("p_deg_s", "q_deg_s", "r_deg_s")) > args.recovery_max_abs_rate_deg_s:
        return "recovery body-rate envelope exceeded"
    return ""


def tapered_multisine(elapsed_s, start_s, duration_s, ramp_s, amplitude, frequencies_hz, phases_rad):
    """Bounded multisine with raised-cosine start/end tapers."""
    local_t = elapsed_s - start_s
    if duration_s <= 0 or local_t < 0 or local_t > duration_s:
        return 0.0
    if not frequencies_hz or len(frequencies_hz) != len(phases_rad):
        raise ValueError("multisine frequencies and phases must be non-empty and have equal length")
    ramp = max(0.0, min(float(ramp_s), duration_s / 2.0))
    envelope = 1.0
    if ramp > 0 and local_t < ramp:
        envelope = 0.5 * (1.0 - math.cos(math.pi * local_t / ramp))
    elif ramp > 0 and local_t > duration_s - ramp:
        envelope = 0.5 * (1.0 - math.cos(math.pi * (duration_s - local_t) / ramp))
    harmonic_sum = sum(
        math.sin(2.0 * math.pi * frequency * local_t + phase)
        for frequency, phase in zip(frequencies_hz, phases_rad)
    )
    return float(amplitude) * envelope * harmonic_sum / len(frequencies_hz)


def comma_floats(text):
    return tuple(float(item.strip()) for item in text.split(",") if item.strip())


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--roll-sp", type=float, default=0.0)
    parser.add_argument("--pitch-sp", type=float, default=6.0)
    parser.add_argument("--K-roll", type=float, default=0.001)
    parser.add_argument("--K-pitch", type=float, default=0.001)
    parser.add_argument("--Ku-roll", type=float, default=33.0)
    parser.add_argument("--Ku-pitch", type=float, default=39.0)
    parser.add_argument("--tau-roll", type=float, default=0.03)
    parser.add_argument("--tau-pitch", type=float, default=0.03)
    parser.add_argument("--routing", choices=("legacy", "corrected"), default="legacy")
    parser.add_argument("--clip", type=float, default=1.0)
    parser.add_argument("--rudder", type=float, default=0.0)
    parser.add_argument("--throttle", type=float, default=-998.0)
    parser.add_argument("--target-altitude-m", type=float, default=5000.0)
    parser.add_argument("--altitude-tolerance-m", type=float, default=200.0)
    parser.add_argument("--target-ias-kts", type=float, default=100.0)
    parser.add_argument("--ias-tolerance-kts", type=float, default=5.0)
    parser.add_argument("--max-start-pitch-error-deg", type=float, default=3.0)
    parser.add_argument("--max-start-roll-error-deg", type=float, default=3.0)
    parser.add_argument("--max-start-rate-deg-s", type=float, default=3.0)
    parser.add_argument("--target-throttle", type=float, default=0.669723)
    parser.add_argument("--throttle-tolerance", type=float, default=0.02)
    parser.add_argument("--recovery-axis", choices=("none", "roll", "pitch"), default="none")
    parser.add_argument("--recovery-pulse-start-s", type=float, default=10.0)
    parser.add_argument("--recovery-pulse-duration-s", type=float, default=0.5)
    parser.add_argument("--recovery-pulse-amplitude", type=float, default=0.0)
    parser.add_argument("--recovery-max-abs-pitch-deg", type=float, default=10.0)
    parser.add_argument("--recovery-max-abs-roll-deg", type=float, default=10.0)
    parser.add_argument("--recovery-max-abs-rate-deg-s", type=float, default=20.0)
    parser.add_argument("--recovery-total-command-limit", type=float, default=0.5)
    parser.add_argument("--identification-axis", choices=("none", "roll", "pitch"), default="none")
    parser.add_argument("--identification-start-s", type=float, default=10.0)
    parser.add_argument("--identification-duration-s", type=float, default=40.0)
    parser.add_argument("--identification-ramp-s", type=float, default=2.0)
    parser.add_argument("--identification-amplitude", type=float, default=0.0)
    parser.add_argument("--identification-frequencies-hz", default="0.10,0.20,0.35,0.55,0.80")
    parser.add_argument("--identification-phases-rad", default="0.0,1.256637,2.513274,3.769911,5.026548")
    parser.add_argument("--rate-units", choices=("deg_s", "rad_s"), required=True)
    parser.add_argument("--engage", action="store_true", help="Actually send controls; omitted means observe-only.")
    parser.add_argument(
        "--override-roll-axis", action="store_true",
        help="While engaged, temporarily own only the roll joystick axis; restore it on exit.",
    )
    parser.add_argument(
        "--override-pitch-axis", action="store_true",
        help="While engaged, temporarily own only the pitch joystick axis; restore it on exit.",
    )
    parser.add_argument(
        "--trim-relative-controls", action="store_true",
        help="Capture start trim and apply unchanged control laws to input perturbations.",
    )
    parser.add_argument("--aircraft-config", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--fuel", required=True)
    parser.add_argument("--weather", required=True)
    parser.add_argument("--failures", required=True)
    parser.add_argument("--test-id", required=True)
    parser.add_argument("--out", required=True)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.hz <= 0 or args.duration <= 0:
        parser.error("--hz and --duration must be positive for a Stage-1 capture")
    if args.recovery_axis != "none" and args.identification_axis != "none":
        parser.error("recovery pulse and identification excitation are mutually exclusive")
    identification_frequencies = comma_floats(args.identification_frequencies_hz)
    identification_phases = comma_floats(args.identification_phases_rad)
    if args.identification_axis != "none" and len(identification_frequencies) != len(identification_phases):
        parser.error("identification frequencies and phases must have equal length")

    roll_ctrl = Backstepping.Backstepping(args.K_roll, args.Ku_roll, args.tau_roll)
    pitch_ctrl = Backstepping.Backstepping(args.K_pitch, args.Ku_pitch, args.tau_pitch)
    roll_ctrl.SetPoint = args.roll_sp
    pitch_ctrl.SetPoint = args.pitch_sp
    metadata = {
        "test_id": args.test_id, "aircraft_config": args.aircraft_config,
        "payload": args.payload, "fuel": args.fuel, "weather": args.weather,
        "failures": args.failures, "rate_units_declared": args.rate_units,
        "target_altitude_m": args.target_altitude_m,
        "altitude_tolerance_m": args.altitude_tolerance_m,
        "target_ias_kts": args.target_ias_kts,
        "ias_tolerance_kts": args.ias_tolerance_kts,
        "max_start_pitch_error_deg": args.max_start_pitch_error_deg,
        "max_start_roll_error_deg": args.max_start_roll_error_deg,
        "max_start_rate_deg_s": args.max_start_rate_deg_s,
        "target_throttle": args.target_throttle,
        "throttle_tolerance": args.throttle_tolerance,
        "recovery_axis": args.recovery_axis,
        "recovery_pulse_start_s": args.recovery_pulse_start_s,
        "recovery_pulse_duration_s": args.recovery_pulse_duration_s,
        "recovery_pulse_amplitude": args.recovery_pulse_amplitude,
        "identification_axis": args.identification_axis,
        "identification_start_s": args.identification_start_s,
        "identification_duration_s": args.identification_duration_s,
        "identification_ramp_s": args.identification_ramp_s,
        "identification_amplitude": args.identification_amplitude,
        "identification_frequencies_hz": args.identification_frequencies_hz,
        "identification_phases_rad": args.identification_phases_rad,
        "override_roll_axis_requested": args.override_roll_axis,
        "override_pitch_axis_requested": args.override_pitch_axis,
        "trim_relative_controls_requested": args.trim_relative_controls,
    }
    fields = [
        "sample", "t_s", "dt_s", "deadline_lateness_s", "lat_deg", "lon_deg", "alt_m",
        "pitch_deg", "roll_deg", "heading_deg", "gear", "p_body", "q_body", "r_body",
        "ias", "tas", "ctrl_before_0", "ctrl_before_1", "ctrl_before_2", "ctrl_before_3",
        "raw_roll_output", "raw_pitch_output", "sent_ctrl_0", "sent_ctrl_1", "sent_ctrl_2",
        "sent_ctrl_3", "ctrl_0_saturated", "ctrl_1_saturated", "roll_sp_deg", "pitch_sp_deg",
        "routing", "engaged", "start_allowed", "start_block_reason",
        "baseline_sent_ctrl_0", "baseline_sent_ctrl_1", "recovery_pulse",
        "recovery_active", "recovery_pulse_latched_off", "recovery_abort_reason",
        "identification_excitation", "identification_active",
        "identification_latched_off", "identification_abort_reason",
        *(field for field, _, _ in MEASUREMENTS),
        "dynamic_pressure_pa", *metadata.keys(),
    ]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    period = 1.0 / args.hz
    started = next_tick = previous_tick = time.monotonic()
    sample_number = 0
    mode = "ENGAGED" if args.engage else "OBSERVE-ONLY"
    start_gate_evaluated = False
    start_allowed = not args.engage
    start_reason = "observe-only"
    recovery_pulse_latched_off = False
    recovery_reason = ""
    identification_latched_off = False
    identification_reason = ""
    print(f"Connecting to X-Plane at {args.host}:{args.port}; mode={mode}; routing={args.routing}")
    print("Output:", out.resolve())

    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client, out.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        initial_roll_override = scalar(client.getDREF(ROLL_OVERRIDE_DREF))
        initial_yoke_roll = scalar(client.getDREF(ROLL_YOKE_DREF))
        initial_pitch_override = scalar(client.getDREF(PITCH_OVERRIDE_DREF))
        initial_yoke_pitch = scalar(client.getDREF(PITCH_YOKE_DREF))
        roll_override_active = False
        pitch_override_active = False
        captured_control_trim = None
        try:
            while True:
                now = time.monotonic()
                if now - started >= args.duration:
                    break
                if now < next_tick:
                    time.sleep(min(0.002, next_tick - now))
                    continue
                scheduled = next_tick
                next_tick += period
                posi = client.getPOSI()
                ctrl = client.getCTRL()
                if captured_control_trim is None and args.trim_relative_controls:
                    captured_control_trim = tuple(float(value) for value in ctrl)
                    print(
                        "Captured control trim: "
                        f"CTRL0={captured_control_trim[0]:+.6g}, "
                        f"CTRL1={captured_control_trim[1]:+.6g}"
                    )
                measurements = read_measurements(client)
                lat, lon, alt, pitch, roll, heading, gear = posi
                command_values = calculate_command(
                    roll_ctrl, pitch_ctrl, roll, pitch, ctrl, args.routing,
                    args.clip, args.rudder, args.throttle,
                    control_trim=captured_control_trim,
                )
                baseline_sent0 = command_values["sent_ctrl_0"]
                baseline_sent1 = command_values["sent_ctrl_1"]
                elapsed = now - started
                if args.recovery_axis != "none" and not recovery_pulse_latched_off:
                    recovery_reason = recovery_abort_reason(args, pitch, roll, measurements)
                    if recovery_reason:
                        recovery_pulse_latched_off = True
                pulse = 0.0 if recovery_pulse_latched_off else smooth_recovery_pulse(
                    elapsed, args.recovery_pulse_start_s,
                    args.recovery_pulse_duration_s, args.recovery_pulse_amplitude,
                )
                if args.identification_axis != "none" and not identification_latched_off:
                    identification_reason = recovery_abort_reason(args, pitch, roll, measurements)
                    if identification_reason:
                        identification_latched_off = True
                identification_excitation = 0.0 if identification_latched_off else tapered_multisine(
                    elapsed, args.identification_start_s, args.identification_duration_s,
                    args.identification_ramp_s, args.identification_amplitude,
                    identification_frequencies, identification_phases,
                )
                if args.recovery_axis == "roll":
                    command_values["sent_ctrl_1"] = baseline_sent1 + pulse
                elif args.recovery_axis == "pitch":
                    command_values["sent_ctrl_0"] = baseline_sent0 + pulse
                if args.identification_axis == "roll":
                    command_values["sent_ctrl_1"] += identification_excitation
                elif args.identification_axis == "pitch":
                    command_values["sent_ctrl_0"] += identification_excitation
                if args.recovery_axis != "none" or args.identification_axis != "none":
                    limit = abs(args.recovery_total_command_limit)
                    command_values["sent_ctrl_0"] = clamp(command_values["sent_ctrl_0"], limit)
                    command_values["sent_ctrl_1"] = clamp(command_values["sent_ctrl_1"], limit)
                command = [command_values[f"sent_ctrl_{index}"] for index in range(4)]
                if args.engage and not start_gate_evaluated:
                    reasons = start_block_reasons(args, alt, pitch, roll, measurements)
                    start_allowed = not reasons
                    start_reason = "; ".join(reasons) if reasons else ""
                    start_gate_evaluated = True
                    print("Start gate:", "PASS" if start_allowed else f"BLOCKED: {start_reason}")
                engaged = args.engage and start_allowed
                if engaged:
                    if args.override_roll_axis and not roll_override_active:
                        client.sendDREF(ROLL_OVERRIDE_DREF, 1.0)
                        roll_override_active = True
                        print("Roll-axis ownership: ACTIVE")
                    if args.override_pitch_axis and not pitch_override_active:
                        client.sendDREF(PITCH_OVERRIDE_DREF, 1.0)
                        pitch_override_active = True
                        print("Pitch-axis ownership: ACTIVE")
                    send_control(
                        client, command, args.routing,
                        direct_roll_axis=args.override_roll_axis,
                        direct_pitch_axis=args.override_pitch_axis,
                    )
                writer.writerow({
                    "sample": sample_number, "t_s": now - started, "dt_s": now - previous_tick,
                    "deadline_lateness_s": now - scheduled, "lat_deg": lat, "lon_deg": lon,
                    "alt_m": alt, "pitch_deg": pitch, "roll_deg": roll, "heading_deg": heading,
                    "gear": gear, "p_body": measurements["p_deg_s"],
                    "q_body": measurements["q_deg_s"], "r_body": measurements["r_deg_s"],
                    "ias": measurements["ias_kts"], "tas": measurements["tas_m_s"],
                    "ctrl_before_0": ctrl[0], "ctrl_before_1": ctrl[1],
                    "ctrl_before_2": ctrl[2], "ctrl_before_3": ctrl[3],
                    "roll_sp_deg": args.roll_sp, "pitch_sp_deg": args.pitch_sp,
                    "routing": args.routing, "engaged": engaged,
                    "start_allowed": start_allowed, "start_block_reason": start_reason,
                    "baseline_sent_ctrl_0": baseline_sent0,
                    "baseline_sent_ctrl_1": baseline_sent1,
                    "recovery_pulse": pulse,
                    "recovery_active": pulse != 0.0,
                    "recovery_pulse_latched_off": recovery_pulse_latched_off,
                    "recovery_abort_reason": recovery_reason,
                    "identification_excitation": identification_excitation,
                    "identification_active": identification_excitation != 0.0,
                    "identification_latched_off": identification_latched_off,
                    "identification_abort_reason": identification_reason,
                    **command_values, **measurements, **metadata,
                })
                previous_tick = now
                sample_number += 1
                if args.engage and not start_allowed:
                    print("No controls sent; baseline capture stopped because the start gate was blocked.")
                    break
        except KeyboardInterrupt:
            print("\nCtrl+C received; closing log cleanly.")
        finally:
            if roll_override_active:
                client.sendDREF(ROLL_YOKE_DREF, initial_yoke_roll)
                client.sendDREF(ROLL_OVERRIDE_DREF, initial_roll_override)
                print(
                    "Roll-axis ownership: RESTORED "
                    f"(override={initial_roll_override:g}, yoke={initial_yoke_roll:+.6g})"
                )
            if pitch_override_active:
                client.sendDREF(PITCH_YOKE_DREF, initial_yoke_pitch)
                client.sendDREF(PITCH_OVERRIDE_DREF, initial_pitch_override)
                print(
                    "Pitch-axis ownership: RESTORED "
                    f"(override={initial_pitch_override:g}, yoke={initial_yoke_pitch:+.6g})"
                )
    print(f"Saved {sample_number} samples:", out.resolve())


if __name__ == "__main__":
    main()
