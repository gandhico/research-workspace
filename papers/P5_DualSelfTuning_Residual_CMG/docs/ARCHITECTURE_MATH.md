# Dual architecture: mathematics (v0, 2026-09-12)

Notation follows the ACC 2027 paper (v9):
- e_q: shortest-path quaternion error vector;
- ω: body rate;
- ℓ: per-axis torque bound;
- j: per-axis tuning inertia;
- sat_ℓ: componentwise saturation.

All vectors are per axis (m = 3) unless stated.

## 1. Base: quaternion PID with conditional integration

```
ξ̇ = e_q             (frozen on any axis whose command saturates)
u_0 = sat_ℓ( −K_p e_q − K_i ξ − K_d ω )
K_p0 = 2 j ω_n²,  K_d0 = 2 ζ j ω_n,  K_i0 = 0.05 K_p0      (ω_n = (4, 4, 3.5), ζ = 0.95)
```

k_i = 0.05 k_q was the best single integral factor on both airframes (ACC 2027 baseline study,
2026-09-10). Reference-rate feedforward (ω → ω − ω_d) is an option, kept off in v0 so the base
matches the ACC 2027 paper.

**Linear stability of the PID.** For one decoupled axis with e_q ≈ θ/2 and ė_q ≈ ω/2 the
characteristic polynomial is

```
j s³ + k_d s² + (k_p/2) s + k_i/2 = 0.
```

Routh–Hurwitz gives stability iff all gains are positive and

```
k_i < k_p k_d / j.                                            (R)
```

With the nominal gains the right side is 4 ζ j ω_n³ and the left is 0.1 j ω_n², so the ratio is
40 ζ ω_n: 152× on roll and pitch, 133× on yaw.

## 2. Self-tuning layer S: bounded multiplicative gains

A second CMG population S produces gain multipliers:

```
K_g(t) = K_g0 ⊙ (1 + β_g σ_g(t)),   σ_g = clip_[−1,1](W_S a_S)_g,   g ∈ {p, i, d},   0 ≤ β_g < 1.
```

**Properties (hold for any W_S; derived as in ACC 2027 Prop. 2):**

1. **Positivity and boxing.** K_g ∈ [(1−β_g)K_g0, (1+β_g)K_g0] > 0 at every step.
2. **Frozen-time Hurwitz (PD part).** For any positive diagonal K_p, K_d the linearized attitude
   matrix A(K) is Hurwitz. The energy/LaSalle argument of ACC 2027 Theorem 1's proof does not
   depend on the gain values.
3. **Frozen-time Hurwitz (PID).** Condition (R) holds on the whole box if
   (1+β_i) k_i0 < (1−β_p)(1−β_d) k_p0 k_d0 / j. With all β = 0.5:
   left = 1.5 · 0.1 j ω_n² = 0.15 j ω_n², right = 0.25 · 4 ζ j ω_n³ = ζ j ω_n³,
   so the condition is 0.15 < ζ ω_n (3.8 roll/pitch, 3.3 yaw), a margin above 22×.
4. **Baseline recovery.** W_S = 0 at t = 0 gives σ = 0, the nominal PID; β_g = 0 disables tuning exactly.
5. **Time variation.** Frozen-time stability does not by itself give stability under time-varying
   gains. The standard sufficient route is slow variation: stability holds if ‖K̇‖ stays small relative
   to the frozen-time decay rate (Khalil, *Nonlinear Systems*, slowly varying systems). S therefore
   learns on a slower timescale than the residual (η_S ≪ η_R). A quantitative bound is open question Q2.

## 3. Self-tuning PES targets (v0, provisional)

S encodes three normalized signals per axis with paired currents, exactly as the ACC 2027 encoding:

```
x = [ clip(e_q/e_ref), clip(ω/ω_ref), clip(ē/e_ref) ],   ē = low-pass(e_q, τ_lp = 1 s)
```

That gives 9 channels, 18 CMG units, and a 9×18 decoder W_S initialized to 0.
The PES update is W_S ← Π[W_S + η_S (y*_S − σ) a_Sᵀ − λ_S W_S], with per-axis targets:

| gain | target y* | rationale (MIT-rule sign heuristic) |
|---|---|---|
| k_p | tanh(\|e_q\| / e_ref) ∈ [0, 1) | stiffen while error magnitude persists; relax toward nominal when small |
| k_d | clip(κ_d (e_q/e_ref)(ω/ω_ref)) ∈ [−1, 1] | e·ė > 0 (error growing, constant reference) → more damping; converging → less |
| k_i | tanh(\|ē\| / e_ref) ∈ [0, 1) | raise integral action only under a persistent low-frequency bias |

**Latched-regime reading (from ACC 2027 §IV-D).** Once S's gates latch, a_S is constant and σ becomes a
first-order low-pass of y*. The gains are then error-scheduled with a lag
τ_S = h / (η_S ‖a_S‖² + λ_S).

**Limitation.** The k_d heuristic uses ω, not the reference-rate error, so on moving references it is
approximate. This is deliberate for v0: giving only the tuner reference-rate knowledge would confound
the comparison.

**Status.** This is our design, inspired by the PES self-tuning idea. It is *not yet* the published
STN-PID-PES law. Aligning with Olivares et al. is Q1.

## 4. Residual layer R (unchanged from ACC 2027)

```
u = sat_ℓ( u_0 + β ℓ ⊙ s ),   s = clip(W_R a_R),   PES target y*_R = clip(−k_e e_q)
```

β = 0.5, η_R = 8×10⁻⁴, λ_R = 10⁻⁶, G = 10⁵. |u − u_0| ≤ β ℓ per axis for any W_R.

## 5. The dual loop and why it may help

```
e_q, ω ─► [S: CMG + PES] ─► K(t) ─► PID ─► u_0 ─► [R: CMG + PES] ─► u ─► allocation ─► plant
```

- **R** learns a bounded correction on the command side.
- **S** reshapes the linear feedback itself, within a provably positive box.

From ACC 2027: latched R acts as lagged proportional action worth about 1.5× the PD stiffness. S can
supply stiffness *and damping* scheduling that R cannot, since R's target is proportional only.

Hypothesis H2 (PLAN) is that the combination reduces error beyond either module alone. The risk is
that both modules add stiffness and over-stiffen Hardstep.

## 6a. The published STN-PID-PES law (Olivares et al., NCA 38:192, 2026) — read 2026-09-12

Source: `2026 Springer NCA Sel-Tuning Neuromorphic_Q2.pdf` in this folder (Sect. 3, Algorithms 1–3, Table 1).

- **Plant and loop.** DJI Tello position loop at 200 Hz. u = desired velocity command; ε = ξ_ref − ξ.
- **PID** (Eq. 1): u = K_p ε + ∫K_i ε dt + K_d Δε, with diagonal gains Kp = diag(60, 60, 160), Ki = 200·I,
  Kd = diag(13, 13, 20).
- **Synaptic derivative.** Δx = (x_τ − x_2τ)/τ, where x_τ is x low-passed with time constant τ = 0.05 s
  (Nengo synapse), and x_2τ likewise with 2τ.
- **Cost and gradient** (Eq. 3): E = ½∫ε² dt. Gradient descent gives
  - K_p ← K_p + μ_Kp ε² ∂ξ/∂u
  - K_d ← K_d + μ_Kd ε Δε ∂ξ/∂u
  - K_i ← K_i + μ_Ki ε ∫ε ∂ξ/∂u

  with μ_Kp = 0.01, μ_Kd = 0.03, μ_Ki = 9×10⁻⁴ (per 5 ms step). **No projection, no leak.**
- **Sensitivity.** STN-PID uses ∂ξ/∂u ≈ Δξ/Δu (Eq. 4), which is singular as Δu → 0. STN-PID-PES learns
  Ŷ ≈ Δξ/Δu with PES from X = Δu (an ensemble of J = 200 LIF neurons; Eq. 5: Δd = κ e a, e = Y − Ŷ),
  and uses Ŷ in the gradients.
