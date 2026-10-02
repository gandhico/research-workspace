# Three learning modes for HyperLIF: a discrete mathematical specification

**Status:** reference derivation for the Julia implementation dated 2026-09-09.  
**Code authority:** `code/julia/learning/src/HyperLIFLearning.jl`.  
**Purpose:** make clear which gradients are exact for the implemented numerical program, which are
surrogates, and where event-time sensitivities cease to exist.

## 1. State, input, and event notation

For neuron `i` at discrete time `k`, let

`x_(i,k) = (v_(i,k), r_(i,k), a_(i,k), d_(i,k)^1, d_(i,k)^2, d_(i,k)^3)`,

where `v` is membrane voltage, `r in [0,1]` is reset/readiness state, `a` is the exploratory slow
adaptation state, and `d^j` are optional dendritic filters. HyperLIF and adaptive HyperLIF use only
`(v,r)` dynamically; the unused states remain zero. Let `I_(i,k)` be the architecture-provided drive.

The physical event observable is the sampled upward crossing

`z_(i,k) = 1[v_(i,k) < theta_e and v_(i,k+1) >= theta_e]`.                       (1)

Above-threshold occupancy is

`o_(i,k+1) = 1[v_(i,k+1) >= theta_e]`.                                           (2)

Equations (1) and (2) are not interchangeable. If voltage stays above threshold for ten samples,
there is one upcrossing but ten occupied samples. Neither observable resets the continuous state.

## 2. One numerical step

### 2.1 Dendritic state and bounded recurrent operator

For the exploratory next cell, each dendritic branch is the exact zero-order-hold update of a stable
first-order filter:

`d_(k+1)^j = rho_j d_k^j + (1-rho_j) I_k`,  `rho_j = exp(-dt/tau_j) in (0,1)`.    (3)

For bounded input, (3) is bounded-input/bounded-state. Learned logits `m_j` are converted to
`pi_j = exp(m_j)/sum_l exp(m_l)`, so the effective drive

`D_k = sum_j pi_j d_(k+1)^j`                                                       (4)

is a convex combination. Thus `min_j d^j <= D <= max_j d^j` componentwise. This gives a useful
interpretability/boundedness property without pretending that the three filters reproduce real
dendritic morphology.

For a recurrent architecture with hidden width `H`, the trainable raw matrix is mapped to

`W_eff = (g_rec/H) tanh(W_raw)` elementwise.                                      (5)

Because `||A||_2 <= ||A||_F` and every entry of `tanh(W_raw)` has magnitude at most one,

`||W_eff||_2 <= ||W_eff||_F <= g_rec`.                                            (6)

Equation (6) is an operator bound, not a global contraction theorem. The neuron Jacobian and input
map must also be bounded tightly enough for a complete contraction result.

### 2.2 Readiness update and its Jacobian

Define

`q_k = alpha (v_k - theta_v - kappa_a a_k + gamma r_k)`,  `s_k = sigma(q_k)`,     (7)

and `rho_r = exp(-dt/tau_r)`. The frozen-target readiness step is

`r_(k+1) = rho_r r_k + (1-rho_r) s_k`.                                            (8)

Since (8) is a convex combination, `[0,1]` is forward invariant if `r_k,s_k in [0,1]`. Away from
the finite numerical clamp boundaries used before evaluating the sigmoid,

`partial r+/partial v = (1-rho_r) alpha s(1-s)`,                                  (9)

`partial r+/partial r = rho_r + (1-rho_r) alpha gamma s(1-s)`,                    (10)

`partial r+/partial a = -(1-rho_r) alpha kappa_a s(1-s)`.                         (11)

Because `s(1-s) <= 1/4`, a conservative bound from (10) is

`partial r+/partial r <= rho_r + (1-rho_r) alpha gamma/4`.                        (12)

The default `alpha gamma` exceeds four, so (12) does not certify contraction. Saturation often makes
the realized derivative much smaller, but that is an empirical/local fact. This is one reason a
global-stability claim would be unjustified.

For the next cell,

`a_(k+1) = rho_a a_k + (1-rho_a) r_(k+1)`,  `rho_a=exp(-dt/tau_a)`.               (13)

It raises the effective threshold by `kappa_a a`; this is readiness adaptation. A separate
event-driven spike-frequency-adaptation state is an ablation, not something already established by
(13).

### 2.3 Adaptive conductance without a cusp at zero drive

