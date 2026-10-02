"""Assert IMU bias/noise constants match Ref 1 (Eqs. 10-21) and references.py."""
import math

from aero2.config import references, sensors


def test_gyro_bias():
    assert sensors.GYRO_BIAS == (0.00985550, -0.01797350, -0.00718040)


def test_gyro_noise_std():
    assert sensors.GYRO_NOISE_STD == (0.00143607, 0.00156495, 0.00168013)


def test_accel_mean_and_noise():
    assert sensors.ACCEL_MEAN == (-0.58528933, -0.20563835, 9.82976163)
    assert sensors.ACCEL_NOISE_STD == (0.01954359, 0.02171578, 0.03740023)


def test_rate_axis_mapping():
    # y-axis -> pitch rate, z-axis -> yaw rate (gyro_z_corr)
    assert sensors.GYRO_AXIS_PITCH_RATE == 1
    assert sensors.GYRO_AXIS_YAW_RATE == 2


def test_reference_square_wave():
    assert references.A_THETA_DEG == 20.0 and references.A_PSI_DEG == 45.0
    assert references.F_THETA_HZ == 0.05 and references.F_PSI_HZ == 0.04
    assert references.A_THETA_RAD == math.radians(20.0)
    # square wave is bipolar about zero
    assert references.square_reference(0.0, 1.0, 0.05) == -1.0
