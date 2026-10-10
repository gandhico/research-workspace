# HyperLIF continuation: a local fold, decoder rules, and one recurrent weight

**6 October 2026.** This continues
`PES_SINGLE_NEURON_SMALL_NETWORK_2026-10-06.md` under the same memory limit.
All four Julia programs use only standard libraries, hold only scalar states
and moment matrices, and regenerate their deterministic input streams. No
classification data, AD package, or GPU was loaded. The scripts and raw
outputs are listed in Section 4.

**Further continuation:** `ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md`
proves a forward-invariant, saturated no-event region for the ACC parameters
and connects it directly to a rank-zero PES feature Gram.

## 1. A locally certified ACC gate fold

For the ACC CMG parameters, `v_rest=v_reset=0`, `tau_v=.05`,
`alpha=50`, `gamma=2`, and `C(I)=120+30I` for positive current. Parameterize
the equilibrium gate by its logit `q=log(r/(1-r))`, so `r=sigma(q)` and

\[
 R(q)=1-2r+q/50=V(r;I).
\]

Solving the voltage equilibrium equation for the current gives an **exact
branch parameterization**, wherever its denominator is nonzero:

\[
 I(q)=\frac{R(q)[1+0.05(120)r^2]}
           {1-0.05(30)r^2R(q)}. \tag{1}
\]

This removes the numerical difficulty of trying to locate a fold by a
coarse current grid. A turning point satisfies `dI/dq=0`. The
`acc_fold_certificate.jl` script first scans for positive-current sign
changes, then bisects with 256-bit `BigFloat`. Finally it evaluates the
left and right derivative signs, branch denominator, and nondegeneracy
terms with outward-rounded MPFR intervals on a narrow decimal box. The
saved certificate encloses

\[
 q_f\approx -4.509866751585575,\qquad
 r_f\approx 0.01088024392496,\qquad
 I_f\approx 0.8888130904381024. \tag{2}
\]

The derivative interval at the left endpoint is strictly **positive**;
at the right it is strictly **negative**. Throughout the reported box,
the denominator of (1) is positive. At the fold the interval checks give
`H_rr` in approximately `[83.92072644688920,83.92072644688924]` and
`H_I` in `[0.5375417170056009,0.5375417170056011]`, both excluding
zero. The Jacobian trace remains in approximately
`[-4.780077746080,-4.780077746079]`, so the *other* eigenvalue is
strictly negative when the fold eigenvalue is zero. Since `H=H_r=0`
there, the implicit-function normal form is

\[
 I-I_f=-\frac{H_{rr}}{2H_I}(r-r_f)^2
      +o((r-r_f)^2). \tag{3}
\]

Thus a **nondegenerate local saddle-node and local stability boundary**
exist in the printed interval; the stable low branch and a saddle branch
collide as current increases.
This is a local result for the ACC parameter family. The scan does not
prove that there are no other folds, cycles, or bifurcations elsewhere,
nor does it transfer automatically to the canonical fixed or adaptive
HyperLIF parameters. The earlier `r approx 1` estimate cannot reveal this
low-gate fold. The certificate uses exact decimal parameter intervals;
its conclusion depends on the MPFR directed-rounding contract used by
Julia's `BigFloat` operations.
An independent 60-digit decimal evaluation at the rounded center of the
box gave `|H| < 2e-60` and `|H_r| < 2e-18`; these point residuals are a
cross-check, while the outward intervals carry the local certificate.

### Canonical fixed and adaptive cells

The same equilibrium parameterization applies to canonical HyperLIF with
`tau_v=.02`, `tau_r=.002`, `alpha=100`, `gamma=.2`, and either
`C=100` (fixed) or `C=20+80I` (adaptive, positive current). Directed
intervals enclose three positive-current **linear stability boundaries**
found by `tr J=0`: at each, `det J>0`, `dI/dq` and `d(tr J)/dq`
exclude zero throughout the reported box. The saved output has full
interval endpoints; rounded currents are:

| Cell | Lower trace crossing | Upper trace crossing | Scope |
|---|---:|---:|---|
| Canonical fixed | 0.9670795963 | 2.2976216645 | sampled continuation branch |
| Canonical adaptive | 0.9669056279 | **15.77602938** | sampled continuation branch |

