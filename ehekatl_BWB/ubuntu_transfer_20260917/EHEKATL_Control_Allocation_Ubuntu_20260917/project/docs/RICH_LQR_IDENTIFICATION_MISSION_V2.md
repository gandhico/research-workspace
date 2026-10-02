# Rich multi-regime LQR identification mission

Purpose: obtain the evidence needed for a publishable LQR controller for the
EHEKATL BWB scale aircraft while preserving the already published backstepping
controller as the nonlinear/recovery benchmark.

This is an offline mission design. It does not replace the existing Stage-1/2
evidence and does not authorize a flight command until each maneuver's
observe-only and safety gates are frozen.

## Publication objective

The target claim is not that LQR dominates nonlinear backstepping globally. The
target claim is:

> A delay-aware, regime-dependent LQR designed from rich flight identification
> data provides repeatable local rate/attitude control in declared operating
> envelopes, while backstepping remains the recovery benchmark for large
> nonlinear disturbances.

The paper must report both successful LQR results and the regimes/conditions in
which the linear model is inadequate.

## Frozen operating-condition matrix for campaign design

Start with six regimes, each from a fresh saved situation:

| ID | Altitude | IAS | Role |
|---|---:|---:|---|
| R1 | 1400 m | 32 kt | low dynamic pressure |
| R2 | 1400 m | 39 kt | low-altitude nominal |
| R3 | 1700 m | 39 kt | existing reference condition |
| R4 | 1700 m | 48 kt | higher effectiveness |
| R5 | 2000 m | 32 kt | altitude sensitivity |
| R6 | 2000 m | 48 kt | combined variation |

The exact saved situation, throttle, weather, weight, failures, automation,
artificial-stability state, and initial attitude/rates must be recorded for
every regime. A regime is rejected if it cannot hold its start envelope long
enough for the baseline and excitation windows.

## Mission sequence per regime

For each regime, perform this sequence:

1. Observe-only availability/timing capture.
2. Controlled trim/state confirmation.
3. Two no-excitation engaged baselines from fresh reloads.
4. Two pitch-only excitation runs.
5. Two roll-only excitation runs.
6. One coupled pitch/roll excitation run only if both single-axis sets pass.
7. One small controlled recovery pulse with the published backstepping law.

Training and validation partitions are frozen separately at each regime. A
validation run cannot influence model order, state selection, delay, filtering,
Q/R selection, or gain scheduling.

## Excitation families

Use the same safety envelope and ownership architecture already verified, with
amplitude selected offline from the regime's model/signal-to-noise prediction:

```text
low-frequency multisine: 0.05, 0.10, 0.20, 0.35 Hz
mid-frequency multisine: 0.55, 0.80, 1.10 Hz when sample quality permits
transient pulse:         half-sine, 0.25--1.0 s duration
candidate amplitudes:    0.0002, 0.0005, 0.0010 normalized command
sample rate:             10 Hz minimum; retain measured timing and gaps
```

No amplitude is increased to overcome divergence. If signal-to-noise is poor,
the regime is marked uninformative and redesigned offline.

## Required rich measurements

Retain the existing rich logger and add/verify, where available:

- angle, body rates, and rate derivatives;
- AOA, sideslip, flight-path angle, IAS/TAS/Mach, dynamic pressure;
- local/body velocities and accelerations;
- aerodynamic moments and load factors;
- pilot/yoke commands, trim, total realized controls;
- elevator/aileron/rudder surface deflections and rates;
- artificial-stability/augmentation and control-ownership datarefs;
- automation, failures, mass, fuel, and configuration metadata.

Total control ratio is the plant input for identification, while sent commands
remain audit inputs. Surface and augmentation channels are needed to explain
why total control differs from the commanded perturbation.

## Model ladder

Fit in this order using training data only:

1. Local short-period/rate models at each regime.
2. Expanded longitudinal/lateral models with AOA, speed, and coupling states.
3. LPV/scheduled models with airspeed, dynamic pressure, altitude, and AOA as
   scheduling variables.
4. Gray-box nonlinear model only if local/LPV residuals remain systematic.

Accept a model only when it passes one-step, multi-step, frequency-response,
residual, delay, controllability, and held-out validation checks. Colored
residuals are reported, not hidden as white noise.

## LQR design ladder

For every accepted regime/model:

1. Design delay-aware inner-rate LQR.
2. Sweep coefficient, delay, actuator, and scheduling uncertainty.
3. Validate inner-rate loops independently.
4. Add slow outer attitude loops.
5. Validate attitude loops independently.
6. Interpolate/schedule gains only after neighboring regimes pass.
7. Compare against backstepping on matched disturbances.

The final implementation may be a scheduled LQR or a bounded LQR correction
around backstepping. The choice must be supported by held-out data, not made by
assumption.

## Paper evidence package

The campaign must produce:

- regime/configuration table;
- train/validation log manifest;
- excitation spectra and realized-input fidelity;
- local A/B matrices and uncertainty;
- LPV scheduling/interpolation error;
- delay and actuator characterization;
- Q/R, gains, poles, limits, and robustness;
- rate and attitude response statistics;
- matched LQR/backstepping comparisons;
- rejected runs and model-failure analysis;
- declared validated envelope and limitations;
- exact reproduction commands and software revision.

## Current status

The current six-regime mission is design-only. Existing near-trim Stage-2 logs
remain valid local evidence and are not discarded. The next authorized work is
offline dataref/mission implementation and regime-specific observe-only tooling;
no new LQR flight is authorized until the mission gates are frozen.
