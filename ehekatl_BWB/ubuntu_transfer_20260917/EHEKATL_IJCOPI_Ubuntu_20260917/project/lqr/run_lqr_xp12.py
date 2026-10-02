#!/usr/bin/env python3
"""
Run the EHEKATL BWB LQR controller against X-Plane 12 through XPlaneConnect.

This runner is retained for future validation after identification. It uses the
same patched xpc.py and supports trim-biased control.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import argparse
import csv
import sys
import time
from pathlib import Path

from LQR import (
    DampedAttitudeConfig,
    DampedAttitudeController,
    EHEKATLLQR,
    LQRConfig,
    LQRCommand,
    RAD_TO_DEG,
    StateSample,
    deg2rad,
    wrapped_angle_error_deg,
)


BRIDGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))


def first_float(value) -> float:
    if isinstance(value, (list, tuple)):
        if not value:
            return 0.0
        return first_float(value[0])
    return float(value)


def angle_delta_deg(new_deg: float, old_deg: float) -> float:
    return (new_deg - old_deg + 180.0) % 360.0 - 180.0


def read_drefs(client, names: list[str]) -> list[float]:
    try:
        values = client.getDREFs(names)
        return [first_float(v) for v in values]
    except Exception:
        values = []
        for name in names:
            try:
                if hasattr(client, "getDREF"):
                    values.append(first_float(client.getDREF(name)))
                else:
                    values.append(first_float(client.getDREFs([name])[0]))
            except Exception:
                raise
        return values


class StateReader:
    def __init__(self, mode: str, rate_units: str, u_trim: float, w_trim: float, v_trim: float):
        self.mode = mode
        self.rate_units = rate_units
        self.u_trim = u_trim
        self.w_trim = w_trim
        self.v_trim = v_trim
        self.previous: tuple[float, float, float, float] | None = None
        self.last_rate_source = "not_read"
        self.last_velocity_source = "attitude_only"

    def read_rates(self, client, now: float, pitch: float, roll: float, heading: float) -> tuple[float, float, float]:
        try:
            roll_rate, pitch_rate, yaw_rate = read_drefs(
                client,
                [
                    "sim/flightmodel/position/P",
                    "sim/flightmodel/position/Q",
                    "sim/flightmodel/position/R",
                ],
            )
            self.last_rate_source = f"datarefs:P_Q_R_{self.rate_units}"
            if self.rate_units == "rad_s":
                roll_rate *= RAD_TO_DEG
                pitch_rate *= RAD_TO_DEG
                yaw_rate *= RAD_TO_DEG
            return pitch_rate, roll_rate, yaw_rate
        except Exception:
            if self.previous is None:
                self.previous = (now, pitch, roll, heading)
                self.last_rate_source = "finite_difference_initial_zero"
                return 0.0, 0.0, 0.0
            old_t, old_pitch, old_roll, old_heading = self.previous
            dt = max(now - old_t, 1e-6)
            self.previous = (now, pitch, roll, heading)
            self.last_rate_source = "finite_difference"
            return (
                angle_delta_deg(pitch, old_pitch) / dt,
                angle_delta_deg(roll, old_roll) / dt,
                angle_delta_deg(heading, old_heading) / dt,
            )

    def read_velocities(self, client) -> tuple[float, float, float]:
        if self.mode != "full":
            self.last_velocity_source = "attitude_only"
            return 0.0, 0.0, 0.0
        try:
            local_vx, local_vy, local_vz = read_drefs(
                client,
                [
                    "sim/flightmodel/position/local_vx",
                    "sim/flightmodel/position/local_vy",
                    "sim/flightmodel/position/local_vz",
                ],
            )
            self.last_velocity_source = "datarefs:local_vx_local_vy_local_vz"
            return local_vx - self.u_trim, local_vz - self.w_trim, local_vy - self.v_trim
        except Exception:
            self.last_velocity_source = "unavailable_zero_fallback"
            return 0.0, 0.0, 0.0

    def sample(self, client, now: float) -> tuple[StateSample, dict[str, float | str]]:
        posi = client.getPOSI()
        lat = float(posi[0])
        lon = float(posi[1])
        altitude = float(posi[2])
        pitch = float(posi[3])
        roll = float(posi[4])
        heading = float(posi[5])

        pitch_rate, roll_rate, yaw_rate = self.read_rates(client, now, pitch, roll, heading)
        u, w, v = self.read_velocities(client)
        sample = StateSample(
            pitch_deg=pitch,
            roll_deg=roll,
            heading_deg=heading,
            pitch_rate_deg_s=pitch_rate,
            roll_rate_deg_s=roll_rate,
            yaw_rate_deg_s=yaw_rate,
            u_perturb_m_s=u,
            w_perturb_m_s=w,
            v_perturb_m_s=v,
        )
        pos = {
            "latitude_deg": lat,
            "longitude_deg": lon,
            "altitude_m": altitude,
            "rate_source": self.last_rate_source,
            "velocity_source": self.last_velocity_source,
        }
        return sample, pos


def import_xpc():
    try:
        import xpc
    except ImportError as exc:
        raise RuntimeError(f"Could not import xpc.py. Expected it in {BRIDGE_DIR}") from exc
    return xpc


def connect_xplane(xpc_module, host: str, port: int):
    try:
        return xpc_module.XPlaneConnect(xpHost=host, xpPort=port)
    except TypeError:
        return xpc_module.XPlaneConnect(host, port)


def read_current_ctrl(client) -> tuple[float, float, float, float]:
    ctrl = client.getCTRL()
    return float(ctrl[0]), float(ctrl[1]), float(ctrl[2]), float(ctrl[3])


def trim_bias_from_ctrl(current_ctrl: tuple[float, float, float, float], routing: str) -> tuple[float, float]:
    if routing == "corrected":
        return current_ctrl[0], current_ctrl[1]
    if routing == "legacy":
        return current_ctrl[1], current_ctrl[0]
    raise ValueError(f"Unsupported routing: {routing}")


def command_sticks(
    command,
    axis: str,
    aileron_bias: float,
    elevator_bias: float,
    trim_mode: str,
) -> tuple[float, float]:
    if trim_mode == "incremental":
        aileron_stick = aileron_bias if axis == "pitch" else aileron_bias + command.aileron_stick
        elevator_stick = elevator_bias if axis == "roll" else elevator_bias + command.elevator_stick
    elif trim_mode == "absolute":
        aileron_stick = aileron_bias if axis == "pitch" else command.aileron_stick
        elevator_stick = elevator_bias if axis == "roll" else command.elevator_stick
    else:
        raise ValueError(f"Unsupported trim mode: {trim_mode}")
    return clamp_stick(aileron_stick), clamp_stick(elevator_stick)


def clamp_stick(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def slew_limit(value: float, previous: float, max_delta: float) -> float:
    if max_delta <= 0.0:
        return clamp_stick(value)
    return clamp_stick(max(previous - max_delta, min(previous + max_delta, value)))


def control_vector_from_sticks(
    aileron_stick: float,
    elevator_stick: float,
    routing: str,
    rudder: float,
    throttle: float,
) -> list[float]:
    rudder = clamp_stick(rudder)

    if routing == "corrected":
        return [aileron_stick, elevator_stick, rudder, throttle]
    if routing == "legacy":
        return [elevator_stick, aileron_stick, rudder, throttle]
    raise ValueError(f"Unsupported routing: {routing}")


def control_vector(command, routing: str, axis: str, rudder: float, throttle: float) -> list[float]:
    aileron_stick, elevator_stick = command_sticks(
        command,
        axis=axis,
        aileron_bias=0.0,
        elevator_bias=0.0,
        trim_mode="absolute",
    )
    return control_vector_from_sticks(aileron_stick, elevator_stick, routing, rudder, throttle)


def excitation_value(elapsed: float, amplitude: float, period: float, kind: str) -> float:
    if amplitude <= 0.0 or period <= 0.0:
        return 0.0
    index = int(elapsed / period)
    if kind == "doublet":
        sequence = (1.0, -1.0, 0.0, 0.0)
    elif kind == "prbs":
        sequence = (1.0, -1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 0.0, 1.0, 0.0, -1.0)
    else:
        raise ValueError(f"Unsupported excitation kind: {kind}")
    return amplitude * sequence[index % len(sequence)]


def excitation_command(elapsed: float, args: argparse.Namespace, sample: StateSample) -> LQRCommand:
    elevator_stick = 0.0
    aileron_stick = 0.0
    if args.axis in {"both", "pitch"}:
        elevator_stick = excitation_value(elapsed, args.excite_amplitude, args.excite_period, args.excite_kind)
    if args.axis in {"both", "roll"}:
        aileron_stick = excitation_value(elapsed, args.excite_amplitude, args.excite_period, args.excite_kind)
    return LQRCommand(
        delta_e_raw_rad=elevator_stick * deg2rad(25.0),
        delta_a_raw_rad=-aileron_stick * deg2rad(25.0),
        delta_e_limited_rad=elevator_stick * deg2rad(25.0),
        delta_a_limited_rad=-aileron_stick * deg2rad(25.0),
        elevator_stick=elevator_stick,
        aileron_stick=aileron_stick,
        x_lon=(
            sample.u_perturb_m_s,
            sample.w_perturb_m_s,
            deg2rad(sample.pitch_rate_deg_s),
            deg2rad(wrapped_angle_error_deg(sample.pitch_deg, args.pitch_sp)),
        ),
        x_lat=(
            sample.v_perturb_m_s,
            deg2rad(sample.roll_rate_deg_s),
            deg2rad(sample.yaw_rate_deg_s),
            deg2rad(wrapped_angle_error_deg(sample.roll_deg, args.roll_sp)),
        ),
    )


def start_attitude_allowed(
    axis: str,
    pitch_error: float,
    roll_error: float,
    max_pitch_error: float,
    max_roll_error: float,
) -> bool:
    check_pitch = axis in {"both", "pitch"} and max_pitch_error > 0.0
    check_roll = axis in {"both", "roll"} and max_roll_error > 0.0
    return not (
        (check_pitch and pitch_error > max_pitch_error)
        or (check_roll and roll_error > max_roll_error)
    )


def start_attitude_block_reason(
    axis: str,
    sample: StateSample,
    pitch_sp: float,
    roll_sp: float,
    max_pitch_error: float,
    max_roll_error: float,
) -> str:
    pitch_error = abs(wrapped_angle_error_deg(sample.pitch_deg, pitch_sp))
    roll_error = abs(wrapped_angle_error_deg(sample.roll_deg, roll_sp))
    if start_attitude_allowed(axis, pitch_error, roll_error, max_pitch_error, max_roll_error):
        return ""
    return (
        "waiting for manual trim: start attitude outside limits "
        f"(pitch_error={pitch_error:.1f} deg, roll_error={roll_error:.1f} deg)"
    )


def safety_stop_reason(
    sample: StateSample,
    max_abs_pitch: float,
    max_abs_roll: float,
    max_abs_rate: float,
) -> str:
    if max_abs_pitch > 0.0 and abs(sample.pitch_deg) > max_abs_pitch:
        return f"abs pitch {abs(sample.pitch_deg):.1f} deg exceeds {max_abs_pitch:.1f}"
    if max_abs_roll > 0.0 and abs(sample.roll_deg) > max_abs_roll:
        return f"abs roll {abs(sample.roll_deg):.1f} deg exceeds {max_abs_roll:.1f}"
    if max_abs_rate > 0.0:
        rate = max(
            abs(sample.pitch_rate_deg_s),
            abs(sample.roll_rate_deg_s),
            abs(sample.yaw_rate_deg_s),
        )
        if rate > max_abs_rate:
            return f"body rate {rate:.1f} deg/s exceeds {max_abs_rate:.1f}"
    return ""


def divergence_stop_reason(
    sample: StateSample,
    axis: str,
    pitch_sp: float,
    roll_sp: float,
    min_error: float,
    min_rate: float,
) -> str:
    if min_error <= 0.0 or min_rate <= 0.0:
        return ""

    if axis in {"both", "pitch"}:
        pitch_error = wrapped_angle_error_deg(sample.pitch_deg, pitch_sp)
        if abs(pitch_error) >= min_error and pitch_error * sample.pitch_rate_deg_s > min_error * min_rate:
            return (
                "pitch error diverging "
                f"(error={pitch_error:+.1f} deg, rate={sample.pitch_rate_deg_s:+.1f} deg/s)"
            )

    if axis in {"both", "roll"}:
        roll_error = wrapped_angle_error_deg(sample.roll_deg, roll_sp)
        if abs(roll_error) >= min_error and roll_error * sample.roll_rate_deg_s > min_error * min_rate:
            return (
                "roll error diverging "
                f"(error={roll_error:+.1f} deg, rate={sample.roll_rate_deg_s:+.1f} deg/s)"
            )

    return ""


def default_out_path(mode: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return PROJECT_ROOT / "logs" / f"lqr_{mode}_xp12_{stamp}.csv"


def make_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "elapsed_s",
        "latitude_deg",
        "longitude_deg",
        "altitude_m",
        "pitch_deg",
        "roll_deg",
        "heading_deg",
        "pitch_rate_deg_s",
        "roll_rate_deg_s",
        "yaw_rate_deg_s",
        "u_perturb_m_s",
        "w_perturb_m_s",
        "v_perturb_m_s",
        "delta_e_raw_deg",
        "delta_a_raw_deg",
        "delta_e_limited_deg",
        "delta_a_limited_deg",
        "elevator_stick",
        "aileron_stick",
        "actual_elevator_stick",
        "actual_aileron_stick",
        "rudder_cmd",
        "throttle_cmd",
        "current_ctrl_0",
        "current_ctrl_1",
        "current_ctrl_2",
        "current_ctrl_3",
        "aileron_bias",
        "elevator_bias",
        "aileron_delta",
        "elevator_delta",
        "actual_aileron_delta",
        "actual_elevator_delta",
        "ctrl_0",
        "ctrl_1",
        "ctrl_2",
        "ctrl_3",
        "axis",
        "controller",
        "trim_source",
        "trim_mode",
        "engaged",
        "stop_reason",
        "elevator_sign",
        "aileron_sign",
        "x_lon_u",
        "x_lon_w",
        "x_lon_q",
        "x_lon_theta",
        "x_lat_v",
        "x_lat_p",
        "x_lat_r",
        "x_lat_phi",
        "rate_source",
        "velocity_source",
    ]
    f = open(path, "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    return f, writer


def run(args: argparse.Namespace) -> None:
    if args.controller == "lqr":
        config = LQRConfig(
            pitch_sp_deg=args.pitch_sp,
            roll_sp_deg=args.roll_sp,
            actuator_limit_deg=args.actuator_limit_deg,
            clip=args.clip,
            mode=args.mode,
            elevator_stick_sign=args.elevator_sign,
            aileron_stick_sign=args.aileron_sign,
        )
        controller = EHEKATLLQR(config)
    elif args.controller == "damped":
        config = DampedAttitudeConfig(
            pitch_sp_deg=args.pitch_sp,
            roll_sp_deg=args.roll_sp,
            pitch_kp=args.pitch_kp,
            pitch_kd=args.pitch_kd,
            roll_kp=args.roll_kp,
            roll_kd=args.roll_kd,
            clip=args.clip,
            elevator_stick_sign=args.elevator_sign,
            aileron_stick_sign=-args.aileron_sign,
        )
        controller = DampedAttitudeController(config)
    elif args.controller == "excite":
        controller = None
    else:
        raise ValueError(f"Unsupported controller: {args.controller}")
    reader = StateReader(
        mode=args.mode,
        rate_units=args.rate_units,
        u_trim=args.u_trim,
        w_trim=args.w_trim,
        v_trim=args.v_trim,
    )
    xpc_module = import_xpc()
    out_path = Path(args.out) if args.out else default_out_path(args.mode)

    duration = None if args.duration <= 0.0 else args.duration
    period = 1.0 / args.hz
    start = time.monotonic()
    next_tick = start
    next_print = start
    trim_initialized = False
    was_waiting = False
    aileron_bias = args.aileron_trim
    elevator_bias = args.elevator_trim
    previous_aileron_stick: float | None = None
    previous_elevator_stick: float | None = None
    previous_command_time: float | None = None

    print(f"Connecting to X-Plane at {args.host}:{args.port}")
    print(
        f"controller={args.controller} mode={args.mode} axis={args.axis} "
        f"routing={args.routing} rate_units={args.rate_units} "
        f"clip={args.clip} elevator_sign={args.elevator_sign:+.0f} "
        f"aileron_sign={args.aileron_sign:+.0f} throttle={args.throttle} "
        f"trim_source={args.trim_source} trim_mode={args.trim_mode} "
        f"stick_slew_rate={args.stick_slew_rate}"
    )
    print(f"Logging to {out_path}")

    f, writer = make_writer(out_path)
    try:
        with connect_xplane(xpc_module, args.host, args.port) as client:
            while True:
                now = time.monotonic()
                elapsed = now - start
                if duration is not None and elapsed >= duration:
                    break
                if now < next_tick:
                    time.sleep(min(next_tick - now, 0.002))
                    continue
                next_tick += period

                sample, pos = reader.sample(client, now)
                current_ctrl = read_current_ctrl(client)
                if not trim_initialized:
                    trim_initialized = True
                    if args.trim_source == "current":
                        aileron_bias, elevator_bias = trim_bias_from_ctrl(current_ctrl, args.routing)
                    elif args.trim_source == "zero":
                        aileron_bias = 0.0
                        elevator_bias = 0.0
                    elif args.trim_source == "manual":
                        aileron_bias = args.aileron_trim
                        elevator_bias = args.elevator_trim
                    else:
                        raise ValueError(f"Unsupported trim source: {args.trim_source}")
                    print(
                        f"CTRL trim bias: aileron={aileron_bias:+.4f} "
                        f"elevator={elevator_bias:+.4f} source={args.trim_source}"
                    )
                if args.controller == "excite":
                    command = excitation_command(elapsed, args, sample)
                else:
                    command = controller.command(sample)
                aileron_stick, elevator_stick = command_sticks(
                    command,
                    axis=args.axis,
                    aileron_bias=aileron_bias,
                    elevator_bias=elevator_bias,
                    trim_mode=args.trim_mode,
                )
                if previous_command_time is None:
                    previous_aileron_stick = aileron_stick
                    previous_elevator_stick = elevator_stick
                    previous_command_time = now
                else:
                    dt = max(now - previous_command_time, 1e-6)
                    max_delta = args.stick_slew_rate * dt
                    aileron_stick = slew_limit(aileron_stick, previous_aileron_stick, max_delta)
                    elevator_stick = slew_limit(elevator_stick, previous_elevator_stick, max_delta)
                    previous_aileron_stick = aileron_stick
                    previous_elevator_stick = elevator_stick
                    previous_command_time = now
                ctrl = control_vector_from_sticks(
                    aileron_stick,
                    elevator_stick,
                    args.routing,
                    args.rudder,
                    args.throttle,
                )
                stop_reason = start_attitude_block_reason(
                    args.axis,
                    sample,
                    args.pitch_sp,
                    args.roll_sp,
                    args.max_start_pitch_error,
                    args.max_start_roll_error,
                )
                if not stop_reason:
                    stop_reason = divergence_stop_reason(
                        sample,
                        args.axis,
                        args.pitch_sp,
                        args.roll_sp,
                        args.divergence_min_error,
                        args.divergence_min_rate,
                    )
                    if not stop_reason:
                        stop_reason = safety_stop_reason(
                            sample,
                            args.max_abs_pitch,
                            args.max_abs_roll,
                            args.max_abs_rate,
                        )

                engaged = not stop_reason
                waiting = not engaged
                if waiting:
                    ctrl = control_vector_from_sticks(
                        aileron_bias,
                        elevator_bias,
                        args.routing,
                        args.rudder,
                        -998.0,
                    )
                    if not was_waiting:
                        print(f"Controller waiting: {stop_reason}.")
                        if not args.dry_run:
                            client.sendCTRL(ctrl)
                    previous_aileron_stick = aileron_bias
                    previous_elevator_stick = elevator_bias
                    previous_command_time = now
                elif was_waiting:
                    print("Controller re-engaged.")

                if engaged and not args.dry_run:
                    client.sendCTRL(ctrl)
                was_waiting = waiting

                row = {
                    "elapsed_s": elapsed,
                    **pos,
                    **asdict(sample),
                    "delta_e_raw_deg": command.delta_e_raw_deg,
                    "delta_a_raw_deg": command.delta_a_raw_deg,
                    "delta_e_limited_deg": command.delta_e_limited_deg,
                    "delta_a_limited_deg": command.delta_a_limited_deg,
                    "elevator_stick": command.elevator_stick,
                    "aileron_stick": command.aileron_stick,
                    "actual_elevator_stick": elevator_stick,
                    "actual_aileron_stick": aileron_stick,
                    "rudder_cmd": args.rudder,
                    "throttle_cmd": args.throttle,
                    "current_ctrl_0": current_ctrl[0],
                    "current_ctrl_1": current_ctrl[1],
                    "current_ctrl_2": current_ctrl[2],
                    "current_ctrl_3": current_ctrl[3],
                    "aileron_bias": aileron_bias,
                    "elevator_bias": elevator_bias,
                    "aileron_delta": command.aileron_stick,
                    "elevator_delta": command.elevator_stick,
                    "actual_aileron_delta": aileron_stick - aileron_bias,
                    "actual_elevator_delta": elevator_stick - elevator_bias,
                    "ctrl_0": ctrl[0],
                    "ctrl_1": ctrl[1],
                    "ctrl_2": ctrl[2],
                    "ctrl_3": ctrl[3],
                    "axis": args.axis,
                    "controller": args.controller,
                    "trim_source": args.trim_source,
                    "trim_mode": args.trim_mode,
                    "engaged": engaged,
                    "stop_reason": stop_reason,
                    "elevator_sign": args.elevator_sign,
                    "aileron_sign": args.aileron_sign,
                    "x_lon_u": command.x_lon[0],
                    "x_lon_w": command.x_lon[1],
                    "x_lon_q": command.x_lon[2],
                    "x_lon_theta": command.x_lon[3],
                    "x_lat_v": command.x_lat[0],
                    "x_lat_p": command.x_lat[1],
                    "x_lat_r": command.x_lat[2],
                    "x_lat_phi": command.x_lat[3],
                }
                writer.writerow(row)

                if now >= next_print:
                    next_print = now + 1.0
                    state = "ENGAGED" if engaged else "WAIT"
                    print(
                        f"t={elapsed:7.2f}s {state:7s} pitch={sample.pitch_deg:7.3f} roll={sample.roll_deg:7.3f} "
                        f"ele={elevator_stick:7.3f} ail={aileron_stick:7.3f} "
                        f"rates={reader.last_rate_source} vel={reader.last_velocity_source}"
                    )
    except KeyboardInterrupt:
        print("\nCtrl+C received. Closing log cleanly.")
    finally:
        f.flush()
        f.close()
        print(f"Saved CSV log: {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EHEKATL BWB LQR runner for X-Plane 12.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--duration", type=float, default=0.0, help="Seconds. Use 0 for no time limit.")
    parser.add_argument("--hz", type=float, default=20.0)
    parser.add_argument("--mode", choices=("attitude", "full"), default="attitude")
    parser.add_argument(
        "--controller",
        choices=("damped", "lqr", "excite"),
        default="damped",
        help="Use damped attitude hold, fixed-gain LQR, or open-loop identification excitation.",
    )
    parser.add_argument(
        "--axis",
        choices=("both", "pitch", "roll"),
        default="both",
        help="Control both axes, pitch/elevator only, or roll/aileron only.",
    )
    parser.add_argument(
        "--rate-units",
        choices=("rad_s", "deg_s"),
        default="deg_s",
        help="Units returned by sim/flightmodel/position/P,Q,R. They are converted to deg/s for logging.",
    )
    parser.add_argument("--routing", choices=("legacy", "corrected"), default="legacy")
    parser.add_argument(
        "--trim-source",
        choices=("current", "zero", "manual"),
        default="current",
        help="Stick bias source. 'current' mirrors the Backstepping runner by starting from getCTRL().",
    )
    parser.add_argument(
        "--trim-mode",
        choices=("incremental", "absolute"),
        default="incremental",
        help="Use controller output as a correction around trim, or as an absolute stick command.",
    )
    parser.add_argument("--pitch-sp", type=float, default=2.0)
    parser.add_argument("--roll-sp", type=float, default=0.0)
    parser.add_argument("--clip", type=float, default=0.03, help="Stick clip in [0,1]. Use 0 for no extra LQR clip.")
    parser.add_argument("--actuator-limit-deg", type=float, default=25.0)
    parser.add_argument("--pitch-kp", type=float, default=0.004)
    parser.add_argument("--pitch-kd", type=float, default=0.001)
    parser.add_argument("--roll-kp", type=float, default=0.004)
    parser.add_argument("--roll-kd", type=float, default=0.001)
    parser.add_argument(
        "--excite-amplitude",
        type=float,
        default=0.015,
        help="Open-loop identification stick amplitude for --controller excite.",
    )
    parser.add_argument(
        "--excite-period",
        type=float,
        default=1.5,
        help="Seconds per identification excitation step for --controller excite.",
    )
    parser.add_argument(
        "--excite-kind",
        choices=("prbs", "doublet"),
        default="prbs",
        help="Identification excitation sequence for --controller excite.",
    )
    parser.add_argument(
        "--stick-slew-rate",
        type=float,
        default=0.08,
        help="Maximum stick change per second. Use 0 to disable actuator command slew limiting.",
    )
    parser.add_argument(
        "--max-start-pitch-error",
        type=float,
        default=8.0,
        help="Wait to engage while controlled pitch error exceeds this many degrees. Use 0 to disable.",
    )
    parser.add_argument(
        "--max-start-roll-error",
        type=float,
        default=8.0,
        help="Wait to engage while controlled roll error exceeds this many degrees. Use 0 to disable.",
    )
    parser.add_argument(
        "--max-abs-pitch",
        type=float,
        default=0.0,
        help="Pause controller corrections if absolute pitch exceeds this many degrees. Use 0 to disable.",
    )
    parser.add_argument(
        "--max-abs-roll",
        type=float,
        default=0.0,
        help="Pause controller corrections if absolute roll exceeds this many degrees. Use 0 to disable.",
    )
    parser.add_argument(
        "--max-abs-rate",
        type=float,
        default=0.0,
        help="Pause controller corrections if any body rate exceeds this many deg/s. Use 0 to disable.",
    )
    parser.add_argument(
        "--divergence-min-error",
        type=float,
        default=2.0,
        help="Pause when a controlled-axis error above this value is still growing. Use 0 to disable.",
    )
    parser.add_argument(
        "--divergence-min-rate",
        type=float,
        default=10.0,
        help="Minimum same-sign controlled-axis rate for the divergence stop. Use 0 to disable.",
    )
    parser.add_argument(
        "--elevator-sign",
        type=float,
        choices=(-1.0, 1.0),
        default=1.0,
        help="Map LQR elevator deflection to X-Plane elevator stick.",
    )
    parser.add_argument(
        "--aileron-sign",
        type=float,
        choices=(-1.0, 1.0),
        default=-1.0,
        help="Map LQR aileron deflection to X-Plane aileron stick.",
    )
    parser.add_argument("--throttle", type=float, default=-998.0)
    parser.add_argument("--rudder", type=float, default=0.0)
    parser.add_argument("--aileron-trim", type=float, default=0.0)
    parser.add_argument("--elevator-trim", type=float, default=0.0)
    parser.add_argument("--u-trim", type=float, default=0.0)
    parser.add_argument("--w-trim", type=float, default=0.0)
    parser.add_argument("--v-trim", type=float, default=0.0)
    parser.add_argument("--out", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Log commands without sending CTRL.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
