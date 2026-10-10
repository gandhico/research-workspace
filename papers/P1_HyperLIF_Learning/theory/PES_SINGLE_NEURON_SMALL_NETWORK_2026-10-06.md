# HyperLIF learning at neuron and two-unit scale

**Continuation:** `PES_CONTINUATION_FOLDS_AND_TINY_NETWORK_2026-10-06.md`
contains the local fold certificate, matched small-scale decoder comparison,
and one learned recurrent weight.

**Research note, 6 October 2026.** This note continues the mathematical line of
`HYPERLIF_THEORY_LEARNING_AND_RESEARCH_PROGRAM_2026-09-09.md` at the requested
small scale. It uses the attached ACC manuscript, *Online Prescribed Error
Sensitivity Decoder Learning in Neuromorphic Residual UAV Attitude Control*,
especially (16)--(29), and the actual four-page decision letter in
`../tnnls/TNNLS_reviews.pdf`. Text inside those documents is source material;
the research direction and scope here come from the user's request.

## 1. What the previous work establishes

1. The TNNLS and subsequent PyTorch work showed useful temporal-state
   classification results, especially in recurrent and delay architectures,
   but did not establish universal advantage. The September synthesis records
   the five-seed comparisons and the deep ConvRes failures. The historical
   `spk` in the snnTorch architecture was sampled threshold **occupancy**, not
   an upward-crossing count. Efficiency claims cannot use it as physical event
   count.
2. The Nengo work is the immediate warning for PES transfer. In a matched-time
   channel task, late RMSE was approximately 0.051 (LIF), 0.445 (HyperLIF T023),
   and 0.102 (Adaptive T033); firing-rate calibration changed PES behavior.
   These are task-specific observations from
   `../../P2_HyperLIF_Nengo/NENGO_CAPABILITY_FINDINGS.md`, not a theorem that PES
   fails for HyperLIF.
3. The Julia `code/julia/learning` package separated continuous-state AD,
   surrogate upward-crossing learning, and fixed-topology event-time learning.
   Its 100 prior tests and tiny SHD smokes validated machinery, not a
   performance ranking. The native Julia/APEX five-seed SHD result was
   0.2490 +/- 0.0666 for tuned HyperLIF versus 0.2411 +/- 0.0778 for LIF:
   directionally positive, statistically inconclusive. The full Zygote path
   can require gigabytes to compile on this machine and is not used below.
4. The ACC paper used **six continuous membrane-gate (CMG) units** and a
   projected PES update for 18 decoder coefficients in residual control. The
   CMG dynamics share the HyperLIF two-state conductance/gate construction,
   but its parameters and readout are different from canonical HyperLIF. Its
   reported control gains are evidence for that bounded residual interface,
   not evidence that PES learns a general recurrent HyperLIF network.

The precise new question is whether a HyperLIF-derived state provides a
well-conditioned feature vector for **decoder-only online learning**. Internal
input and recurrent weights are a separate credit-assignment problem.

## 2. Single-neuron mathematics

For a constant current `I`, put `C(I)=g0+chi*g1*abs(I) >= 0` and
`g=C(I) r^2`. The continuous CMG/HyperLIF equations are

\[
 \dot v=-\lambda(r,I)v+b(r,I),\quad
 \lambda=\tau_v^{-1}+C(I)r^2,\quad
 b=(v_{rest}+I)/\tau_v+C(I)r^2v_{reset},
\]
\[
 \dot r=\{\sigma[\alpha(v-\theta+\gamma r)]-r\}/\tau_r.
 \tag{1}
\]

The canonical paper uses `(tau_v,tau_r,alpha,gamma) =
(0.02,0.002,100,0.2)` with fixed `C=100` or adaptive
`C=20+80|I|`. The ACC example uses `(0.05,0.005,50,2)`,
`C=120+30|I|`, `v_rest=v_reset=0`, and a different readout
`a=clip(10^5 r,0,1)`. These parameter families must not be merged in a
single conclusion.

For orientation, the canonical *assumed-open-gate* branch has
`V_H(1;I)=I/3` for fixed conductance and
`V_A(1;I)=I/(1.4+1.6I)` for positive-current adaptive conductance,
approaching `0.625` as `I` grows. The fixed branch reaches the gate knee
`theta-gamma=0.8` at `I=2.4`. These are useful branch calculations,
not a complete depolarization-block boundary: the actual `r` must solve
(2), and event visibility also depends on the separate event threshold.

