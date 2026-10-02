# Rich identification mission

This document defines the intended evidence chain without authorizing a later
stage before its gate passes. The current stage remains Stage 1.

## Data objective

The final identification dataset must separate reference commands, stabilizing
backstepping commands, identification perturbations, final commands actually
sent, realized aircraft controls, and aircraft response. Every log must retain
timestamps, configuration metadata, engagement and saturation state, abort
reasons, and explicit units.

The state/response set includes position and attitude; P/Q/R and angular
accelerations; IAS, TAS, groundspeed and flight path; angle of attack and
sideslip; local- and body-axis velocities; local acceleration and load factors;
altitude and vertical speed; total forces/moments where available; mass, fuel,
air density and dynamic pressure; trim, flap and speedbrake configuration;
pilot and total control ratios; engine throttles; and automation state.

## Stage sequence

1. Three repeatable 60-second, 10 Hz engaged backstepping baselines at one
   frozen configuration.
2. Offline confirmation that an identification wrapper with zero perturbation
   is numerically identical to the baseline controller.
3. Observe-only and zero-perturbation X-Plane checks.
4. Small single-axis longitudinal maneuvers under backstepping stabilization.
5. Repeated longitudinal training and held-out validation maneuvers.
6. Small single-axis lateral-directional maneuvers under stabilization.
7. Repeated lateral training and held-out validation maneuvers.
8. Only after single-axis evidence passes, mutually distinguishable multi-axis
   maneuvers for coupling information.
9. Model structure selection, estimation, uncertainty analysis, residual tests,
   and independent prediction validation.
10. Discrete LQR synthesis, offline replay, inner-rate-loop tests, attitude-loop
    tests, combined control, and matched recovery comparison.

Excitation waveforms, amplitudes, frequency bands, slew limits, state envelope,
abort thresholds, and acceptance criteria will be frozen only after Stage 1
passes. No values in later stages may be selected merely to make a failed run
continue.

## Dataset partitioning

Maneuvers must be assigned to training or validation before model fitting.
Validation logs must never be used to choose model structure, tune filters, or
adjust parameters. Repeat runs are required so a favorable single realization
cannot be mistaken for repeatability.

## Recovery architecture

Identification perturbations will eventually be added to the stabilizing
backstepping output and logged independently. An abort removes and latches off
the perturbation while leaving backstepping available for recovery. Automatic
perturbation restart is prohibited.
