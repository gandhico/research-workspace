# HyperLIF and Adaptive HyperLIF: rigorous theory, evidence, and research program

**Research memorandum — 9 September 2026**  
**Scope:** neuron mathematics, numerical realization, learning, architecture, biological extensions, and the path toward embodied and multi-agent AI.

This memorandum separates four kinds of statements:

- **proved here:** a mathematical consequence of the stated equations;
- **computed here:** a result produced by the included audit scripts;
- **observed previously:** an empirical result in the current manuscripts or result bundles;
- **proposed:** a falsifiable next research step, not a present capability.

The exact TNNLS decision letter and verbatim reviewer report were not found in the available drives. The reviewer constraints below are reconstructed from the project audit and advisor briefing, and should not be presented as quotations.[^1]

## Executive position

HyperLIF is best understood as a **two-state nonlinear continuous-reset recurrent cell with an optional event surface**, not as a universally superior replacement for LIF. Its useful novelty is the coupling of:

1. a membrane-like state (v),
2. a fast, bounded reset/readiness gate (r),
3. a state-dependent dissipative conductance (G(r,J)), and
4. an event observation (z) that does not overwrite the continuous state.

That distinction immediately clarifies both its strengths and its limits.

- The continuous ((v,r,G)) path can carry graded temporal information even when there are few or no emitted events.
- Removing the hard reset jump does **not** make the binary event map differentiable. Event-dependent training still needs a surrogate derivative or explicit event-time sensitivity.
- HyperLIF can operate as a spiking oscillator, a subthreshold analog recurrent unit, or a high-voltage latched unit. The operating regime depends strongly on current, gate gain, hysteresis, reset anchor, and event threshold.
- Adaptive HyperLIF can prevent the fixed-gain high-voltage latch on the frozen open-gate branch, but the usual (eta) inequality is not a global-stability theorem.
- Existing classification evidence supports temporal/state-readout value. It does not support universal dominance, exact biological realism, or a hardware-energy claim.
- A newly identified semantics mismatch means the historical architecture “event counts” are threshold-occupancy samples for HyperLIF but hard-reset spikes for LIF. Those totals cannot yet establish physical spike or energy savings.

The strongest defensible scientific thesis is therefore:

> **HyperLIF turns reset from an information-destroying state overwrite into an explicit nonlinear dissipative state variable. That variable can support temporal representation across spiking and near-non-spiking regimes, but its value must be demonstrated against equally stateful continuous and spiking baselines under common event semantics and measured cost.**

## 1. What is learning?

“Learning” should not be reduced to “the loss decreased.” For this research program it has four nested meanings.

### 1.1 Statistical learning

Let data be drawn from an unknown distribution (mathcal D), a model with parameters (phi) produce (f_phi(x)), and loss be (ell). Training minimizes empirical risk

\[
\widehat R_n(\phi)=\frac1n\sum_{i=1}^n \ell(f_\phi(x_i),y_i),
\]

while the scientific target is low population risk

\[
R(\phi)=\mathbb E_{(x,y)\sim\mathcal D}\bigl[\ell(f_\phi(x),y)\bigr].
\]

A neuron “learns better” only if its inductive bias improves generalization, optimization, calibration, robustness, sample efficiency, or resource cost under a controlled comparison. Training accuracy alone does not establish this.

### 1.2 Dynamical representation learning

For a temporal model, the state evolves as

\[
x_{k+1}=F_\phi(x_k,u_k),\qquad y_k=H_\phi(x_k).
\]

Learning selects parameters so that the state (x_k) becomes a sufficient and robust summary of the relevant history (u_{0:k}). In HyperLIF, (x=(v,r)). The gate is scientifically important only if it adds predictive information beyond voltage, event history, and matched stateful baselines.

### 1.3 Credit assignment

Learning also means assigning an outcome error to earlier states and parameters. Backpropagation through time computes

\[
\frac{\partial L}{\partial \phi}
=\sum_{k=0}^{T-1}\lambda_{k+1}^{\mathsf T}
\frac{\partial F_\phi(x_k,u_k)}{\partial \phi},
\qquad
\lambda_k=\frac{\partial \ell_k}{\partial x_k}
+\left(\frac{\partial F_k}{\partial x_k}\right)^{\mathsf T}\lambda_{k+1}.
\]

This is mathematically distinct from the forward neuron dynamics. A biologically inspired forward equation does not imply a biologically plausible learning rule.

### 1.4 Embodied adaptation

For a robot or multi-agent system, learning is a closed-loop change in policy, model, estimator, or communication strategy that improves an objective while satisfying constraints:

\[
\min_\pi\; \mathbb E\!\left[\sum_{k=0}^{T} c(x_k,u_k)\right]
\quad\text{s.t.}\quad
x_{k+1}=f(x_k,u_k,w_k),\; x_k\in\mathcal X_{\rm safe}.
\]

Here, good offline classification is only preliminary evidence. The eventual test is whether HyperLIF state improves estimation or control under latency, noise, distribution shift, communication limits, and measured energy.

## 2. Why SNNs—and when not to use them

SNNs are justified when events are native to the problem or deployment:

- event cameras, tactile events, asynchronous sensors, sparse communications;
- temporal state must persist without reconstructing full frames;
- hardware can exploit conditional synaptic updates and local memory;
- latency or communication, rather than only multiply count, is limiting;
- online adaptation benefits from local eligibility traces.

They are **not automatically efficient**. If every neuron updates dense floating-point (v) and (r) at every millisecond, and all gates are transmitted between layers, the implementation is a clocked recurrent neural network with binary side outputs. Sparse spikes do not by themselves imply lower wall power. Energy must be measured as something like

