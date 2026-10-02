# Track 2 — model-based baselines, and CMG–PES on top of them

2026-09-10. Attitude-only MuJoCo runner (the Table V setting): 45 s,
dt = 0.5 ms, X2 and CF2 (1.5× rotors), five missions, noise-free unless
stated. Mean quaternion-angle error [rad]. Families follow Gandhi's Aero 2
formulations (`C:\Research\aero2\aero2\control\`), extended to a 3-axis
torque-input rigid body with reference-rate feedforward. Design
considerations: `CONSIDERATIONS.md`.

## Part A — the baselines on their own (final)

### A1. Table V's PD was held back twice

1. **No reference-rate feedforward.** Adding `ω − ω_d` alone removes 76–99%
   of PD's error on the moving-reference missions (earlier today).
2. **Bandwidth ~3× below its own optimum.** PD+ff tuned over 0.75–8× the
   PD's `ωₙ`, best single setting per platform by mission-mean error:

| PD+ff, X2 | 1× (Table V gains) | **3× (tuned)** |
|---|---|---|
| Roll | 0.00298 | **0.00034** |
| Full3 | 0.07210 | **0.01009** |
| Hard45 | 0.07102 | **0.01054** |
| Hardstep | 0.45477 | **0.26591** |
| Yaw360 | 0.00178 | **0.00020** |

The optimum is **interior at 3× on both platforms**, and it is the same
under the paper's "realistic" measurement noise — so it is not an artifact of
noise-free tuning. Above 3× the smooth missions keep improving but **Hardstep
saturates** (CF2 diverges from 4× upward, rotors at a bound 83–97% of the
time). Hardstep is what limits the gain for every family.

**Bandwidth-tuned PD+ff beats CMG-on-PD in every Table V cell, Hardstep
included** (X2 Hardstep 0.266 vs 0.359).

### A2. The five families, each at its own tuned bandwidth

Change in error relative to **tuned PD+ff** (positive = better than PD+ff):

| X2 | tuned bw | Roll | Full3 | Hard45 | Hardstep | Yaw360 |
|---|---|---|---|---|---|---|
| LQR | 3× | +29% | +32% | +32% | −10% | +41% |
| **Backstepping** | 3× | **+30%** | **+30%** | **+32%** | **−1%** | **+42%** |
| SMC | 1.5× | −176% | −123% | −118% | −126% | −132% |
| MPC (unconstrained) | 3× | +17% | +23% | +23% | −8% | +32% |

| CF2 | tuned bw | Roll | Full3 | Hard45 | Hardstep | Yaw360 |
|---|---|---|---|---|---|---|
| LQR | 2× | +88% | +62% | +71% | −0.2% | +95% |
| **Backstepping** | 3× | **+95%** | **+65%** | **+73%** | **+0.5%** | **+98%** |
| SMC | 1× | +55% | +14% | +33% | −110% | +81% |
| MPC (unconstrained) | 2× | +86% | +61% | +70% | −0.9% | +95% |

Every optimum is interior. Reading:

- **Backstepping (computed torque) is the strongest baseline.** It is PD+ff
  plus the model terms `J ω̇_d + ω×Jω`; those terms alone are worth ~30% on
  X2's smooth missions and 65–98% on CF2's.
- **LQR ≈ backstepping**, as expected: on a decoupled double integrator LQR is
  a PD with ζ = 1/√2, plus the same model feedforward. It loses 10% on X2
  Hardstep, where its lower damping overshoots into saturation.
- **Unconstrained MPC ≈ LQR**, as predicted: without active constraints the
  finite-horizon first-move gain converges to the LQR gain. MPC's real
  advantage, constraint handling, needs an online QP solver.
- **SMC underperforms.** Its best bandwidth is low (1–1.5×) and its reaching
  term saturates on Hardstep (2× worse on both airframes). As parameterised
  here — reaching acceleration η = 0.5 of the axis limit, boundary layer set
  so the linear region is critically damped at ωₙ — it is not competitive;
  a different η/φ split might be.
- **Nobody beats PD+ff meaningfully on Hardstep.** It is an actuator-limit
  problem, not a control-structure problem.

### A3. A metric issue in the paper's Table VI

Under noise, Roll and Yaw360 sit at **0.0320 rad at every bandwidth** — flat
to five digits. The runner applies measurement noise to `q_meas` *before*
computing the error, so `qerr` is **measured** attitude error and includes the
sensor noise itself. For isotropic noise with σ = 0.02 rad per axis the
expected rotation angle is σ√(8/π) = **0.0319 rad** — the observed floor to
within 6×10⁻⁵.

So Table VI's Yaw360 drop (60.6% → 47.8%) is largely the noise floor sitting
inside the metric, not degraded control. **Recommendation:** report *true*
attitude error (from the noise-free state) under noise, or state explicitly
that Table VI reports measured error.

## Part B — CMG–PES on top of each tuned family

Residual authority `β` swept over {0.5, 0.2, 0.1, 0.05, 0.02} per
(family, platform), with a rule fixed in `sweep_cmg_beta_2026_09_10.py`
**before the results existed**: admissible if every mission stays below 1 rad
and saturation below 0.5; score = geometric mean over the five missions of
CMG error ÷ family error (equal weight per mission — the mission-mean is
dominated by Hardstep); score < 1 means CMG helps that family.

### Verdicts

| family | X2 | CF2 |
|---|---|---|
| **PD + ff** | **helps** — β 0.5, geo-ratio **0.64** | **helps, modestly** — β 0.05, **0.94** |
| LQR | does not help — best 1.02 | does not help — 1.66 |
| Backstepping | does not help — 1.02 | does not help — 1.68 |
| SMC | **helps** — β 0.5, **0.85** | does not help — 1.64 |
| MPC (unconstrained) | does not help — 1.02 | does not help — 1.66 |

CMG on tuned PD+ff, per mission (change vs PD+ff alone):

| | Roll | Full3 | Hard45 | Hardstep | Yaw360 |
|---|---|---|---|---|---|
| X2, β 0.5 | **+78%** | **+12%** | **+14%** | −17% | **+42%** |
| CF2, β 0.05 | **+23%** | +1.3% | +1.8% | −1.3% | +5.6% |

On CF2, β ≥ 0.1 drives Hardstep into divergence (≈2.1 rad), so the rule
could only admit a small authority there.

### Reading

**CMG helps exactly the baselines that lack the model terms, and none of
those that carry them.** PD+ff and SMC have no `J ω̇_d + ω×Jω`; LQR,
backstepping and MPC all do. That is what a residual is for — learning
dynamics the baseline does not model — and with an exact model there is
nothing left to learn.

On X2 the model-based families show the same split every time: CMG improves
Full3, Hard45 and Yaw360 (+1% to +44%) but worsens Roll (−16% to −115%) and
Hardstep, and the net is slightly negative.

On CF2, whose baseline errors are near zero, CMG adds an **error floor** that
grows with β — CF2 backstepping Roll goes from 3×10⁻⁵ rad alone to
1.2×10⁻⁴ (β 0.02) and 4.9×10⁻⁴ (β 0.5). Percentages on such small
baselines look dramatic ("−331%") but are thousandths of a degree.

**The grid-edge warnings do not hide a win.** For the model-based families
the ratio falls monotonically toward 1 as β shrinks: less authority means
less harm, and β → 0 is the baseline itself. For PD+ff on X2, the choice sits
at the top of the grid (0.5); β is bounded by 1 by construction, and Hardstep
already costs 17% at 0.5.

### The caveat that decides how to read this

The model-based controllers use **MuJoCo's own inertia — an exact model**.
That is the best case for model-based control and the worst case for a
learned residual. A real vehicle's `J` is never exact, so backstepping was
re-run with its model inertia at **0.6× and 1.6× the truth**, alone and with
CMG at β 0.05 and 0.2 (same rule).

| backstepping, bw 3 | model J | vs tuned PD+ff (geo) | CMG vs backstepping (best admissible geo) |
|---|---|---|---|
| X2 | 0.6× | 0.93 | 1.12 — does not help |
| X2 | 1.0× (exact) | 0.72 | 1.05 — does not help |
| X2 | 1.6× | 0.57 | 1.01 — does not help |
| CF2 | 0.6× | 0.78 | none admissible (Hardstep diverges) |
| CF2 | 1.0× (exact) | 0.16 | 2.21 — does not help |
| CF2 | 1.6× | 0.55 | 1.10 — does not help |

**Backstepping is robust to inertia error, and CMG does not help it there
either.** A wrong `J` in computed torque mostly rescales the loop gains
(overestimating it even stiffens the loop, which helps X2), so the loop stays
stable and accurate and little error is left. And the PES target is
error-proportional (`y* = −k_e e_q`), so the residual cannot learn the
*structure* of a model error — one proportional to reference acceleration,
say. A residual that should learn model error needs a teaching signal built
for that, not a PD-like target.

### Unmodelled disturbance torque

An unmodelled disturbance torque (aerodynamic moments, CoM offset, rotor
imbalance) is what no model feedforward can represent. Tuned backstepping,
exact model, continuous multi-sine body torque throughout each mission:
0.15 N m on X2, and its inertia-scaled equivalent 5.9×10⁻⁵ N m on CF2
(both load the most-loaded axis to ≈21–35% of its limit).

| CMG vs backstepping | Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo-ratio |
|---|---|---|---|---|---|---|
| X2, β 0.05 | +1.5% | +1.4% | +1.4% | −1.2% | +1.5% | 0.991 |
| X2, β 0.2 | **+5.9%** | **+5.3%** | **+5.4%** | −7.2% | **+5.9%** | **0.968** |
| CF2, β 0.05 | +1.7% | +1.3% | +1.4% | −0.8% | +1.7% | — |
| CF2, β 0.2 | **+7.8%** | **+5.2%** | **+5.4%** | −29.6% | **+7.8%** | — |

Under disturbance, backstepping and PD+ff are nearly tied (X2 ≈ 0.03 rad
everywhere, CF2 ≈ 0.016–0.019): the disturbance, not the model, dominates the
error, and the residual rejects part of it.

**CF2 caveat, stated plainly.** Under continuous disturbance **every
controller loses tracking on CF2 Hardstep**, backstepping and PD+ff included
(1.67 rad, rotors at a bound 62% of the time). The pre-declared rule therefore
admits nothing on CF2 — it was written to screen CMG settings, not a baseline
that fails on its own. Excluding Hardstep, **post hoc and labelled as such**,
CMG at β 0.2 gives a four-mission geo-ratio of ≈0.94 on both airframes.

**So CMG does have a place next to model-based control — a modest one:
5–8% lower error on smooth missions under unmodelled disturbance, at a
cost on Hardstep.** That is consistent with what a residual is for.

*An earlier CF2 run at 0.004 N m is kept in `disturbance/` but invalid: that
is 14× CF2's per-axis torque limit and every controller lost control. The
value was misremembered from the 09-05 hover study, which actually used
0.00015 N m — see `../final_sweep_2026-09-05/PROVENANCE_NOTE_2026-09-11.md`.*

## Part C — NMPC

NMPC in the aero2 form (grid of constant torque offsets around a nominal
computed-torque law, RK4 shooting, 100 Hz with zero-order hold) needed two
fixes before it was worth benchmarking:

1. **Closed-loop prediction.** aero2 holds each candidate's torque constant
   over the whole horizon, which mis-models a loop that re-plans every 10 ms.
   Here the nominal law is re-evaluated on each predicted state and the
   candidate adds a constant offset.
2. **No rate-error weight in the cost.** The metric scores angle error; a
   rate weight let the optimiser trade angle for rate matching.

Its one-period prediction is accurate (0.002°, against 0.33° assuming no
motion), so the quaternion propagation is right.

A 3-s smoke test suggested NMPC was still 33% worse than its nominal law
(0.160 vs 0.118 rad, X2 Full3). **That was the initial transient, not the
steady behaviour.** Over the full 45-s missions, tuned over 1.5–4× (interior
optimum at 3× on both platforms):

| mission-mean error | NMPC (100 Hz) | backstepping, its nominal (2 kHz) |
|---|---|---|
| X2, bw 3 | 0.0573 | 0.0568 — NMPC 1% worse |
| CF2, bw 3 | **0.0524** | 0.0532 — NMPC **1.5% better** |

**NMPC is competitive with the best baseline** while updating 20× less
often; on CF2 it is slightly better, mainly on Hardstep (0.257 vs 0.261).
A proper NLP solver (CasADi/acados) would be the next step, in a separate
venv so numpy never moves under the Table V numbers.

**CMG on tuned NMPC** (same rule): does not help — best admissible
geo-ratio **1.022** on X2 (β 0.02) and **1.638** on CF2 (β 0.02; β ≥ 0.1
drives CF2 Hardstep into divergence). The same split as the other
model-based families: on X2, gains on Full3/Hard45/Yaw360 are outweighed by
Roll and Hardstep; on CF2, the residual's error floor dominates near-zero
baseline errors. NMPC completes the pattern: **CMG helps model-free baselines
(PD+ff, SMC on X2) and none of the four model-based ones.**