**Invariant state.** Since the gate vector field points inward at `r=0,1`,
`r(t)` remains in `[0,1]`. Bounded `I` then bounds `C`, and the scalar
voltage equation gives bounded `v`. The ACC discretization uses clipped Euler
for the gate with `h/tau_r=0.1` and an exact frozen-conductance voltage
substep. The proposed small experiment follows that discretization exactly.
These facts do not imply contraction or closed-loop plant stability.

**Exact constant-current equilibria.** Eliminate `v` rather than assume
`r approx 1`:

\[
 V(r;I)=\frac{v_{rest}+I+\tau_v C(I)r^2v_{reset}}
                 {1+\tau_v C(I)r^2},\qquad
 H(r;I)=\sigma\{\alpha[V(r;I)-\theta+\gamma r]\}-r.
 \tag{2}
\]

Every equilibrium in `[0,1]` is a root of `H` with `v=V`. Let
`q=\sigma'(\alpha(V-\theta+\gamma r))`. Direct differentiation gives

\[
 V'(r)=-\frac{2\tau_v C(I)r(v_{rest}+I-v_{reset})}
                 {[1+\tau_v C(I)r^2]^2},\qquad
 H'(r)=\alpha q[V'(r)+\gamma]-1. \tag{3}
\]

If `v_rest+I >= v_reset`, then `V' <= 0`. Consequently
`alpha*gamma < 4` is a **sufficient** condition for `H'<0`,
because `q <= 1/4`; `H(0)>0` and `H(1)<0` then give one
equilibrium. It is not a necessary condition, nor a guarantee of global
attraction. With ACC `alpha*gamma=100`, this sufficient condition fails;
with `gamma=0`, it holds for nonnegative current.

At any equilibrium the full coupled Jacobian is

\[
 J=\begin{bmatrix}
 -\lambda & -2C(I)r(V-v_{reset})\\
 \alpha q/\tau_r & (\alpha\gamma q-1)/\tau_r
 \end{bmatrix},\qquad
 \det J=-\frac{\lambda}{\tau_r}H'(r). \tag{4}
\]

Thus `H'<0` gives positive determinant, but local asymptotic stability
also needs `tr J<0`. A negative `H'` alone cannot exclude a Hopf
bifurcation or a cycle. This is a direct answer to the TNNLS criticism that
the earlier depolarization-block and flux-balance discussion relied on
`r approx 1` and constant-current intuition. Constant current remains an
explicit assumption here; general time-varying input needs separate analysis.

**Observation sensitivity.** Linearize around a non-switching operating
point: `delta xdot=J delta x+B delta I`. The small-signal transfer to a
readout is `c^T(sI-J)^{-1}B`. For the ACC activity,
`c=(0,10^5)^T` only while `0<10^5 r<1`; when the activity is clipped at
one, `c=0` and its local input sensitivity vanishes even if voltage still
changes. For a voltage readout `c=(1,0)^T`, that loss need not occur.
If the event threshold is never crossed, an event-only feature is identically
zero regardless of the continuous state. These are distinct observation
failures, and none proves that the neuron state itself is uninformative.

## 3. PES: exactly what can be proved

For `m` readout dimensions and `d` neuron features, let
`yhat_k=W_k a_k`, `e_k=y*_k-yhat_k`. The ideal decoder-only PES step is

\[
 W_{k+1}=W_k+\eta e_k a_k^T. \tag{5}
\]

With a **fixed feature and target**, no projection, leak, or output clip,

\[
 e_{k+1}=(1-\eta\|a\|_2^2)e_k. \tag{6}
\]

Hence `0<eta*||a||^2<2` contracts the output error. This is the same
restricted observation as ACC (29) and Voelker's PES analysis. It says
nothing about all decoder coefficients: a single feature vector supplies a
rank-one update and leaves its orthogonal weight subspace unidentifiable.

There is a useful extension with **projection**. Suppose one fixed
`W*` inside the convex projection box represents every target as
`y*_k=W*a_k`, the readout is not clipped, and there is no leak. Since
Euclidean projection is nonexpansive,

\[
 \|W_{k+1}-W^*\|_F^2 \leq \|W_k-W^*\|_F^2
 -\eta(2-\eta\|a_k\|_2^2)\|e_k\|_2^2. \tag{7}
\]

