#!/usr/bin/env python3
"""Run Gandhi's original EHEKATL backstepping controller against X-Plane.

Controller equations and gains are preserved from the uploaded code. This wrapper
only adds: Python 3 compatible XPC, CLI parameters, CSV logging, optional runtime,
and explicit routing mode for the control vector.

XPC sendCTRL order is: [aileron/lat stick, elevator/long stick, rudder, throttle].
The uploaded legacy script sends [pitch_output, roll_output, rudder, throttle].
Use --routing legacy to reproduce it exactly, or --routing corrected to use
[roll_output, pitch_output, rudder, throttle].
"""
import argparse
import csv
import math
import time
from pathlib import Path

import xpc
import Backstepping


def clamp(x, limit):
    if limit is None or limit <= 0:
        return float(x)
    return max(-limit, min(limit, float(x)))


def main():
    ap = argparse.ArgumentParser(description='EHEKATL BWB XP12 backstepping test.')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=49009)
    ap.add_argument('--timeout-ms', type=int, default=2000)
    ap.add_argument('--hz', type=float, default=10.0)
    ap.add_argument('--duration', type=float, default=60.0, help='Seconds. Use 0 for infinite until Ctrl+C.')
    ap.add_argument('--roll-sp', type=float, default=0.0, help='Roll setpoint in degrees.')
    ap.add_argument('--pitch-sp', type=float, default=6.0, help='Pitch setpoint in degrees.')
    ap.add_argument('--K-roll', type=float, default=0.001)
    ap.add_argument('--K-pitch', type=float, default=0.001)
    ap.add_argument('--Ku-roll', type=float, default=33.0)
    ap.add_argument('--Ku-pitch', type=float, default=39.0)
    ap.add_argument('--tau-roll', type=float, default=0.03)
    ap.add_argument('--tau-pitch', type=float, default=0.03)
    ap.add_argument('--routing', choices=['legacy', 'corrected'], default='legacy')
    ap.add_argument('--clip', type=float, default=1.0, help='Stick saturation. 1.0 means full stick. Use 0 for no wrapper clipping.')
    ap.add_argument('--rudder', type=float, default=0.0)
    ap.add_argument('--throttle', type=float, default=-998.0, help='-998 keeps current throttle.')
    ap.add_argument('--out', default='xp12_backstepping_log.csv')
    args = ap.parse_args()

    roll_ctrl = Backstepping.Backstepping(args.K_roll, args.Ku_roll, args.tau_roll)
    pitch_ctrl = Backstepping.Backstepping(args.K_pitch, args.Ku_pitch, args.tau_pitch)
    roll_ctrl.SetPoint = args.roll_sp
    pitch_ctrl.SetPoint = args.pitch_sp

    dt = 1.0 / args.hz
    out_path = Path(args.out)
    fieldnames = [
        't_s', 'lat_deg', 'lon_deg', 'alt_m', 'pitch_deg', 'roll_deg', 'heading_deg', 'gear',
        'xpc_ctrl_aileron', 'xpc_ctrl_elevator', 'xpc_ctrl_rudder', 'xpc_ctrl_throttle',
        'roll_output', 'pitch_output', 'routing'
    ]

    print('Connecting to X-Plane at {}:{} ...'.format(args.host, args.port))
    print('Routing mode:', args.routing)
    print('Ctrl+C stops the test and leaves the last controls commanded.')

    t0 = time.monotonic()
    next_t = t0
    n = 0
    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client, out_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        try:
            while True:
                now = time.monotonic()
                elapsed = now - t0
                if args.duration > 0 and elapsed >= args.duration:
                    break
                if now < next_t:
                    time.sleep(min(0.005, next_t - now))
                    continue
                next_t += dt

                posi = client.getPOSI()
                ctrl = client.getCTRL()
                lat, lon, alt, pitch, roll, heading, gear = posi
                current_aileron = ctrl[0]
                current_elevator = ctrl[1]

                roll_ctrl.update(roll, current_aileron)
                pitch_ctrl.update(pitch, current_elevator)
                roll_out = roll_ctrl.output
                pitch_out = pitch_ctrl.output

                if args.routing == 'legacy':
                    # Uploaded code exactly: ctrl = [new_ele_ctrl, new_ail_ctrl, rudder, throttle]
                    ail_cmd = pitch_out
                    ele_cmd = roll_out
                else:
                    # XPC documented order: [aileron, elevator, rudder, throttle]
                    ail_cmd = roll_out
                    ele_cmd = pitch_out

                clip = None if args.clip == 0 else abs(args.clip)
                ail_cmd = clamp(ail_cmd, clip)
                ele_cmd = clamp(ele_cmd, clip)
                rud_cmd = clamp(args.rudder, clip)
                client.sendCTRL([ail_cmd, ele_cmd, rud_cmd, args.throttle])

                writer.writerow({
                    't_s': elapsed, 'lat_deg': lat, 'lon_deg': lon, 'alt_m': alt,
                    'pitch_deg': pitch, 'roll_deg': roll, 'heading_deg': heading, 'gear': gear,
                    'xpc_ctrl_aileron': ail_cmd, 'xpc_ctrl_elevator': ele_cmd,
                    'xpc_ctrl_rudder': rud_cmd, 'xpc_ctrl_throttle': args.throttle,
                    'roll_output': roll_out, 'pitch_output': pitch_out, 'routing': args.routing
                })
                n += 1
                if n % max(1, int(args.hz)) == 0:
                    print('t={:6.2f}s  roll={:8.3f}  pitch={:8.3f}  ail={:8.3f}  ele={:8.3f}  alt={:9.2f}'.format(
                        elapsed, roll, pitch, ail_cmd, ele_cmd, alt))
        except KeyboardInterrupt:
            print('\nStopped by user.')

    print('Saved log:', out_path.resolve())


if __name__ == '__main__':
    main()