- **Neural budget.** 9 ensembles × 200 neurons.
- **Reported result.** Real flights, PES version vs non-PES version: ITSE −15 to −66%, smoother gains,
  lower energy. **No comparison with a fixed-gain PID and no stability proof** (Sect. 5.2 names stability
  as future work).

**Reading.** This is the classical MIT-rule gradient adaptation (Åström–Wittenmark). It is known to be
unstable for large adaptation gains or excitation. Parks (IEEE TAC 11(3):362–367, 1966) replaced it with a
Lyapunov redesign for exactly that reason. Our v0 CF2 Hardstep divergence (gains driven up while the rotors
saturate) is the same mechanism, so *bounded* adaptation is the gap this project can close.

## 6b. CMG mapping of STN-PID-PES to quaternion attitude (v1)

**Sign conventions.** Passive quaternions give e_q ≈ (θ − θ_d)/2, so the paper-form error is ε := −e_q
(half-angle units). The PID base is unchanged: u_0 = K_p ε + K_i ∫ε + K_ω(−ω), where ∫ε = −ξ and the derivative
channel signal is −ω (∂u/∂K_d). The attitude sensitivity ∂θ/∂u is positive per axis.

**Normalized multiplicative gradients.** Airframe inertias differ by 10³, so the paper's absolute rates cannot
transfer. With K_g = K_g0 ⊙ m_g:

```
ṁ_p = μ_p (ε/e_ref)² Ŷ
ṁ_d = μ_d (ε/e_ref)(−ω/ω_ref) Ŷ
ṁ_i = μ_i (ε/e_ref)(∫ε/ξ_ref) Ŷ
```

**CMG sensitivity estimator** (replaces the LIF ensemble):
- X = Δu/ℓ, the synaptic derivative (τ, 2τ; τ = 0.05 s) of the applied torque command, normalized per axis.
- Six paired CMG units with a 3×6 PES decoder initialized to 0, so Ŷ = 0 and no adaptation happens until
  the estimator learns.
- Target Y = clip(κ_s (ω̄/ω_ref)/(Δu/ℓ)), with ω̄ = ω low-passed at τ. Samples with |Δu/ℓ| < 10⁻³ are
  skipped (the singular set).
- Learning rate η_s = 8×10⁻⁴, leak 10⁻⁶.

**Variants:**
- `stn`: faithful. The multipliers integrate the gradients with no bound, leak, or freeze.
- `stn_b`: bounded, our contribution.
  - (i) projection m ∈ [0.5, 1.5];
  - (ii) σ-leak toward nominal, ṁ ← ṁ − λ_m(m − 1);
  - (iii) conditional adaptation: while the axis command or any rotor saturated at the previous step,
    increases of m_p and m_i are blocked (decreases and leak still act).
- `dual_stn_b`: stn_b plus the ACC 2027 residual R.

**Properties of stn_b.** Positive gains in a box (projection). Frozen-time Hurwitz on the box (§2 items 2–3).
Baseline recovery when Ŷ ≡ 0. Adaptation cannot raise gains during saturation, which removes the windup path
seen in v0. The slow-variation stability bound (Q2) remains open. With λ_m > 0 and bounded gradients, ‖ṁ‖ is
bounded uniformly, which is the quantity such a bound needs.

## 6c. Why the closed-loop sensitivity estimate has the wrong sign (derived 2026-09-12)

Take one axis with small errors: j θ̈ = u, and the PD law u = −(k_q/2)(θ − r) − k_ω θ̇ (from e_q ≈ (θ − r)/2).
Differentiating,

```
u̇ = −(k_q/2)(θ̇ − ṙ) − k_ω θ̈ = −(k_q/2)(θ̇ − ṙ) − (k_ω/j) u .
```

**Regulation** (ṙ = 0), whenever the term (k_ω/j)u is small relative to (k_q/2)θ̇ (away from command peaks):

```
Δθ/Δu ≈ θ̇/u̇ ≈ −2/k_q < 0 .
```

The estimate reflects the **inverse of the feedback gain, not the plant** (open-loop ∂θ/∂u > 0). This is
the classic closed-loop identification bias (the input is correlated with the output through the controller).

