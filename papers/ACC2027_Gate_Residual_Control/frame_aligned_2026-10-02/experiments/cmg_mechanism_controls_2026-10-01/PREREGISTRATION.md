# Preregistration — CMG mechanism controls (2026-10-01)

Written after Phase 0 (archived-trace diagnostics) and the Phase 1 harness gates,
**before any new arm was simulated**. Phase 0 and the gates use only archived runs
or reproductions of archived runs.

## Question

In the tested regime (paper Table I: alpha=50, gamma=2, G=1e5, tau=0.05 s,
tau_r=5 ms, I in [0.75, 2]), what does the CMG neuron contribute to the
CMG-PES residual beyond (i) a constant basis, (ii) a per-unit two-level latch
schedule, and (iii) a low-pass filter followed by the same saturating logistic
readout?

## Facts established before this study (Phase 0, `analysis/phase0/`)

- alpha*gamma = 100 > 4: the gate is bistable. The release fold is at v ~ -0.89,
  below v_reset = 0, so a latched gate can never release. Confirmed: 0 releases in
  all 10 archived strict_exact CMG runs; latched v = 0.092.
- Resting readout a_rest = 0.372803 (computed from the CMG equations at I = 0.75).
- Roll and Yaw360 (both platforms): 0/6 units latch; ||a||^2 ~ 0.85; PES corner ~ 1.4 rad/s.
  Hard45/Hardstep: 4-6/6 latch within 0.04-0.22 s (yaw pair later or never); corner -> 9.6 rad/s.
  Full3: 4/6 latch. Some unlatched units stay graded (X2 Full3 +-x, CF2 Hard45 yaw).
- The archived constant basis was a = 1 on all six units (`family_basis_adapter.py`).
  With a = 1 the decoder output is exactly a leaky first-order tracker of
  y* = clip(-8 e_q): constant-one *is* the PD+ff + matched-lag proportional baseline
  (corner 9.6 rad/s).

## Harness (Phase 1, `results/gates/GATES.json`)

- Nengo CMG applies PES with a one-step delay: W_k uses (y*_{k-1} - s_{k-1}) a_{k-1}^T.
  The archived NumPy constant-one/paired arms update from the same step. All new
  NumPy arms use the Nengo ordering, so they differ from CMG only in the basis.
- G1: NumPy CMG with this ordering reproduces the archived Nengo CMG X2 Hard45 run
  to 3e-13 (90,000 closed-loop steps). G2: Nengo CMG via the new wrapper is
  bit-identical to the archive. G3: archived constant-one rerun is bit-identical.

## Arms (only the paired-current -> activity map changes)

| Arm | Definition |
|---|---|
| `lpf-logistic` | a = clip(G sigma(alpha(LPF_tau(I) - v_th)), 0, 1); same tau, alpha, v_th, G, clip; no gate state, no gamma feedback, no conductance |
| `constant-rest` | a = a_rest = 0.372803 on all six units |
| `latch-replay` | a_j = a_rest before unit j's archived CMG latch time (first r > 0.5) for the same platform/mission, 1 afterwards |
| `cmg` with chi = 0 | canonical Nengo CMG, conductance adaptation off (G = 1e5) |
| `constant-one-nengo-order` | a = 1 with Nengo ordering (quantifies the ordering effect vs the archived constant-one) |

Frozen across arms: plant, rho = 3 PD + desired-rate feedforward, allocation,
beta (X2 0.5, CF2 0.2), CF2 actuator scale 1.5, eta = 8e-4, k_error = 8, k_rate = 0,
decoder init [I, -I], leak 1e-6, projection +-6, output gate
`torque-saturation-opposition`, 45 s, dt = 0.5 ms, seed 1 (deterministic, noise-free).

**Confirmatory matrix:** 5 arms x {X2, CF2-rotor} x {roll, full3, hard45, hardstep, yaw360} = 50 runs.
Reference arms are the archived strict_exact runs (classical, CMG, constant-one, paired-current).

**Development check (12 runs, X2, roll + hard45, 15 s):** CMG with G in {1, 1e3, 1e5} x chi in {0, 1}.
Reference: archived 15-s classical in `neuron_basis_decisive_2026-09-24/results/development_baseline`.

## Metric

Per platform: geometric mean over the five missions of the mean true quaternion-angle
error ratio to classical; improvement = 100 (1 - ratio) — identical to Sec. VI-D.
Also reported per mission: improvement, residual NRMS, gate-blocked fraction, units latched,
mean ||a||^2.

## Predictions

1. `cmg` chi = 0 vs chi = 1: |difference in improvement| < 1 percentage point on both
   platforms. Reason: a depends only on r; no gate releases; pre-latch conductance
   gain*r^2 is negligible.
2. `constant-rest`: within 3 pp of CMG on Roll and Yaw360 (where CMG never latches);
   clearly worse than CMG on Hard45/Hardstep.
3. `latch-replay`: close to CMG where units latch early and stay latched (Hardstep, X2 Hard45)
   and where nothing latches (Roll, Yaw360); deviations expected where unlatched units are
   graded (X2 Full3, CF2 Hard45).
4. `lpf-logistic`: no directional prediction. This is the decisive test of the gate's
   hysteresis/conductance.
5. `constant-one-nengo-order`: within 0.5 pp of the archived constant-one (10.34 / 4.29).
6. Development: chi changes improvement by < 1 pp at every G. G is carried into a
   confirmatory matrix only if some G differs from G = 1e5 by > 3 pp on either development mission.

## Decision rules (per arm, both platforms)

- **Reproduces CMG:** >= 90% of CMG's improvement (X2 >= 33.6%, CF2 >= 20.2%).
- **Fails:** <= 50% of CMG's improvement (X2 <= 18.7%, CF2 <= 11.2%).
- Otherwise **partial**.

Interpretation:

- `latch-replay` reproduces CMG -> in this regime the CMG contribution is a per-unit,
  state-triggered two-level switch (persistence + timing); graded dynamics are negligible.
- `lpf-logistic` reproduces CMG -> hysteresis and conductance are unnecessary; LPF +
  saturating logistic suffices.
- Both fail while CMG remains best -> the closed-loop, state-dependent generation of the
  latch pattern matters (replay is open-loop; lpf-logistic has no memory).
- `constant-rest` within 3 pp of CMG on Roll/Yaw360 -> on low-error missions CMG-PES is a
  slow (1.4 rad/s) constant-basis lagged-P residual.

All results, including negative ones and failed runs, will be reported. No arm, mission,
or parameter is tuned after seeing confirmatory results.
