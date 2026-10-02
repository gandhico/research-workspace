"""run_state_estimation.py — reproduce Ref 1 calibration + pitch-rate comparison.

Validates the Phase-4 IO layer against the migrated M1 hardware logs (no device):
  1) estimate gyro bias / noise + accel mean from the stationary log and compare
     to the constants in config.sensors (Ref 1, Eqs. 7-8, 10-21);
  2) confirm the bias correction reproduces the logged *_corrected columns (Eq. 22);
  3) compare the bias-corrected y-gyro pitch rate with the quantized encoder
     finite-difference, showing the gyro is smoother (Ref 1, Eqs. 23-24, Fig. 34).
"""
from __future__ import annotations

import numpy as np

from aero2.config import sensors
from aero2.io import correct_rate, estimate_bias, estimate_noise_std, find_log, load_log

STATIONARY = "M1_aero2_02_imu_noise_bias.csv"
STATE_EST = "M1_aero2_06_bias_corrected_state_estimation.csv"


def _ok(a, b, tol):
    return "OK " if np.all(np.abs(np.asarray(a) - np.asarray(b)) <= tol) else "DIFF"


def reproduce_calibration() -> None:
    log = load_log(find_log(STATIONARY))
    gyro = np.column_stack([log["gyro_x"], log["gyro_y"], log["gyro_z"]])
    accel = np.column_stack([log["accel_x"], log["accel_y"], log["accel_z"]])

    bias = estimate_bias(gyro)
    noise = estimate_noise_std(gyro)
    amean = estimate_bias(accel)

    print(f"=== M1 IMU calibration ({STATIONARY}, N={len(gyro)}) ===")
    print(f"  gyro bias   est={np.round(bias,8)}  config={np.array(sensors.GYRO_BIAS)}  [{_ok(bias, sensors.GYRO_BIAS, 5e-4)}]")
    print(f"  gyro noise  est={np.round(noise,8)}  config={np.array(sensors.GYRO_NOISE_STD)}  [{_ok(noise, sensors.GYRO_NOISE_STD, 5e-4)}]")
    print(f"  accel mean  est={np.round(amean,6)}  config={np.array(sensors.ACCEL_MEAN)}  [{_ok(amean, sensors.ACCEL_MEAN, 5e-2)}]")

    # bias correction reproduces the logged corrected columns (Eq. 22)
    my_corr = correct_rate(gyro, sensors.GYRO_BIAS)
    logged = np.column_stack([log["gyro_x_corrected"], log["gyro_y_corrected"], log["gyro_z_corrected"]])
    print(f"  correct_rate vs logged *_corrected: max|diff|={np.max(np.abs(my_corr-logged)):.2e}  [{_ok(my_corr, logged, 1e-6)}]")


def compare_pitch_rate() -> None:
    log = load_log(find_log(STATE_EST))
    gyro_rate = log["gyro_y_corr"]          # bias-corrected y-gyro (Ref 1, Eq. 23)
    fd_rate = log["theta_dot_num"]          # encoder finite difference (Ref 1, Eqs. 24/45)

    # "spikiness": RMS of successive changes; the quantized encoder derivative jumps.
    gyro_jerk = float(np.sqrt(np.mean(np.diff(gyro_rate) ** 2)))
    fd_jerk = float(np.sqrt(np.mean(np.diff(fd_rate) ** 2)))
    print(f"\n=== Pitch-rate source comparison ({STATE_EST}, N={len(gyro_rate)}) ===")
    print(f"  gyro_y_corr   : std={np.std(gyro_rate):.4f}  RMS(d)={gyro_jerk:.4f} rad/s")
    print(f"  encoder dtheta/Ts : std={np.std(fd_rate):.4f}  RMS(d)={fd_jerk:.4f} rad/s")
    print(f"  -> gyro is {fd_jerk / max(gyro_jerk, 1e-9):.1f}x smoother (lower RMS(d)); "
          f"preferred for feedback (Ref 1).")


def main() -> None:
    reproduce_calibration()
    compare_pitch_rate()


if __name__ == "__main__":
    main()
