# EHEKATL XP12 Controller Progress Log

## Completed

1. Earlier work consolidated controllers in a combined bridge; the 2026-07-10
   cleanup separated the canonical paths into `backstepping/`, `pid/`, and
   `lqr/`.
2. Preserved the former bridge and compatibility material in `archive/`.
3. Added trim-biased LQR/damped attitude runner for X-Plane 12.
4. Added axis isolation for pitch-only, roll-only, and combined runs.
5. Added wait-and-reengage behavior for real-time operation:
   - The runner no longer exits when attitude is outside limits.
   - It logs `engaged=False` and re-engages after manual trim recovers the
     aircraft.
6. Added divergence supervision.
7. Added actuator command slew limiting.
8. Added pitch model identification script:
   - `lqr/identify_pitch_model.py`
9. Added open-loop excitation mode:
   - `--controller excite`
   - `--excite-kind prbs`
   - `--excite-amplitude`
   - `--excite-period`
10. Documented the real-time gain methodology and equations in:
    - `docs/REAL_TIME_GAIN_METHODOLOGY.md`

## Latest Pitch Log Review

Analyzed:

```text
logs/lqr_pitch_lqr_20260709_202936.csv
```

Summary:

```text
duration_s: 45.55
engaged_fraction: 0.741
pitch_min_deg: -10.14
pitch_max_deg: 15.41
pitch_rms_deg: 7.29
q_min_deg_s: -15.47
q_max_deg_s: 20.00
q_rms_deg_s: 6.02
elevator_delta_min: -0.025
elevator_delta_max: 0.025
elevator_saturation_fraction: 1.0
```

Preliminary first-order pitch-rate fit:

```text
q_dot = a q + b u_e
a = -0.475478 1/s
b = 526.268 deg/s^2/stick
RMS q_dot residual = 18.6193 deg/s^2
```

This fit is not final because the elevator input was saturated for all samples.
It is good enough to show that the correct next step is not more closed-loop
gain tuning. The next step is a small open-loop identification excitation around
manual trim.

## Next Required Experiment

Run a pitch identification excitation from trimmed, near-level flight:

```bash
python lqr/run_lqr_xp12.py \
  --duration 45 \
  --hz 20 \
  --controller excite \
  --mode attitude \
  --axis pitch \
  --rate-units deg_s \
  --routing legacy \
  --trim-source current \
  --trim-mode incremental \
  --pitch-sp 2 \
  --roll-sp 0 \
  --excite-amplitude 0.015 \
  --excite-period 1.5 \
  --excite-kind prbs \
  --stick-slew-rate 0.08 \
  --throttle -998 \
  --max-start-pitch-error 5 \
  --max-start-roll-error 8 \
  --max-abs-pitch 20 \
  --max-abs-roll 35 \
  --max-abs-rate 60 \
  --divergence-min-error 0 \
  --out logs/pitch_id_$(date +%Y%m%d_%H%M%S).csv
```

Then identify:

```bash
python lqr/identify_pitch_model.py \
  logs/pitch_id_YYYYMMDD_HHMMSS.csv
```

## Acceptance Criteria Before Lateral-Directional Work

Pitch should meet these before moving to lateral-directional dynamics:

```text
elevator_saturation_fraction < 0.25 during identification
pitch remains within safe envelope during excitation
identified b has repeatable sign and similar magnitude across at least 2 runs
closed-loop pitch-rate damping is non-oscillatory
outer pitch attitude hold does not produce sustained limit cycles
```
