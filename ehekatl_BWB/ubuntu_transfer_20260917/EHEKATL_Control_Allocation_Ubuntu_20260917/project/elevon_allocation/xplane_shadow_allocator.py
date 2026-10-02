"""Read-only X-Plane shadow test for the EHEKATL elevon allocator.

This script never calls sendCTRL or sendDREF. It reads the current aircraft
state, computes a virtual angular-acceleration demand, allocates that demand to
eight proposed elevons and two proposed rudders, and logs the result. The
surface commands are proposals only because the supplied project does not
contain the .acf file or a verified independent-surface write mapping.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import xpc  # noqa: E402

from elevon_allocation.allocator import BoxQPAllocator, EffectivenessModel, SURFACES  # noqa: E402


DREFS = (
    "sim/flightmodel/position/phi",
    "sim/flightmodel/position/theta",
    "sim/flightmodel/position/psi",
    "sim/flightmodel/position/P",
    "sim/flightmodel/position/Q",
    "sim/flightmodel/position/R",
    "sim/flightmodel/position/indicated_airspeed",
    "sim/operation/prefs/replay_mode",
    "sim/time/paused",
)


def scalar(value) -> float:
    return float(value[0] if isinstance(value, (list, tuple, np.ndarray)) else value)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Read-only EHEKATL elevon-allocation shadow test")
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=49009)
    result.add_argument("--timeout-ms", type=int, default=500)
    result.add_argument("--duration", type=float, default=20.0)
    result.add_argument("--hz", type=float, default=20.0)
    result.add_argument("--roll-setpoint", type=float, default=0.0)
    result.add_argument("--pitch-setpoint", type=float, default=0.0)
    result.add_argument("--yaw-setpoint", type=float, default=None)
    result.add_argument("--output", type=Path)
    return result


def main() -> None:
    args = parser().parse_args()
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    output = args.output or ROOT / "logs" / f"elevon_allocator_shadow_{timestamp}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    period = 1.0 / args.hz
    allocator = BoxQPAllocator(EffectivenessModel.research_prior(), period, covariance_weight=20.0)
    kp = np.array([2.4, 2.9, 1.75])
    kd = np.array([2.15, 2.35, 1.8])
    limits_deg = np.r_[np.full(8, 25.0), np.full(2, 20.0)]
    fields = ["elapsed_s", "roll_deg", "pitch_deg", "yaw_deg", "p_deg_s", "q_deg_s", "r_deg_s",
              "ias_kts", "paused", "replay", "virtual_roll_deg_s2", "virtual_pitch_deg_s2",
              "virtual_yaw_deg_s2", *[f"proposed_{name}_norm" for name in SURFACES],
              *[f"proposed_{name}_deg" for name in SURFACES], "controls_sent"]

    with xpc.XPlaneConnect(xpHost=args.host, xpPort=args.port, timeout=args.timeout_ms) as client, \
            output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        start = time.monotonic()
        next_tick = start
        yaw_reference = args.yaw_setpoint
        while time.monotonic() - start < args.duration:
            try:
                response = client.getDREFs(DREFS)
            except OSError as error:
                raise SystemExit(
                    "No read-only XPlaneConnect response. Start X-Plane 12, load the "
                    "EHEKATL aircraft, and confirm the XPlaneConnect plugin is enabled. "
                    f"No controls were sent. Details: {error}"
                ) from None
            values = [scalar(value) for value in response]
            roll, pitch, yaw, p_rate, q_rate, r_rate, ias, replay, paused = values
            if yaw_reference is None:
                yaw_reference = yaw
            angle_error = np.array([args.roll_setpoint - roll, args.pitch_setpoint - pitch,
                                    ((yaw_reference - yaw + 180.0) % 360.0) - 180.0])
            rates = np.array([p_rate, q_rate, r_rate])
            virtual = np.clip(kp * angle_error - kd * rates, -55.0, 55.0)
            allocation = allocator.allocate(virtual)
            row = {
                "elapsed_s": time.monotonic() - start,
                "roll_deg": roll,
                "pitch_deg": pitch,
                "yaw_deg": yaw,
                "p_deg_s": p_rate,
                "q_deg_s": q_rate,
                "r_deg_s": r_rate,
                "ias_kts": ias,
                "paused": paused,
                "replay": replay,
                "virtual_roll_deg_s2": virtual[0],
                "virtual_pitch_deg_s2": virtual[1],
                "virtual_yaw_deg_s2": virtual[2],
                "controls_sent": 0,
            }
            row.update({f"proposed_{name}_norm": allocation.command[i] for i, name in enumerate(SURFACES)})
            row.update({f"proposed_{name}_deg": allocation.command[i] * limits_deg[i] for i, name in enumerate(SURFACES)})
            writer.writerow(row)
            next_tick += period
            time.sleep(max(0.0, next_tick - time.monotonic()))
    print(f"READ-ONLY shadow log: {output}")


if __name__ == "__main__":
    main()