\[
E_{\rm total}=N_{\rm MAC}e_{\rm MAC}+N_{\rm AC}e_{\rm AC}
+N_{\rm state}e_{\rm state}+N_{\rm memory}e_{\rm memory}
+N_{\rm comm}e_{\rm comm},
\]

on a named device and workload. Model-level operation estimates may motivate hardware experiments, but they are not hardware measurements.

As of 2026, the broad neural-network frontier is dominated by large pretrained Transformer, selective state-space, and hybrid models, plus multimodal vision-language-action policies for robotics. Mamba is representative of the selective state-space direction; OpenVLA is representative of the embodied VLA direction.[^2] SNNs do not lead the general language, vision, or robotics frontier. Their credible frontier is narrower: temporal/event sensing, specialized sequence models, local learning, and hardware/software co-design. Recent SNN work has reached strong ImageNet-scale results and developed parallel, dendritic, and local-learning alternatives, but paper-reported energy reductions remain model- and hardware-dependent.[^3]

The opportunity for HyperLIF is therefore not to claim “brain-inspired SOTA.” It is to show a precise advantage in the intersection

\[
\text{continuous temporal state}
\cap \text{sparse events}
\cap \text{stable online dynamics}
\cap \text{deployable local computation}.
\]

### 2.1 A practical 2026 SOTA map

“State of the art” is not one leaderboard. It depends on the capability and resource constraint.

| Axis | Mainstream neural frontier | SNN/neuromorphic frontier | Consequence for HyperLIF |
|---|---|---|---|
| general sequence learning | pretrained Transformers, selective state-space models, and hybrids at scale | parallel temporal neurons, spiking attention/Transformers, long-sequence resonant cells | compare memory, scaling, and stability—not only LIF accuracy |
| representation learning | self-supervised and multimodal pretraining followed by task adaptation | direct spiking training, ANN-to-SNN conversion, sparse/event-native encoding | a new neuron alone is insufficient; pretraining and data dominate many tasks |
| embodied AI | vision-language-action policies, diffusion/action chunking, hierarchical planning | event-camera perception, low-power state estimation/control, early spike-native policies | place HyperLIF first in low-level temporal estimation/residual control, not as an immediate VLA replacement |
| credit assignment | backpropagation/adjoints plus large-scale optimization | surrogate BPTT, exact event gradients on restricted systems, e-prop, predictive coding, learned plasticity | state exactly which gradient is used and what locality claim is made |
| deployment | GPU/TPU accelerators and quantization | Loihi/SpiNNaker/Speck/Xylo-class platforms and portable IRs | report end-to-end device energy/latency; sparsity is only a mechanism |
| biological modeling | abstract differentiable models optimized for tasks | multicompartment/dendritic/adaptive/resonant models and differentiable biophysical simulators | derive reduced cells from measured phenomena before using “biophysical” |

For scale, SpikedAttention reported 80.0% ImageNet accuracy with 28.7M parameters and a model-specific 42% energy estimate reduction relative to Swin-T; another 2024 study reported high performance with approximately 0.3 spikes per neuron on its evaluated models.[^13] These results show that deep sparse SNNs are viable. They do not establish that SNNs generally dominate ANNs, nor that the same energy ratio transfers to HyperLIF, recurrent control, or a different chip.

## 3. Mathematical specification

### 3.1 Continuous dynamics

For input current (J(t)), define

\[
\tau_v\dot v
=-(v-v_{\rm rest})+J
-\tau_v G(r,J)(v-v_{\rm reset}),
\tag{1}
\]

\[
\tau_r\dot r
=\sigma\!\left(\alpha[v-\theta+\gamma r]\right)-r,
\qquad
\sigma(s)=\frac{1}{1+e^{-s}}.
\tag{2}
\]

The effective gate knee is (	heta_{\rm eff}(r)=\theta-\gamma r). For fixed HyperLIF,

\[
G_H(r)=G_b r^2.
\tag{3}
\]

For Adaptive HyperLIF,

\[
G_A(r,J)=(G_0+\beta|J|)r^2.
\tag{4}
\]

The reset conductance is dissipative with respect to the reset anchor because its contribution is (-G(v-v_{\rm reset})). “Adaptive” here means input-dependent reset capacity. It is not synaptic plasticity, threshold adaptation, or online parameter learning.

### 3.2 Event observation

The continuous state is not reset at threshold. A sampled upward-crossing event is

\[
z_{k+1}=\mathbf 1[v_k<\theta_e\le v_{k+1}].
\tag{5}
\]

This must be distinguished from sampled threshold occupancy

\[
o_{k+1}=\mathbf 1[v_{k+1}\ge\theta_e].
\tag{6}
\]

If voltage enters and remains above threshold, (5) produces one event while (6) remains one at every sample. The Nengo/standalone reference uses (5). The historical snnTorch/APEX-v2 architecture and original portable Julia path use (6). This is not a cosmetic implementation difference: it changes recurrence, readout statistics, event counts, and energy interpretation.

### 3.3 Network architecture

For neuron (i), a recurrent layer can be written

\[
J_{i,k}=\sum_j W^{\rm in}_{ij}u_{j,k}
+\sum_j W^{\rm rec}_{ij}q_{j,k-1}+b_i,
\tag{7}
\]

where (q) must be named explicitly. It may be a crossing event (z), occupancy (o), gate (r), or another continuous feature. These define different models:

- (q=z): event-driven recurrent SNN;
- (q=o): clocked binary recurrent network;
- (q=r): gated continuous RNN with an event monitor;
- (q=[v,r,G,z]): hybrid continuous/event network.

The existing deep convolutional harness propagates (r) between HyperLIF layers because sparse event propagation starved deep networks. That is a legitimate model, but it should be called a gated continuous/hybrid network rather than a fully spike-driven SNN.

## 4. Properties proved or derived from the equations

### 4.1 Forward invariance of the gate

**Proposition 1.** If (r(0)\in[0,1]), then (r(t)\in[0,1]) for all later time for which the solution exists.

**Proof.** At (r=0),

\[
\dot r=\sigma(\alpha[v-\theta])/\tau_r>0.
\]

At (r=1),

\[
\dot r=(\sigma(\alpha[v-\theta+\gamma])-1)/\tau_r<0.
\]

Thus the vector field points inward at both boundaries. (square)

The numerical clip to ([0,1]) is therefore a floating-point guard, not part of the ideal continuous flow. It does introduce non-smooth points into the implemented map.

### 4.2 Boundedness under bounded drive

Rewrite (1) as

\[
\dot v=-a(t)v+b(t),
\quad
a(t)=\tau_v^{-1}+G(r,J)\ge \tau_v^{-1}>0,
\]

\[
b(t)=\frac{v_{\rm rest}+J(t)}{\tau_v}+G(r,J)v_{\rm reset}.
\]

If (J(t)) is bounded, then (r\in[0,1]) makes (G) and (b) bounded. Variation of constants gives

\[
v(t)=e^{-\int_0^t a(s)ds}v(0)
+\int_0^t e^{-\int_s^t a(q)dq}b(s)ds,
\]

so (v) is bounded. This proves forward boundedness; it does not prove convergence to one equilibrium.

### 4.3 Exact coupled equilibria

For constant (J), a true equilibrium satisfies

\[
v^*(r;J)=
\frac{v_{\rm rest}+J+\tau_vG(r,J)v_{\rm reset}}
{1+\tau_vG(r,J)},
\tag{8}
\]

and the implicit gate equation

\[
r^*=\sigma\!\left(\alpha[v^*(r^*;J)-\theta+\gamma r^*]\right).
\tag{9}
\]

The common substitution (r=1) is a saturated-branch approximation; the logistic gate is never exactly one for a finite argument. Consequently a formula obtained on the (r=1) branch is not, by itself, an exact bifurcation boundary.

### 4.4 Local stability

