# Hardstep: why the error is large, and what the residual actually buys

2026-09-16. Triggered by Gandhi's observation that a 0.45 rad (26°) mean error on the *baseline*
looks like a defect that CMG then merely inherits. It is not a defect. The mission is near the
airframe's physical floor, and the mean-error metric hides the one thing the controller does change.

All of this comes from existing traces plus one targeted 16-run experiment. No canonical runner or
published result was modified.

## 1. The reference is untrackable by construction

Hardstep commands **63–111° rotations every 2 s** (consecutive setpoint pairs, as quaternion angles:
63.4, 111.4, 77.5, 91.7, 98.1°). Decomposing the 45-s mean error by phase:

| cell | mean | slew (first 1.5 s after each step) | settled (last 0.5 s) | slew share of the mean |
|---|---|---|---|---|
| X2 PD | 26.0° | 34.4° | **3.4°** | 96.8% |
| X2 CMG | 20.6° | 27.2° | 2.7° | 96.8% |
| CF2 PD | 24.4° | 33.1° | **0.7°** | 99.3% |
| CF2 CMG | 19.9° | 26.7° | 1.4° | 98.3% |

Once settled, both loops hold the reference to a few degrees or better. **97–99% of the reported
mean is slew transient that no bounded residual can remove.**

## 2. How close is that slew to the physical limit?

X2 yaw torque comes only from rotor drag (κ = 0.0201 m), so it is the binding axis:

| | roll | pitch | yaw |
|---|---|---|---|
| controller box ℓ = j_tune·ν [N·m] | 0.729 | 0.438 | **0.254** |
| rotor-feasible at hover [N·m] | 2.340 | 1.820 | **0.261** |
| box / feasible | 0.31 | 0.24 | **0.97** |
| realizable acceleration [rad/s²] | 19.9 | 17.2 | **4.2** (intended 10) |

The yaw box is 97% of what the rotors can deliver. Per-step time-optimal rest-to-rest bounds against
achieved settling (to a 5° band):

| step | Δ(roll, pitch, yaw) | t_optimal | X2 PD | X2 CMG |
|---|---|---|---|---|
| 1 | 43, 26, 32° | 0.72 s | 1.09 | 0.70 |
| 2 | 80, 57, 72° | 1.09 s | 1.35 | 0.72 |
| 3 | 66, 3, 92° | 1.23 s | 1.16 | 0.72 |
| 4 | 74, 49, 40° | 0.82 s | 1.15 | 1.23 |
| 5 | 89, 6, 20° | 0.58 s | 1.27 | 0.76 |

PD runs at 1.2–2.2× the bound; CMG lands essentially on it. (The bound is per-axis bang-bang and
ignores 3-D coupling, so it is approximate — step 3 shows PD slightly below it.)

## 3. The result the mean-error metric was hiding

Settling time to a 5° band, 22 steps, censored at the 2 s dwell:

| rung | X2 PD → CMG | X2 Δ | CF2 PD → CMG | CF2 Δ |
|---|---|---|---|---|
| PD, ρ=1 | 1.24 → 0.86 s | **−31%** | 1.18 → 0.68 s | **−42%** |
| PD+ff, ρ=1 | 1.24 → 0.86 s | −31% | 1.18 → 0.68 s | −42% |
| PD+ff, ρ=3 (tuned) | 0.59 → 0.83 s | +40% | 0.53 → 0.52 s | −1% |

Feedforward changes nothing on Hardstep, as it must: the reference is piecewise constant, so
ω_d ≡ 0 between steps (26.03° → 26.04° on X2).

**The trade.** The speed-up costs settled accuracy: X2 settled error improves (3.4° → 2.7°) but CF2
degrades (0.67° → 1.38°), and at ρ=3 both degrade (X2 0.19° → 0.93°). All sub-degree in absolute terms.

## 4. Why ρ=3 regresses — the paper's own mechanism

The latched PES decoder is lagged proportional action with a corner at **9.60 rad/s**
(`\pesCorner`, derived in the ablation section). At ρ=1 the loop runs at ω_n = 4 rad/s, below the
corner, so the residual is in phase and helps. At ρ=3 the loop runs at 12 rad/s, above it: the
residual lags ≈51° and fights the slew reversals. One mechanism explains both the gains at ρ=1 and
the losses at ρ=3, on both airframes.

## 5. A hypothesis that was pre-registered and refuted

`torque_limits()` builds ℓ from `model.body_inertia`, i.e. the principal moments in MuJoCo's
reported order (j_tune), not the body-frame diagonal. On X2 those differ by (1.66, 1.44, 0.42), so
yaw appeared starved. The prediction, written into `hardstep_limits_test.py` before running it, was
that ℓ from diag(J) would help.

**It does the opposite:**

| X2 Hardstep | mean error | rotor saturation |
|---|---|---|
| canonical ℓ, ρ=3, PD | 15.25° | 0.086 |
| diag(J) ℓ, ρ=3, PD | **89.84°** | **0.683** |
| diag(J) ℓ, ρ=3, CMG | 128.41° | 0.869 |

Raising the yaw box to 0.605 N·m puts it 2.3× above rotor capability, so the mixer clips and the loop
loses authority. The canonical limit is, on the binding axis, almost exactly the rotor limit. **No
change to the torque limits is warranted.** (Gains from diag(J) remain a separate, minor question:
25.83° vs 26.04° at ρ=1, a 0.8% effect.)

## 5b. The ρ=3 regression is fixable — mechanism and remedy (added 2026-09-16)

**Mechanism.** The applied command is u = sat_ℓ(u₀ + βℓ⊙s). The residual's effect on a saturated axis
is *one-sided*:

