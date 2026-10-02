# 01 — Platform & I/O (Ref 1)

Status: **Phase 4 complete.** Code: `aero2/io/`. Constants: `config.sensors`,
`config.params`. Validated against the migrated M1 logs (no device):
`python runners/run_state_estimation.py`.

## Encoders — `io/encoders.py`
`θ = 2π·n_θ/2880` (pitch), `ψ = 2π·n_ψ/4096` (yaw). `pitch_counts/yaw_counts` invert;
`quantize_pitch/quantize_yaw` snap a continuous angle to the nearest tick (used to
emulate encoder quantization offline). Resolutions: pitch `2.18e-3`, yaw `1.53e-3` rad.

## IMU calibration — `io/imu_calibration.py` (Ref 1, Eqs. 6-8, 22, 46-48)
Stationary defaults in `config.sensors`. `correct_rate(ω, b) = ω − b`.
`ImuCalibration.pitch_rate/yaw_rate` return the bias-corrected y/z gyro.
`estimate_bias/estimate_noise_std` reproduce the M1 calibration from a log.

**Validation (reproduced exactly from `M1_aero2_02_imu_noise_bias.csv`, N=1414):**
gyro bias `[0.0098555, −0.0179735, −0.0071804]`, noise `[0.00143607, 0.00156495,
0.00168013]`, accel mean `[−0.585289, −0.205638, 9.829762]` — all match `config.sensors`.
`correct_rate` reproduces the logged `*_corrected` columns to `max|diff| = 4.8e-9`.

## State estimation — `io/state_estimation.py` (Ref 1, Eqs. 23-24, 45, 49)
`Aero2StateEstimator(rate_source=...)` returns `[θ, θ̇, ψ, ψ̇]`:
- `"gyro"` (preferred): `θ̇ = ω_y − b_y`, `ψ̇ = ω_z − b_z` (smooth).
- `"encoder"`: finite difference `Δθ/Ts`, `Δψ/Ts` (quantized, spiky).
Falls back to the encoder derivative if no raw gyro is present.
`PitchStateEstimator` gives the two-state `x_θ = [θ, θ̇]` (Eq. 49). Selectable via
`io.make_estimator("aero2"|"pitch"|"passthrough")`.

**Validation (from `M1_aero2_06_..._state_estimation.csv`, N=2688, 200 Hz):**
bias-corrected y-gyro pitch rate `RMS(Δ)=0.0022` vs encoder `Δθ/Ts` `RMS(Δ)=0.1315`
rad/s → **gyro is 58.6× smoother**, so it is preferred for feedback (Ref 1, Fig. 34).

## Sampling / ZOH — `io/sampling.py` (Ref 1, Eqs. 1-2, 25)
`ZeroOrderHold` holds `u_d(k)` over `[kTs,(k+1)Ts)`; `zoh_resample` replays a held
input schedule; `ts_from_fs`. The `OfflineBackend` already realizes ZOH (holds the
last applied command between reads). Rates: 100 Hz (sampling/IMU), 200 Hz (state est).

## Log loading — `io/logs.py`
`load_log(path)` → `{column: np.ndarray}`; `find_log(name)` locates a migrated CSV
under `data/raw_logs/` (see `data/raw_logs/MANIFEST.md`).

## What works / what doesn't
The full Ref-1 chain (sampling → bias/noise → ZOH → state estimation) reproduces the
logged constants and the gyro-vs-encoder result exactly from recorded data. Live
hardware acquisition (`DirectHilAero2IO`) is Phase 6 and needs the Quanser HIL SDK
(not installed here) + the device.
