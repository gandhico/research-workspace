"""Find the Cube's AHRS_ORIENTATION for the Omnidrone's 6DoF (mixer) frame from gravity alone.

The mixer defines the ArduPilot body frame (FRD) in twin coordinates:
    forward = twin +z,  right = twin -y,  down = twin +x.
Rest the cube on three faces; at rest the accelerometer reads minus gravity, so each
pose fixes one known direction in FRD:

    pose     face on the floor                      rotors on that face   expected accel (FRD)
    LEVEL    BOTTOM = twin +x (hover attitude)      5, 6, 7, 8            (0, 0, -g)
    NOSE     FORWARD = twin +z                      2, 4, 6, 8            (-g, 0, 0)
    RIGHT    RIGHT = twin -y                        1, 2, 5, 6            (0, -g, 0)

The board->FRD rotation is the least-squares (Wahba/SVD) fit.  ArduPilot applies a custom
rotation as v_body = R(roll, pitch, yaw) v_board with R built by Matrix3::from_euler (321 order;
AP_CustomRotations.cpp, Copter-4.7.1), so the result is written as Custom 1:
CUST_ROT_ENABLE=1, CUST_ROT1_ROLL/PITCH/YAW, AHRS_ORIENTATION=101.

If AHRS_ORIENTATION is already set, the IMU data is already rotated: the tool then reports the
residual, which must be ~0 deg for the setting to be correct.

    python board_orientation.py           # Mission Planner and the bridge must be closed (UDP 14550)
"""
from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
import sys
import time

import numpy as np
from pymavlink import mavutil

from ap_link import connect

HERE = Path(__file__).resolve().parent
POSES = (("LEVEL", "BOTTOM face (twin +x; rotors 5,6,7,8) on the floor = hover attitude", (0.0, 0.0, -1.0)),
         ("NOSE", "FORWARD face (twin +z; rotors 2,4,6,8) on the floor", (-1.0, 0.0, 0.0)),
         ("RIGHT", "RIGHT face (twin -y; rotors 1,2,5,6) on the floor", (0.0, -1.0, 0.0)))


def wahba(sources, targets):
    """Rotation R minimizing sum |t - R s|^2 for unit vectors."""
    b = sum(np.outer(t, s) for s, t in zip(sources, targets))
    u, _, vt = np.linalg.svd(b)
    d = np.sign(np.linalg.det(u @ vt))
    return u @ np.diag([1.0, 1.0, d]) @ vt


def euler321(r):
    """(roll, pitch, yaw) [deg] with r = Rz(yaw) Ry(pitch) Rx(roll)."""
    return (math.degrees(math.atan2(r[2, 1], r[2, 2])), math.degrees(math.asin(max(-1.0, min(1.0, -r[2, 0])))),
            math.degrees(math.atan2(r[1, 0], r[0, 0])))


def from_euler(roll, pitch, yaw):
    cr, sr, cp, sp, cy, sy = (f(math.radians(a)) for a in (roll, pitch, yaw) for f in (math.cos, math.sin))
    return np.array([[cp * cy, sr * sp * cy - cr * sy, cr * sp * cy + sr * sy],
                     [cp * sy, sr * sp * sy + cr * cy, cr * sp * sy - sr * cy],
                     [-sp, sr * cp, cr * cp]])


def standard_orientation(roll, pitch, yaw):
    """AHRS_ORIENTATION value for single-axis rotations, else None.

    Only unambiguous cases (one rotation axis) are mapped: their meaning does not depend on the
    composition order of the label (Yaw45..Yaw315 = 1..7, Roll180 = 8, Pitch180 = 12, Roll90 = 16,
    Roll270 = 20, Pitch90 = 24, Pitch270 = 25; Copter-4.7.1 AHRS_ORIENTATION value list).
    """
    r, p, y = (round(a) % 360 for a in (roll, pitch, yaw))
    if r == 0 and p == 0 and y % 45 == 0:
        return y // 45
    return {(180, 0, 0): 8, (0, 180, 0): 12, (90, 0, 0): 16, (270, 0, 0): 20,
            (0, 90, 0): 24, (0, 270, 0): 25}.get((r, p, y))


def angle_deg(r):
    return math.degrees(math.acos(max(-1.0, min(1.0, (np.trace(r) - 1) / 2))))


def read_param(link, name):
    link.tx.mav.param_request_read_send(link.target_system, link.target_component, name.encode(), -1)
    end = time.time() + 3
    while time.time() < end:
        m = link.rx.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
        if m is not None and (m.param_id.decode() if isinstance(m.param_id, bytes) else m.param_id).rstrip("\x00") == name:
            return m.param_value
    return None


def drain(link):
    """Discard every message already buffered (they were sent while the vehicle was being moved)."""
    count = 0
    while link.rx.recv_match(blocking=False) is not None:
        count += 1
    return count


def collect(link, seconds=3.0, settle_s=1.0):
    # 2026-11-04 fix: the first version averaged RAW_IMU messages that had queued up in the UDP
    # buffer while the operator was turning the cube (622 samples in a 3 s window instead of ~60),
    # mixing the previous pose into the new one.  Settle, drop the backlog, then measure.
    time.sleep(settle_s)
    drain(link)
    samples = []
    end = time.time() + seconds
    while time.time() < end:
        m = link.rx.recv_match(type="RAW_IMU", blocking=True, timeout=0.5)
        if m is not None:
            samples.append((m.xacc, m.yacc, m.zacc))          # milli-g, after AHRS_ORIENTATION
    return np.array(samples, dtype=float)


