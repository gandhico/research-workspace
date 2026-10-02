"""QArm Mini raw <-> joint-frame maps. Use these instead of PAL's for this unit.

Joints: PAL's bias map (pal/products/qarm_mini.py), checked against the physical rest
configuration on 2026-09-27 (yaw -9.1, shoulder +191.6, elbow -139.8, wrist +7.6 deg,
matching Quanser's "Rest Configuration").

Gripper: MEASURED on this unit on 2026-09-27 (torque off, moved by hand, read-only probe):
fully open raw 1.6659 rad, fully closed raw 4.0819 rad. Raw increases as it closes.
PAL's maps are wrong for this unit: write_gripper_position (x -1.8) has the wrong
direction; read_write_std (x +1.68) reads open as -0.34 and closed as 1.10.
"""
from __future__ import annotations

import numpy as np

THETA_BIAS = np.array([0.0, -np.pi / 2, np.pi / 2, -np.pi / 2])
ACTUATOR_BIAS = np.array([np.pi - 1.178, np.pi + 0.1834, np.pi - 0.1834 + 0.07, np.pi])
JOINT_MIN = np.array([-10 * np.pi / 18, -np.pi / 6, -5 * np.pi / 6, -np.pi / 10])
JOINT_MAX = np.array([4 * np.pi / 3, 13 * np.pi / 12, np.pi / 6, 8 * np.pi / 9])

GRIPPER_RAW_OPEN = 1.6659031356438063
GRIPPER_RAW_CLOSED = 4.0819228765636915
# Commandable range. The servo firmware REJECTS goals more open than about raw 2.24-2.27
# (gripper sweep 2026-09-27: 0.25 / raw 2.27 accepted, 0.15 / raw 2.03 rejected with no
# motion and zero load; this matches PAL's open = pi - 0.9 = 2.2416). Hand-opening reaches
# raw 1.666, beyond what the servo may drive. 0.95 stays off the closed stop.
GRIPPER_CMD_MIN, GRIPPER_CMD_MAX = 0.27, 0.95


# Measured rest configuration of this unit (probe after gripper sweep, 2026-09-27), elbow
# clamped to the PAL limit. Demos end here so nothing is preloaded when torque drops.
REST_POSE = np.radians([-10.38, 190.15, -150.0, 20.92])


def raw_to_joint(raw4):
    return np.asarray(raw4, dtype=float) - THETA_BIAS - ACTUATOR_BIAS


# The servo firmware silently REJECTS goals at/just beyond the PAL limits (it keeps the old goal).
# Demo 20260927_204210: elbow -150.0 deg (= PAL min -5pi/6) rejected, -149.6 deg accepted, which left
# the elbow stuck at -90 deg on "back to rest". Commands are therefore clamped this far inside.
JOINT_CMD_MARGIN = 0.02  # rad (~1.1 deg)


def joint_to_raw(q4):
    q = np.clip(np.asarray(q4, dtype=float), JOINT_MIN + JOINT_CMD_MARGIN, JOINT_MAX - JOINT_CMD_MARGIN)
    return q + THETA_BIAS + ACTUATOR_BIAS


def raw_to_gripper(raw):
    return (float(raw) - GRIPPER_RAW_OPEN) / (GRIPPER_RAW_CLOSED - GRIPPER_RAW_OPEN)


def gripper_to_raw(frac):
    f = float(np.clip(frac, GRIPPER_CMD_MIN, GRIPPER_CMD_MAX))
    return GRIPPER_RAW_OPEN + f * (GRIPPER_RAW_CLOSED - GRIPPER_RAW_OPEN)