In the normalized units of §6b, Y = (ω/ω_ref)/(u̇/ℓ) ≈ −2ℓ/(k_q ω_ref). Since
ℓ/k_q = ν/(2ω_n²) = 0.375 on roll and pitch, this gives Y ≈ −0.75 on both airframes.

**Tracking.** The ṙ term adds positive episodes. The time average therefore mixes signs, as the smoke test
showed (Ŷ ≈ −0.17 to −0.35).

**Consequence.** With Ŷ < 0 the MIT-rule gradient *decreases* stiffness exactly when error persists, i.e.
de-tuning. Remedies:
- (a) Use the known open-loop sign (`*_ks` ablation).
- (b) Identify the sensitivity from a signal uncorrelated with feedback: a dither, or the residual channel,
  whose contribution is not a function of the PD error.
- (c) Estimate the plant gain from the model (∂θ/∂u ≈ h²/(2j) per step).

Option (b) is a natural *dual-architecture* coupling: the residual R perturbs the command independently of
the PID. It is a candidate for v2.

## 7. v3 mechanisms (declared 2026-09-12, before any v3 run)

### 7.1 Thrust-priority allocation (TPA): protect the collective, scale the torque

With four rotors and B invertible, write f_T = B⁻¹[T, 0]ᵀ and f_τ = B⁻¹[0, τ]ᵀ.

1. **Collective feasibility.** For rotors with c_i = (B⁻¹)_{i,0} > 0, T ← min(T, min_i f_max,i / c_i).
2. **Torque scaling.** The largest α ∈ [0, 1] with 0 ≤ f_T + α f_τ ≤ f_max componentwise is

```
α* = clip( min_i  { (f_max,i − f_T,i)/f_τ,i  if f_τ,i > 0 ;   f_T,i/(−f_τ,i)  if f_τ,i < 0 } , 0, 1 ).
```

3. **Output.** f = clip(f_T + α* f_τ, 0, f_max). The clip is inactive by construction whenever f_T is feasible.

**Property (derived).** Whenever f_T is feasible, the realized wrench is exactly [T, α* τ]ᵀ.
- The collective is preserved.
- The torque *direction* is preserved, with no cross-axis leakage (contrast ACC 2027, where L_A = 3.3–4.5 is
  caused by per-rotor clipping).
- The torque magnitude is scaled by α* ∈ [0, 1].

The CF2 crash mode (v1/v2: aggressive attitude steals collective) is removed at the interface, for every controller.

**Tuner saturation flag.** Under TPA, the axis-saturation signal used by the tuners is α* < 1 or a command clip.
Headroom (v2 gate) is computed from the rotor forces as before.

### 7.2 Sensitivity identified from a dither (removes the §6c sign bias)

A small multisine torque dither enters through the residual/command channel:
d_i(t) = a_d ℓ_i sin(2π f_i t), with a_d = 0.02 and f = (9, 11, 13) Hz. The closed-loop attitude bandwidth is
about 0.6 Hz and the latched-residual corner about 1.5 Hz, so the feedback barely reacts at the dither frequencies.
The response is open-loop: j θ̈ ≈ a_d ℓ sin(wt), so ω ≈ −(a_d ℓ/(j w)) cos(wt).

**Lock-in demodulation:**

```
z_i ← z_i + (h/τ_d)(ω_i cos(w_i t) − z_i),   τ_d = 0.5 s
ŝ_i = −2 j_i w_i z_i / (a_d ℓ_i)                        (≈ +1 for the nominal open-loop plant)
```

This is perturbation-based gradient estimation, as in extremum seeking (Krstić & Wang, Automatica 36(4), 2000).
It avoids closed-loop identification bias (Forssell & Ljung, Automatica 35(7), 1999) because the excitation is
external and uncorrelated with the feedback error.

**PES target.** The CMG-PES sensitivity estimator keeps its structure (X = Δu/ℓ, paired CMG units, PES decoder)
but learns the target Y = clip(ŝ) instead of the singular closed-loop ratio Δθ/Δu. The sign is robust; the
magnitude scales with the j_tune mismatch.