def main():
    link = connect()
    try:
        orientation = read_param(link, "AHRS_ORIENTATION")
        custom = [read_param(link, n) for n in ("CUST_ROT_ENABLE", "CUST_ROT1_ROLL", "CUST_ROT1_PITCH", "CUST_ROT1_YAW")]
        print(f"AHRS_ORIENTATION={orientation}, CUST_ROT_ENABLE/ROLL/PITCH/YAW={custom}")
        link.tx.mav.command_long_send(link.target_system, link.target_component,
                                      mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                                      mavutil.mavlink.MAVLINK_MSG_ID_RAW_IMU, 50000, 0, 0, 0, 0, 0)
        sources, targets = [], []
        for name, text, expected in POSES:
            input(f"\n{name}: put the vehicle with its {text}. Hands off, then press Enter...")
            data = collect(link)
            if len(data) < 20:
                sys.exit("no RAW_IMU data received")
            mean, spread = data.mean(0), data.std(0).max()
            norm = np.linalg.norm(mean)
            print(f"   accel {np.round(mean).astype(int)} mg, |a| {norm:.0f} mg, noise {spread:.0f} mg, "
                  f"{len(data)} samples in 3 s")
            if spread > 30 or not 900 < norm < 1100:
                sys.exit("   not still (or accelerometer uncalibrated): repeat this pose")
            sources.append(mean / norm)
            targets.append(np.asarray(expected))
    finally:
        link.close()

    r = wahba(sources, targets)                               # board(as reported) -> FRD
    fit = [math.degrees(math.acos(max(-1.0, min(1.0, float(t @ (r @ s)))))) for s, t in zip(sources, targets)]
    print(f"\nfit error per pose [deg]: {[round(f, 2) for f in fit]}")
    if max(fit) > 5:
        sys.exit("poses disagree by more than 5 deg: check the face labels and repeat")
    residual = angle_deg(r)
    if orientation not in (None, 0):
        print(f"AHRS_ORIENTATION is already {orientation:.0f}: residual rotation {residual:.1f} deg "
              + ("-> CORRECT (< 3 deg)" if residual < 3 else "-> WRONG, set AHRS_ORIENTATION 0, reboot, rerun"))
        return
    if residual < 3:
        print("The board is already aligned with the mixer frame: keep AHRS_ORIENTATION 0.")
        return
    roll, pitch, yaw = euler321(r)
    if angle_deg(from_euler(roll, pitch, yaw).T @ r) > 0.01:
        sys.exit("internal Euler conversion check failed")
    snapped = tuple(round(a / 90.0) * 90.0 for a in (roll, pitch, yaw))
    if angle_deg(from_euler(*snapped).T @ r) < 5:
        roll, pitch, yaw = (a + 0.0 for a in snapped)       # board on a cube face: use exact 90-deg angles
    out = HERE / "config" / "stage3_board_orientation.param"
    standard = standard_orientation(roll, pitch, yaw)
    if standard is not None and angle_deg(from_euler(roll, pitch, yaw).T @ r) < 5:
        out.write_text("\n".join([
            f"# Omnidrone board orientation, measured {datetime.now().isoformat(timespec='seconds')} by board_orientation.py",
            f"# board->FRD = roll {roll:.0f}, pitch {pitch:.0f}, yaw {yaw:.0f} deg; per-pose fit "
            f"{[round(f, 2) for f in fit]} deg -> standard rotation, no custom rotation needed.",
            "# Load: python ap_param_load.py config\\stage3_board_orientation.param, reboot,",
            "# then rerun board_orientation.py (must say CORRECT), then accel calibration + level.",
            f"AHRS_ORIENTATION,{standard}", ""]), encoding="utf-8")
        print(f"board -> FRD: roll {roll:.0f}, pitch {pitch:.0f}, yaw {yaw:.0f} deg = standard AHRS_ORIENTATION {standard}")
        print(f"wrote {out}")
        return
    out.write_text("\n".join([
        f"# Omnidrone board orientation, measured {datetime.now().isoformat(timespec='seconds')} by board_orientation.py",
        f"# board->FRD rotation {residual:.1f} deg; per-pose fit {[round(f, 2) for f in fit]} deg",
        "# Load CUST_ROT_ENABLE first, reboot (CUST_ROT1_* then appear), load again, reboot,",
        "# then rerun board_orientation.py: it must report a residual < 3 deg. Then calibrate accel + level.",
        "CUST_ROT_ENABLE,1",
        f"CUST_ROT1_ROLL,{roll:.2f}", f"CUST_ROT1_PITCH,{pitch:.2f}", f"CUST_ROT1_YAW,{yaw:.2f}",
        "AHRS_ORIENTATION,101", ""]), encoding="utf-8")
    print(f"board -> FRD: roll {roll:.2f}, pitch {pitch:.2f}, yaw {yaw:.2f} deg (321)")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