The historical adaptive gain used `|D|`, which is not differentiable at `D=0`. The new reference
uses

`A_epsilon(D) = sqrt(D^2+epsilon^2)-epsilon`,                                     (14)

with derivative `D/sqrt(D^2+epsilon^2)`. It is smooth, nonnegative, zero at zero, and converges
pointwise to `|D|` as `epsilon -> 0`. Conductance is

`G_k = g_k r_(k+1)^2`,                                                            (15)

where `g_k=g_reset` for HyperLIF and
`g_k=g_base+beta A_epsilon(D_k)` for adaptive/next cells.

### 2.4 Frozen-conductance voltage step

Set

`lambda_k = 1/tau_v + G_k > 0`,                                                   (16)

`b_k = v_rest/tau_v + D_k/tau_v + G_k v_reset`,                                  (17)

`vbar_k = b_k/lambda_k`, and `E_k=exp(-lambda_k dt)`. The step is

`v_(k+1) = vbar_k + E_k (v_k-vbar_k)`.                                            (18)

Equation (18) exactly solves the scalar affine voltage equation while `D_k` and `G_k` are frozen.
It does not exactly solve the coupled continuous `(v,r,a,d)` system over the whole step.

For any differentiable scalar parameter `p`, its differential is

`d v+ = E d v + (1-E) d vbar - dt E (v-vbar) d lambda`,                           (19)

where

`d vbar = (lambda d b - b d lambda)/lambda^2`.                                   (20)

Equations (9)–(20), composed through time, are the derivatives used by continuous-state reverse-mode
learning away from clamp boundaries. They are derivatives of the discrete solver, not automatically
continuous-time adjoint sensitivities.

## 3. The three learning contracts

### 3.1 Continuous-state learning

Let `Phi_k` be the complete state map and `h(x_1,...,x_T)` a continuous readout such as mean voltage,
mean readiness, mean conductance, or their hybrid. For cross-entropy loss `L`, reverse-mode
differentiation computes products of discrete Jacobians:

`dL/dp = sum_k lambda_(k+1)^T partial Phi_k/partial p`,                            (21)

`lambda_k = (partial Phi_k/partial x_k)^T lambda_(k+1) + partial L/partial x_k`.   (22)

The hard event in (1) is not on the differentiated path. This mode is therefore valid for a
near-non-spiking HyperLIF: information may be present in `(v,r,G)` even when `z=0`. The honest name is
a continuous/hybrid recurrent network with an event monitor, not a spike-only SNN.

Its scientific comparison set must include equally stateful continuous cells (for example coRNN,
UnICORNN, LEM/state-space baselines) as well as LIF-family neurons. Otherwise performance cannot be
attributed specifically to the reset-state construction.

### 3.2 Surrogate-event learning

The forward event remains exactly (1). The Boolean map has derivative zero almost everywhere and is
undefined at its boundary. The implementation declares the pseudo-derivative

`psi'(u) = beta_s / (1 + beta_s |u|)^2`,  `u=v_(k+1)-theta_e`,                     (23)

and sends `delta z psi'(u)` to `v_(k+1)`. It deliberately assigns no derivative through the
`v_k<theta_e` predicate. Consequently this is neither the classical derivative of (1) nor an exact
event-time derivative; it is a biased credit-assignment rule whose slope `beta_s` is a model
hyperparameter.

Required sensitivity analysis:

- at least three surrogate slopes;
- pure event-count versus `event+readiness` readout;
- gradient norm, no-event fraction, and seed failure rate;
- identical forward event semantics for all neuron baselines.

### 3.3 Event-time learning

Suppose one step has a strict transversal crossing:

`v_k < theta_e < v_(k+1)` and `Delta v = v_(k+1)-v_k > 0`.                        (24)

Linear interpolation gives

`t* = t_k + dt (theta_e-v_k)/Delta v`.                                             (25)

Within a neighborhood in which the same event exists in the same step,

`partial t*/partial v_k = dt (theta_e-v_(k+1))/(Delta v)^2`,                      (26)

`partial t*/partial v_(k+1) = -dt (theta_e-v_k)/(Delta v)^2`,                    (27)

`partial t*/partial theta_e = dt/Delta v`.                                        (28)

Thus conditioning deteriorates as `Delta v -> 0`; in continuous language, as crossing velocity
approaches zero. If a perturbation creates, deletes, or moves the event to another integration step,
the local computation graph changes and (26)–(28) are no longer the relevant derivative.