**Cost.** The dither adds a 2% ℓ torque ripple at ≥ 9 Hz. Its attitude effect is a_d ℓ/(j w²), about
10⁻³–10⁻⁴ rad, and is charged to the controller's own error.

### 7.3 Correction to §7.2: an external dither removes the sign bias, not the closed-loop magnitude bias (2026-09-12)

**Setup.** An external dither removes the correlation (sign) bias of §6c. The measured response is still the
closed-loop one. On one axis at the dither frequency, with e_q ≈ θ/2 and k = m k_q/2:

```
J θ̈ + m k_ω θ̇ + k θ = d,   d = A sin wt,   H(jw) = ω/d = jw / (k − J w² + j m k_ω w)
z_s = LPF(ω sin wt) → A Re H / 2,          z_c = LPF(ω cos wt) → A Im H / 2
```

**Quadrature estimate (§7.2).**

```
ŝ_quad = −2 j w z_c / A = j w² (J w² − k) / ((k − J w²)² + (m k_ω w)²)
```

- It is unbiased only when k ≪ J w² and m k_ω ≪ J w, which holds at the quaternion bandwidth (wn = 4): predicted
  X2 1.59 / 1.41 / 0.42, observed 1.58 / 1.38 / 0.42.
- At the 6-DOF tuned bandwidth (wn = 20–24) it is biased low: predicted CF2 roll 0.62 where the truth is 1.
- The resulting gain law raises m, which raises k and m k_ω, which biases ŝ further. This is a self-reinforcing loop,
  observed in the 6-DOF pilot (CF2 roll m → 1.97).

**Known-controller (indirect) estimate.** Use the complex response and the known PD gains:

```
H = 2 (z_s + j z_c)/A,   1/H = m k_ω + j (J w² − k)/w
Ĵ = (w Im(1/H) + k) / w²,   ŝ = j_tune / Ĵ,   consistency c = Re(1/H) / (m k_ω)  (≈ 1 if the axis model holds)
```

- In the 6-DOF pilot it is correct on CF2 (ŝ 0.95–1.01, c ≈ 0.97) and on X2 yaw (ŝ 0.42, c 0.92).
- X2 roll/pitch fail with c = 0.09–0.37, so the check flags that the single-axis model does not hold there.
- The residual R is additional unmodelled feedback. A dual controller must either exclude R from the
  identification window or include R's latched-regime gain (ACC 2027: added stiffness 1.5–1.63× PD, pole 0.9952)
  in 1/H. v4 quaternion evidence: ŝ = −12 on CF2 Hardstep with R active.

**Inversion noise (v4).** Inverting the instantaneous ŝ with direction-asymmetric (headroom-scaled) updates rectifies
the estimator noise into a downward gain drift. Estimate first, then invert: average ŝ (or H) on a slow second stage,
update log m symmetrically, and gate on c.

## 8. Generalizing S beyond PID (v5/v6, 2026-09-25) -- extends §2, does not replace it

**Context.** `AdvancedBaseline` (ACC 2027 repo) gives lqr, backstepping, mpc, nmpc a common form once
feedforward is included: acc = ω̇_d − k_1 e − k_2 ω_e, τ_0 = clip(J·acc + gyro, −ℓ, ℓ) (mpc: k_1, k_2 replaced
by K_0[:,0], K_0[:,1], the closed-form finite-horizon LQ gain; nmpc: same nominal law plus a grid-searched
offset, which S does not touch). None of these families has an integral term in this form.

