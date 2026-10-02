# data/raw_logs/ — migrated recorded logs (Phase 2)

Recorded hardware/QLabs CSV logs migrated from the original project
(`C:\02_Research\01_Robotics_Quanser\01_Aero2`). These are real logged data — no
device needed to develop/validate Phases 4-5 against them.

| Folder | Source | Use |
|---|---|---|
| `M1_computer_controlled/` | `aero2_clean/M1_.../data/raw/` | Ref 1: sampling, IMU bias/noise, ZOH, step, yaw chirp, **bias-corrected state estimation** (Phase 4) |
| `M2_nonparametric/` | `aero2_clean/M2_.../data/raw/` | Ref 2/3: step/impulse, linearity, correlation FRF, yaw authority (Phase 5) |
| `M3_parametric/` | `aero2_clean/M3_.../data/raw/` | Ref 3: pitch/yaw PRBS for ARX/DARX (Phase 5) |
| `hardware_closed_loop/` | `aero2lab_project/data/raw/*hw*` | hardware ID/validation/closed-loop logs (Phase 5/11) |

## Common schema (M1-M3)
`k, t, Ts, fs, theta, psi, motor0_speed, motor1_speed, motor0_current,
motor1_current, gyro_x, gyro_y, gyro_z, accel_x, accel_y, accel_z, u_left, u_right`
plus, where computed: `gyro_*_corrected`/`gyro_*_corr`, `accel_*_centered`,
`theta_dot_num`, `psi_dot_num`, `u_common`, `u_diff`.

Load with `aero2.io.load_log(path)` (or `find_log(filename)`). Validate the IMU
calibration + pitch-rate estimator with `python runners/run_state_estimation.py`.

> Not migrated: derived `results/*.csv` prediction logs (regeneratable) and the
> bulk QLabs intermediate logs. Add more as later phases need them.
