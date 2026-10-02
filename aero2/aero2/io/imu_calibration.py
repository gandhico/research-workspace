"""IMU bias / noise calibration and correction (Ref 1, Eqs. 6-8, 22, 46-48).

Stationary defaults live in config.sensors. `correct_rate` removes the bias
(omega_c = omega_meas - b). `estimate_*` reproduce the M1 calibration from a
stationary log so the constants are auditable, not just asserted.
"""
from __future__ import annotations

import numpy as np

from aero2.config import sensors


# --- stationary estimators (Ref 1, Eqs. 7-8) -------------------------------
def estimate_bias(samples) -> np.ndarray:
    """Sample mean per axis (Ref 1, Eq. 7)."""
    return np.mean(np.asarray(samples, dtype=float), axis=0)


def estimate_noise_std(samples) -> np.ndarray:
    """Sample std per axis, ddof=1 (Ref 1, Eq. 8)."""
    return np.std(np.asarray(samples, dtype=float), axis=0, ddof=1)


# --- correction (Ref 1, Eqs. 22, 46-48) ------------------------------------
def correct_rate(omega, bias=sensors.GYRO_BIAS) -> np.ndarray:
    """omega_c = omega_meas - b."""
    return np.asarray(omega, dtype=float) - np.asarray(bias, dtype=float)


class ImuCalibration:
    """Holds gyro/accel calibration and applies bias correction."""

    def __init__(
        self,
        gyro_bias=sensors.GYRO_BIAS,
        gyro_noise_std=sensors.GYRO_NOISE_STD,
        accel_mean=sensors.ACCEL_MEAN,
        accel_noise_std=sensors.ACCEL_NOISE_STD,
    ) -> None:
        self.gyro_bias = np.asarray(gyro_bias, dtype=float)
        self.gyro_noise_std = np.asarray(gyro_noise_std, dtype=float)
        self.accel_mean = np.asarray(accel_mean, dtype=float)
        self.accel_noise_std = np.asarray(accel_noise_std, dtype=float)

    def correct(self, gyro) -> np.ndarray:
        return np.asarray(gyro, dtype=float) - self.gyro_bias

    def pitch_rate(self, gyro) -> float:
        """Bias-corrected y-gyro = pitch rate (Ref 1, Eq. 23)."""
        return float(np.asarray(gyro, dtype=float)[sensors.GYRO_AXIS_PITCH_RATE] - self.gyro_bias[sensors.GYRO_AXIS_PITCH_RATE])

    def yaw_rate(self, gyro) -> float:
        """Bias-corrected z-gyro = yaw rate (gyro_z_corr)."""
        return float(np.asarray(gyro, dtype=float)[sensors.GYRO_AXIS_YAW_RATE] - self.gyro_bias[sensors.GYRO_AXIS_YAW_RATE])

    @classmethod
    def from_stationary(cls, gyro_samples, accel_samples) -> "ImuCalibration":
        """Estimate calibration from a stationary log (reproduces M1)."""
        return cls(
            gyro_bias=estimate_bias(gyro_samples),
            gyro_noise_std=estimate_noise_std(gyro_samples),
            accel_mean=estimate_bias(accel_samples),
            accel_noise_std=estimate_noise_std(accel_samples),
        )


__all__ = ["estimate_bias", "estimate_noise_std", "correct_rate", "ImuCalibration"]
