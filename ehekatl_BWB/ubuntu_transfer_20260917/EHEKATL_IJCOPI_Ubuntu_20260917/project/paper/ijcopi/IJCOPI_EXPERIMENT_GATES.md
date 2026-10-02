# IJCOPI experiment gates for the EHEKATL LQR and DeePC paper

## Submission decision

The present manuscript is complete as a bounded real-time feasibility and
implementation-gap paper. Its evidence supports safe local execution of both
controllers, exact runtime reproduction, constraint compliance, fallback
readiness and actuator restoration. It does not support a claim that DeePC is
superior to LQR.

A stronger comparative paper should not be submitted with only the two direct
demonstrations because they began from separate simulator reloads. The smallest
defensible additional programme is the paired experiment below. No current
result justifies relaxing the frozen command limits, safety envelope or
backstepping fallback.

## Gate 1 paired comparison

- Validate controller switching, DeePC history warm-up and backstepping handoff
  first in observe-only mode and then in one design pilot that is excluded from
  confirmation.
- Freeze the controller binaries, hashes, initial-state gate, pulse waveform,
  exclusion rules and paired primary metric before opening confirmation data.
- Collect 24 within-session, sign-balanced pulse pairs per controller at R3.
  The present moving-block bootstrap is the first design that exceeded 0.80
  prospective power for paired mean per-pulse integral absolute roll-rate error.
- Randomise or counterbalance controller order within each pair. Preserve the
  same trim, disturbance, timing, limits, safety logic and log schema.
- Report the paired effect with a 95% confidence interval. Do not round the
  earlier 0.7967 power at 16 pairs to 0.80.

This gate is mandatory only if the paper claims comparative superiority or
non-inferiority. It is not mandatory for the current feasibility claim.

## Gate 2 operating-condition robustness

Use shared disturbances and random seeds at low, nominal and high dynamic
pressure. At each condition, test nominal timing and bounded increases in
input delay, measurement noise and control effectiveness loss. Report the full
matrix, including safety stops. A minimum useful matrix is:

| Factor | Levels | Evidence role |
|---|---|---|
| Dynamic pressure | low, R3 nominal, high | local generalisation |
| Additional delay | 0, 1 and 2 samples | delay sensitivity |
| Rate-noise standard deviation | nominal, 2x and 4x | estimation sensitivity |
| Effectiveness scale | 1.0, 0.85 and 0.70 | actuator/model mismatch |
| Controller | LQR and DeePC | common comparison |

The outer cells can begin as deterministic replay or software-in-the-loop
evidence. Only cells that pass the frozen start and safety gates should move to
engaged X-Plane tests.

## Gate 3 optimisation ablations

Run these offline on training and held-out trajectories, without retuning on the
confirmation set.

- DeePC: data length, past window, prediction horizon, regularisation,
  constraints on or off and noise level.
- LQR: delay state on or off, Bryson-normalised weights, command and slew
  saturation, and identified-matrix covariance.
- Both: identical primary and secondary metrics, exact dataset provenance and
  a machine-readable configuration hash.

## Gate 4 computation and reproducibility

- Report median, 95th percentile, 99th percentile and maximum execution time,
  plus deadline misses, for both controllers on the same computer.
- Retain raw logs, seed files, environment lock, controller configuration,
  analysis scripts and generated figures.
- Update `paper/DATASET_REGISTRY.csv` and `paper/CLAIMS_MATRIX.md` before any
  manuscript claim is strengthened.

## Morning X-Plane boundary

The current project can exercise the existing aggregate yoke/CTRL path and can
observe distributed surface deflections. It cannot yet command eight elevons
independently because the supplied project contains no aircraft `.acf` file and
no verified writable per-surface dataref mapping. The new allocator must remain
in shadow mode until the exact EHEKATL aircraft file, surface indices, actuator
signs and writable override mechanism are verified. An aggregate-control flight
does not validate distributed control allocation.
