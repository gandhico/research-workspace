# MuJoCo-matched Hard45 shadow review, 13:13

Review date: 2026-08-28. No physical motor voltage was applied because both
runs used `armed=false`.

## Provenance

| Item | PD | PD-CMG |
|---|---|---|
| Run | `pd_dryrun_20260828_131330` | `pd-cmg_dryrun_20260828_131336` |
| Runner SHA-256 | `4d4d...b597` | `4d4d...b597` |
| Profile | MuJoCo quaternion PD | same PD plus CMG/PES |
| Neural integration | inactive | 10 x 0.5 ms per sample |
| Samples | 1000 | 1000 |
| Abort/deadline misses | none / 0 | none / 0 |

The experiment is a valid final-runner shadow test. The measured rig remained
at its tared zero orientation while the five-second Hard45 reference was
evaluated, so the reported 43.394 degree mean and 64.837 degree maximum errors
are reference magnitudes, not closed-loop performance.

## Actuator-feasibility diagnostic

| Metric | PD | PD-CMG |
|---|---:|---:|
| Raw baseline motor request | -67.929 to 78.956 V | same |
| Samples with at least one computed motor at 0 or 24 V | 100% | 100% |
| Per-motor lower-saturation fraction | 49.325% | 49.375% |
| Per-motor upper-saturation fraction | 38.325% | 38.500% |
| Maximum control computation time | 1.729 ms | 2.788 ms |

The 200 Hz timing budget passed. The exact MuJoCo PD demand, however, lies far
outside the Hover voltage box when the plant is held stationary against the
Hard45 reference. An armed plant can reduce the error by moving, so this shadow
test does not predict its eventual closed-loop saturation fraction. It does
show that jumping directly to an armed Hard45 experiment is not a justified
first physical test.

## CMG/PES diagnostic

The CMG run used the requested matched parameters except for the staged 0.3 V
hardware cap:

\[
\beta=0.5,\quad\eta=8\times10^{-4},\quad k_e=8,\quad k_\omega=0,
\quad\Delta t_n=0.0005\;s.
\]

| Metric | Value |
|---|---:|
| Requested residual RMS | 0.291407 N m |
| Realized post-projection residual RMS | 0.002315 N m |
| Realized/requested RMS ratio | 0.794% |
| Maximum applied motor residual | 0.300 V |
| Gate-state range | approximately 0 to 1 |
| Activity range | approximately 0 to 1 |
| CMG current range | 0.750 to 1.811 |

Mean gate state by unit was

\[
[0.000004,\ 0.988774,\ 0.972338,\ 0.891689,\ 0.582329,\ 0.133704].
\]

This is consistent with directional positive/negative unit activation under a
large, time-varying signed torque demand. Decoder row norms changed from
approximately `[1.4142, 1.4142, 1.4142]` to
`[1.4216, 1.3899, 1.4216]`, confirming online PES evolution.

The very small realized/requested ratio is caused by the combination of the
0.3 V residual cap and an already saturated baseline. It must not be described
as a hardware CMG performance result.

## Decision for the physical sequence

No controller code, gain, CMG equation, or frozen paper parameter is changed as
a result of this shadow run. Proceed only through:

1. armed zero-reference PD qualification;
2. armed low-amplitude `roll` PD qualification;
3. matched `roll` PD-CMG at the 0.3 V cap;
4. only if stable, staged 0.6 V and 1.2 V residual-cap qualifications;
5. then the matched Hard45, Full3, and Yaw360 pairs.

If the low-amplitude PD qualification shows sustained saturation, incorrect
sign, limit cycling, or growing oscillation, stop. Any actuator-aware PD gain or
reference change must become a separately named and reported Hover adaptation,
applied identically to both PD and PD-CMG—not a hidden CMG-only retune.