Let (S=G_b) for HyperLIF and (S=G_0+\beta|J|) for Adaptive HyperLIF. At an equilibrium, (G=Sr^2) and (sigma'(\cdot)=r(1-r)). The full Jacobian is

\[
\mathcal J=
\begin{bmatrix}
-(\tau_v^{-1}+G) & -2Sr(v-v_{\rm reset})\\[2mm]
\alpha r(1-r)/\tau_r & [\alpha\gamma r(1-r)-1]/\tau_r
\end{bmatrix}.
\tag{10}
\]

Local asymptotic stability requires both eigenvalues to have negative real part, equivalently for a real (2\times2) system,

\[
\operatorname{tr}\mathcal J<0,
\qquad
\det\mathcal J>0.
\tag{11}
\]

Because (r(1-r)\le1/4), the simple bound

\[
\alpha\gamma<4
\tag{12}
\]

guarantees that the gate's direct self-feedback term is negative. It is only a sufficient component-wise condition, not a necessary full-system stability criterion. The default (alpha\gamma=100(0.2)=20) violates it, so no general contraction claim follows from the default parameters. The positive hysteretic feedback can support unstable equilibria and relaxation oscillations.

### 4.5 Frozen open-gate estimates

On the approximation (r=1), fixed HyperLIF has

\[
v_H^*(1;J)=
\frac{v_{\rm rest}+J+\tau_vG_bv_{\rm reset}}
{1+\tau_vG_b}.
\tag{13}
\]

Equating this branch with the open-gate knee (	heta-\gamma) gives

\[
J_{\rm DB}^{(r=1)}
=(\theta-\gamma)(1+\tau_vG_b)
-v_{\rm rest}-\tau_vG_bv_{\rm reset}.
\tag{14}
\]

For the defaults this is (2.4). The notation should say “open-gate branch estimate,” not exact global DB onset.

For positive large (J), Adaptive HyperLIF has

\[
\lim_{J\to\infty}v_A^*(1;J)
=v_{\rm reset}+\frac{1}{\tau_v\beta}.
\tag{15}
\]

Keeping this branch below the knee requires

\[
\beta>
\frac{1}{\tau_v(\theta-\gamma-v_{\rm reset})},
\qquad \theta-\gamma>v_{\rm reset}.
\tag{16}
\]

With (v_{\rm reset}=0), the threshold is (62.5); (eta=80) gives the asymptote (0.625). Equation (16) says only that the positive-drive saturated branch is below the gate knee. It does not prove global stability, oscillation, repeated threshold crossing, recurrent-network stability, or good learning.

## 5. Discretization and differentiability

The implementation freezes the gate target over a step:

\[
r_{k+1}=\operatorname{clip}_{[0,1]}\left[
r_\infty(v_k,r_k)+(r_k-r_\infty)e^{-\Delta t/\tau_r}
\right].
\tag{17}
\]

It then freezes (J_k) and (G(r_{k+1},J_k)) and solves the scalar voltage subproblem exactly:

\[
v_{k+1}=v_ke^{-\lambda_k\Delta t}
+\frac{d_k}{\lambda_k}(1-e^{-\lambda_k\Delta t}),
\]

\[
\lambda_k=\tau_v^{-1}+G_k,
\qquad
d_k=v_{\rm rest}/\tau_v+J_k/\tau_v+G_kv_{\rm reset}.
\tag{18}
\]

Equation (18) is exact and contractive for the **frozen scalar subproblem**. The complete update is an operator-split approximation to the coupled nonlinear ODE. Calling the whole method “exact” or “A-stable” is too strong.

The smoothness ledger is:

| Component | Mathematical status | Learning consequence |
|---|---|---|
| fixed HyperLIF ODE away from clipping | smooth | ordinary autodiff/adjoint is valid |
| Adaptive (|J|) | non-differentiable at (J=0) | use a subgradient or document a smooth replacement such as (sqrt{J^2+\varepsilon^2}) |
| numerical `clip` and voltage floor | piecewise smooth | zero/undefined derivatives at active boundaries |
| occupancy/event indicator | discontinuous | surrogate, smoothing, or event-time calculus required |
| spike-count change | topology change | objective is generally only piecewise differentiable |

For a transversal continuous event (h(v(t^*),p)=v(t^*,p)-\theta_e=0), the implicit-function theorem gives

\[
\frac{dt^*}{dp}=
-\frac{\partial v(t^*,p)/\partial p}{\dot v(t^*,p)},
\tag{19}
\]

provided (dot v(t^*)\ne0). Grazing crossings make this derivative ill-conditioned; created or destroyed events change the computation graph. Exact event-time gradient methods exist under explicit regularity conditions, so “surrogate-free” is possible only with those conditions and machinery, not merely because reset is continuous.[^4]

## 6. New theorem-to-simulation audit

Two new reproducible scripts accompany this memorandum:

- [`hyperlif_equilibrium_audit.py`](C:/Research/papers/P1_HyperLIF_Learning/theory/hyperlif_equilibrium_audit.py) solves (9), evaluates (10), and writes every sampled branch and eigenvalue.
- [`hyperlif_constant_drive_audit.py`](C:/Research/papers/P1_HyperLIF_Learning/theory/hyperlif_constant_drive_audit.py) simulates the validated split map and separately reports occupancy and upward crossings.

Default contract: (	au_v=0.02), (	au_r=0.002), (alpha=100), (gamma=0.2), (G_b=100), (G_0=20), (eta=80), (v_{\rm rest}=v_{\rm reset}=0), and (	heta=	heta_e=1). Current was swept from 0 to 6 in increments of 0.01. Trajectories used (Delta t=10^{-4}) s, 2 s duration, and a 1 s transient.

**Computed here:**

| Property | HyperLIF | Adaptive HyperLIF |
|---|---:|---:|
| sampled current range with unstable equilibrium | 0.97–2.29 | 0.97–6.00 |
| sampled periodic upward-crossing range | 1.45–2.21 | 1.51–3.62 |
| peak crossing rate | 74 Hz | 151 Hz |
| stable high-occupancy/zero-new-crossing range | 3.00–6.00 | none |

The exact equilibrium sweep found one equilibrium at each sampled current, not multiple equilibria. For fixed HyperLIF, the unstable interval corresponds to an oscillatory band; at high current the trajectory converges above the event threshold and emits no further upward crossings. That is a high-occupancy depolarized latch. Adaptive HyperLIF remains dynamically oscillatory at high current, but for (J>3.62) its oscillation is below the default event surface. It is therefore **dynamically active but event-silent at (	heta_e=1)**. Lowering (	heta_e) to 0.95, as in the calibrated Nengo variants, changes observation without changing the continuous dynamics.

These results explain the “best-spiking” versus “almost non-spiking” variants without mysticism:

- the neuron dynamics generate a voltage/gate limit cycle;
- the event surface may intersect, graze, or lie above that limit cycle;
- moving (	heta_e) changes event visibility but not the underlying orbit;
- gate/voltage readouts can learn from a subthreshold orbit even when the event channel is silent.

This is a genuine hybrid-computation capability. It is not automatically a neuromorphic energy advantage because dense state updates may remain.

## 7. What the tuned versions actually show

The project contains several parameter families that should not be conflated.

| Family | Defining change | Regime / intended role | Evidence boundary |
|---|---|---|---|
| canonical HyperLIF | (G=100r^2,	heta_e=1) | sparse oscillation followed by fixed-gain latch | benchmark accuracy and state readouts; high-drive failure is real |
| canonical Adaptive | (G=(20+80|J|)r^2) | input-scaled discharge; high-drive subthreshold oscillation | avoids fixed-gain latch branch; not a global-stability proof |
| (	heta_e=0.95) variants | lower observation surface | turns near-threshold orbit into visible events | changes event rate, not neuron ODE |
| origin/AHP variants | (v_{\rm reset}<0) or gate-coupled reset anchor | stronger after-hyperpolarization and state separation | biologically inspired hypothesis; not biophysically validated |
| Nengo T002 | base HyperLIF, high threshold/weak calibration | approximately 6–13 Hz | weak representation/PES |
| Nengo T023 | (	heta_e=.95,v_{\rm reset}=-.6,) broader current calibration | approximately 33–40 Hz | strong general representation/dynamics, slow PES |
| Nengo T033 | Adaptive with T023-style calibration | approximately 55–63 Hz | better memory/PES than T023, not universally better |
| Julia/APEX NSA | separate APEX (eta,gamma) calibration | small cross-framework SHD study | parameter names are not guaranteed identical to (eta=80) above |

### 7.1 PyTorch architecture evidence

**Observed previously, five seeds:**[^5]

| Dataset | LIF | HyperLIF | Adaptive |
|---|---:|---:|---:|
| SHD, feedforward | .484±.008 | **.637±.016** | .581±.016 |
| SSC, feedforward | .128±.008 | **.215±.010** | .212±.010 |
| DVS32, feedforward | .698±.010 | **.818±.020** | .790±.010 |
| DVS48, feedforward | .719±.016 | **.786±.030** | .751±.016 |
| N-MNIST, feedforward | .895±.009 | **.908±.007** | .904±.006 |

The shrinking advantage on near-static N-MNIST is consistent with a temporal-state mechanism. It is not causal proof; dataset and architecture differences can confound the comparison.

Architecture transfer was strongest in recurrent and learnable-delay audio models: RSNN SHD was .536/.674/.588 and delay SSC was .138/.308/.258 for LIF/HyperLIF/Adaptive. Convolutional gains were smaller but often positive. Deep ConvRes experiments are a boundary: short smoke tests showed finite forward/backward behavior, but full benchmark training left HyperLIF/Adaptive near chance while LIF learned. The likely mechanism is gate saturation and gradient starvation through deep stacks, but this remains a diagnosis to test, not a proven cause.

Reviewer-facing SHD shortlists show why universal-superiority language is wrong:

| Architecture | LIF | PLIF | ALIF | HyperLIF |
|---|---:|---:|---:|---:|
| feedforward | .4238 | .4235 | **.5570** | .5475 |
| recurrent | .4640 | .4637 | .5473 | **.5695** |
| delay | .4945 | .4940 | **.5650** | .5593 |

With only five paired seeds, the smallest possible two-sided exact sign-flip (p)-value is (2/2^5=.0625). Report means, dispersion, confidence intervals, and effect sizes; do not claim exact paired significance at (p<.05) from these five seeds.

The gate-only comparison (.776 for HyperLIF versus .131 for a zero/absent LIF gate channel on DVS32) proves that a HyperLIF gate contains decodable information. It does **not** prove that the gate is better than every feature-matched two-state LIF/ALIF/control baseline, because LIF was structurally denied a homologous channel.

### 7.2 Nengo representation evidence

**Observed previously:** the calibrated five-seed state-decoder study reported mean rates of 100.5 Hz (LIF), 40.3 Hz (T023 HyperLIF), and 53.3 Hz (T033 Adaptive). Nengo decoded error was similar (.2269, .2273, .2339), while richer state features improved scalar decoding: HyperLIF gate error .1110, Adaptive gate error .1269, and Adaptive spikes+voltage error .0973. These are useful proofs of decodable state in bounded scalar signal tasks; they are not high-dimensional perception or closed-loop control results.[^6]

Matched-time PES remained a weakness: approximately .051 error for LIF, .445 for HyperLIF, and .103 for Adaptive. Tuning the HyperLIF firing region improved it but did not close the gap. This says the neuron can represent a signal yet adapt poorly under that learning rule and calibration.

### 7.3 Julia results

The portable Julia package implements dense, recurrent, and temporal-delay architectures, six readouts, fixed and adaptive conductance, explicit centered-offline versus causal-online delay, and explicit `:occupancy` versus `:upcrossing` event modes.[^7]

The new `code/julia/learning` package adds end-to-end continuous-state, surrogate-upcrossing, and interpolated-event-time learning for HyperLIF, Adaptive HyperLIF, and an exploratory multiscale/adaptation cell. **Verified today:** all 100 assertions pass. They include a finite-difference event-time derivative, hard-forward/nonzero-backward surrogate test, all nine cell/mode loss-gradient combinations, recurrent operator-norm bound, prediction independence from unrelated batch members, and architecture contracts. CPU and CUDA mechanism preflights pass all three learning modes. A bundled real-SHD CUDA optimizer smoke completed all three modes and wrote checkpoints/provenance; each obtained 4.69% on only 64 test examples (chance 5%), so it is not a performance result. Across modes it measured 11.47–12.41 true upcrossings/sample versus 118.22–127.05 occupancy states/sample, confirming that the historical metric distinction is material.

**Observed previously:** existing shared-weight APEX-v2 fixtures reproduce PyTorch dense, recurrent, and centered-delay features/logits with maximum reported HyperLIF feature error (1.05\times10^{-5}) and Adaptive error (5.09\times10^{-4}), under feature/logit tolerances (10^{-4}/10^{-3}). A fixed-trunk head smoke test reduced loss from 4.0835 to 1.7929. These validate forward computation and a trainable linear head, not full end-to-end architecture learning.

The native Julia/APEX SHD experiment, 10 epochs and five seeds, obtained:

| Model | accuracy | loss |
|---|---:|---:|
| LIF | .2411±.0778 | 2.3359 |
| tuned HyperLIF/NSA | .2490±.0666 | 2.2768 |

The small difference is overwhelmed by seed variance. The defensible result is **bounded cross-framework reproduction of a slight directional advantage**, not statistical superiority or competitive SHD performance.

## 8. Learning HyperLIF rigorously

### 8.1 Three honest training modes

1. **Continuous-state learning.** The loss reads (v,r,G), and recurrent layers transmit continuous state. Ordinary BPTT is valid away from (|J|=0) and active clamps. This is best described as a nonlinear continuous/hybrid RNN.
2. **Surrogate-event learning.** Forward events use (5) or a threshold indicator; backward uses a declared surrogate (widetilde H'). Report surrogate shape and slope as part of the model.
3. **Event-time learning.** Use (19) and jump/saltation conditions for a hybrid adjoint. This is mathematically principled but fails at grazing events or changing event topology.

An experiment must not use mode 1 and then attribute performance to sparse spike communication unless inference actually communicates only events.

### 8.2 Parameter constraints

Use differentiable parameterizations:

\[
\tau_v=\tau_{\min}+\operatorname{softplus}(\rho_v),
\quad
\tau_r=\tau_{r,\min}+\operatorname{softplus}(\rho_r),
\]

\[
G_b=\operatorname{softplus}(g_b),
\quad
G_0=\operatorname{softplus}(g_0),
\quad
\beta=\operatorname{softplus}(b).
\]

Constrain or regularize (alphagamma). Very large (alpha) makes the gate nearly binary and creates vanishing gradients away from its knee; large (gamma) adds positive feedback. A useful training regularizer is

\[
L_{\rm stability}=\lambda_s
\mathbb E\left[\max(0,\Re\lambda_{\max}(\mathcal J)-m)^2\right],
\tag{20}
\]

evaluated on sampled states or equilibria, with declared margin (m\le0). This does not guarantee global stability but directly controls a meaningful local quantity.

### 8.3 Make the spikes/continuous-state trade explicit

Use a multi-objective loss

\[
L=L_{\rm task}
+\lambda_z\sum_{i,k}z_{i,k}
+\lambda_o\sum_{i,k}o_{i,k}
+\lambda_c C_{\rm measured}
+\lambda_r R_{\rm state},
\tag{21}
\]

where (z), (o), and measured cost are separate. Penalizing occupancy can eliminate latching; penalizing crossings can reduce communication; neither is equivalent to minimizing actual energy.

### 8.4 Local and online learning

For embodied deployment, e-prop-style eligibility traces factor a weight gradient approximately into a local trace and a broadcast learning signal,

\[
\Delta W_{ij}\propto-\sum_t L_i(t)e_{ij}(t).
\tag{22}
\]

HyperLIF offers a natural two-state eligibility system because (r) stores threshold proximity and reset history. This is a hypothesis, not yet established. A rigorous experiment must compare against ALIF/LSNN eligibility traces, since adaptive thresholds already provide long local state.[^8] Difference predictive coding is another current local, spike-native direction and reports communication savings, but only on its tested tasks and representation.[^9]

## 9. Biological inspiration without overclaiming

The correct phrase today is **biologically inspired**, not biophysically validated. HyperLIF has no fitted ion-channel kinetics, morphology, membrane units, or experimental parameter identification. Biology is useful here as a source of computational hypotheses.

Promising abstractions are:

- **spike-frequency adaptation:** introduce a slow state that raises event threshold or adds after-hyperpolarizing current;
- **multiple dendritic compartments:** separate frequency bands, modalities, or error/forward streams;
- **dendritic plateau and history windows:** use local regenerative state with slow inactivation;
- **resonance:** represent phase/frequency with a complex or second-order subthreshold state;
- **homeostasis/metaplasticity:** learn the plasticity rule or target activity, not only weights;
- **local predictive errors:** split representation and error compartments;
- **heterogeneous time constants:** distribute memory across temporal scales.

Recent work supports dendritic heterogeneity as a useful temporal-computing abstraction, dendritic resonate-and-fire models for long sequences, and differentiable biophysical simulation as a route from data to reduced mathematical models.[^10] Experimental dendritic dynamics are history-dependent and spatially structured; copying a single sigmoid gate is not enough to claim equivalence.[^11]

### 9.1 Proposed next-generation cell

A minimal research extension should add one mechanism at a time:

\[
\tau_{d,m}\dot d_m=-d_m+\phi_m(W_mu+b_m),
\qquad m=1,\ldots,M,
\tag{23}
\]

\[
\tau_v\dot v=-(v-v_{\rm rest})
+\sum_m c_md_m
-G(r,J)(v-v_{\rm reset})-g_a a,
\tag{24}
\]

\[
\tau_r\dot r=\sigma(\alpha[v-\theta_0-\kappa_a a+\gamma r])-r,
\tag{25}
\]

\[
\tau_a\dot a=-a+z(t),
\qquad
z: v-\theta_e-\kappa_a a=0\text{ upward}.
\tag{26}
\]

Here (d_m) are dendritic/filter compartments and (a) is slow adaptation. The scientific sequence should be:

1. prove invariance/boundedness;
2. derive the equilibrium and Jacobian;
3. map bifurcations versus ((\alpha,\gamma,G_b,\beta,\tau_r,\tau_a));
4. test system identification and long-memory tasks;
5. ablate each state against parameter-matched continuous RNN, ALIF, PLIF, TC-LIF, and dendritic/RF baselines;
6. only then test hardware or biological correspondence.

Do not introduce all compartments simultaneously. That would make causal attribution and identifiability worse.

## 10. Reviewer-facing claim and experiment ledger

The reconstructed TNNLS concerns are best answered as follows.

| Concern | Rigorous response | Required evidence |
|---|---|---|
| novelty versus gated continuous RNNs | define HyperLIF as a dissipative two-state hybrid cell and compare the exact state map | coRNN/UnICORNN/LTC/selective-SSM parameter-matched baselines |
| simplifying (r\approx1,J\approx\)constant theory | label formulas as frozen-branch estimates and analyze (9)–(11) | continuation/bifurcation plots and trajectory verification |
| unsupported “biophysical” language | use “biologically inspired” | fit to electrophysiology before stronger claims |
| MLP-only evidence | architecture transfer is now present, with deep failure disclosed | add causal control and long-sequence tests |
| weak statistics | five seeds are descriptive | at least 10–20 paired seeds or power analysis; CIs/effect sizes |
| weak baselines | PLIF/ALIF added, with ALIF competitive | add TC-LIF/PSN and continuous gated RNNs |
| theory not tied to ML benefit | link eigenstructure, memory, crossing surface, and gradient conditioning | preregister parameter-to-performance predictions |
| practical advantage unclear | focus on state observability and event/continuous trade | semantics-matched events plus device-measured latency/energy |

Two manuscript corrections have already been applied:

- the P1 and P2 text no longer says the whole spiking system is fully differentiable;
- the P2 text now scopes the DB and (eta) expressions to the frozen open-gate branch and describes the numerical step as an exact scalar substep, not a global A-stability proof.

## 11. Progressive research program

### Stage A — neuron

- Maintain one canonical equation and parameter/units table across Python, Julia, and Nengo.
- Add bifurcation continuation and Lyapunov/Floquet analysis of the limit cycle.
- Recompute all event statistics with upward crossings for every neuron family.
- Quantify gradient spectra (|\partial x_T/\partial x_t|) across operating regimes.

### Stage B — architecture

- Dense, causal delay, recurrent, and convolutional networks.
- Explicitly label transmitted variable (q\in\{z,o,r,v,[v,r]\}).
- Compare against parameter/FLOP/state-matched continuous cells, not only LIF.
- Treat centered delay as offline/noncausal; use causal delay for control.

### Stage C — learning

- BPTT with continuous readouts.
- Surrogate-event BPTT under a common surrogate.
- Event-time adjoint on small networks.
- e-prop/predictive-coding local learning.
- Meta-learned plasticity and homeostatic thresholds.

### Stage D — embodied AI

- Begin with system identification: predict one-step and rollout plant state from Pendulum, Aero2, and Hover data.
- Use a classical observer/controller as the safety baseline.
- Add HyperLIF as residual dynamics model, state encoder, or disturbance estimator before using it as the full policy.
- Evaluate tracking error, constraint violations, recovery, latency, and measured energy.

The Julia connection layer for Pendulum/Aero2 is documented in [`julia_bridge`](C:/Research/julia_bridge/README.md); the Hover bridge is documented in [`hover3dof/julia`](C:/Research/hover3dof/julia/README.md). The Hover smoke suite passed 103 assertions and the bridge inventory resolves all 15 declared boards, but no live hardware connection was opened. Those are software-integration results, not hardware-control validation.

### Stage E — multi-agent systems

For agent (i), use

\[
x_{i,k+1}=f_i(x_{i,k},u_{i,k},w_{i,k}),
\qquad
m_{ij,k}=Q(z_i,r_i,\widehat x_i),
\]

and optimize task cost plus communication and safety:

\[
L=\sum_i L_i^{\rm task}
+\lambda_{\rm comm}\sum_{i,j,k}\|m_{ij,k}\|_0
+\lambda_{\rm safe}\sum_{i,k}\operatorname{violation}(x_{i,k}).
\]

The distinctive HyperLIF hypothesis is that agents communicate sparse events while retaining continuous local gate state. Test this against periodic continuous messages, event-triggered classical control, and learned binary communication. Multi-agent novelty should come from a demonstrated communication/performance frontier, not merely replacing an ANN cell with a spiking cell.

## 12. Immediate priorities

1. **Freeze semantics.** Make `upcrossing` the physical-event evaluation mode everywhere; retain `occupancy` only for historical parity.
2. **Repair the efficiency figures.** Recompute common crossing counts and remove energy language until hardware cost is measured.
3. **Run a bifurcation continuation.** The new sampled Jacobian/trajectory audit is evidence, but numerical continuation should locate Hopf or other transitions precisely.
4. **Add continuous baselines.** UnICORNN/coRNN/LTC/GRU and a two-state parameter-matched dissipative cell are essential for the novelty question.[^12]
5. **Scale Julia end-to-end.** Automatic differentiation and a complete optimizer smoke now work. Next add shared-weight gradient parity against PyTorch, run the Thursday screen, then the full five-seed benchmark.
6. **Use a causal control benchmark.** Pendulum first, then Aero2/Hover; report identification error before controller performance.
7. **Separate biological hypotheses.** Adaptation, dendrites, resonance, and local plasticity should be independent ablations.

## Reproduction

```powershell
# Julia reference package
julia --project="C:\Research\papers\P1_HyperLIF_Learning\code\julia\portable" -e "using Pkg; Pkg.test()"

# Three end-to-end learning modes (100 assertions)
julia --project="C:\Research\papers\P1_HyperLIF_Learning\code\julia\learning" -e "using Pkg; Pkg.test()"

# One HDF5/GPU/gradient preflight (point HLL_CACHE at all exported datasets)
julia --project="C:\Research\papers\P1_HyperLIF_Learning\code\julia\learning" `
  "C:\Research\papers\P1_HyperLIF_Learning\code\julia\learning\preflight.jl" $env:HLL_CACHE

# Exact coupled equilibria and local stability
& "C:\Research\spacecraft_twin\.venv\Scripts\python.exe" `
  "C:\Research\papers\P1_HyperLIF_Learning\theory\hyperlif_equilibrium_audit.py"

# Constant-drive occupancy versus upward-crossing audit
& "C:\Research\spacecraft_twin\.venv\Scripts\python.exe" `
  "C:\Research\papers\P1_HyperLIF_Learning\theory\hyperlif_constant_drive_audit.py"
```

Machine-readable outputs:

- [`equilibrium summary`](C:/Research/papers/P1_HyperLIF_Learning/theory/results/default_equilibria/summary.json)
- [`all equilibrium branches`](C:/Research/papers/P1_HyperLIF_Learning/theory/results/default_equilibria/equilibria.csv)
- [`constant-drive summary`](C:/Research/papers/P1_HyperLIF_Learning/theory/results/constant_drive/summary.json)
- [`constant-drive sweep`](C:/Research/papers/P1_HyperLIF_Learning/theory/results/constant_drive/constant_drive.csv)

## Sources

[^1]: Local review reconstruction: `C:\Research\papers\_planning\REVIEWER_ADVISOR_AUDIT.md`; `C:\Research\papers\P1_HyperLIF_Learning\ADVISOR_BRIEFING_2026-07-08.md`; `C:\Research\papers\_planning\PEER_REVIEW_AUDIT_2026-08-19.md`.
[^2]: Gu and Dao, “Mamba: Linear-Time Sequence Modeling with Selective State Spaces,” COLM 2024, <https://openreview.net/pdf?id=tEYskw1VY2>; Kim et al., “OpenVLA,” CoRL/PMLR 2025, <https://proceedings.mlr.press/v270/kim25c.html>.
[^3]: Yao et al., “SpikedAttention,” NeurIPS 2024, <https://proceedings.neurips.cc/paper_files/paper/2024/hash/7c9341ad0263428b5057d92f4d88dfa0-Abstract-Conference.html>; Fang et al., “Parallel Spiking Neurons,” NeurIPS 2023, <https://proceedings.neurips.cc/paper_files/paper/2023/hash/a834ac3dfdb90da54292c2c932c997cc-Abstract-Conference.html>; Xing et al., “TC-LIF,” AAAI 2024, <https://ojs.aaai.org/index.php/AAAI/article/view/29625>.
[^4]: Lee et al., “Exact Gradient Computation for Spiking Neural Networks through Forward Propagation,” AISTATS/PMLR 2023, <https://proceedings.mlr.press/v206/lee23b.html>.
[^5]: Primary local experiment and manuscript source: `C:\Research\papers\P1_HyperLIF_Learning\main.tex` and its cited result bundles.
[^6]: Primary local Nengo manuscript/source: `C:\Research\papers\P2_HyperLIF_Nengo\paper\main.tex` and `C:\Research\papers\P2_HyperLIF_Nengo\results`.
[^7]: Portable Julia implementation and contract: `C:\Research\papers\P1_HyperLIF_Learning\code\julia\portable\src\HyperLIFArchitectures.jl` and `MATH_AND_PARITY.md`.
[^8]: Bellec et al., “A solution to the learning dilemma for recurrent networks of spiking neurons,” NeurIPS 2018, <https://papers.nips.cc/paper_files/paper/2018/hash/c203d8a151612acf12457e4d67635a95-Abstract.html>; Bellec et al., “A solution to the learning dilemma for recurrent networks of spiking neurons,” Nature Communications 2020 e-prop extension, <https://www.nature.com/articles/s41467-020-17236-y>.
[^9]: Karlsson et al., “Difference Predictive Coding for Training Spiking Neural Networks,” ICLR 2026, <https://openreview.net/forum?id=iu9dbz2lB9>.
[^10]: Zheng et al., “Temporal dendritic heterogeneity incorporated with spiking neural networks,” Nature Communications 2024, <https://www.nature.com/articles/s41467-023-44614-z>; Zhang et al., “Dendritic Resonate-and-Fire Neuron,” NeurIPS 2025, <https://proceedings.neurips.cc/paper_files/paper/2025/hash/9a6ca401f890aeb2c272d2bb26196d3f-Abstract-Conference.html>; Deistler et al., “Differentiable simulation and optimization of detailed biophysical neuron models,” Nature Methods 2025, <https://www.nature.com/articles/s41592-025-02895-w>.
[^11]: O'Hare et al., “Dendritic excitations govern back-propagation via a spike-rate accelerometer,” Nature Communications 2025, <https://www.nature.com/articles/s41467-025-55819-9>.
[^12]: Rusch and Mishra, “UnICORNN,” ICML/PMLR 2021, <https://proceedings.mlr.press/v139/rusch21a.html>. PLIF source: Fang et al., ICCV 2021, <https://openaccess.thecvf.com/content/ICCV2021/html/Fang_Incorporating_Learnable_Membrane_Time_Constant_To_Enhance_Learning_of_Spiking_ICCV_2021_paper.html>.

Additional interoperability context: Pedersen et al., “Neuromorphic intermediate representation,” Nature Communications 2024, demonstrated models across seven simulators and four hardware platforms, <https://www.nature.com/articles/s41467-024-52259-9>. This is a useful target for eventual HyperLIF portability, but custom state/gate primitives will require an explicit lowering strategy.

[^13]: Yao et al., “SpikedAttention,” NeurIPS 2024, <https://proceedings.neurips.cc/paper_files/paper/2024/hash/7c9341ad0263428b5057d92f4d88dfa0-Abstract-Conference.html>; Shen et al., “High-performance deep spiking neural networks with 0.3 spikes per neuron,” Nature Communications 2024, <https://www.nature.com/articles/s41467-024-51110-5>. Numerical energy values are the authors' estimates for their configurations, not direct evidence about HyperLIF.
