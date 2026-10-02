"""`StateEstimator` interface + a pass-through default (brief §5, §7).

The Application composes (Backend, Controller, StateEstimator). The estimator
turns a raw `Measurement` into the state vector the controller consumes.

Phase 1 ships only the interface and a trivial pass-through. The real Ref-1
estimator — bias-corrected gyro pitch rate vs. quantized finite-difference
encoder derivative, with a switch (Ref 1, Eqs. 23-24, 45, 49) — lands in Phase 4.
"""
from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

import numpy as np

from aero2.config import sensors
from aero2.execution.backend import Measurement
from aero2.io.imu_calibration import ImuCalibration


@runtime_checkable
class StateEstimator(Protocol):
    def reset(self) -> None: ...
    def estimate(self, meas: Measurement, dt: float) -> np.ndarray: ...


class PassThroughEstimator:
    """Trust the backend's reported angles/rates as the state.

    Adequate for the offline backend (which reports ground truth) and as a
    placeholder until the Ref-1 estimator is implemented.
    """

    name = "passthrough"

    def reset(self) -> None:
        pass

    def estimate(self, meas: Measurement, dt: float) -> np.ndarray:
        return meas.state()


def _finite_diff(x: float, x_prev: Optional[float], dt: float) -> float:
    """Quantized encoder derivative (Ref 1, Eqs. 24, 45) — spiky by construction."""
    if x_prev is None or dt <= 0.0:
        return 0.0
    return (x - x_prev) / dt


class Aero2StateEstimator:
    """Full state [theta, theta_dot, psi, psi_dot] from a `Measurement` (Ref 1).

    rate_source:
      "gyro"    theta_dot = gyro_y - b_y, psi_dot = gyro_z - b_z (Ref 1, Eq. 23) — preferred,
                smoother than the quantized encoder derivative.
      "encoder" finite difference of the encoder angle (Ref 1, Eqs. 24/45) — quantized/spiky.
    Falls back to the encoder derivative if no raw gyro is present in the Measurement.
    """

    name = "aero2"

    def __init__(self, rate_source: str = "gyro", calib: Optional[ImuCalibration] = None) -> None:
        if rate_source not in ("gyro", "encoder"):
            raise ValueError("rate_source must be 'gyro' or 'encoder'")
        self.rate_source = rate_source
        self.calib = calib or ImuCalibration()
        self._prev_theta: Optional[float] = None
        self._prev_psi: Optional[float] = None

    def reset(self) -> None:
        self._prev_theta = None
        self._prev_psi = None

    def estimate(self, meas: Measurement, dt: float) -> np.ndarray:
        theta, psi = float(meas.theta), float(meas.psi)
        if self.rate_source == "gyro" and meas.gyro is not None:
            theta_dot = self.calib.pitch_rate(meas.gyro)
            psi_dot = self.calib.yaw_rate(meas.gyro)
        else:
            theta_dot = _finite_diff(theta, self._prev_theta, dt)
            psi_dot = _finite_diff(psi, self._prev_psi, dt)
        self._prev_theta, self._prev_psi = theta, psi
        return np.array([theta, theta_dot, psi, psi_dot], dtype=float)


class PitchStateEstimator:
    """Two-state pitch estimator x_theta = [theta, theta_dot] (Ref 1, Eq. 49).

    `rate_source` switches between the bias-corrected y-gyro (preferred) and the
    quantized finite-difference encoder derivative.
    """

    name = "pitch"

    def __init__(self, rate_source: str = "gyro", calib: Optional[ImuCalibration] = None) -> None:
        self._est = Aero2StateEstimator(rate_source, calib)

    def reset(self) -> None:
        self._est.reset()

    def estimate(self, meas: Measurement, dt: float) -> np.ndarray:
        x = self._est.estimate(meas, dt)
        return x[:2]


__all__ = [
    "StateEstimator", "PassThroughEstimator",
    "Aero2StateEstimator", "PitchStateEstimator",
]