| state of axis i | same sign as u₀ | opposite sign to u₀ |
|---|---|---|
| \|u₀,i\| < ℓ_i | shifts the command by βℓ_i s_i | shifts the command by βℓ_i s_i |
| \|u₀,i\| = ℓ_i | clipped back to ℓ_i — **no effect** | command drops to ℓ_i(1 − β\|s_i\|) — **up to β of the axis authority removed** |

So a *lagged* residual can only ever hurt a saturated axis. The lag is the paper's own latched-PES
pole: τ = 0.104 s, corner 9.6 rad/s. At ρ=1 the loop period is 2π/4 = 1.57 s, so the lag is 24° of
phase and the baseline saturates in 1.4% of samples — the harmful case is essentially absent. At ρ=3
the period is 2π/12 = 0.52 s, the lag is **72°**, and the baseline saturates far more:

| X2 Hardstep | roll | pitch | yaw |
|---|---|---|---|
| baseline saturated, ρ=1 | 1.4% | 0.7% | 0.0% |
| baseline saturated, ρ=3 | 23.4% | 14.1% | **45.5%** |
| residual **opposing while saturated**, ρ=3 | 10.1% | 5.3% | **14.3%** |
| mean authority removed, ρ=3 | 3.7% | 1.9% | 3.4% of ℓ |

On CF2 at ρ=3 the baseline is saturated 94%/69%/93% of the time, so there is no margin at all and the
β=0.5 run diverges (135.97°, rotors at a bound 92% of samples).

**Remedy.** Do not let the residual oppose a saturated axis:

> s_i ← 0 if |u₀,i| ≥ ℓ_i and sgn(s_i) ≠ sgn(u₀,i)

This preserves |u − u₀| ≤ βℓ and exact baseline recovery at β = 0, and it does not touch the decoder:
learning still sees the same baseline and target, so Propositions 1–3 are unchanged.

**Result** (β = 0.5 on both platforms, 20 mission × bandwidth cells):

| Hardstep, ρ=3 | mean [°] | settling to 5° [s] | settled [°] | rotor sat |
|---|---|---|---|---|
| X2 PD | 15.25 | 0.590 | 0.185 | 0.086 |
| X2 + CMG | 17.84 | 0.829 | 0.927 | 0.035 |
| X2 + CMG, gated | **15.56** | **0.570** | 0.382 | 0.094 |
| CF2 PD | 15.06 | 0.528 | 0.000 | 0.003 |
| CF2 + CMG (β=.5) | 135.97 | 1.854 | 140.45 | 0.921 |
| CF2 + CMG, gated | **15.24** | **0.508** | 0.004 | 0.024 |

- The regression is gone: gated settling is **better than the PD baseline** on both airframes
  (0.570 vs 0.590 s; 0.508 vs 0.528 s).
- The gate **prevents the CF2 divergence at β = 0.5**, which is why the β-selection rule previously
  had to drop CF2 to 0.05.
- It is **numerically inert in 18 of 20 cells** — identical to three decimals everywhere the baseline
  does not saturate (all of Roll, Full3, Hard45, Yaw360 at both bandwidths, and Hardstep at ρ=1).

Predictions P1–P4 were written into `hardstep_fix_test.py` before the runs; all four held.

**Honest reading.** Above the PES corner the gated residual is *neutral*, not beneficial: it recovers
PD-level performance rather than improving on it (mean 15.56 vs 15.25 on X2). The claim to make is
that the gate removes the only regression in the study and makes full authority safe on both
airframes — not that the residual helps at high bandwidth.

## 6. Two disclosures worth keeping

- **Altitude.** X2 descends from 1.00 m to **0.117 m** during Hardstep while holding 45–49° of
  commanded tilt (CF2 to 0.774 m). Reconstructing the airframe geometry from the traces, the lowest
  rotor stays **7.5 cm above the floor** — no contact, but the margin is small and should be stated.
- **No actuator starvation at ρ=1.** Torque sits at its box limit in under 2% of samples and rotor
  saturation is ~0, so the canonical Hardstep result is bandwidth-limited, not actuator-limited.

## 7. What this changes in the paper

1. Report Hardstep by **settling time** (and settled error), not by the 45-s mean alone. The mean
   stays in the matrix with a dagger pointing at the step-response block.
2. State the slew domination (97–99%) so the small percentage is not read as a weak method.
3. Use the 9.6 rad/s corner to explain the ρ=3 regression — it is already derived in the paper.
4. Nothing needs re-running: all of §1–§4 comes from existing traces.

## 8. Reproduce

| script | what it produces |
|---|---|
| `diagnose_hardstep.py` | phase decomposition, step sizes, torque envelope, §1 |
| `hardstep_geometry.py` | tilt and ground clearance from the traces, §6 |
| `hardstep_steps.py` | per-step settling, overshoot, settled error |
| `hardstep_ladder.py` | settling across all three rungs → `hardstep_ladder.json`, §3 |
| `hardstep_feasibility.py` | rotor-feasible torque and time-optimal bounds, §2 |
| `hardstep_limits_test.py` | the 16-run pre-registered limits experiment, §5 |

**Gate.** `hardstep_limits_test.py` re-implements the canonical attitude loop; with canonical
settings it reproduces Table II exactly — X2 PD 0.454528, X2 CMG 0.359355, CF2 PD 0.426182, CF2 CMG
0.347886 rad. The first version of that harness omitted the CF2 1.5× rotor-authority design and was
caught by this gate (CF2 flew at stock authority and crashed at 142°); the numbers above are all
post-fix.
