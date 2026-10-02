import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import qarm_mini_calibration as cal  # noqa: E402


def test_measured_gripper_endpoints():
    assert cal.raw_to_gripper(cal.GRIPPER_RAW_OPEN) == 0.0
    assert np.isclose(cal.raw_to_gripper(cal.GRIPPER_RAW_CLOSED), 1.0)
    # The rest-pose reading on 2026-09-27 (raw 4.0282) was nearly closed.
    assert 0.95 < cal.raw_to_gripper(4.0282) < 1.0


def test_gripper_open_command_is_inside_firmware_limit():
    # Sweep 2026-09-27: raw 2.27 accepted, raw 2.03 rejected by the servo firmware.
    assert cal.gripper_to_raw(0.0) >= 2.26


def test_gripper_commands_stay_off_end_stops():
    assert np.isclose(cal.raw_to_gripper(cal.gripper_to_raw(0.0)), cal.GRIPPER_CMD_MIN)
    assert np.isclose(cal.raw_to_gripper(cal.gripper_to_raw(1.0)), cal.GRIPPER_CMD_MAX)


def test_joint_roundtrip_and_rest_pose():
    q = np.array([0.0, np.pi / 2, -np.pi / 2, np.pi / 2])  # PAL HOME
    assert np.allclose(cal.raw_to_joint(cal.joint_to_raw(q)), q)
    rest_raw = [1.8055, 5.0974, 2.1598, 1.7043]  # probe 2026-09-27
    deg = np.degrees(cal.raw_to_joint(rest_raw))
    assert np.allclose(deg, [-9.06, 191.55, -139.75, 7.65], atol=0.05)


def test_joint_commands_are_clamped_inside_pal_limits():
    m = cal.JOINT_CMD_MARGIN
    q = cal.raw_to_joint(cal.joint_to_raw([10, 10, -10, 10]))
    assert np.allclose(q, [cal.JOINT_MAX[0] - m, cal.JOINT_MAX[1] - m, cal.JOINT_MIN[2] + m, cal.JOINT_MAX[3] - m])


def test_rest_elbow_command_is_inside_firmware_limit():
    # -149.6 deg accepted, -150.0 deg rejected by the elbow firmware (2026-09-27).
    elbow = cal.raw_to_joint(cal.joint_to_raw(cal.REST_POSE))[2]
    assert np.degrees(elbow) >= -149.6 + 0.5
