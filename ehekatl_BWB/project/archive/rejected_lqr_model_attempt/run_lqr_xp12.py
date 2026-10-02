#!/usr/bin/env python3
"""Run the data-identified roll/pitch LQR controller against X-Plane 12."""

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

import xpc
from LQR import LQRController


def clamp(value, limit):
    return max(-limit, min(limit, float(value)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="lqr_model.json")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    parser.add_argument("--timeout-ms", type=int, default=2000)
    parser.add_argument("--hz", type=float, default=10.0)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--roll-sp", type=float, default=0.0)
    parser.add_argument("--pitch-sp", type=float, default=6.0)
    parser.add_argument("--q", type=float, nargs=4, default=[8.0, 8.0, 0.5, 0.5], metavar=("ROLL", "PITCH", "P", "Q"))
    parser.add_argument("--r", type=float, nargs=2, default=[25.0, 25.0], metavar=("AIL", "ELE"))
    parser.add_argument("--rate-alpha", type=float, default=0.35)
    parser.add_argument("--clip", type=float, default=0.25, help="Absolute stick limit; start conservatively.")
    parser.add_argument("--rudder", type=float, default=0.0)
    parser.add_argument("--throttle", type=float, default=-998.0)
    parser.add_argument("--out", default="xp12_lqr_log.csv")
    args = parser.parse_args()
    if args.hz <= 0 or args.clip <= 0:
        parser.error("--hz and --clip must be positive")

    model = json.loads(Path(args.model).read_text())
    controller = LQRController(model["A"], model["B"], np.diag(args.q), np.diag(args.r), model["trim_input"], args.rate_alpha)
    print("LQR gain K:\n", controller.K)
    print("Closed-loop eigenvalues:", controller.closed_loop_eigenvalues)
    if np.max(np.abs(controller.closed_loop_eigenvalues)) >= 1:
        raise RuntimeError("identified LQR closed loop is not discrete-time stable; do not fly")

    fields = ["t_s", "lat_deg", "lon_deg", "alt_m", "pitch_deg", "roll_deg", "heading_deg", "gear",
              "roll_rate_deg_s", "pitch_rate_deg_s", "xpc_ctrl_aileron", "xpc_ctrl_elevator",
              "xpc_ctrl_rudder", "xpc_ctrl_throttle", "roll_sp_deg", "pitch_sp_deg", "controller"]
    dt = 1.0 / args.hz
    started = next_time = time.monotonic()
    out = Path(args.out)
    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client, out.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        try:
            while args.duration <= 0 or time.monotonic() - started < args.duration:
                now = time.monotonic()
                if now < next_time:
                    time.sleep(min(0.005, next_time - now))
                    continue
                elapsed = now - started
                next_time += dt
                lat, lon, alt, pitch, roll, heading, gear = client.getPOSI()
                command, state = controller.update(roll, pitch, args.roll_sp, args.pitch_sp, dt)
                ail, ele = [clamp(v, args.clip) for v in command]
                rud = clamp(args.rudder, args.clip)
                client.sendCTRL([ail, ele, rud, args.throttle])
                writer.writerow(dict(zip(fields, [elapsed, lat, lon, alt, pitch, roll, heading, gear,
                    state[2], state[3], ail, ele, rud, args.throttle, args.roll_sp, args.pitch_sp, "lqr"])))
                if int(elapsed * args.hz) % max(1, int(args.hz)) == 0:
                    print(f"t={elapsed:6.2f}s roll={roll:8.3f} pitch={pitch:8.3f} ail={ail:8.3f} ele={ele:8.3f}")
        except KeyboardInterrupt:
            print("\nStopped by user.")
    print("Saved log:", out.resolve())


if __name__ == "__main__":
    main()
