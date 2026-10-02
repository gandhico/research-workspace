"""IMU bias / noise calibration constants (Ref 1, Module 1).

Stationary-estimate defaults from the M1 IMU characterization experiment
(fs = 100 Hz, N = 1414 samples, 15 s). Used as defaults for state estimation
and for injectable sensor models in the offline backend.

Provenance: Ref 1 "Sample-data real-time hardware tests on the Quanser Aero2
platform for digital control", Eqs. 10-21 and 46-49.

Axis order is (x, y, z). Key facts:
  * gyro y-axis (after bias removal) is the pitch-rate signal  (Ref 1 Eq. 23)
  * gyro z-axis (after bias removal) is the yaw-rate signal    -> gyro_z_corr,
    central to yaw identification (yaw angle is encoder-limited).
"""
from __future__ import annotations

# --- Gyroscope bias [rad/s] (Ref 1, Eqs. 10-12) ----------------------------
GYRO_BIAS = (0.00985550, -0.01797350, -0.00718040)      # (x, y, z)

# --- Gyroscope noise std [rad/s] (Ref 1, Eqs. 13-15) -----------------------
GYRO_NOISE_STD = (0.00143607, 0.00156495, 0.00168013)   # (x, y, z)

# --- Accelerometer mean [m/s^2] (Ref 1, Eqs. 16-18) ------------------------
ACCEL_MEAN = (-0.58528933, -0.20563835, 9.82976163)     # (x, y, z); z ~ g

# --- Accelerometer noise std [m/s^2] (Ref 1, Eqs. 19-21) -------------------
ACCEL_NOISE_STD = (0.01954359, 0.02171578, 0.03740023)  # (x, y, z)

# Convenience: index of the gyro axis used for each rate.
GYRO_AXIS_PITCH_RATE = 1   # y-axis (Ref 1 Eq. 23)
GYRO_AXIS_YAW_RATE = 2     # z-axis (gyro_z_corr)

__all__ = [
    "GYRO_BIAS", "GYRO_NOISE_STD", "ACCEL_MEAN", "ACCEL_NOISE_STD",
    "GYRO_AXIS_PITCH_RATE", "GYRO_AXIS_YAW_RATE",
]
