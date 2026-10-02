#!/usr/bin/env python3
"""Run the original EHEKATL PID attitude controller against X-Plane 12."""

import argparse
import csv
import time
from pathlib import Path

import PID
import xpc


def clamp(value, limit):
    if limit is None or limit <= 0:
        return float(value)
    return max(-limit, min(limit, float(value)))


def main():
    parser = argparse.ArgumentParser(description="EHEKATL BWB XP12 PID controller.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--duration", type=float, default=60.0, help="Seconds; 0 runs until Ctrl+C.")
    parser.add_argument("--roll-sp", type=float, default=-9.0)
    parser.add_argument("--pitch-sp", type=float, default=12.0)
    parser.add_argument("--P-roll", type=float, default=0.03)
    parser.add_argument("--I-roll", type=float, default=0.003)
    parser.add_argument("--D-roll", type=float, default=0.0)
    parser.add_argument("--P-pitch", type=float, default=0.03)
    parser.add_argument("--I-pitch", type=float, default=0.003)
    parser.add_argument("--D-pitch", type=float, default=0.0)
    parser.add_argument("--routing", choices=("legacy", "corrected"), default="legacy")
    parser.add_argument("--clip", type=float, default=1.0, help="Use 0 for no wrapper clipping.")
    parser.add_argument("--rudder", type=float, default=0.0)
    parser.add_argument("--throttle", type=float, default=-998.0)
    parser.add_argument("--out", default="xp12_pid_log.csv")
    args = parser.parse_args()

    roll_controller = PID.PID(args.P_roll, args.I_roll, args.D_roll)
    pitch_controller = PID.PID(args.P_pitch, args.I_pitch, args.D_pitch)
    roll_controller.SetPoint = args.roll_sp
    pitch_controller.SetPoint = args.pitch_sp
    sample_period = 1.0 / args.hz
    roll_controller.setSampleTime(sample_period)
    pitch_controller.setSampleTime(sample_period)

    fields = [
        "t_s", "lat_deg", "lon_deg", "alt_m", "pitch_deg", "roll_deg",
        "heading_deg", "gear", "xpc_ctrl_aileron", "xpc_ctrl_elevator",
        "xpc_ctrl_rudder", "xpc_ctrl_throttle", "roll_output",
        "pitch_output", "routing",
    ]
    output_path = Path(args.out)
    print(f"Connecting to X-Plane at {args.host}:{args.port} ...")
    print("Routing mode:", args.routing)

    started = time.monotonic()
    next_sample = started
    count = 0
    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client, output_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        try:
            while True:
                now = time.monotonic()
                elapsed = now - started
                if args.duration > 0 and elapsed >= args.duration:
                    break
                if now < next_sample:
                    time.sleep(min(0.005, next_sample - now))
                    continue
                next_sample += sample_period

                lat, lon, alt, pitch, roll, heading, gear = client.getPOSI()
                roll_controller.update(roll)
                pitch_controller.update(pitch)
                roll_output = roll_controller.output
                pitch_output = pitch_controller.output

                if args.routing == "legacy":
                    aileron_command, elevator_command = pitch_output, roll_output
                else:
                    aileron_command, elevator_command = roll_output, pitch_output
                limit = None if args.clip == 0 else abs(args.clip)
                aileron_command = clamp(aileron_command, limit)
                elevator_command = clamp(elevator_command, limit)
                rudder_command = clamp(args.rudder, limit)
                client.sendCTRL([aileron_command, elevator_command, rudder_command, args.throttle])

                writer.writerow({
                    "t_s": elapsed, "lat_deg": lat, "lon_deg": lon, "alt_m": alt,
                    "pitch_deg": pitch, "roll_deg": roll, "heading_deg": heading,
                    "gear": gear, "xpc_ctrl_aileron": aileron_command,
                    "xpc_ctrl_elevator": elevator_command,
                    "xpc_ctrl_rudder": rudder_command,
                    "xpc_ctrl_throttle": args.throttle, "roll_output": roll_output,
                    "pitch_output": pitch_output, "routing": args.routing,
                })
                count += 1
                if count % max(1, int(args.hz)) == 0:
                    print(f"t={elapsed:6.2f}s  roll={roll:8.3f}  pitch={pitch:8.3f}  ail={aileron_command:8.3f}  ele={elevator_command:8.3f}  alt={alt:9.2f}")
        except KeyboardInterrupt:
            print("\nStopped by user.")
    print("Saved log:", output_path.resolve())


if __name__ == "__main__":
    main()
