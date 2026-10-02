#!/usr/bin/env python3
"""
Run the EHEKATL BWB LQR controller against X-Plane 12 through XPlaneConnect.

This runner reuses the patched xpc.py from the working Backstepping bridge and
does not modify any Backstepping/PID files.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import argparse
import csv
import sys
import time

from LQR import EHEKATLLQR, LQRConfig, StateSample


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKSTEPPING_BRIDGE = PROJECT_ROOT / "backstepping" / "ehekatl_xplane12_backstepping_bridge"
if str(BACKSTEPPING_BRIDGE) not in sys.path:
    sys.path.insert(0, str(BACKSTEPPING_BRIDGE))


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
    def __init__(self, mode: str, u_trim: float, w_trim: float, v_trim: float):
        self.mode = mode
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
            self.last_rate_source = "datarefs:P_Q_R"
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
        raise RuntimeError(
            f"Could not import xpc.py. Expected it in the working bridge: {BACKSTEPPING_BRIDGE}"
        ) from exc
    return xpc


def connect_xplane(xpc_module, host: str, port: int):
    try:
        return xpc_module.XPlaneConnect(xpHost=host, xpPort=port)
    except TypeError:
        return xpc_module.XPlaneConnect(host, port)


def control_vector(command, routing: str, rudder: float, throttle: float) -> list[float]:
    if routing == "corrected":
        return [command.aileron_stick, command.elevator_stick, rudder, throttle]
    if routing == "legacy":
        return [command.elevator_stick, command.aileron_stick, rudder, throttle]
    raise ValueError(f"Unsupported routing: {routing}")


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
        "rudder_cmd",
        "throttle_cmd",
        "ctrl_0",
        "ctrl_1",
        "ctrl_2",
        "ctrl_3",
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
    config = LQRConfig(
        pitch_sp_deg=args.pitch_sp,
        roll_sp_deg=args.roll_sp,
        actuator_limit_deg=args.actuator_limit_deg,
        clip=args.clip,
        mode=args.mode,
    )
    controller = EHEKATLLQR(config)
    reader = StateReader(mode=args.mode, u_trim=args.u_trim, w_trim=args.w_trim, v_trim=args.v_trim)
    xpc_module = import_xpc()
    out_path = Path(args.out) if args.out else default_out_path(args.mode)

    duration = None if args.duration <= 0.0 else args.duration
    period = 1.0 / args.hz
    start = time.monotonic()
    next_tick = start
    next_print = start

    print(f"Connecting to X-Plane at {args.host}:{args.port}")
    print(f"mode={args.mode} routing={args.routing} clip={args.clip} throttle={args.throttle}")
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
                command = controller.command(sample)
                ctrl = control_vector(command, args.routing, args.rudder, args.throttle)
                if not args.dry_run:
                    client.sendCTRL(ctrl)

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
                    "rudder_cmd": args.rudder,
                    "throttle_cmd": args.throttle,
                    "ctrl_0": ctrl[0],
                    "ctrl_1": ctrl[1],
                    "ctrl_2": ctrl[2],
                    "ctrl_3": ctrl[3],
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
                    print(
                        f"t={elapsed:7.2f}s pitch={sample.pitch_deg:7.3f} roll={sample.roll_deg:7.3f} "
                        f"ele={command.elevator_stick:7.3f} ail={command.aileron_stick:7.3f} "
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
    parser.add_argument("--routing", choices=("legacy", "corrected"), default="corrected")
    parser.add_argument("--pitch-sp", type=float, default=2.0)
    parser.add_argument("--roll-sp", type=float, default=0.0)
    parser.add_argument("--clip", type=float, default=0.25, help="Extra stick clip in [0,1]. Use 0 for no extra clip.")
    parser.add_argument("--actuator-limit-deg", type=float, default=25.0)
    parser.add_argument("--throttle", type=float, default=-998.0)
    parser.add_argument("--rudder", type=float, default=0.0)
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
