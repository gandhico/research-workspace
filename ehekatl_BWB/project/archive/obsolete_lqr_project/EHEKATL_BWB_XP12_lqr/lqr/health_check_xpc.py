#!/usr/bin/env python3
"""Small XPlaneConnect health check for the EHEKATL XP12 controller project."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKSTEPPING_BRIDGE = PROJECT_ROOT / "backstepping" / "ehekatl_xplane12_backstepping_bridge"
if str(BACKSTEPPING_BRIDGE) not in sys.path:
    sys.path.insert(0, str(BACKSTEPPING_BRIDGE))


def connect_xplane(xpc_module, host: str, port: int):
    try:
        return xpc_module.XPlaneConnect(xpHost=host, xpPort=port)
    except TypeError:
        return xpc_module.XPlaneConnect(host, port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check XPlaneConnect POSI access.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=49009)
    args = parser.parse_args()

    import xpc

    with connect_xplane(xpc, args.host, args.port) as client:
        posi = client.getPOSI()
        ctrl = client.getCTRL()
        print(f"Connected to X-Plane at {args.host}:{args.port}")
        print(f"POSI length={len(posi)} values={posi}")
        print(f"CTRL values={ctrl}")


if __name__ == "__main__":
    main()
