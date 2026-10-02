"""Phase 4 IO / state-estimation tests, validated against migrated M1 logs (Ref 1)."""
import math

import numpy as np
import pytest

from aero2.config import sensors
from aero2.execution.backend import Measurement
from aero2.io import encoders, find_log, load_log
from aero2.io.imu_calibration import ImuCalibration, correct_rate, estimate_bias
from aero2.io.sampling import ZeroOrderHold, zoh_resample
from aero2.io.state_estimation import Aero2StateEstimator, PitchStateEstimator


# --- encoders --------------------------------------------------------------
def test_encoder_resolution_and_roundtrip():
    assert encoders.PITCH_RESOLUTION_RAD == pytest.approx(2 * math.pi / 2880)
    assert encoders.YAW_RESOLUTION_RAD == pytest.approx(2 * math.pi / 4096)
    assert encoders.pitch_angle(2880) == pytest.approx(2 * math.pi)
    assert encoders.yaw_angle(4096) == pytest.approx(2 * math.pi)
    # quantization snaps to within half a tick
    q = encoders.quantize_pitch(0.123456)
    assert abs(q - 0.123456) <= encoders.PITCH_RESOLUTION_RAD


# --- IMU calibration / correction -----------------------------------------
def test_correct_rate_removes_bias():
    g = np.array([0.02, -0.01, 0.03])
    assert np.allclose(correct_rate(g, sensors.GYRO_BIAS), g - np.array(sensors.GYRO_BIAS))


def test_calibration_reproduces_logged_bias():
    log = load_log(find_log("M1_aero2_02_imu_noise_bias.csv"))
    gyro = np.column_stack([log["gyro_x"], log["gyro_y"], log["gyro_z"]])
    bias = estimate_bias(gyro)
    assert np.allclose(bias, sensors.GYRO_BIAS, atol=5e-4)         # reproduces Ref 1 Eqs. 10-12
    # bias correction reproduces the logged *_corrected columns (Eq. 22)
    logged = np.column_stack([log["gyro_x_corrected"], log["gyro_y_corrected"], log["gyro_z_corrected"]])
    assert np.allclose(correct_rate(gyro, sensors.GYRO_BIAS), logged, atol=1e-6)


def test_imu_pitch_yaw_rate_helpers():
    cal = ImuCalibration()
    g = np.array([0.0, 0.05, -0.03])
    assert cal.pitch_rate(g) == pytest.approx(0.05 - sensors.GYRO_BIAS[1])
    assert cal.yaw_rate(g) == pytest.approx(-0.03 - sensors.GYRO_BIAS[2])


# --- state estimation (gyro vs encoder switch) -----------------------------
def test_estimator_gyro_mode():
    est = Aero2StateEstimator(rate_source="gyro")
    m = Measurement(t=0.0, theta=0.1, psi=0.2, gyro=np.array([0.0, 0.05, -0.03]))
    x = est.estimate(m, 0.005)
    assert x[0] == 0.1 and x[2] == 0.2
    assert x[1] == pytest.approx(0.05 - sensors.GYRO_BIAS[1])
    assert x[3] == pytest.approx(-0.03 - sensors.GYRO_BIAS[2])


def test_estimator_encoder_mode_finite_diff():
    est = Aero2StateEstimator(rate_source="encoder")
    est.reset()
    assert est.estimate(Measurement(t=0.0, theta=0.0, psi=0.0), 0.005)[1] == 0.0  # first step
    x = est.estimate(Measurement(t=0.005, theta=0.01, psi=0.02), 0.005)
    assert x[1] == pytest.approx(2.0)      # 0.01/0.005
    assert x[3] == pytest.approx(4.0)      # 0.02/0.005


def test_estimator_gyro_falls_back_to_encoder():
    est = Aero2StateEstimator(rate_source="gyro")   # no gyro in measurement
    est.reset()
    est.estimate(Measurement(t=0.0, theta=0.0, psi=0.0), 0.005)
    x = est.estimate(Measurement(t=0.005, theta=0.01, psi=0.0), 0.005)
    assert x[1] == pytest.approx(2.0)


def test_pitch_state_estimator_two_state():
    est = PitchStateEstimator(rate_source="gyro")
    x = est.estimate(Measurement(t=0.0, theta=0.3, psi=0.0, gyro=np.array([0.0, 0.0, 0.0])), 0.005)
    assert x.shape == (2,) and x[0] == 0.3


# --- ZOH -------------------------------------------------------------------
def test_zero_order_hold():
    zoh = ZeroOrderHold(initial=0.0)
    assert zoh.value == 0.0
    zoh.update(1.5)
    assert zoh.value == 1.5
    held = zoh_resample([0.0, 0.004, 0.011], [0.0, 0.005, 0.010], [10.0, 20.0, 30.0])
    assert list(held) == [10.0, 10.0, 30.0]
