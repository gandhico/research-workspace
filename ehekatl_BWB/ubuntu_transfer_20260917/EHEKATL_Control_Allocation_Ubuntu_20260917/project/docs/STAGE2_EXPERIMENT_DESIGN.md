# Stage 2 roll-identification experiment design

Status: software design frozen; observe-only X-Plane validation required before
the first engaged run.

## Operating condition

Use the clean saved `stage 2m` situation: EHEKATL BWB G33 scale model, X-Plane
12.4.3-r2, 14 lb / 6.350295 kg, zero modeled fuel, Manual/Clear weather, no
failures, automation off, approximately 1700 m, 39 KIAS, and 0.0235 throttle.

## Stabilizing controller

The original backstepping equations and gains remain unchanged. Logical roll is
routed through legacy CTRL1. Identification excitation is added after the
backstepping calculation and logged separately from both the baseline and final
commands.

## Frozen roll excitation

```text
waveform                 tapered five-frequency multisine
axis                     logical roll / legacy CTRL1
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

## Frozen safety and abort logic

The excitation latches off permanently if absolute pitch exceeds 10 degrees,
absolute roll exceeds 10 degrees, or any body rate exceeds 20 deg/s.
Backstepping remains active. Automatic excitation restart is prohibited.

An engaged run fails if it has any abort/latch, start-gate block, missing rich
measurement, command saturation, sample completeness below 99 percent, timing
gap above 0.25 s, or manual input.

## Evidence allocation

The first engaged run is a software/response pilot and cannot be used to fit the
final model. After its gate passes, freeze the repeated maneuver allocation
before collection: at least two training runs and two held-out validation runs.
Validation logs must not influence model structure, filtering, or parameter
selection.

## Required order

1. Run `scripts/run_stage2_roll_id_observe.sh`; it sends no controls.
2. Verify waveform timing, taper, amplitude, routing, complete fields, and zero
   backstepping-equation error.
3. Reload the clean saved situation.
4. Run exactly one pilot with `scripts/run_stage2_roll_id.sh`.
5. Review safety, timing, response amplitude, spectral content, and signal-to-
   noise before authorizing repeated training/validation runs.
