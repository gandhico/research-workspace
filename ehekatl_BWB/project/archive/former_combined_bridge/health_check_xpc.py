#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys


BRIDGE_DIR = Path(__file__).resolve().parent
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

import xpc


def main():
    ap = argparse.ArgumentParser(description='Quick XPlaneConnect health check for EHEKATL XP12.')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=49009)
    ap.add_argument('--timeout-ms', type=int, default=2000)
    args = ap.parse_args()
    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client:
        posi = client.getPOSI()
        ctrl = client.getCTRL()
        print('CONNECTED')
        print('POSI [lat, lon, alt_m, pitch_deg, roll_deg, heading_deg, gear] =')
        print(posi)
        print('CTRL [aileron, elevator, rudder, throttle, gear, flaps, speedbrake] =')
        print(ctrl)

if __name__ == '__main__':
    main()
