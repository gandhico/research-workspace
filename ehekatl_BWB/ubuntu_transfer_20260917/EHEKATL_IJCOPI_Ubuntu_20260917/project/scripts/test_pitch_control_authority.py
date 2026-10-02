#!/usr/bin/env python3
"""Test a tiny pitch-input increment with scoped ownership and restoration."""

import argparse
import csv
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import xpc

OVERRIDE = "sim/operation/override/override_joystick_pitch"
YOKE = "sim/joystick/yoke_pitch_ratio"
STATE_DREFS = (
    OVERRIDE, YOKE, "sim/joystick/FC_ptch",
    "sim/cockpit2/controls/total_pitch_ratio",
    "sim/flightmodel/position/theta", "sim/flightmodel/position/Q",
    "sim/flightmodel/controls/elv1_def", "sim/flightmodel/controls/elv2_def",
)


def sequence(value):
    while isinstance(value, (list, tuple)) and len(value) == 1 and isinstance(value[0], (list, tuple)):
        value = value[0]
    if isinstance(value, (list, tuple)):
        return [float(item) for item in value]
    return [float(value)]


def scalar(value):
    result = sequence(value)
    if not result:
        raise RuntimeError("empty X-Plane dataref value")
    return result[0]


def snapshot(client, phase, elapsed_s):
    observed = client.getDREFs(list(STATE_DREFS))
    return {
        "elapsed_s": elapsed_s,
        "phase": phase,
        "override_joystick_pitch": scalar(observed[0]),
        "yoke_pitch_ratio": scalar(observed[1]),
        "fc_pitch": scalar(observed[2]),
        "total_pitch_ratio": scalar(observed[3]),
        "pitch_deg": scalar(observed[4]),
        "q_deg_s": scalar(observed[5]),
        "elv1_max_abs_deg": max(map(abs, sequence(observed[6])), default=0.0),
        "elv2_max_abs_deg": max(map(abs, sequence(observed[7])), default=0.0),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--increment", type=float, default=0.005)
    parser.add_argument("--duration", type=float, default=0.5)
    parser.add_argument("--hz", type=float, default=20.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--engage", action="store_true")
    args = parser.parse_args()
    if abs(args.increment) > 0.005:
        parser.error("absolute --increment must not exceed 0.005")
    if not 0.1 <= args.duration <= 1.0:
        parser.error("--duration must be between 0.1 and 1.0 seconds")
    if not 1.0 <= args.hz <= 50.0:
        parser.error("--hz must be between 1 and 50")

    rows = []
    started = time.monotonic()
    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client:
        paused, sim_speed, replay_mode = [
            scalar(item) for item in client.getDREFs(
                ["sim/time/paused", "sim/time/sim_speed", "sim/operation/prefs/replay_mode"]
            )
        ]
        initial_override = scalar(client.getDREF(OVERRIDE))
        initial_yoke = scalar(client.getDREF(YOKE))
        commanded_yoke = initial_yoke + args.increment
        if not -1.0 <= commanded_yoke <= 1.0:
            raise RuntimeError("increment would place pitch input outside [-1, 1]")
        rows.append(snapshot(client, "before", time.monotonic() - started))
        if args.engage:
            if paused != 0.0 or sim_speed <= 0.0 or replay_mode != 0.0:
                raise RuntimeError(
                    "engagement blocked: X-Plane must be live "
                    f"(paused={paused:g}, sim_speed={sim_speed:g}, replay_mode={replay_mode:g})"
                )
            try:
                client.sendDREF(OVERRIDE, 1.0)
                deadline = time.monotonic() + args.duration
                while time.monotonic() < deadline:
                    client.sendDREF(YOKE, commanded_yoke)
                    rows.append(snapshot(client, "command", time.monotonic() - started))
                    time.sleep(1.0 / args.hz)
            finally:
                client.sendDREF(YOKE, initial_yoke)
                client.sendDREF(OVERRIDE, initial_override)
                time.sleep(0.1)
                rows.append(snapshot(client, "restored", time.monotonic() - started))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"mode={'ENGAGED' if args.engage else 'READ-ONLY'}")
    print(f"paused={paused:g}; sim_speed={sim_speed:g}; replay_mode={replay_mode:g}")
    print(
        f"initial yoke={initial_yoke:+.6f}; increment={args.increment:+.6f}; "
        f"command={commanded_yoke:+.6f}; initial override={initial_override:g}"
    )
    for row in rows:
        print(
            f"{row['phase']:8s} yoke={row['yoke_pitch_ratio']:+.6f} "
            f"total={row['total_pitch_ratio']:+.6f} "
            f"elv={row['elv1_max_abs_deg']:.6f}deg "
            f"pitch={row['pitch_deg']:+.4f}deg Q={row['q_deg_s']:+.4f}deg/s"
        )
    print(f"Output: {args.out.resolve()}")


if __name__ == "__main__":
    main()
