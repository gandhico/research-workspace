# Dual racing RL pilot — result (2026-09-30)

Status: **pre-registered pilot, negative.** Protocol and decision rule: `PREREGISTRATION.md` (written before results).
Exploratory; not an ACC 2027 result.

## Verified before training

- Zero dual action reproduces the geometric teacher exactly (Codex's `results/parity`, and again through the new
  worker: an untrained zero-mean policy gives 0.0 m position difference over 600 steps under gusts).
- Baseline (teacher): gust mean position error 0.1937 m, nominal 0.0331 m, 4 gates, 0 collisions in 12 s.

## Result (X2, seed 1, 10 x 600 PPO steps per arm, trained on gust)

| Arm | Feature | Gust mean err (m) | Gust change | Gust gates / coll. | Nominal mean err (m) | Nominal change | Action RMS | Gain range | Candidate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | - | 0.1937 | +0.0% | 4 / 0 | 0.0331 | +0.0% | 0.000 | 1.00-1.00 | - |
| self | mlp | 0.1936 | -0.0% | 4 / 0 | 0.0334 | +0.7% | 0.131 | 0.95-1.02 | no |
| self | graded | 0.1937 | -0.0% | 4 / 0 | 0.0333 | +0.6% | 0.092 | 0.97-1.01 | no |
| residual | mlp | 0.2006 | +3.6% | 4 / 0 | 0.0617 | +86.2% | 0.120 | 1.00-1.00 | no |
| residual | graded | 0.1959 | +1.1% | 4 / 0 | 0.0632 | +90.6% | 0.121 | 1.00-1.00 | no |
| dual | mlp | 0.2018 | +4.2% | 4 / 0 | 0.0513 | +55.0% | 0.120 | 0.99-1.06 | no |
| dual | graded | 0.2022 | +4.4% | 4 / 0 | 0.0477 | +43.9% | 0.077 | 1.00-1.02 | no |

No arm meets the rule (>= 5% lower gust error, no lost gates, no collisions, nominal <= 5% worse). All arms keep
4 gates and 0 collisions; gate times stay within 0.02 s of the baseline. Machine-readable:
`results/pilot_analysis/comparison.{csv,md}`.

## Failure mode (diagnosed from the traces)

1. **Training made tracking monotonically worse.** For residual and dual arms the rollout mean position error rose
   steadily over all ten rollouts (e.g. dual/graded 0.1925 -> 0.2000 m). Gain-only arms stayed flat at 0.1935 m.
2. **The learned policy is a near-constant bias.** The mean action is identical in gust and nominal evaluation
   (e.g. residual/mlp: thrust -0.16, roll-rate -0.16, every episode). The policy ignores the observation, so it
   cannot cancel a time-varying gust; the constant offset is what degrades nominal flight by 44-91%.
3. **Likely cause: the learning signal.** The reward's dominant terms (gate progress, gate bonus) barely depend on
   these small modulations, while the tracking term is about -0.02 per step at 0.2 m error. After advantage
   normalization the update is driven mostly by noise; with a zero-weight mean head, the bias drifts first. The
   exploration log-std did not move from -1.6 in any arm, consistent with no useful gradient.

This says nothing for or against CMG: neither feature learned a state-dependent correction.

## What would make the next run informative (not yet run)

1. **Headroom check first.** A fixed, hand-designed correction (e.g. integral action on position error into the
   thrust/rate residual) on the same gust. If even that cannot reduce error, the gust is not the right test.
2. **A reward that measures the objective.** Tracking error relative to the teacher's own error on the same
   episode (both deterministic), dropping action-insensitive progress terms from the learner's reward.
3. **Memory where the task needs it.** Gust rejection is integral-like; a memoryless MLP cannot integrate, while
   the CMG basis and a GRU can. That is the comparison that actually tests CMG's temporal state.
4. Larger budget only after 1-3; then 3 seeds, CF2, held-out tracks.
