"""Platform definitions for the shared offline validation campaign."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


Disturbance = Callable[[float], np.ndarray]


@dataclass(frozen=True)
class PlatformConfig:
    key: str
    label: str
    description: str
    state_labels: tuple[str, ...]
    control_labels: tuple[str, ...]
    target_state_indices: tuple[int, ...]
    a_matrix: np.ndarray
    b_matrix: np.ndarray
    baseline_gain: np.ndarray
    control_limits: np.ndarray
    initial_state: np.ndarray
    dt: float
    disturbance: Disturbance
    safety_limits: dict[str, float]
    baseline_name: str


def _qcar_disturbance(t: float) -> np.ndarray:
    curve = 0.018 * np.sin(0.55 * t)
    if 6.0 <= t <= 9.0:
        curve += 0.035
    if 13.0 <= t <= 16.0:
        curve -= 0.030
    return np.array([curve, 0.020 * np.sin(0.35 * t)], dtype=float)


def _servo_disturbance(t: float) -> np.ndarray:
    d = np.zeros(4, dtype=float)
    d[1] = 0.22 * np.sin(0.45 * t) + 0.08 * np.sin(1.7 * t)
    d[3] = 0.04 * np.sin(0.80 * t)
    return d


def _aero_disturbance(t: float) -> np.ndarray:
    d = np.zeros(4, dtype=float)
    d[1] = 0.045 * np.sin(0.70 * t)
    d[3] = 0.060 * np.sin(0.35 * t)
    if 9.0 <= t <= 12.0:
        d[3] += 0.090
    return d


def _qdrone_disturbance(t: float) -> np.ndarray:
    d = np.zeros(8, dtype=float)
    d[1] = 0.050 * np.sin(0.75 * t)
    d[3] = -0.045 * np.sin(0.62 * t)
    d[5] = 0.035 * np.sin(0.40 * t)
    d[7] = 0.060 * np.sin(0.28 * t)
    if 10.0 <= t <= 14.0:
        d[7] -= 0.110
    return d


PLATFORM_CONFIGS: dict[str, PlatformConfig] = {
    "qcar": PlatformConfig(
        key="qcar",
        label="QCar/QCar2 lane following",
        description="Image-lane error and heading-error abstraction for QCar lane keeping.",
        state_labels=("lane_error", "heading_error"),
        control_labels=("steering",),
        target_state_indices=(0,),
        a_matrix=np.array([[-0.15, 0.95], [0.0, -0.85]], dtype=float),
        b_matrix=np.array([[0.0], [2.15]], dtype=float),
        baseline_gain=np.array([[1.15, 0.62]], dtype=float),
        control_limits=np.array([0.35], dtype=float),
        initial_state=np.array([0.18, -0.04], dtype=float),
        dt=0.01,
        disturbance=_qcar_disturbance,
        safety_limits={"max_steering_rad": 0.35, "max_throttle": 0.04},
        baseline_name="image-space PID/SMC-style steering baseline",
    ),
    "servo_pendulum": PlatformConfig(
        key="servo_pendulum",
        label="Qube Servo/Pendulum",
        description="Conservative near-upright servo/pendulum error abstraction with one motor-voltage command.",
        state_labels=("arm_error", "arm_rate", "pendulum_error", "pendulum_rate"),
        control_labels=("motor_voltage",),
        target_state_indices=(0, 2),
        a_matrix=np.array(
            [
                [0.0, 1.0, 0.0, 0.0],
                [-1.9, -0.45, 1.2, 0.08],
                [0.0, 0.0, 0.0, 1.0],
                [0.6, 0.08, -4.5, -0.55],
            ],
            dtype=float,
        ),
        b_matrix=np.array([[0.0], [5.0], [0.0], [2.0]], dtype=float),
        baseline_gain=np.array([[0.60, 0.20, 1.20, 0.35]], dtype=float),
        control_limits=np.array([5.0], dtype=float),
        initial_state=np.array([0.12, 0.0, 0.12, 0.0], dtype=float),
        dt=0.005,
        disturbance=_servo_disturbance,
        safety_limits={"max_voltage": 5.0, "max_arm_angle_rad": 1.2, "max_pendulum_angle_rad": 0.45},
        baseline_name="upright-balance PD/LQR-style motor-voltage baseline",
    ),
    "aero2": PlatformConfig(
        key="aero2",
        label="Aero2 two-DOF helicopter",
        description="Pitch/yaw error abstraction with cross-axis coupling.",
        state_labels=("pitch_error", "pitch_rate", "yaw_error", "yaw_rate"),
        control_labels=("pitch_voltage", "yaw_voltage"),
        target_state_indices=(0, 2),
        a_matrix=np.array(
            [
                [0.0, 1.0, 0.0, 0.0],
                [-2.2, -0.80, 0.22, 0.05],
                [0.0, 0.0, 0.0, 1.0],
                [0.12, 0.10, -0.95, -0.42],
            ],
            dtype=float,
        ),
        b_matrix=np.array([[0.0, 0.0], [2.6, 0.18], [0.0, 0.0], [0.15, 1.75]], dtype=float),
        baseline_gain=np.array([[1.35, 0.45, 0.10, 0.03], [0.08, 0.02, 1.05, 0.38]], dtype=float),
        control_limits=np.array([10.0, 10.0], dtype=float),
        initial_state=np.array([0.14, 0.0, -0.20, 0.0], dtype=float),
        dt=0.01,
        disturbance=_aero_disturbance,
        safety_limits={"max_voltage": 10.0, "max_pitch_rad": 0.65, "max_yaw_rate_rad_s": 2.0},
        baseline_name="2-axis PD baseline",
    ),
    "qdrone": PlatformConfig(
        key="qdrone",
        label="QDrone/QDrone2 attitude and altitude",
        description="Roll/pitch/yaw/altitude error abstraction for hover and waypoint hold.",
        state_labels=(
            "roll_error",
            "roll_rate",
            "pitch_error",
            "pitch_rate",
            "yaw_error",
            "yaw_rate",
            "z_error",
            "z_rate",
        ),
        control_labels=("roll_cmd", "pitch_cmd", "yaw_cmd", "thrust_delta"),
        target_state_indices=(0, 2, 4, 6),
        a_matrix=np.array(
            [
                [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [-3.2, -1.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, -3.0, -1.00, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, -1.6, -0.55, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.2, -0.85],
            ],
            dtype=float,
        ),
        b_matrix=np.array(
            [
                [0.0, 0.0, 0.0, 0.0],
                [3.8, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 3.8, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 2.3, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 2.8],
            ],
            dtype=float,
        ),
        baseline_gain=np.array(
            [
                [1.15, 0.38, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
                [0.00, 0.00, 1.12, 0.36, 0.00, 0.00, 0.00, 0.00],
                [0.00, 0.00, 0.00, 0.00, 0.72, 0.26, 0.00, 0.00],
                [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.05, 0.42],
            ],
            dtype=float,
        ),
        control_limits=np.array([0.35, 0.35, 0.35, 0.45], dtype=float),
        initial_state=np.array([0.10, 0.0, -0.11, 0.0, 0.16, 0.0, -0.22, 0.0], dtype=float),
        dt=0.01,
        disturbance=_qdrone_disturbance,
        safety_limits={"max_attitude_cmd": 0.35, "max_thrust_delta": 0.45, "min_altitude_m": 0.3},
        baseline_name="cascaded PD-style attitude/altitude baseline",
    ),
}


def get_platform_config(key: str) -> PlatformConfig:
    normalized = key.strip().lower().replace("-", "_")
    aliases = {
        "qcar2": "qcar",
        "qube": "servo_pendulum",
        "qube_servo": "servo_pendulum",
        "pendulum": "servo_pendulum",
        "qdrone2": "qdrone",
    }
    normalized = aliases.get(normalized, normalized)
    try:
        return PLATFORM_CONFIGS[normalized]
    except KeyError as exc:
        options = ", ".join(sorted(PLATFORM_CONFIGS))
        raise ValueError(f"unknown platform {key!r}; choose one of: {options}") from exc
