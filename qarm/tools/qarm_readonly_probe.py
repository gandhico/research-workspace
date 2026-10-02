"""Read-only QArm (qarm_usb) connection probe.

Opens the HIL board, reads identity properties and samples sensor channels.
It never calls any HIL write/set function, never sets board-specific options,
and never enables a watchdog. Channel map: QUARC doc quarc/doc/qarm_usb.html.
"""
import json
import sys
import time

import numpy as np
from quanser.hardware import HIL, HILError, IntegerProperty as IP, StringProperty as SP

JOINTS = ["yaw", "shoulder", "elbow", "wrist", "gripper"]
POS = np.array([1000, 1001, 1002, 1003, 1004], dtype=np.uint32)
VEL = np.array([3000, 3001, 3002, 3003, 3004], dtype=np.uint32)
TEMP = np.array([10000, 10001, 10002, 10003, 10004], dtype=np.uint32)
PWM = np.array([11000, 11001, 11002, 11003, 11004], dtype=np.uint32)
CUR = np.array([5, 6, 7, 8, 9], dtype=np.uint32)
# Documented command ranges (Other Outputs table) used only as reference limits.
LIMITS = {"yaw": (-3.0, 3.0), "shoulder": (-np.pi / 2, np.pi / 2),
          "elbow": (-1.74, 1.39), "wrist": (-3.0, 3.0), "gripper": (0.0, 1.0)}
CUR_RANGE = [4.4, 8.8, 4.4, 2.3, 1.4]


def main(duration=2.0, rate_hz=50.0):
    report = {}
    card = HIL()
    try:
        card.open("qarm_usb", "0")
    except HILError as e:
        print("OPEN FAILED:", e.get_error_message())
        return 2
    try:
        report["is_valid"] = bool(card.is_valid())
        props = {}
        for name in ["VENDOR_ID", "PRODUCT_ID", "FIRMWARE_MAJOR_VERSION",
                     "FIRMWARE_MINOR_VERSION", "FIRMWARE_BUILD", "FIRMWARE_REVISION"]:
            try:
                buf = np.zeros(1, dtype=np.int32)
                card.get_integer_property(np.array([getattr(IP, name)], dtype=np.int32), 1, buf)
                props[name] = int(buf[0])
            except Exception as e:  # noqa: BLE001
                props[name] = f"n/a ({e})"
        for name in ["MANUFACTURER", "PRODUCT_NAME", "MODEL_NAME", "SERIAL_NUMBER", "FIRMWARE_VERSION"]:
            try:
                props[name] = card.get_string_property(getattr(SP, name), 128)
            except Exception as e:  # noqa: BLE001
                props[name] = f"n/a ({e})"
        report["properties"] = props

        other_ch = np.concatenate([POS, VEL, TEMP, PWM])
        other = np.zeros(len(other_ch), dtype=np.float64)
        analog = np.zeros(len(CUR), dtype=np.float64)
        n = int(duration * rate_hz)
        samples, stamps = [], []
        period = 1.0 / rate_hz
        t0 = time.perf_counter()
        for k in range(n):
            target = t0 + k * period
            while time.perf_counter() < target:
                pass
            stamps.append(time.perf_counter() - t0)
            card.read_other(other_ch, len(other_ch), other)
            card.read_analog(CUR, len(CUR), analog)
            samples.append(np.concatenate([other, analog]).copy())
        s = np.array(samples)
        dt = np.diff(stamps)
        report["timing"] = {"samples": n, "rate_hz": rate_hz,
                            "dt_mean_ms": float(dt.mean() * 1e3),
                            "dt_std_ms": float(dt.std() * 1e3),
                            "dt_max_ms": float(dt.max() * 1e3),
                            "jitter_pct": float(dt.std() / dt.mean() * 100)}
        joints = {}
        for i, j in enumerate(JOINTS):
            pos = s[:, i]
            lo, hi = LIMITS[j]
            joints[j] = {
                "pos_mean": float(pos.mean()), "pos_std": float(pos.std()),
                "pos_deg": float(np.degrees(pos.mean())) if j != "gripper" else None,
                "within_doc_range": bool(lo <= pos.mean() <= hi),
                "vel_mean": float(s[:, 5 + i].mean()), "vel_absmax": float(np.abs(s[:, 5 + i]).max()),
                "temp_C": float(s[:, 10 + i].mean()),
                "pwm_mean": float(s[:, 15 + i].mean()),
                "current_A": float(s[:, 20 + i].mean()), "current_absmax_A": float(np.abs(s[:, 20 + i]).max()),
                "current_range_A": CUR_RANGE[i],
                "all_finite": bool(np.all(np.isfinite(s[:, [i, 5 + i, 10 + i, 15 + i, 20 + i]]))),
            }
        report["joints"] = joints
    finally:
        card.close()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

