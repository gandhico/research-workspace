# Dual (self-tuning + residual) racing RL pilot — pre-registration

Written 2026-09-30, 20:40 (America/Denver), **before any training result of this stage exists**.
Continues Codex's work in this folder: `dual_env.py` and the baseline-recovery gate `probe_dual.py`
(`results/parity/summary.json`: zero modulation reproduces the geometric teacher exactly, 0.0 m position
difference, 4 gates, X2 and CF2, nominal and gust).

## Why this stage

The direct-policy pilot (`../rl_cmg_2026_09_30/PILOT_REPORT.md`) replaced the race controller with a learned
4-D command and passed **zero gates** in every arm, MLP included. The dual interface keeps the geometric
controller and learns only a bounded modulation of it, as the ACC paper does for attitude. At zero action the
vehicle flies the teacher's trajectory, so learning starts from a policy that already passes gates.

## Question

On X2 under the declared gust disturbance, does a bounded learned modulation of the geometric racing
controller reduce position tracking error without losing gates or adding collisions? Which part helps:
inner-rate gain self-tuning (`self`), additive wrench residual (`residual`), or both (`dual`)? Does a
continuous-CMG activity basis help relative to a no-neuron MLP with identical inputs?

## Fixed design (not changed after results)

| Item | Value |
|---|---|
| Plant / course | `dual_env.DualEnv`, X2, Codex's seven-gate course, 12-s episodes (teacher passes 4 gates) |
| Clocks | policy 20 ms, MuJoCo 2 ms, CMG cells 0.5 ms |
| Action | latent `z` in [-1,1]^7 = tanh(actor output); arm masks unused slots to 0 |
| Arms | `baseline` (z = 0, no learning), `self` (3 gain slots), `residual` (4 wrench slots), `dual` (7) |
| Bounds | as in `dual_env.py`: residual scale [0.06, 0.12, 0.12, 0.08], gain factor 1 +/- 0.20 |
| Features | `mlp` (26 observations + 32 zeros) and `graded` (26 observations + 32 continuous-CMG gate activities, Codex's pre-declared retuned preset; **not** the ACC CMG parameters) |
| Learner | PPO (Codex's update: GAE 0.99/0.95, clip 0.2, 4 epochs, Adam 2e-4), 2x64 tanh actor-critic |
| Initialization | actor mean head weights and bias = 0, so the deterministic initial policy **is** the teacher; log-std = -1.6 |
| Budget | 10 rollouts x 600 policy steps = 6,000 decisions = 60,000 MuJoCo steps (120 s simulated) per arm; no behavior cloning |
| Training condition | `gust` |
| Seed | 1 (pilot) |

## Evaluation (deterministic actor)

- **Development condition:** gust, 12 s.
- **Held-out condition:** nominal (no gust), 12 s; never trained on.
- Metrics: mean and maximum position error to the planned reference, gates passed in order, collisions,
  termination reason, rotor-saturation fraction, action RMS, gain-factor range, episode return.

## Decision rule (fixed now)

An arm counts as an **improvement candidate** only if, on the gust evaluation, mean position error is at least
5% below the matched baseline **and** gates passed >= baseline **and** collisions = 0, **and** on the held-out
nominal evaluation mean error is not more than 5% worse than baseline. This is a single-seed pilot: results are
descriptive, not inferential. Candidates advance to 3 training seeds before any ranking or claim; CF2 transfer
and gate-only observations come after that. A CMG-vs-MLP statement requires the same arm to pass under both
features across seeds.

## Out of scope

No ACC 2027 manuscript claim. No Swift/UZH equivalence (different course). No DVS in the loop. No energy claim
from CPU time.
