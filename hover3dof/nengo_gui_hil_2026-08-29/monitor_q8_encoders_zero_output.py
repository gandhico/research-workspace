"""Display live 3DOF Hover encoder angles while forcing all Q8 AO to zero."""
from __future__ import annotations

import argparse
import array as arr
import time

import numpy as np
from quanser.hardware import HIL


K_EC_PITCH = 2.0 * np.pi / (8 * 1024)
K_EC_ROLL = 2.0 * np.pi / (8 * 1024)
K_EC_YAW = -2.0 * np.pi / (8 * 1024)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=120.0)
    parser.add_argument("--rate-hz", type=float, default=5.0)
    args = parser.parse_args()
    if args.duration <= 0 or args.rate_hz <= 0:
        parser.error("duration and rate-hz must be positive")

    card = HIL()
    ao = arr.array("i", [0, 1, 2, 3])
    enc = arr.array("i", [0, 1, 2])
    counts = arr.array("i", [0, 0, 0])
    zero = arr.array("d", [0.0, 0.0, 0.0, 0.0])
    period = 1.0 / args.rate_hz
    try:
        card.open("q8_usb", "0")
        card.write_analog(ao, 4, zero)
        print("ZERO-OUTPUT encoder monitor. Move the frame by hand only; Ctrl-C stops.", flush=True)
        start = time.perf_counter()
        while time.perf_counter() - start < args.duration:
            card.write_analog(ao, 4, zero)
            card.read_encoder(enc, 3, counts)
            ypr_deg = np.rad2deg(
                [counts[2] * K_EC_YAW, counts[0] * K_EC_PITCH, counts[1] * K_EC_ROLL]
            )
            print(
                f"raw yaw={ypr_deg[0]:+8.3f} deg | pitch={ypr_deg[1]:+7.3f} deg | roll={ypr_deg[2]:+7.3f} deg",
                flush=True,
            )
            time.sleep(period)
    finally:
        try:
            card.write_analog(ao, 4, zero)
        finally:
            card.close()
        print("All four Q8 analog outputs forced to zero. Card closed.", flush=True)


if __name__ == "__main__":
    main()
