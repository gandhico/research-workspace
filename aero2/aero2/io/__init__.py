"""Sensing / I/O / state estimation (Ref 1): encoders, IMU calibration,
ZOH/sampling, log loading, and the state estimators."""
from __future__ import annotations

from aero2.io import encoders, sampling
from aero2.io.imu_calibration import ImuCalibration, correct_rate, estimate_bias, estimate_noise_std
from aero2.io.logs import RAW_LOGS, find_log, load_log
from aero2.io.sampling import ZeroOrderHold
from aero2.io.state_estimation import (
    Aero2StateEstimator,
    PassThroughEstimator,
    PitchStateEstimator,
    StateEstimator,
)

#: name -> StateEstimator factory (config-driven selection)
ESTIMATORS = {
    "passthrough": PassThroughEstimator,
    "aero2": Aero2StateEstimator,
    "pitch": PitchStateEstimator,
}


def make_estimator(name: str, **kwargs) -> StateEstimator:
    key = name.lower()
    if key not in ESTIMATORS:
        raise ValueError(f"unknown estimator: {name!r}; choose from {sorted(ESTIMATORS)}")
    return ESTIMATORS[key](**kwargs)


__all__ = [
    "encoders", "sampling", "ZeroOrderHold",
    "ImuCalibration", "correct_rate", "estimate_bias", "estimate_noise_std",
    "RAW_LOGS", "load_log", "find_log",
    "StateEstimator", "PassThroughEstimator", "Aero2StateEstimator", "PitchStateEstimator",
    "ESTIMATORS", "make_estimator",
]