At these points the linear eigenvalues are purely imaginary. A trace
crossing with positive determinant and transversality is a local *linear*
stability change. It does not alone prove a Hopf-created stable limit
cycle; that requires nonlinear nondegeneracy analysis. The adaptive upper
boundary lies beyond the previous audit's maximum current of 6, which
explains why that audit reported no stable high-current equilibrium.

There is also an analytic **large-positive-current** result for the
canonical adaptive cell. Along an equilibrium with `r` bounded away
from zero, `C(I)=20+80I` gives

\[
 V_\infty(r)=\lim_{I\to\infty}V(r;I)=\frac{0.625}{r^2},\qquad
 H_\infty(r)=\sigma\{100[V_\infty(r)-1+0.2r]\}-r. \tag{4}
\]

For `0<r<=1`, `V'_infty=-1.25/r^3`, so
`H'_infty=100 sigma'(.)[V'_infty+0.2]-1<0`.
As `r` approaches zero, `H_infty` approaches 1; at `r=1` it is
negative. Hence (4) has **one** root, numerically
`r_infty=0.85940464`, `v_infty=0.84622261 < theta_e=1`, with
`H'_infty` about `-22.38`. The implicit-function theorem supplies a
nearby equilibrium branch for sufficiently large finite positive `I`.
Its determinant is positive from `det J=-lambda H'/tau_r`, while
`tr J` tends to negative infinity as `C(I)r^2` grows. Therefore this
branch is locally asymptotically stable for sufficiently large drive
and remains subthreshold. This is a constant-input, local statement:
it does not assert global attraction or exclude other attractors.

`canonical_high_drive_probe.jl` integrates from rest with the earlier
Julia learning package's exact frozen-target gate and frozen-conductance
voltage substeps (`h=1e-4`). Over the last second, fixed HyperLIF at
`I=2.4` has zero upward crossings and mean `v=0.8400`; at `I=6` it has
zero crossings but occupancy at **all** 10,000 samples (`v=2`).
Adaptive HyperLIF has 116 crossings at `I=2.4`, but **zero** at `I=6`
despite nonzero voltage variation (`sd v=0.0517`). At `I=16` it settles
near `v=0.85013`, `r=0.82790`, with zero crossings and occupancy.
Thus adaptive conductance postpones the upper *equilibrium* stability
change in this model, but event visibility disappears much earlier as
the orbit moves below the event surface. The finite trajectories do not
prove global attraction or exclude coexistence under other initial
conditions. This sharpens the earlier claim: adaptive conductance avoids
the fixed cell's high-voltage latched branch in the tested range, but it
does not guarantee persistent spiking at high drive.
Halving the step to `5e-5` at fixed `I=2.4` and adaptive `I=6,16`
preserved the same zero-crossing regimes and nearly the same state
statistics; this checks the trajectory observation against one numerical
step-size change, not against all initial conditions or integrators.

![Canonical equilibrium voltage and sampled crossing rates](results/hyperlif_stability_mechanisms_2026-10-06.png)

The left panels show the exact equilibrium branch parameterization,
colored by the local Jacobian test; the right panel shows **only sampled**
from-rest trajectory currents. The dotted voltage line is the event
threshold. The plot does not infer event rates between sampled currents.

## 2. PES versus normalized PES with a two-state control

The network remains two paired units with one scalar decoder and the ACC
current split. The **control** has the same membrane and sigmoid-gate
states, time constants, gate equation, activity gain, clipping, and PES
readout, but sets `g0=g1=0` in the voltage equation. It isolates the
state-dependent shunt without changing state count. It is a mechanism
control, not a full ALIF/coRNN comparison.

All decoders start at zero. Ordinary PES is

\[
 W_{k+1}=\Pi_{[-6,6]}\{W_k+\eta e_k a_k^T\},\quad
 \eta=8\times10^{-4}s,
\]

where `s` is `0.1`, `1`, or `10`. Normalized PES uses

