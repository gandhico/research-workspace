# Omnicopter progressive mission results

Controller: unchanged hover PD (position 4/3.6, attitude 16/7.2), moving pose references, ideal state feedback. Model and inputs unchanged. Simulation only.

Pass criteria were set before the runs. A failed mission stops escalation; skipped missions have not been validated.

| Stage | Mission | Result | Peak position error (cm) | Peak attitude error (deg) | Peak input (N) | Saturated (%) | Actual signed turn (deg) |
|---|---|---|---:|---:|---:|---:|---:|
| 0 | hover | pass | 0.00 | 0.00 | 7.320 | 0.000 | - |
| 0 | quaternion_sign | pass | 0.00 | 0.00 | 7.320 | 0.000 | - |
| 1 | translate_x | pass | 6.67 | 0.00 | 7.340 | 0.000 | - |
| 1 | translate_y | pass | 6.67 | 0.00 | 7.328 | 0.000 | - |
| 1 | translate_z | pass | 5.33 | 0.00 | 7.341 | 0.000 | - |
| 2 | attitude_x_15 | pass | 0.02 | 3.07 | 7.598 | 0.000 | - |
| 2 | attitude_y_15 | pass | 0.02 | 3.07 | 8.398 | 0.000 | - |
| 2 | attitude_z_15 | pass | 0.01 | 3.07 | 7.324 | 0.000 | - |
| 3 | attitude_x_45 | pass | 0.03 | 4.71 | 7.601 | 0.000 | - |
| 3 | attitude_y_45 | pass | 0.03 | 4.71 | 9.052 | 0.000 | - |
| 3 | attitude_y_90 | pass | 0.04 | 6.31 | 9.063 | 0.000 | - |
| 3 | attitude_x_180 | pass | 0.04 | 7.58 | 7.642 | 0.000 | - |
| 4 | yaw_360 | pass | 0.02 | 8.43 | 7.322 | 0.000 | 360.00 |
| 4 | yaw_minus_360 | pass | 0.02 | 8.43 | 7.322 | 0.000 | -360.00 |
| 4 | spin_x_360 | pass | 0.04 | 6.33 | 7.644 | 0.000 | 360.00 |
| 4 | spin_y_360 | pass | 0.04 | 6.33 | 9.134 | 0.000 | 360.00 |
| 5 | circle | pass | 6.51 | 0.00 | 7.336 | 0.000 | - |
| 5 | figure_eight | pass | 7.78 | 0.00 | 7.327 | 0.000 | - |
| 5 | helix | pass | 4.13 | 0.00 | 7.328 | 0.000 | - |
| 5 | circle_yaw_360 | pass | 4.39 | 6.33 | 7.320 | 0.000 | 360.00 |
| 6 | hover_push | pass | 7.65 | 2.64 | 7.802 | 0.000 | - |
| 6 | circle_yaw_push | pass | 9.91 | 8.12 | 8.036 | 0.000 | 360.00 |
| 7 | yaw_360_24s | pass | 0.03 | 12.65 | 7.323 | 0.000 | 360.00 |
| 7 | yaw_360_12s | fail | 0.05 | 25.23 | 7.330 | 0.000 | 360.00 |
| 7 | yaw_360_6s | skipped | - | - | - | - | - |

## Gate failures

- yaw_360_12s: gates ['peak_attitude_error_deg', 'rotation_progress_peak_error_deg']; abort None.

![Campaign summary](campaign_summary.png)

![Actual rotation progress](rotation_progress.png)

## Interpretation

A full turn is checked using signed accumulated quaternion increments as well as attitude error. Equivalent start/end orientations alone do not count as success.

The pose-only PD damps absolute velocity and angular rate, so moving references produce tracking lag. A quality-gate failure may occur without saturation or loss of stability. Inspect allocation residuals and saturation before attributing a failure to actuator authority.

These ideal-model results do not validate hardware or unmodeled motor/estimator/communication dynamics.