**§2 items 1-2 already cover this, verbatim, and were not re-derived.** Item 1 (positivity/boxing) and item 2
(frozen-time Hurwitz "for any positive diagonal K_p, K_d") make no reference to where K_p, K_d came from --
only that they are positive and diagonal. k_1, k_2 (lqr/backstepping/nmpc-nominal) and K_0[:,0], K_0[:,1] (mpc,
positive by construction: Q, R positive-definite in `_mpc_first_gain`'s finite-horizon LQ solve) satisfy that
hypothesis exactly. So S: K_g(t) = K_g0 ⊙ (1 + β_g σ_g), σ_g ∈ [−1, 1] gives K_g(t) ∈ [(1−β_g)K_g0, (1+β_g)K_g0]
and frozen-time Hurwitz on the PD part, for every family here, by the SAME argument already on file -- the
generalization is free once the common (e, ω_e)-linear form is recognized, which is the substance of this
section, not a new stability proof.

**e_ref must be per-family (v5's empirical finding, now stated as the reason).** §3's targets use tanh(|e_q|/e_ref)
and a (e_q/e_ref)(ω/ω_ref) cross term -- e_ref is a SCALE, not a stability parameter (it does not appear in §2's
box or Hurwitz conditions at all). v0's e_ref = 0.1 rad was never derived; it was whatever PID's own,
feedforward-free, ~10x larger baseline error happened to need. v5 ran it unchanged on families whose baseline
error is an order of magnitude smaller (feedforward already present) and found σ stayed within a few percent of
0 (multiplier max 1.01-1.05 on Hard45): not a stability finding, a **dead-band** finding -- tanh(x) ≈ x for
|x| ≪ 1, so an e_ref ten times too large linearizes the target to near-zero for every error this baseline
actually produces. Rescaling e_ref to the family's own error scale (probe: e_ref = 0.005 rad ≈ lqr/backstepping's
own Hard45 mean error, vs. the unchanged 0.1 rad) moved σ back into the regime tanh was designed for and
recovered PID-scale engagement (multiplier mean 1.06-1.13, matching PID's own 1.05-1.09) and a larger gain
(+8-10% dual-vs-residual, vs. PID's 2-5%). **v6 rule:** e_ref_{family,platform} := that family/platform's own
`*_base` mean error on Hard45 (representative, non-saturating, already computed by v5 -- read from
`results/v5_2026-09-25/{family}/{platform}/hard45/base/summary.json`, not re-derived by hand, to avoid
transcription error).

**Saturation-aware gate for S (new), mirroring R's own eq:gate exactly, in kind not just in spirit.** R's gate
(ACC 2027 eq:gate) blocks an axis's residual only when the baseline is already loaded there AND the residual
opposes it -- it never blocks a correction that is *helping* an already-loaded axis. §2's frozen-time Hurwitz
result says nothing about *why* Hardstep still regresses under S (v5 deep-dive, PLAN.md): the answer is not
instability, it is the same latched-decoder-lag mechanism already documented for R (ACC 2027 Sec. VI-E) -- a
gain boost learned during a slew persists a little into the settling tail, exactly as R's residual does, on an
axis that is no longer the bottleneck once it un-saturates. **Applying R's own principle to S**: a *decrease*
in gain (σ_g < 0) can only reduce commanded torque, never push an already-loaded axis further past its limit,
so it is never blocked. An *increase* (σ_g > 0) on an axis already at |τ_{0,i}| ≥ ℓ_i cannot produce a larger
realized torque -- it only inflates a command that gets clipped anyway, at the cost of a larger post-slew
settling transient once the axis un-saturates (R's own documented failure mode). Define, per axis i, using the
same one-step-delayed convention this codebase already uses for headroom (negligible at h = 0.5 ms):

```
loaded_i[k] := | τ_{0,i}[k−1] | ≥ ℓ_i                      (which axis was already at its box last step)
m_i(σ_g)    := 1 + β_g σ_{g,i}                              (§2's unclipped multiplier, per gain-group g)
m̃_i(σ_g)    := 1 + β_g σ_{g,i} · [ σ_{g,i} ≤ 0  or  ¬loaded_i[k] ]     (gated multiplier, applied to K_g0)
```

**Proposition (gated S, bounded and exactly baseline-recovering).** For every axis i and gain-group g:
(i) m̃_i ∈ [(1−β_g), (1+β_g)] -- the gate only ever moves m̃_i *toward* 1 relative to the ungated m_i, so it
cannot widen §2's own box; (ii) on any axis with loaded_i[k] = 1, m̃_i ≤ 1 -- the gate exactly recovers the
un-boosted gain on that axis whenever an increase was the ungated proposal, mirroring R's own exact-recovery
structure (ACC 2027 Prop. 1(iii)) rather than merely bounding the deviation; (iii) §2 item 2's frozen-time
Hurwitz argument is unaffected, since m̃ is still positive and diagonal by (i). Proof of (i)-(ii): immediate
from the definition -- the indicator is 1 exactly when σ_{g,i} ≤ 0 (m̃_i = m_i ≤ 1, no widening) or the axis is
unloaded (m̃_i = m_i, no change needed), and 0 exactly when σ_{g,i} > 0 and loaded_i[k] (m̃_i = 1, the exact
nominal gain). (iii) follows because Hurwitz was established (§2) for *any* positive diagonal gain in the box,
and (i) keeps m̃ in that same box.

**Combined dual envelope (S gated, R gated, both from ACC 2027 Prop. 1 and the proposition above).** With gated
S setting K(t) and gated R adding a command-side correction bounded by β_R ℓ per axis (Prop. 1(iii)), the full
realized command at any step satisfies
τ_i ∈ [ (1−β_g) K_{g0,i} · (linear PD/PD-ff term)_i − β_R ℓ_i ,  (1+β_g) K_{g0,i} · (linear PD/PD-ff term)_i + β_R ℓ_i ],
clipped to [−ℓ_i, ℓ_i] by the same outer sat_ℓ every family already uses -- i.e. **the dual architecture's
worst-case commanded torque is bounded in closed form by the nominal baseline's own box, regardless of what S
or R have learned**, for every family covered here. This is the audit-relevant statement for hardware: nothing
in the learning dynamics of either module can command outside a range fixed entirely by the a-priori
hyperparameters (β_g, β_R, e_ref only rescales *when* the box is used, never its width), so a hardware anomaly
under this architecture is, by this proposition, not a symptom of an unbounded or unstable command -- it would
have to come from the sim-to-real gap (actuator dynamics, delay, mismatch) the proposition does not model, which
is exactly the boundary Gandhi asked this section to establish before Phase 5.

**Q3 (interaction, revisited empirically).** v5/v6's logged `WS_final_fro` and `WR_final_fro` give a first,
cheap check of whether S and R fight each other (large, oppositely-trending norms) or are independent (comparable
growth to their single-module runs) -- worth reading off the v6 campaign once run, not yet done.

- **Q1.** ~~The exact published self-tuning law.~~ Resolved 2026-09-12; see §6a–6b.
- **Q2.** A quantitative slow-variation bound on ‖K̇‖ that keeps the time-varying loop stable (an
  input-to-state stability statement analogous to ACC 2027 Theorem 1).
- **Q3.** Interaction: does S learn to cancel R, or R to cancel S? Monitor the decoder norms and the
  correlation of the two contributions.
- **Q4.** 6-DOF extension. Position-loop PID gains become a second tuned block; the Omnicopter needs a
  6-channel wrench and 8-rotor allocation. Its existing `residual.py` already has 6-channel CMG–PES.
  - *Pilot 2026-09-12.* On the tuned cascade, attitude-level R and S change position error by ≤ 1%.
  - Test a position-only vs attitude-only split of the FF6 6-channel augmentor next.
- **Q5.** Why does the X2 roll/pitch dither response not fit the single-axis model at wn_att = 20 (c = 0.09–0.37)?
  Candidates:
  - J_xz = −0.0021 coupling into the soft yaw loop;
  - outer-loop coupling through ω_des;
  - mixer moment arms.
- **Q6 (opened 2026-09-25, extends Q2).** §2 item 5's slow-variation bound was stated for PID and never derived
  quantitatively even there. It is still open for lqr/backstepping/mpc/nmpc under §8's gated S -- the gate makes
  m̃ *discontinuous* in time at the loaded/unloaded boundary (a hard indicator, matching R's own eq:gate, which
  has the same property and is not covered by a slow-variation argument either). Whether the switching itself
  needs a separate argument (e.g. a dwell-time or hysteresis bound) or is benign because the box (§8 Proposition)
  bounds the consequence regardless of the switching rate is open; the v6 campaign's saturation-fraction and
  qerr traces on Hardstep are the empirical check, not a substitute for resolving this.
