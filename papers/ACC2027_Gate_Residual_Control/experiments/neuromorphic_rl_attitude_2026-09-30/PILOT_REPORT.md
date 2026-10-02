# First neuromorphic RL attitude pilot: frozen observations

Date: 2026-09-30. Status: **exploratory method check, not an ACC result**.
All figures and raw runs are under this folder's `results/` and `analysis/`.
The original paper's PES campaign is untouched.

## What was implemented and verified

`run_rl.py` reuses the frozen `rho=3` PD+desired-rate-feedforward law,
quaternion reference generator, MuJoCo X2/CF2-rotor models, height loop,
4-rotor inverse allocation, torque bounds, and output saturation-opposition
gate. A 2-s X2 Full3 zero-residual run matches the frozen classical runner's
mean quaternion-angle error to `4.2e-17 rad`. That checks the baseline path;
it does not validate the new RL update as an optimal learning algorithm.

The new policy is a 16-feature, three-action linear Gaussian actor with a
linear TD(lambda) critic. Six features come from either the exact Nengo CMG
neuron cell, tuned Nengo LIFRate cell, or a no-neuron paired-current encoder.
The actor acts at 50 Hz; MuJoCo and the neuron cell update at 2 kHz.
Training alternates Full3/Hard45 for six 10-s episodes, then freezes weights.
All evaluations below run 15 s with deterministic actor output. The
comparison uses the same 15-s baseline for each platform. The two
development missions are Full3/Hard45; Roll/Hardstep/Yaw360 are held out.

The direct RL arm uses `delta=beta*l*b`. The separately labeled envelope
arm uses `delta=beta*l*min(theta/0.03,1)*b` and increases the actor-action
penalty from `0.03` to `0.3`. This is a new design choice to reduce the
near-zero-error residual floor, not a hidden alteration of the ACC CMG-PES
controller. `beta=.5` for X2 and `.2` for CF2.

## Results: percent reduction in mean true quaternion-angle error

Positive means improvement over the matched zero-residual PD+ff. All rows
are one training seed and one deterministic evaluation, so these are
descriptive numerical observations, with no confidence interval.

| Platform / activity / RL variant | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Five-mission geometric change |
|---|---:|---:|---:|---:|---:|---:|
| X2 CMG, direct | -400.87% | -4.86% | -13.50% | -0.00% | -54.26% | -55.86% |
| X2 CMG, error envelope | -3.05% | -2.38% | -4.43% | -0.63% | -0.48% | -2.19% |
| X2 tuned LIFRate, error envelope | -3.12% | -0.90% | -1.44% | +1.87% | -1.15% | -0.93% |
| X2 static paired current, error envelope | -0.69% | -0.91% | -1.02% | +0.32% | -0.23% | -0.50% |
| CF2 CMG, error envelope | -0.32% | -0.99% | -0.34% | -0.12% | -0.36% | -0.43% |

Machine-readable tables and clearly labeled figures:

- `analysis/pilot_x2/comparison.csv`, `comparison.md`, `comparison.png/.pdf`
- `analysis/pilot_cf2/comparison.csv`, `comparison.md`, `comparison.png/.pdf`

Each run contains `policy.npz`, `training.json`, `manifest.json`, and each
mission's `summary.json`, `policy_trace.csv`, and `full_rate_trace.npz`.
The full-rate archive records activity/current, CMG membrane/gate where
applicable, true error, baseline/requested/applied torque, output-gate mask
and rotor-saturation mask.

## Mechanistic interpretation and limits

The direct actor made a persistent low-error residual. On X2 Roll, its
normalized residual RMS was `0.014` and it increased the tiny baseline
error fivefold. The envelope reduced that RMS to `0.001` and brought Roll
near parity, but did not make it positive. Thus low-error authority scaling
addresses one failure mode but does not solve reward credit assignment.

The CMG activity in the X2 envelope evaluation was at its `a=1` ceiling
for about 74% of unit-samples on Full3, 88% on Hard45, and 93% on Hardstep.
This is consistent with the paper's latched-gate regime. A reward learner
cannot necessarily extract more task-relevant state from a feature after it
has saturated. It is an observation from this run, not proof that CMG cannot
support RL. In particular, the internal CMG parameters were fixed: only the
actor/critic readouts learned.

The LIFRate and static-paired controls also have negative aggregate changes,
though LIFRate's one-seed Hardstep improvement is +1.87%. Therefore the
present study **does not show a CMG advantage in RL**. It suggests that the
first bottleneck is the small reward signal around an already strong nominal
controller and/or the short training budget. The PES controller has a dense
signed teaching target at every 0.5-ms step; this RL actor gets a scalar
reward and delayed TD update every 20 ms. Feature choice alone cannot make
those learning problems equivalent.

These 15-s trajectories are not the paper's 45-s missions. Yaw360 completes
360 degrees in 15 s rather than 45 s, so the pilot's yaw and geometric means
must not be compared with Table II of the manuscript. No injected sensor
noise, unmodeled inertia, camera feedback or race gates were used.

## Frozen-policy replay on the exact 45-s missions

After the short pilot, we replayed the same six-episode CMG envelope actor
for 45 s on X2 and CF2 with **no further learning or tuning**. The comparison
uses the archived 45-s `rho=3` classical rows from
`experiments/final_robustness_gating_2026-09-20/results/final_nominal.csv`.
The baseline implementation was independently matched to the new runner at
the two-second step level, and the 45-s RL replays use the same mission
generator, plant clock, rotor limits and allocation. Results:

| Platform | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geometric change |
|---|---:|---:|---:|---:|---:|---:|
| X2 | -1.20% | -0.79% | -4.10% | -0.52% | -0.96% | -1.50% |
| CF2-rotor | -0.03% | -1.05% | -0.33% | -0.11% | -0.13% | -0.33% |

Every mission is slightly worse than the tuned baseline. The result is
stronger as a *negative check* than the 15-s pilot because it uses the exact
paper reference durations, but it still has one training seed and only 60 s
of total reward-driven experience per platform. It says nothing conclusive
about a well-trained PPO/SNN policy or CMG as an RL basis in general.
The files are `analysis/full45/comparison.csv`, `comparison.md` and
`comparison.png/.pdf`; each evaluation also has a 90,000-sample full-rate
trace and its configuration/source manifest. `audit_full45.py` passed on all
10 runs: sample count and time span, finite data, summary/trace mean,
activity and residual bounds, gate identity, torque box, source hash and
model hash (`analysis/full45/audit.json`).

## Decision

Keep this pilot and its negative results as a reproducible method checkpoint.
Do not add them to the ACC 2027 manuscript. Before a 45-s seven-basis study,
freeze an improved development protocol that trains under a declared
disturbance/model-mismatch distribution and tests nominal and disturbed
conditions separately. Compare a standard PPO/recurrent policy and a
PES-bootstrapped RL hybrid if sample efficiency remains poor, labeling the
hybrid precisely. Run multiple training seeds and report confidence or
dispersion before claiming a neuron-family effect. Only then move the
residual and dual versions to perfect-state racing, followed by DVS-based
perception in the loop.
