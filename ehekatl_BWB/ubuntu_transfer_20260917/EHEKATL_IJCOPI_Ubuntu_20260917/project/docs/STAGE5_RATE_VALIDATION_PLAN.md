# Stage 5 inner-rate validation plan

Frozen: 2026-07-12 after completion of pitch design pilots. Future confirmation
runs must not change these metrics or the pitch controller.

## Claim boundary

Stage 5 validates body-rate damping around the frozen local operating condition.
It does not require a zero-angle-feedback controller to restore attitude.
Attitude tracking and attitude return are Stage-6 claims.

The rate metric is referenced to the measured pre-pulse rate mean because small
sensor/trim bias is not a rate-damping error:

```text
delta_rate(t) = measured_rate(t) - mean(measured_rate for t < 10 s)
```

Pitch and roll attitude remain safety/envelope measurements and must be fully
reported, but final attitude offset is not a Stage-5 performance gate.

## Frozen pitch-rate maneuver

```text
controller                 frozen delay-aware pitch-rate LQR
angle feedback             exactly zero
other-axis stabilization   original roll backstepping
rate reference             zero
disturbance                +0.0002 normalized pitch half-sine
disturbance window         10.0--10.5 s
run                        30 s at 10 Hz
perturbation magnitude     <=0.003
perturbation slew          <=0.0005/sample
```

## Frozen per-run pitch acceptance criteria

- 300 samples, at least 99% completeness, maximum gap <=0.25 s.
- Start gate PASS and 100% engagement.
- No pause, replay, latch, abort, saturation, or ownership-restoration failure.
- Sent pitch input agrees with realized total pitch input at the expected
  one-sample lag.
- Peak post-pulse `|delta_Q| >= 0.008 deg/s` (measurable response).
- Final-five-second maximum `|delta_Q| <= 0.015 deg/s`.
- Final-five-second RMS `delta_Q / peak |delta_Q| <= 0.45`.
- Pitch/roll remain within 10 deg and all body rates remain within 20 deg/s.
- Final attitude offset, altitude, IAS, lateral coupling, and command use are
  reported even though attitude return is reserved for Stage 6.

The `0.015` and `0.45` thresholds were frozen using the completed design pilots
and model audit, including the revised-gain design pilot's persistent bounded
background oscillation. Those pilots are excluded from validation evidence.

## Evidence allocation

1. Collect two new pitch-rate confirmation runs from fresh clean `stage 2m`
   reloads. Both must pass every frozen criterion. They are held-out from any
   further pitch-rate gain or threshold changes.
2. Prepare roll-rate software offline using the frozen roll-rate gain and the
   same safety architecture.
3. Freeze the roll disturbance and response thresholds from roll model
   uncertainty before flight.
4. Pass roll observe-only, then one excluded roll design pilot.
5. Freeze roll implementation and collect two new held-out roll confirmation
   runs from fresh reloads. Both must pass.

Stage 5 passes only after both pitch confirmations and both roll confirmations
pass. A failure stops repeated collection and returns work offline without
widening limits or retrospectively changing that run's criteria.

## Paper outputs

For every accepted run report pre-pulse bias, peak rate perturbation, final
maximum/RMS rate perturbation, decay ratio, attitude drift, cross-axis rates,
altitude/IAS, command peak/RMS/slew, realized-input lag/correlation, timing,
safety flags, and ownership restoration. Retain rejected pilots in the paper's
methodology/failure-analysis record.