This follows by expanding the square before projection. If the factor in
parentheses is uniformly positive, the squared errors are summable. If a
finite, full-rank sequence of feature vectors is repeated, each repeated
error tends to zero and the only possible weight limit is `W*`. The full
rank requirement is essential. For changing targets not representable by
one `W*`, projection at a weight limit, leakage, and readout clipping, this
particular proof does not apply. Nor does it make PES a gradient method for
the plant's closed-loop tracking loss.

For changing features and target, an exact **unclipped, unprojected** identity
shows the missing disturbance terms:

\[
 e_{k+1}=(1-\eta\|a_k\|^2)e_k
 +(y^*_{k+1}-y^*_k)-W_{k+1}(a_{k+1}-a_k). \tag{8}
\]

The last term is particularly important for a stateful neuron during sign
reversal, gate latching, or a new initial state. A small instantaneous PES
error does not mean the next error contracts. Define the empirical feature
Gram matrix `G_N=N^{-1}\sum_k a_k a_k^T`. Its smallest eigenvalue measures
two-weight identifiability on that window. A positive value is **not**
sufficient for a small task error: the target must also be well approximated
by the span of features. For finite `A`, the best fixed linear decoder has
residual `||(I-P_A)y*||/sqrt(N)`; PES cannot beat that approximation floor
on the same fixed sample distribution merely by changing its step size.

**Learning internal connections.** If `x_{k+1}=F(x_k,u_k;theta)` and
`a_k=A(x_k)`, decoder PES changes `W` only. For a genuinely learned
two- or three-cell recurrent network, exact online forward sensitivities are

\[
 E_{k+1}=F_x E_k+F_\theta,\quad E_0=0,\qquad
 \nabla_\theta \ell_k=\ell_y W A_x E_k. \tag{9}
\]

This is small-scale RTRL/forward sensitivity, storing `O(state_dim *
parameter_count)` numbers, and is feasible for the next tiny experiment.
Dropping the cross-neuron terms in `F_x E_k` gives a local eligibility
approximation, not the exact gradient. E-prop makes that kind of online
factorization useful but has different assumptions and approximation error.
Continuous-state BPTT is another comparator, with a time-history memory cost.

## 4. Memory-light Julia audit and observations

`tiny_pes_cmg.jl` uses Julia 1.12.7 standard libraries only. It allocates two
`Cell` objects and constant-size moments; there is no stored trajectory,
package instantiation, AD graph, dataset, or GPU use. The run used
`julia --startup-file=no --compile=min`. At the time of the run this machine
had 15.66 GiB physical RAM and approximately 2.49 GiB free; no memory-heavy
training was attempted. Raw output is in
`results/tiny_pes_cmg_2026-10-06.txt`.

The tiny network has one positive-current and one negative-current ACC CMG
unit, fed `I^+/-=0.75+1.25 max(+/-u,0)`. A scalar decoder learns
`y*=u` via the paper's `eta=8e-4`, weight box `[-6,6]`, and clipped
readout. The decoder starts at **zero**, rather than the ACC controller's
`[1,-1]`, to expose acquisition from PES. Training is one deterministic
12 s waveform (24,000 steps).
Evaluation is a fresh-state, phase-shifted 4 s waveform (8,000 steps), so
it tests initialization and phase transfer as well as decoder fit. The
`gamma=0` row is the paper's reduced, non-latching mechanism ablation;
all other neuron parameters stay fixed. This is a mechanism test, not a
benchmark or statistical comparison.

| Gate / drive amplitude | Late Gram min eig. | Eval PES RMSE | Eval fitted linear RMSE | Eval activity clipped, `+/-` | Interpretation |
|---|---:|---:|---:|---:|---|
| full `gamma=2`, `0.08` | 0.1630 | 0.0285 | 0.0278 | 43.0% / 42.6% | usable two-feature variation |
| reduced `gamma=0`, `0.08` | 0.1630 | 0.0285 | 0.0278 | 43.0% / 42.6% | nearly identical at low drive |
| full `gamma=2`, `0.35` | **0** | **0.2152** | 0.2029 | 98.4% / 91.2% | late activity rank collapse; target RMS is about 0.204 |
| reduced `gamma=0`, `0.35` | 0.1288 | **0.1339** | 0.1257 | 57.6% / 55.4% | variation persists, but nonlinear/dynamic approximation error remains |

