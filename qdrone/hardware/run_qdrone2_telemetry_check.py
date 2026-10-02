from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path


QUANSER_PYTHON = Path(r"C:\Quanser\0_libraries\python")
LOG_DIR = Path(__file__).resolve().parent / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QDrone2 read-only telemetry stream check.")
    parser.add_argument("--connect", action="store_true", help="Actually connect to the QDrone2 stream.")
    parser.add_argument("--ip", default="192.168.2.15")
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--sample-rate", type=float, default=100.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"qdrone2_telemetry_check_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    if not args.connect:
        print("Dry run only. Add --connect to open the QDrone2 telemetry stream.")
        print(f"Planned log path: {log_path}")
        return

    sys.path.insert(0, str(QUANSER_PYTHON))
    from pal.products.qdrone2 import QDrone2StreamStack

    stream = None
    sample_time = 1.0 / args.sample_rate
    try:
        stream = QDrone2StreamStack(ip=args.ip)
        fieldnames = [
            "time_s",
            "new_packet",
            "state_0",
            "state_1",
            "state_2",
            "state_3",
            "state_4",
            "state_5",
            "state_6",
            "state_7",
            "state_8",
            "motor_cmd_0",
            "motor_cmd_1",
            "motor_cmd_2",
            "motor_cmd_3",
            "motor_current",
            "battery_voltage",
            "low_battery",
            "timestamp_rec",
        ]
        with log_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            start = time.time()
            while time.time() - start < args.duration:
                loop = time.time()
                elapsed = loop - start
                new = stream.read(elapsed)
                row = {
                    "time_s": elapsed,
                    "new_packet": int(bool(new)),
                    "motor_current": float(stream.motorCurrent),
                    "battery_voltage": float(stream.battVoltage),
                    "low_battery": float(stream.lowBattery),
                    "timestamp_rec": float(stream.timestampREC),
                }
                row.update({f"state_{i}": float(value) for i, value in enumerate(stream.state_vec)})
                row.update({f"motor_cmd_{i}": float(value) for i, value in enumerate(stream.motorCmd)})
                writer.writerow(row)
                sleep_time = sample_time - (time.time() - loop)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        print(f"Telemetry check complete. Log: {log_path}")
    finally:
        if stream is not None:
            stream.terminate()


if __name__ == "__main__":
    main()

