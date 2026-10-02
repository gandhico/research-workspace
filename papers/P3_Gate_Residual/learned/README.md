# Paper 5 — Online-Learned HyperLIF Gate Residual (Adaptive / Performance story)

Companion to **Paper 4** (gate-state residual *mechanism*). Paper 5 is the
**adaptive / performance** paper: an online-learned HyperLIF gate decode (PES /
e-prop) that **beats** the hand-tuned adaptive STN-PID-PES baseline and
**generalizes across platforms**, plus two rigorous boundary results.

## Headline
- Learned HyperLIF gate: **J = 0.0383 (+86.7%)** on Bitcraze/hard45 — beats
  STN-PID-PES (+83.3%).
- Generalizes cross-platform (Skydio +57%) where STN-PID-PES ≈ classical.
- Adaptive HyperLIF ≡ HyperLIF in gate mode (numerically identical + proof).
- Behavioral cloning diverges (covariate shift) ⇒ online learning wins.
- Performance–robustness frontier via the learning target's damping term.

## Contents
- `paper/main.tex` — full IEEEtran draft (first version, 2026-07-05).
- `paper/references.bib` — bibliography (TODO: complete fields).
- `docs/full_results_dossier.md` — all tables, parameters, runners, mechanism.

## Code & reproduction
`neuromorphic-robotics-control/experiments/controller_benchmarks/learned_gate_experiment.py`
(self-contained; reproduces classical + fixed-gate bit-for-bit). See the dossier
§8 for commands.

## Status
MuJoCo core complete and validated (2 platforms × 2 missions × frontier). Pending:
**Aero2 HIL** + **static quadrotor** hardware validation → Section VI / Table V.
Then: author info, figures, references.
