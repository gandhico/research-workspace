from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path


QAL_DIR = Path(os.environ.get("QAL_DIR", Path.home() / "Documents" / "Quanser"))
QUANSER_PYTHON = Path(
    os.environ.get("QUANSER_PYTHON", QAL_DIR / "0_libraries" / "python")
)
LOG_DIR = Path(__file__).resolve().parent / "logs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qube Servo read-only sensor check with zero motor voltage.")
    parser.add_argument("--connect", action="store_true", help="Actually connect to the Qube hardware/virtual device.")
    parser.add_argument("--version", type=int, choices=[2, 3], default=3)
    parser.add_argument("--id", type=int, default=0)
    parser.add_argument("--hardware", type=int, choices=[0, 1], default=1, help="1=hardware, 0=virtual.")
    parser.add_argument("--pendulum", type=int, choices=[0, 1], default=1)
    parser.add_argument("--sample-rate", type=float, default=500.0)
    parser.add_argument("--duration", type=float, default=10.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"qube_sensor_check_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    if not args.connect:
        print("Dry run only. Add --connect to open the Qube device and log sensors.")
        print(f"Planned log path: {log_path}")
        return

    sys.path.insert(0, str(QUANSER_PYTHON))
    from pal.products.qube import QubeServo2, QubeServo3

    qube_cls = QubeServo3 if args.version == 3 else QubeServo2
    qube = None
    sample_time = 1.0 / args.sample_rate

    try:
        qube = qube_cls(
            id=args.id,
            hardware=args.hardware,
            frequency=int(args.sample_rate),
            pendulum=args.pendulum,
            readMode=1,
        )
        qube.write_voltage(0.0)
        fieldnames = [
            "time_s",
            "motor_position_rad",
            "motor_speed_rad_s",
            "pendulum_position_rad",
            "pendulum_speed_rad_s",
            "motor_current_a",
            "amplifier_fault",
            "motor_stall_detected",
            "motor_stall_error",
        ]
        with log_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            start = time.time()
            while time.time() - start < args.duration:
                loop = time.time()
                qube.write_voltage(0.0)
                qube.read_outputs()
                writer.writerow(
                    {
                        "time_s": loop - start,
                        "motor_position_rad": float(qube.motorPosition),
                        "motor_speed_rad_s": float(qube.motorSpeed),
                        "pendulum_position_rad": float(qube.pendulumPosition),
                        "pendulum_speed_rad_s": float(getattr(qube, "pendulumSpeed", 0.0)),
                        "motor_current_a": float(qube.motorCurrent),
                        "amplifier_fault": float(qube.amplifierFault),
                        "motor_stall_detected": float(qube.motorStallDetected),
                        "motor_stall_error": float(qube.motorStallError),
                    }
                )
                sleep_time = sample_time - (time.time() - loop)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        print(f"Sensor check complete. Log: {log_path}")
    finally:
        if qube is not None:
            qube.write_voltage(0.0)
            qube.terminate()


if __name__ == "__main__":
    main()