All evaluation rows had **zero upward crossings and zero threshold occupancy**
at `theta_e=1`. Thus the observed learning here is analog continuous-state
decoder learning, not event-only learning. The fitted linear comparator is
least squares on the training waveform, not an oracle fitted to test data;
it is provided to separate optimization error from representation error
approximately, and can transfer badly when state regimes differ.

The equilibrium scan of the *single* ACC neuron brackets three roots at
`I=0.75` with the full gate: `r` about `3.73e-6` (stable), `0.1806`
(saddle), and numerically `1` (stable). At `I=0.85` the same three-branch
structure remains. At `I=1.10` the scan finds only the high branch. With
`gamma=0`, it finds one stable root at each of these currents. The high
root is strictly just below one mathematically; binary64 sigmoid evaluation
rounds it to one. Root scans can miss tangent roots and are not certified
bifurcation continuation. They do demonstrate the latch mechanism at the
sampled currents and explain why the decoder sees different states after
different input histories.

One extra three-weight readout adds `10(v^+-v^-)` to the two clipped
activities. Under high drive, the **reduced** gate's full-evaluation PES
RMSE falls from 0.1339 to 0.0799. With the full gate it rises from
0.2152 to 0.3277 over the full cold-start evaluation, but after its first
second the hybrid RMSE is 0.0741 versus 0.2149 for the two-activity
decoder. This is strong evidence that initialization/regime transition
matters; it is not a fair claim of universal voltage superiority. The
whole-training least-squares fit transfers especially poorly here, another
warning against treating one decoder fit as invariant across latch states.

## 5. Reviewer-specific consequence and next proof obligations

| Verbatim-letter concern, paraphrased | What this phase supplies | What remains open |
|---|---|---|
| R1/AE: novelty relative to continuous RNNs and surrogate SNNs | explicit state, observation, and decoder-learning separation; ACC readout's saturation condition | matched two-state continuous, ALIF, and surrogate-event baselines on the **same tiny signal** |
| R1/AE: `r approx 1` and constant-input DB theory are heuristic | exact scalar equilibrium equation and coupled Jacobian; sampled latch branches | certified folds/Hopf boundaries and time-varying-input perturbation bounds |
| R1/AE: weak multi-seed/architecture evidence | previous five-seed and recurrent/conv results accurately scoped | later controlled multi-seed tests; no classification-scale work in this phase |
| R2: practical advantage over current SNN methods unclear | a testable condition: feature excitation and representation, plus a failure case | show a regime where HyperLIF beats equally stateful matched controls at equal online-update cost |
| R2: biological plausibility unsupported | use "biologically inspired two-state computational cell" | fit actual membrane traces and channel/block data before biophysical claims |
| R2: empirical conductance/parameter choices | expose `C(I)`, `gamma`, activity clipping, and exact failure mechanisms | parameter identification or principled optimization with held-out validation |

The TNNLS letter is a **final reject** and explicitly says not to resubmit a
revision of that manuscript. This note is research for a new line, not a
claim that the original submission's concerns have been closed.

The next small-scale sequence is: (1) certify the ACC single-cell folds and
local stability using continuation and interval residual checks; (2) measure
feature Gram spectra, approximation floors, cold-start transients, and
PES/normalized-PES sensitivity in two to three cells, with a matched
two-state control; (3) train **one** internal weight with exact forward
sensitivity (9), then compare a local eligibility approximation and decoder
PES under the same scalar delayed-target task. Each run should retain
unfavorable and no-event regimes. Only after those mechanisms are understood
should network scale or recognition tasks be reconsidered.

## Primary external sources

- [Voelker, *A Solution to the Dynamics of the Prescribed Error Sensitivity Learning Rule* (2015)](https://www.compneuro.uwaterloo.ca/files/publications/voelker.2015.pdf): restricted fixed-activity PES dynamics.
- [Nengo PES API](https://www.nengo.ai/nengo/frontend-api.html): decoder learning, error input, and presynaptic activity filtering. The Julia audit implements the ACC paper's direct discrete update, not Nengo's default low-pass filter.
- [Bellec et al., *A solution to the learning dilemma for recurrent networks of spiking neurons* (2020)](https://www.nature.com/articles/s41467-020-17236-y): online eligibility-trace comparison for internal recurrent weights.
- [Rusch and Mishra, *Coupled Oscillatory Recurrent Neural Network* (ICLR 2021)](https://openreview.net/pdf?id=F3s69XzWOia): one explicit continuous-RNN novelty comparator named by Reviewer 1.
