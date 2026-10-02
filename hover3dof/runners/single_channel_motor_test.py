"""Vendor Section 4.1.1 motor bring-up test, ONE channel at a time.

Applies ~4V (DAQ analog-output volts; at amplifier gain=3 this is ~12V at
the motor -- within the 24V/3A rating) to exactly one Analog Output channel
for a brief pulse, ramped (not stepped) to avoid a sudden jolt, then zeros
ALL FOUR channels unconditionally (try/finally, plus on Ctrl-C). This is a
purely open-loop identification test -- it does not read encoders or
attempt any balancing.

Usage: python single_channel_motor_test.py --channel 0 --volts 4.0 --hold 1.0
"""
from __future__ import annotations

import argparse
import time
import array as arr

from quanser.hardware import HIL, HILError


def pulse(channel: int, volts: float, hold: float, ramp: float) -> None:
    card = HIL()
    card.open("q8_usb", "0")
    channels = arr.array("i", [0, 1, 2, 3])
    zero = arr.array("d", [0.0, 0.0, 0.0, 0.0])
    try:
        card.write_analog(channels, 4, zero)
        print(f"All 4 channels confirmed at 0V. Ramping channel {channel} to {volts}V over {ramp}s...")

        steps = 30
        for i in range(steps + 1):
            v = arr.array("d", [0.0, 0.0, 0.0, 0.0])
            v[channel] = volts*i/steps
            card.write_analog(channels, 4, v)
            time.sleep(ramp/steps)

        print(f"Holding channel {channel} at {volts}V for {hold}s...")
        time.sleep(hold)

        print(f"Ramping channel {channel} back to 0V over {ramp}s...")
        for i in range(steps, -1, -1):
            v = arr.array("d", [0.0, 0.0, 0.0, 0.0])
            v[channel] = volts*i/steps
            card.write_analog(channels, 4, v)
            time.sleep(ramp/steps)

        card.write_analog(channels, 4, zero)
        print("Done. All 4 channels at 0V.")
    finally:
        card.write_analog(channels, 4, zero)
        card.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", type=int, required=True, choices=[0, 1, 2, 3])
    parser.add_argument("--volts", type=float, default=4.0)
    parser.add_argument("--hold", type=float, default=1.0)
    parser.add_argument("--ramp", type=float, default=0.4)
    args = parser.parse_args()
    try:
        pulse(args.channel, args.volts, args.hold, args.ramp)
    except HILError as ex:
        print(f"HIL error: {ex.get_error_message()}")
        raise
