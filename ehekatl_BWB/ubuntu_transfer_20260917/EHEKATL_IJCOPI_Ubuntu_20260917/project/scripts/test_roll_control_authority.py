#!/usr/bin/env python3
"""Safely test whether a tiny overridden roll input reaches X-Plane surfaces."""

import argparse
import csv
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import xpc


OVERRIDE = "sim/operation/override/override_joystick_roll"
YOKE_ROLL = "sim/joystick/yoke_roll_ratio"
PAUSED = "sim/time/paused"
SIM_SPEED = "sim/time/sim_speed"
REPLAY_MODE = "sim/operation/prefs/replay_mode"
READ_DREFS = (
    OVERRIDE,
    YOKE_ROLL,
    "sim/joystick/FC_roll",
    "sim/cockpit2/controls/total_roll_ratio",
    "sim/flightmodel/position/phi",
    "sim/flightmodel/position/P",
    "sim/flightmodel/controls/ail1_def",
    "sim/flightmodel/controls/ail2_def",
)


def values(value):
    if isinstance(value, (list, tuple)):
        if len(value) == 1 and isinstance(value[0], (list, tuple)):
            return values(value[0])
        return [float(item) for item in value]
    return [float(value)]


def first(value):
    sequence = values(value)
    if not sequence:
        raise RuntimeError("X-Plane returned an empty dataref value")
    return sequence[0]


def snapshot(client, phase, elapsed_s):
    observed = client.getDREFs(list(READ_DREFS))
    ail1 = values(observed[6])
    ail2 = values(observed[7])
    return {
        "elapsed_s": elapsed_s,
        "phase": phase,
        "override_joystick_roll": first(observed[0]),
        "yoke_roll_ratio": first(observed[1]),
        "fc_roll": first(observed[2]),
        "total_roll_ratio": first(observed[3]),
        "roll_deg": first(observed[4]),
        "p_deg_s": first(observed[5]),
        "ail1_max_abs_deg": max(map(abs, ail1), default=0.0),
        "ail2_max_abs_deg": max(map(abs, ail2), default=0.0),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--command", type=float, default=0.005)
    parser.add_argument("--duration", type=float, default=0.5)
    parser.add_argument("--hz", type=float, default=20.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--engage",
        action="store_true",
        help="temporarily take only roll-axis ownership and send the tiny command",
    )
    args = parser.parse_args()

    if abs(args.command) > 0.005:
        parser.error("absolute --command must not exceed 0.005")
    if not 0.1 <= args.duration <= 1.0:
        parser.error("--duration must be between 0.1 and 1.0 seconds")
    if not 1.0 <= args.hz <= 50.0:
        parser.error("--hz must be between 1 and 50")

    rows = []
    start = time.monotonic()
    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client:
        paused, sim_speed, replay_mode = [
            first(item) for item in client.getDREFs([PAUSED, SIM_SPEED, REPLAY_MODE])
        ]
        initial_override = first(client.getDREF(OVERRIDE))
        initial_roll = first(client.getDREF(YOKE_ROLL))
        rows.append(snapshot(client, "before", time.monotonic() - start))

        if args.engage:
            if paused != 0.0 or sim_speed <= 0.0 or replay_mode != 0.0:
                raise RuntimeError(
                    "engagement blocked: X-Plane must be unpaused, at positive sim speed, "
                    f"and out of replay (paused={paused:g}, sim_speed={sim_speed:g}, "
                    f"replay_mode={replay_mode:g})"
                )
            try:
                client.sendDREF(OVERRIDE, 1.0)
                deadline = time.monotonic() + args.duration
                period = 1.0 / args.hz
                while time.monotonic() < deadline:
                    client.sendDREF(YOKE_ROLL, args.command)
                    rows.append(snapshot(client, "command", time.monotonic() - start))
                    time.sleep(period)
            finally:
                client.sendDREF(YOKE_ROLL, initial_roll)
                client.sendDREF(OVERRIDE, initial_override)
                time.sleep(0.1)
                rows.append(snapshot(client, "restored", time.monotonic() - start))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"mode={'ENGAGED' if args.engage else 'READ-ONLY'}")
    print(f"paused={paused:g}; sim_speed={sim_speed:g}; replay_mode={replay_mode:g}")
    print(f"initial override={initial_override:.6g}; initial yoke roll={initial_roll:.6g}")
    for row in rows:
        print(
            f"{row['phase']:8s} yoke={row['yoke_roll_ratio']:+.6f} "
            f"total={row['total_roll_ratio']:+.6f} "
            f"ail1={row['ail1_max_abs_deg']:.6f}deg "
            f"ail2={row['ail2_max_abs_deg']:.6f}deg "
            f"roll={row['roll_deg']:+.4f}deg P={row['p_deg_s']:+.4f}deg/s"
        )
    print(f"Output: {args.out.resolve()}")


if __name__ == "__main__":
    main()