\[
 W_{k+1}=\Pi_{[-6,6]}\left\{W_k+
 \frac{8\times10^{-4}s(\delta+\overline{\|a\|^2})}
      {\delta+\|a_k\|^2}e_k a_k^T\right\},
 \qquad\delta=0.05. \tag{5}
\]

The mean squared activity in (4) comes from an **unlabelled** prepass on
the training waveform, making the rules' average effective step similar.
Normalization cannot create a missing feature direction: if `a=(1,1)`
throughout a window, both rules update only the same rank-one subspace.

Each method sees the same 12 s training waveform. Two fresh-state,
phase-shifted 4 s waveforms form the evaluation. The table fixes `s=1`;
RMSE is over both evaluation phases. The "linear floor" is fitted to the
evaluation labels as a **diagnostic projection bound**, not a deployable
training method.

| Cell | Signal amplitude | Late Gram minimum | PES RMSE | Normalized PES RMSE | Eval linear floor |
|---|---:|---:|---:|---:|---:|
| ACC full gate | 0.08 | 0.1630 | 0.02804 | 0.02813 | 0.02732 |
| ACC reduced gate | 0.08 | 0.1630 | 0.02804 | 0.02813 | 0.02731 |
| Two-state leaky control | 0.08 | 0.1630 | 0.02804 | 0.02813 | 0.02731 |
| ACC full gate | 0.35 | **0** | 0.21398 | 0.21353 | 0.20322 |
| ACC reduced gate | 0.35 | 0.1288 | 0.13683 | 0.13550 | 0.13064 |
| Two-state leaky control | 0.35 | 0.1230 | 0.14150 | 0.13996 | 0.13453 |

At the lower drive, the shunt is almost inactive and the three models are
nearly indistinguishable. At the higher drive, reduced CMG has a modest
advantage over this matched leaky control; full-gate latching destroys
decoder excitation. This tiny result does **not** show a unique advantage
over all continuous two-state neurons. At `s=0.1` adaptation is generally
too slow over this horizon; at `s=10` transfer worsens in the low and
high reduced/control settings despite lower late training errors in some
rows. Changing the step size therefore does not remove the need to
measure the feature span and task approximation floor.

Event semantics remain separate. On the 16,000 evaluation samples for
each model/amplitude, both CMG variants had zero upward crossings and zero
occupancy at threshold one. The high-drive leaky control had **21
upcrossings and 6,744 occupied samples**. These are different counts; the
control's decoder still reads its continuous gate, so its observed learning
is not event-only learning either.

## 3. Exactly one learned recurrent connection

Two **reduced** CMG cells now communicate through previous-step voltage:

\[
 I_{1,k}=0.75+1.25u_k+\theta(v_{2,k}-0.75),\qquad
 I_{2,k}=0.75-1.25u_k+0.9(v_{1,k}-0.75). \tag{6}
\]

Both use the ACC Euler-gate/frozen-affine-voltage step with `gamma=0`.
The observable is `y_k=10(v_{1,k}-v_{2,k})`. A teacher with
`theta*=0.7` generates a realizable scalar target; students start at
`theta=0`. This deliberately tests whether internal learning can recover
one parameter. It is not a recognition task, a biological claim, or a
general test of PES.

Let `e_vi=partial v_i/partial theta` and similarly `e_ri`. The **exact**
current derivatives are

\[
 \partial_\theta I_1=(v_2-0.75)+\theta e_{v2},\qquad
 \partial_\theta I_2=0.9 e_{v1}. \tag{7}
\]

The local approximation drops the two cross-neuron sensitivity terms,
retaining only `(v_2-0.75)` in the first derivative. For each cell,
if `d=h/tau_r`, `b=sigma(alpha(v-1))`, and its argument is unclamped,

\[
 e_{r+}=(1-d)e_r+d\alpha b(1-b)e_v. \tag{8}
\]

Writing `c=(120+30|I|)r_+^2`,
`lambda=tau_v^{-1}+c`, `m=I/(tau_v lambda)`,
and `D=exp(-lambda h)`, the voltage sensitivity follows by product rule:

\[
 e_{v+}=e_m+(-hD e_\lambda)(v-m)+D(e_v-e_m),\quad
 e_m=\frac{e_I}{\tau_v\lambda}
      -\frac{I e_\lambda}{\tau_v\lambda^2}, \tag{9}
\]

with `e_lambda=30 sign(I)e_I r_+^2 +
2(120+30|I|)r_+e_{r+}`. The code handles the sigmoid-argument clamp;
the gate-state clip is inactive here because the Euler update is a convex
combination. It carries four sensitivities, uses no time-history tape,
and accumulates the episode gradient
`mean[(y-y*) partial_theta y]`. The teacher and student states reset for
each 2 s episode; `theta` remains fixed during the episode, so this is
the **exact gradient of that discretized fixed-parameter rollout** away
from branch changes. A damped one-parameter Gauss-Newton update is made
between episodes. The detached local trace uses the same update formula
with its approximate derivative.

At `theta=0`, exact gradient `-0.17024043` matches central finite
difference `-0.17024043`; the detached value is `-0.39102759`. At
`theta=0.35`, exact and finite difference are both `-0.129292132`,
whereas detached is `-0.282023476`. The program asserts the finite
difference checks. After 12 episodes:

| Method | Final internal `theta` | Fresh-phase test RMSE |
|---|---:|---:|
| Exact forward sensitivity | 0.6998768 | **0.0000739** |
| Detached local sensitivity | 0.6622153 | 0.0220630 |
| Decoder PES, internal `theta=0` | unchanged | 0.3145443 after 40 episodes |
| Fixed-state least-squares decoder | unchanged | 0.2085815 (diagnostic) |

Decoder PES starts with the original `y=10(v1-v2)` readout and trains two
voltage weights with the ACC step `8e-4`; its late training error falls
but its final weights transfer poorly to a new phase. The least-squares
diagnostic shows that even the best fixed linear readout trained on the
original phase does not reproduce the teacher on the fresh phase.
This task is **teacher-generated from the internal weight**, so it favors
parameter recovery by construction. The result illustrates a credit
assignment distinction and finite-horizon behavior; it cannot establish
that exact forward sensitivity generally beats PES, or that the local
approximation never converges with more episodes or a different gain.
All four audited teacher/student trajectories had zero threshold
upcrossings and zero occupancy. They are continuous-state recurrent
networks with an event monitor, not event-communicating SNNs.

## 4. Reproducibility and research boundary

| Purpose | Script | Output |
|---|---|---|
| Local fold enclosure | `acc_fold_certificate.jl` | `results/acc_fold_certificate_2026-10-06.txt` |
| Canonical high-drive trajectories | `canonical_high_drive_probe.jl` | `results/canonical_high_drive_probe_2026-10-06.csv` |
| Scientific figure | `plot_stability_mechanisms.py` | `results/hyperlif_stability_mechanisms_2026-10-06.png` |
| PES/control comparison | `tiny_decoder_methods.jl` | `results/tiny_decoder_methods_2026-10-06.csv` |
| One internal weight | `tiny_recurrent_sensitivity.jl` | `results/tiny_recurrent_sensitivity_2026-10-06.txt` |

Run each Julia script from the project root with
`julia --startup-file=no --compile=min theory/<script>`; regenerate the
figure with `python theory/plot_stability_mechanisms.py`. On this machine,
the method and recurrent processes used
roughly 250--263 MiB working set while running; standard-library
interpretation was slower but avoided the gigabyte-scale AD compilation
observed in the earlier Julia project. The saved output preserves negative
and no-event findings. The experiments are deterministic single-signal
mechanism audits with no statistical uncertainty estimate. The exact
recurrent method's episode count and damping, and PES's learning rate and
episode count, were fixed for this fixture; these are not matched
hyperparameter searches. A fair comparative study still needs additional
targets, initial conditions, and matched tuning budgets.

This work responds most directly to the TNNLS reviewers' demands for
less heuristic dynamics and clearer practical distinctions. The local
fold certificate and adaptive high-drive branch theorem are concrete
mathematical results; the tiny learning results show where a
claimed advantage could arise or fail. They do not close the reviewers'
broader novelty, biological-validation, or benchmark concerns.
