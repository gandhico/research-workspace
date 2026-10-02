"""Encoder counts <-> angles (Ref 1; Ref 3 setup / DirectHilAero2IO.read).

    theta = 2*pi*n_theta / 2880      (pitch)
    psi   = 2*pi*n_psi   / 4096      (yaw)

Counts-per-rev live in config.params. `quantize_*` snap a continuous angle to the
nearest encoder tick (used to emulate encoder quantization offline).
"""
from __future__ import annotations

import math

from aero2.config import params

PITCH_RESOLUTION_RAD: float = 2.0 * math.pi / params.PITCH_COUNTS_PER_REV
YAW_RESOLUTION_RAD: float = 2.0 * math.pi / params.YAW_COUNTS_PER_REV


def pitch_angle(counts) -> float:
    return 2.0 * math.pi * float(counts) / params.PITCH_COUNTS_PER_REV


def yaw_angle(counts) -> float:
    return 2.0 * math.pi * float(counts) / params.YAW_COUNTS_PER_REV


def pitch_counts(angle: float) -> int:
    return int(round(float(angle) * params.PITCH_COUNTS_PER_REV / (2.0 * math.pi)))


def yaw_counts(angle: float) -> int:
    return int(round(float(angle) * params.YAW_COUNTS_PER_REV / (2.0 * math.pi)))


def quantize_pitch(angle: float) -> float:
    return pitch_angle(pitch_counts(angle))


def quantize_yaw(angle: float) -> float:
    return yaw_angle(yaw_counts(angle))


__all__ = [
    "PITCH_RESOLUTION_RAD", "YAW_RESOLUTION_RAD",
    "pitch_angle", "yaw_angle", "pitch_counts", "yaw_counts",
    "quantize_pitch", "quantize_yaw",
]
