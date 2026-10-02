"""Read-only QArm Mini (qarm_mini) connection probe.

Opens the HIL board, reads identity, joint/gripper sensors and the 25 servo
error flags, and closes. It calls no HIL write/set function and never uses
PAL's QArmMini class, whose terminate() commands the home pose. Channel map:
QUARC doc quarc/doc/qarm_mini.html. Joint-frame conversion: Quanser PAL
pal/products/qarm_mini.py (read_outputs).

Known PAL inconsistency (2026-07-31 release): the gripper raw<->percent map
differs between write_gripper_position (x -1.8), read_write_std (x +1.68) and
read_outputs (inverse with the wrong sign on 0.9). The probe reports both
candidate readings so the true direction can be checked by hand on hardware.
"""
import json
import sys
import time

import numpy as np
from quanser.hardware import HIL, HILError, IntegerProperty as IP, StringProperty as SP

JOINTS = ["yaw", "shoulder", "elbow", "wrist", "gripper"]
# The 15 documented other inputs. (PAL also reads PWM 11000-11004; on 2026-09-27 those
# returned values like 23.1, outside the documented +/-1, so they are left out.)
OTHER_IN = np.array([1000, 1001, 1002, 1003, 1004, 3000, 3001, 3002, 3003, 3004,
                     10000, 10001, 10002, 10003, 10004], dtype=np.uint32)
# Consistency gate: at rest, every position sample must agree with the median within this.
# With the FTDI latency timer at 16 ms (Windows default), reads came back channel-shifted
# or zeroed (2026-09-27); Quanser's quick start requires the COMx latency timer at 2 ms.
CONSISTENCY_TOL = 0.02  # rad
ANALOG_IN = np.array([0, 1, 2, 3, 4], dtype=np.uint32)   # 0,4 load %; 1-3 current A (+/-3.21)
DIGITAL_IN = np.arange(25, dtype=np.uint32)
ERROR_NAMES = ["input_voltage", "overheating", "motor_encoder", "electrical_shock", "overload"]

# PAL joint frame: joint = raw - thetaBias_w - actuatorBias_w (write biases).
THETA_BIAS_W = np.array([0, -np.pi / 2, np.pi / 2, -np.pi / 2])
ACT_BIAS_W = np.array([np.pi - 1.178, np.pi + 0.1834, np.pi - 0.1834 + 0.07, np.pi])
PAL_MIN = np.array([-10 * np.pi / 18, -np.pi / 6, -5 * np.pi / 6, -np.pi / 10])
PAL_MAX = np.array([4 * np.pi / 3, 13 * np.pi / 12, np.pi / 6, 8 * np.pi / 9])


def main(board_id="0", duration=2.0, rate_hz=50.0):
    # Board id = the COM port number of the Mini's "USB Serial Port (COMx)" (Quanser quick start).
    card = HIL()
    try:
        card.open("qarm_mini", str(board_id))
    except HILError as e:
        print(json.dumps({"connected": False, "error": e.get_error_message(),
                          "hint": "Plug in the QArm Mini USB and power, then re-run."}, indent=2))
        return 2
    report = {"connected": True}
    try:
        props = {}
        for name in ["VENDOR_ID", "PRODUCT_ID", "FIRMWARE_MAJOR_VERSION", "FIRMWARE_MINOR_VERSION"]:
            try:
                buf = np.zeros(1, dtype=np.int32)
                card.get_integer_property(np.array([getattr(IP, name)], dtype=np.int32), 1, buf)
                props[name] = int(buf[0])
            except HILError as e:
                props[name] = f"n/a ({e.get_error_message()})"
        for name in ["MANUFACTURER", "PRODUCT_NAME", "MODEL_NAME", "SERIAL_NUMBER", "FIRMWARE_VERSION"]:
            try:
                props[name] = card.get_string_property(getattr(SP, name), 128)
            except HILError as e:
                props[name] = f"n/a ({e.get_error_message()})"
        report["properties"] = props

        other, analog = np.zeros(len(OTHER_IN)), np.zeros(5)
        digital = np.zeros(25, dtype=np.int8)
        samples, stamps, flags_any = [], [], np.zeros(25, dtype=bool)
        t0 = time.perf_counter()
        for k in range(int(duration * rate_hz)):
            while time.perf_counter() < t0 + k / rate_hz:
                pass
            stamps.append(time.perf_counter() - t0)
            analog[:] = np.nan  # so "no data" is not mistaken for 0 A
            # One combined read, as PAL does: on this driver a standalone read_analog
            # leaves the buffer untouched (verified 2026-09-27), the combined read fills it.
            card.read(ANALOG_IN, 5, None, 0, None, 0, OTHER_IN, len(OTHER_IN), analog, None, None, other)
            try:
                card.read_digital(DIGITAL_IN, 25, digital)
                flags_any |= digital.astype(bool)
            except HILError as e:
                report["digital_read_error"] = e.get_error_message()
            samples.append(np.concatenate([other, analog]).copy())
        s = np.array(samples)
        dt = np.diff(stamps)
        report["timing"] = {"samples": len(s), "dt_max_ms": float(dt.max() * 1e3),
                            "jitter_pct": float(dt.std() / dt.mean() * 100)}
        med = np.median(s[:, 0:5], axis=0)
        bad = np.any(np.abs(s[:, 0:5] - med) > CONSISTENCY_TOL, axis=1)
        report["consistency"] = {
            "position_samples_deviating_frac": float(bad.mean()),
            "consistent": bool(not bad.any()),
            "note": "if not consistent: set COMx Latency Timer to 2 ms and replug USB; do NOT command motion",
        }
        raw = med
        joint = raw[:4] - THETA_BIAS_W - ACT_BIAS_W
        report["joints"] = {
            j: {"raw_rad": float(raw[i]), "raw_std": float(s[:, i].std()),
                "pal_joint_rad": float(joint[i]), "pal_joint_deg": float(np.degrees(joint[i])),
                "within_pal_limits": bool(PAL_MIN[i] <= joint[i] <= PAL_MAX[i]),
                "vel_absmax": float(np.abs(s[:, 5 + i]).max()), "temp_C": float(np.median(s[:, 10 + i])),
                ("load_pct" if i == 0 else "current_A"): float(s[:, 15 + i].mean())}
            for i, j in enumerate(JOINTS[:4])}
        g = raw[4]
        report["gripper"] = {"raw_rad": float(g), "temp_C": float(np.median(s[:, 14])),
                             "load_pct": float(s[:, 19].mean()),
                             "pct_if_write_gripper_position_map": float((g - np.pi + 0.9) / -1.8),
                             "pct_if_read_write_std_map": float((g - np.pi + 0.9) / 1.68)}
        report["error_flags_set"] = [f"{JOINTS[i // 5]}:{ERROR_NAMES[i % 5]}"
                                     for i in range(25) if flags_any[i]]
        report["all_finite"] = bool(np.all(np.isfinite(s)))
        report["analog_all_nan"] = bool(np.all(np.isnan(s[:, 15:20])))
    finally:
        card.close()
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="0", help="COM port number, e.g. 6 for COM6")
    sys.exit(main(ap.parse_args().id))
