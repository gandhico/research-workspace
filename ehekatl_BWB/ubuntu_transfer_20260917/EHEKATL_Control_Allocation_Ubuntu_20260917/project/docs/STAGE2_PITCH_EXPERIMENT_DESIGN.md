# Stage 2 pitch-identification experiment design

Status: design pilot PASS; repeated design frozen for two training and two
held-out validation runs.

## Purpose and operating condition

Identify the local longitudinal response around the same clean `stage 2m`
condition used for the accepted roll datasets: EHEKATL BWB G33 scale model,
X-Plane 12.4.3-r2, 14 lb / 6.350295 kg, zero modeled fuel, Manual/Clear weather,
no failures, automation off, approximately 1700 m, 39 KIAS, and 0.0235
throttle.

The original backstepping equations and gains remain active. Both joystick axes
are temporarily owned so the trim-relative stabilizing commands persist. The
excitation is added only to logical pitch / legacy CTRL0. Total pitch ratio is
the realized plant input; sent CTRL0 and excitation remain audit signals.

## Frozen pitch excitation

```text
waveform                 tapered five-frequency multisine
axis                     logical pitch / legacy CTRL0
sample rate              10 Hz
total run                60 s
baseline before input    10 s
excitation window        40 s
post-input recovery      10 s
taper                    2 s raised cosine at each edge
peak bound               0.003 normalized command
frequencies              0.10, 0.20, 0.35, 0.55, 0.80 Hz
phases                   0, 1.256637, 2.513274, 3.769911, 5.026548 rad
total command limit      0.5
```

The amplitude is not permission to increase authority after an unfavorable
result. It matches the bounded roll design and remains below the separately
verified +0.005 pitch-authority increment.

## Frozen gates and evidence allocation

The unchanged latch disables excitation permanently if absolute pitch or roll
exceeds 10 degrees or any body rate exceeds 20 deg/s; backstepping remains
active. A run fails for any latch/abort, blocked start, manual input, missing
rich measurement, saturation, completeness below 99 percent, gap above 0.25 s,
or failure to restore either owned axis.

The observe-only run validates waveform, metadata, timing, and routing only.
The first engaged run is a design pilot and is excluded from model fitting. If
its safety, realized-input, and spectral-informativeness gates pass, freeze and
collect two training runs followed by two held-out validation runs from fresh
reloads. Held-out responses cannot influence model order, delay, state choice,
filtering, or regularization.

## Required order

1. Run `scripts/run_stage2_pitch_id_observe.sh` and audit the saved log.
2. Reload the clean `stage 2m` situation and confirm the frozen start gates.
3. Run exactly one pilot with `scripts/run_stage2_pitch_id.sh`.
4. Review safety, completeness, realized-input fidelity, and response spectra.
5. Only after pilot PASS, collect two training and two held-out validation runs.