For no-event neurons, the implementation emits a masked zero time feature. Pure first-event-time
learning therefore has no local rescue gradient for a silent unit. `hybrid_time_vr` adds voltage and
readiness as a continuation scaffold. A fair paper must show both; the hybrid cannot be advertised as
a pure temporal code.

## 4. Architecture/readout identifiability

Each minibatch sample is normalized across its own feature dimension before the linear head. This
avoids predictions depending on unrelated members of the evaluation batch. A test enforces this
invariance.

Readouts answer different mechanistic questions:

| Readout | Question |
|---|---|
| `membrane` | is ordinary continuous voltage sufficient? |
| `gate` | does readiness contain label information? |
| `conductance` | does dissipative/reset strength add information? |
| `spike_count` | can true upcrossings alone solve the task? |
| `first_event_time` | can timing alone solve the task under valid topology? |
| `hybrid_vr` | does readiness improve a continuous state code? |
| `hybrid_zr` | does readiness scaffold sparse crossing communication? |
| `hybrid_time_vr` | can continuous state scaffold event-time optimization? |
| `hybrid_next` | do multiscale/adaptation states add predictive information? |

Readout success is decodability, not causality. To claim that a state causes improvement, use nested
ablations, matched dimensions/parameter counts, several seeds, and preferably interventions on that
state.

## 5. What can become a strength

1. **Nearly non-spiking regimes:** treat them as a falsifiable analog-state hypothesis; compare
   continuous-state accuracy with true event communication and measure the accuracy/activity frontier.
2. **Surrogate mismatch:** make it an explicit algorithmic choice and report slope robustness rather
   than implying exact differentiability.
3. **Event-time singularities:** expose them with no-event and crossing-speed diagnostics; hybrid
   continuation becomes a principled optimization ablation.
4. **Dendritic inspiration:** use a convex multiscale filter bank whose mathematical role is clear;
   reserve biological claims for trace-level or morphology-linked validation.
5. **Recurrent instability:** constrain the linear recurrent operator and report realized Jacobian
   spectra; do not promote the operator bound into a global theorem.
6. **Event/occupancy discrepancy:** turn the historical error into a reproducibility lesson and rerun
   all efficiency tables under common upcrossing semantics.

## 6. Code-to-equation map and tests

| Mathematics | Julia symbol | Verification |
|---|---|---|
| (1) | `hard_upcrossing` | crossing/occupancy counterexample |
| (3)–(4) | `_dendritic_update` | all-cell forward/gradient tests |
| (5)–(6) | `_bounded_recurrent_matrix` | numerical operator-norm bound |
| (7)–(20) | `neuron_step` | finite/state/gradient suite |
| (23) | `surrogate_upcrossing` adjoint | hard forward + nonzero backward test |
| (25)–(28) | `interpolated_event_time` | finite-difference derivative test |
| (21)–(22) | `classification_loss` + Zygote | 3 cells × 3 modes |
| batch independence | per-sample normalization in `_forward` | single versus mixed batch test |

The tests validate implementation contracts, not scientific superiority.

## 7. References connected to the program

- Lee et al., “Exact Gradient Computation for Spiking Neural Networks through Forward Propagation,”
  AISTATS 2023: <https://proceedings.mlr.press/v206/lee23b.html>.
- Bellec et al., e-prop / learning dilemma, NeurIPS 2018 and Nature Communications 2020:
  <https://papers.nips.cc/paper_files/paper/2018/hash/c203d8a151612acf12457e4d67635a95-Abstract.html>,
  <https://www.nature.com/articles/s41467-020-17236-y>.
- Rusch and Mishra, “UnICORNN,” ICML 2021:
  <https://proceedings.mlr.press/v139/rusch21a.html>.
- Fang et al., learnable membrane time constants (PLIF), ICCV 2021:
  <https://openaccess.thecvf.com/content/ICCV2021/html/Fang_Incorporating_Learnable_Membrane_Time_Constant_To_Enhance_Learning_of_Spiking_ICCV_2021_paper.html>.
- Zheng et al., temporal dendritic heterogeneity, Nature Communications 2024:
  <https://www.nature.com/articles/s41467-023-44614-z>.
- Pedersen et al., neuromorphic intermediate representation, Nature Communications 2024:
  <https://www.nature.com/articles/s41467-024-52259-9>.

These references motivate comparisons and methods; none proves that the present next-cell abstraction
is biologically correct or superior.

