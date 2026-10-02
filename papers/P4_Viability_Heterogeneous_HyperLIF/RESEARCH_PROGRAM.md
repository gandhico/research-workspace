# Viability-Aware Heterogeneous HyperLIF for Neuromorphic Robotics

## Executive judgment

The idea is technically possible and scientifically worth testing. A single continuous-reset
HyperLIF family can be parameterized into different temporal and excitability regimes, its continuous
states and true threshold upcrossings can both carry information, and a robot-level viability signal
can arbitrate among population outputs. Homeostatic threshold adaptation can regulate population
activity, while a separate control-barrier or reachability supervisor protects the plant.

The ingredients are not individually new. Heterogeneous spiking time constants and thresholds,
homeostatic plasticity, mixed spiking/non-spiking sensorimotor networks, homeostatic robots, and safe
learning filters all have precedents.[^1][^2][^3][^4][^5] The open research question is whether their
specific coupling produces a measurable advantage:

> Can a robot-state-viability-modulated bank of one continuous-reset HyperLIF family, deliberately
> spanning subthreshold through high-upcrossing regimes, preserve complementary computation under
> learning while using less event communication and fewer safety interventions than matched
> homogeneous controllers?

No indexed public record for the name “HyperLIF” surfaced in the web search performed for this
report. The local P1 manuscript is therefore the current model authority. Until a formal Scopus,
Web of Science, and Google Scholar review is completed, novelty language must say **“to our
knowledge”**, and no priority claim should be based on the model name alone.

## Why the hypothesis is plausible

Heterogeneous neuron parameters can improve temporal learning and robustness, and threshold
heterogeneity can change gating, entrainment, dimensionality, and decoding capacity.[^1][^2]
Diffusive homeostasis provides a particularly relevant precedent: it stabilized population activity
while preserving heterogeneous individual firing rates and broadened the responsive input range.[^3]
This directly supports the proposition that homeostasis need not homogenize a network.

The almost-non-spiking population also has a concrete precedent. Strohmer and colleagues operated a
spiking model below threshold to obtain continuous non-spiking interneurons that modulated spiking
populations in a closed-loop sensorimotor circuit.[^4] That work does not test a learned continuum of
one HyperLIF family, plant viability, or certified safety, but it makes the low-event side of the idea
credible.

At the high-activity side, caution is essential. In a continuous-reset neuron, high input need not
produce more true events. It may produce a single upcrossing followed by persistent above-threshold
occupancy. The first P4 sweep reproduced this depolarization-block-like failure. Consequently, every
experiment must report both upward crossings and threshold occupancy; “high spiking” is an empirical
regime, never a parameter label.

## Prior-art boundary

| Established result | What it contributes | What remains open here |
|---|---|---|
| Heterogeneous LIF/SNN parameters improve temporal task robustness.[^1] | Strong baseline for parameter distributions. | No plant viability, homeostatic arbitration, or one-family subthreshold/high-event continuum. |
| Threshold heterogeneity controls SNN computations.[^2] | Treat distribution width as a mechanistic variable. | No embodied learning or safety envelope. |
| Diffusive homeostasis preserves firing-rate heterogeneity.[^3] | Population regulation need not force identical rates. | No task controller or robot viability constraint. |
| Mixed spiking/non-spiking sensorimotor network.[^4] | Subthreshold continuous units can modulate spikes in closed loop. | No learned HyperLIF continuum or viability-aware arbitration. |
| FPGA homeostatic SNN robot controller.[^5] | Homeostatic self-repair can support obstacle avoidance. | Neural/hardware fault tolerance, not plant-state viability. |
| Cross-homeostatic E/I plasticity on DYNAP-SE2.[^6] | Stable self-calibration despite hardware mismatch. | No task policy, plant safety, or firing-regime routing. |
| Homeostatic dendritic neuromorphic device.[^7] | Multi-timescale processing plus autonomous activity stabilization. | No robot or population-level viability coupling. |
| SpikeAEC role-specialized spiking robot controller.[^8] | Distinct neural roles and neuromodulated arbitration. | No explicit viability set, firing-rate bands, HyperLIF, or CBF certificate. |
| Homeostatic reinforcement learning.[^9] | Drive reduction links reward to internal state. | A reward is not hard set invariance. |
| Viability-boundary learning for manipulators.[^10] | Direct robot viability-kernel approximation. | No SNN or neural homeostasis. |
| CBF/reachability safety supervisors.[^11][^12] | Conditions for forward invariance and minimal intervention. | Coupling to HyperLIF regimes is the proposed contribution. |

The strongest defensible contribution is therefore not “first heterogeneous SNN,” “first
homeostatic robot,” or “first safe learned controller.” It is the explicit, falsifiable link between
the plant's viability margin and the operating-regime arbitration and plasticity of a heterogeneous
continuous-reset HyperLIF network.

## Mathematical construction

### Plant and viability

Let a control-affine robot model be

\[
\dot x=f(x)+G(x)u+d, \qquad x\in\mathbb R^n,\ u\in\mathbb R^m,
\]

with state components such as attitude error, angular rate, obstacle distance, battery state,
motor temperature, and actuator margin. Define admissible operation by

\[
\mathcal V=\{x:h_j(x)\ge 0,\ j=1,\ldots,M\}.
\]

The first code implementation uses an axis-aligned box

\[
\ell_j\le x_j\le u_j
\]

because its barriers are explicit and auditable. For each dimension, define normalized slacks

\[
s_j^-=\frac{x_j-\ell_j}{u_j-\ell_j},\qquad
s_j^+=\frac{u_j-x_j}{u_j-\ell_j}.
\]

The exact health margin used by P4 is

\[
q(x)=2\min_j\{s_j^-,s_j^+\}.
\]

It equals one at the center of the box, zero at any boundary, and is negative outside. Nested modes
are nominal \(q>0.5\), adaptive \(0.2<q\le0.5\), protective \(0<q\le0.2\), and emergency
\(q\le0\). These thresholds are policy choices to ablate, not biological constants.

### Canonical HyperLIF population dynamics

Partition \(N\) neurons into \(K\) populations \(\mathcal P_k\). All use the same P1 equations, but
each population has a distinct parameter tuple

\[
\Theta_k=(\tau_{v,k},\tau_{r,k},\alpha_k,\gamma_k,\theta_k,
g_{0,k},\beta_k,\text{input gain}_k,\ldots).
\]

For neuron \(i\in\mathcal P_k\), the current P1 discrete contract is

\[
\theta^{\mathrm{eff}}_{i,t}=\theta_{k}+\kappa_a a_{i,t}-\gamma_k r_{i,t},
\]

\[
\hat r_{i,t}=\sigma\!\left(\alpha_k
(v_{i,t}-\theta^{\mathrm{eff}}_{i,t})\right),
\qquad
r_{i,t+1}=\hat r_{i,t}+(r_{i,t}-\hat r_{i,t})e^{-\Delta t/\tau_{r,k}}.
\]

With smoothed input magnitude

\[
A_\epsilon(I)=\sqrt{I^2+\epsilon^2}-\epsilon,
\]

the conductance is

\[
g_{i,t}=\big(g_{0,k}+\beta_k A_\epsilon(I_{i,t})\big)r_{i,t+1}^2,
\]

where base HyperLIF uses a fixed reset scale and Adaptive HyperLIF uses the input-dependent scale.
Let

\[
\lambda_{i,t}=\tau_{v,k}^{-1}+g_{i,t},\qquad
b_{i,t}=v_{\rm rest}\tau_{v,k}^{-1}+I_{i,t}\tau_{v,k}^{-1}+g_{i,t}v_{\rm reset}.
\]

The frozen-conductance voltage substep is

\[
v_{i,t+1}=v_{i,t}e^{-\lambda_{i,t}\Delta t}
+\frac{b_{i,t}}{\lambda_{i,t}}
\left(1-e^{-\lambda_{i,t}\Delta t}\right).
\]

Readiness stays in \([0,1]\) because its update is a convex combination of two values in that
interval. The voltage substep is the exact solution of a scalar affine equation with frozen current
and conductance. Neither fact proves global stability of the fully coupled recurrent network.

The physical event is always the upward crossing

\[
z_{i,t+1}=\mathbf 1[v_{i,t}<\theta_{e,k}\ \land\
v_{i,t+1}\ge\theta_{e,k}],
\]

not sampled occupancy \(\mathbf 1[v_{i,t+1}\ge\theta_{e,k}]\). Continuous-state training may use
\((v,r)\) even when \(z=0\); it must then be described as a continuous/hybrid recurrent computation,
not a spike-only implementation.

### Heterogeneous evidence fusion

Each population generates a decoded signal \(y_k\). In recognition, \(y_k\) is a class-logit vector.
In control, it is a candidate action \(u_k\). P4 combines a learned preference \(b_k\) with a
viability prior

\[
p_k(q)=\operatorname{softmax}_k\left[-\frac{1}{2T_a}
\left(\frac{q-c_k}{w_k}\right)^2\right],
\]

where high-health centers are assigned to low-event regimes and a near-boundary center to the
high-reactivity regime. The normalized mixture is

\[
\omega_k(q)=\frac{p_k(q)e^{b_k}}
{\sum_\ell p_\ell(q)e^{b_\ell}},\qquad
y=\sum_k\omega_k(q)y_k.
\]

Recognition experiments first use a uniform prior so that complementarity is tested without
inventing a robot state. Closed-loop experiments use \(p_k(q(x))\) and must verify that aggregate
high-reactivity weight increases monotonically as the viability margin shrinks.

### Population homeostasis

Let the observed population rate be true upcrossings per neuron per sampled step,

\[
\bar z_{k,t}=\frac{1}{|\mathcal P_k|T}\sum_{i\in\mathcal P_k}\sum_{\tau=t-T+1}^{t}z_{i,\tau}.
\]

The slow rate estimate and threshold offset are

\[
a_{k,t+1}=(1-\lambda_h)a_{k,t}+\lambda_h\bar z_{k,t},
\]

\[
\xi_{k,t+1}=\Pi_{[-\xi_{\max},\xi_{\max}]}
\left[\xi_{k,t}+\eta_h G(q_t)(a_{k,t}-\mu_k)\right].
\]

Here \(\mu_k\) is the midpoint of a population-specific activity band. Excess activity raises the
threshold; insufficient activity lowers it. Distinct \(\mu_k\) values preserve heterogeneity rather
than pushing every population to one rate. The plant-level plasticity gate is

\[
G(q)=\sigma\!\left(\frac{q-q_{\rm freeze}}{T_g}\right),
\]

and learning must be forced to zero whenever the production safety controller intervenes.

The intended time-scale ordering is

\[
\tau_r<\tau_v\ll\tau_{\rm task}\ll\tau_{\rm homeostasis}.
\]

Fast danger response should come from arbitration and the safety filter, not from destabilizing rapid
threshold learning. Fast Hebbian learning without a sufficiently fast stabilizing detector is known
to be risky.[^13]

### Safety filter and its claim boundary

For lower and upper box barriers, the exponential CBF condition

\[
\dot h_j+\kappa h_j\ge0
\]

gives affine inequalities \(Au\le b\). P4 constructs

\[
-G_j u\le f_j+\kappa(x_j-\ell_j),\qquad
G_j u\le-f_j+\kappa(u_j-x_j),
\]

plus action bounds. The reference implementation projects the neural action cyclically onto these
halfspaces and returns `certified=true` only if the final maximum violation is below tolerance.

Under locally Lipschitz dynamics, an initial state in \(\mathcal V\), valid CBF relative-degree
assumptions, feasible constraints, and exact-enough model evaluation, satisfying the CBF inequalities
implies forward invariance.[^11] The current cyclic projection is a test oracle, not the production
certificate. Robot work must replace it with a monitored QP solver, incorporate model-error margins,
measure solver deadlines, and invoke a separately validated backup controller on infeasibility.

### Training objectives

Recognition should minimize

\[
\mathcal L_{\rm cls}=\mathcal L_{\rm CE}
+\lambda_h\sum_k\big([\ell_k-a_k]_+^2+[a_k-u_k]_+^2\big)
+\lambda_{\rm route}\mathcal L_{\rm route}
+\lambda_{\rm sat}\mathcal L_{\rm saturation}.
\]

The current runner implements cross-entropy plus a separate slow threshold update. It records the
rate-band penalty but does not yet differentiate it because true events are discrete.

Closed-loop control should report the components of

\[
J=\sum_t\gamma^t\left(e_t^\top Qe_t+u_t^\top Ru_t
+\lambda_{\Delta u}\|\Delta u_t\|^2
+\lambda_I\|u_t-u_{\rm neuro,t}\|^2
+\lambda_V\sum_j[-h_j(x_t)]_+^2\right).
\]

Activity accounting must remain separated:

\[
E_{\rm proxy}=c_{\rm state}NT+c_{\rm syn}N_{\rm synops}
+c_{\rm event}N_{\rm crossings}.
\]

Subthreshold neurons still require state updates. A lower spike count is not a hardware-energy claim;
real energy requires a named device, measurement boundary, latency, and power instrumentation.

## Falsifiable hypotheses

| ID | Hypothesis | Falsifier |
|---|---|---|
| H1 | Subthreshold \((v,r)\) features add predictive information beyond high-rate spikes. | Matched feature ablation or conditional permutation removes no accuracy/log-likelihood. |
| H2 | Static heterogeneity improves corrupted temporal recognition at matched state, parameter, and optimization budgets. | Gain disappears after compute matching or is absent on both temporal modalities. |
| H3 | Population-specific homeostasis restores separated activity bands after input-gain drift without erasing task performance. | Rates collapse, remain outside bands, or adaptation harms accuracy beyond the noninferiority margin. |
| H4 | Near-boundary arbitration increases high-reactivity weight and reduces recovery time without materially raising nominal events. | Routing is non-monotone or recovery/events do not improve. |
| H5 | A safety filter reduces violation probability/severity while retaining tracking noninferiority. | No safety improvement, infeasible QPs, missed deadlines, or excessive nominal intervention. |
| H6 | Benefits are stronger on SHD/SSC/DVS-Gesture than on near-static N-MNIST. | Uniform gains across modalities weaken the temporal-mechanism interpretation. |

## Experimental program

### Stage 0 — Evidence and data gate

- Freeze the canonical P1 equation and upcrossing semantics.
- Hash every cache and split; never regenerate an absent cache under the same dataset identity.
- Recover the exact prior N-MNIST/DVS/SSC files before calling any run a replication.
- Add the new P4 Git remote or bundle before multi-agent edits leave the machine.

Exit criterion: each intended dataset has a path, SHA-256, preprocessing provenance, class count,
time bins, and train/validation/test rule.

### Stage 1 — Dynamics and regime atlas

- Compare discrete Julia steps against a high-accuracy ODE reference under constant, ramp, pulse, and
  chirp currents.
- Map event rate, occupancy, readiness, voltage, release time, and crossing-speed conditioning.
- Detect intentional subthreshold computation separately from depolarization block.
- Calibrate regime parameters only on synthetic currents or training-only current quantiles.

Exit criterion: four nonoverlapping empirical bands exist on the declared input envelope, remain
finite over seeds, and avoid high-occupancy/zero-crossing block except where retained as a deliberate
negative control.

### Stage 2 — Recognition discovery

Use the identical event/image and audio caches from P1. The primary pair should be SHD for audio and
DVS-Gesture-32 for dynamic vision; N-MNIST is the near-static negative control. SSC and DVS-Gesture-48
are replications. SHD and SSC are explicitly timing-dependent audio benchmarks.[^14] N-MNIST is a
saccade-converted static-image benchmark.[^15]

Run three seeds, capped training, and the following minimum comparisons:

1. matched homogeneous HyperLIF;
2. four separately homogeneous regime models;
3. static heterogeneous HyperLIF with uniform fusion;
4. learned fusion;
5. learned fusion plus population homeostasis;
6. remove subthreshold population;
7. remove high-reactivity population;
8. spike-only versus continuous \((v,r)\) versus hybrid evidence.

Exit criterion: finite training, preserved regime separation, no test-based selection, and at least
one effect large enough to justify the confirmation budget.

### Stage 3 — Recognition confirmation

- Ten fresh paired seeds for the selected architecture.
- Same example order, time bins, total hidden state, trainable parameter budget, optimizer steps, and
  early-stopping rule across comparisons.
- Exact paired seed-level randomization tests and hierarchical bootstrap confidence intervals over
  seeds and examples.
- Holm correction across preregistered primary comparisons.
- Report accuracy, negative log-likelihood, calibration error, corruption robustness, true events,
  occupancy, state updates, parameters, wall time, and failure rate.

Suggested preregistered gate against the best matched homogeneous HyperLIF:

- accuracy lower confidence bound greater than -1 absolute percentage point;
- event-proxy ratio upper confidence bound below 0.80;
- reproduction on both primary modalities;
- regime-separation index remains positive under gain drift.

### Stage 4 — Closed-loop robot simulation

Integrate with the existing Crazyflie/Skydio gate-residual benchmark, but keep a validated classical
controller as the baseline and backup. The neural network should first propose only a bounded residual.

Stressors: wind, mass/inertia shift, motor degradation, sensor delay/dropout, battery sag, thermal
limit, obstacle approach, and combined disturbances. Use common presampled scenario files across all
controllers.

Compare classical controller; homogeneous HyperLIF residual; static heterogeneous residual;
homeostatic heterogeneous residual; viability-routed residual; and full routed controller plus safety
filter. Report tracking, recovery time, violations, minimum margin, intervention norm/rate, control
effort, events, occupancy, deadline misses, and infeasibility.

Exit criterion: safety improvement with tracking noninferiority, monotone risk routing, bounded
intervention in nominal episodes, and no silent numerical failures.

### Stage 5 — Hardware

Proceed only after the simulator gates pass. Require a physical emergency stop, conservative actuator
limits, prevalidated backup controller, QP timing below the control deadline, logging independent of
the learned controller, and a stop rule on the first unexplained hard-limit crossing.

## Required baselines and ablations

- LIF, PLIF, ALIF/LSNN, and current multi-parametric LIF where reproducible.
- Homogeneous HyperLIF matched by mean parameters.
- Four homogeneous HyperLIF ensembles matched to heterogeneous state and parameter counts.
- Heterogeneity width sweep and shuffled population labels.
- No, low→high, high→low, and bidirectional cross-population communication.
- Fixed, learned, and monotone viability-based arbitration.
- Shared versus population-specific rate targets.
- Homeostasis off, frozen after calibration, or active during learning.
- Safety penalty only versus hard CBF-QP filter.
- True upward crossings versus legacy occupancy.
- Equal event budget and equal measured compute/energy budget; do not conflate them.

## Statistics and failure policy

For recognition, use paired seeds and paired example predictions. Primary comparisons use a paired
randomization test and bootstrap 95% confidence intervals. For robot episodes, use configuration as a
fixed effect and seed/scenario as random effects; analyze any-violation probability separately from
continuous severity and recovery outcomes.

A numerical run fails for NaN/Inf, readiness outside tolerance, missed/excess crossings against the
reference, non-releasing gate, depolarization block outside a declared negative-control condition, or
missing provenance. Infrastructure failures may rerun with the identical seed. Model failures remain
in the denominator and require a worst-case sensitivity analysis.

The mechanism is unsupported if gains disappear under matched compute, the subthreshold population
adds no conditional information, routing is not monotone in risk, homeostasis destroys rather than
preserves rate diversity, or the safety layer cannot meet its assumptions and deadlines.

## Evidence generated in the first session

The P4 Julia tests cover viability geometry, nested region classification, risk arbitration,
construction of four HyperLIF configurations, heterogeneous forward/gradient propagation, coupled
homeostatic threshold updates, plasticity gating, and CBF halfspace projection.

The first naive high-reactivity parameters failed: they entered persistent high occupancy with almost
no upcrossings. A label-free constant-current search selected a candidate with \(\theta=1.05\), reset
gain 400, \(\tau_r=0.5\) ms, \(\gamma=0.1\), and \(\alpha=60\). It reached a peak event fraction of
0.49 with no high-occupancy block over the screened drive interval. This is mechanism calibration,
not a task result.

A per-regime input-gain calibration on the exact local SHD cache produced initial rates of 0.00356,
0.01962, 0.04253, and 0.05725 upcrossings per neuron-step. Tiny one- and three-epoch pilots ran
end to end at 7.5% test accuracy against 5% chance.

## Correction from the second session

Three of those first-session statements do not survive measurement, and the correction changes the
program rather than merely qualifying it. The detail and the file-level evidence are in
`PROGRESS_REGISTER.md` (findings F1–F5); the consequences for the design are:

**Input gain is not the regime lever on this cache.** Sweeping `input_scale` from 0.5 to 512 on
training-only SHD input drives all four regimes to the same ceiling of 0.049–0.061 upcrossings per
neuron-step, roughly one crossing per neuron per 20-step sequence. At the calibrated gains the burst
population already receives drive with standard deviation 52.9 against a threshold of 1.05, with
46.8% of its neuron-time steps above threshold. The four "different initial activity rates" were
four points on a saturation curve, not four firing regimes, and two of the four gains were the
maximum of the search grid rather than interior optima. The existing block screen missed this
because occupancy stayed just below its 0.50 trigger while events remained non-zero. **Any
diagnosis of a firing regime must therefore screen for saturation as well as for block**, and a
calibration that terminates on its grid boundary must be reported as unresolved rather than as a
recommendation.

**The 20-bin horizon is not the cause.** Under synthetic constant current at the same horizon the
burst regime still reaches 8 crossings per neuron. The limiter is the input's approximately
zero-mean, high-variance 700-channel fan-in: raising the gain scales a symmetric noise distribution
instead of moving neurons into a different regime. This matters for Stage 1, whose exit criterion
was written against synthetic currents; **the atlas must be re-declared on the empirical input
envelope, not on constant drive**, or its bands will not transfer again.

**A shared gain restores the regimes.** At one shared gain of 1.4 the four regimes measure
0.0024 / 0.0057 / 0.0116 / 0.0221 upcrossings per neuron-step, in order, with 9.1× separation and
burst occupancy 0.037. A shared gain is also the better experiment: under per-regime gains any
population difference conflates intrinsic dynamics with input signal-to-noise, so the heterogeneity
hypothesis could not have been cleanly tested even had the regimes separated.

**The paired homeostasis pilot compared a model to itself.** Both runs selected epoch 1, and
threshold offsets were applied only after each epoch's validation evaluation, so both selected the
untouched reference configurations; the test dictionaries are byte-identical. The reported
penalty difference came from checkpoints that were never selected, and under homeostasis the
penalty actually rose. The burst offset also reached -0.30 of a -0.40 clamp in two epochs because
its band midpoint of 0.17, inherited from the synthetic atlas, is unreachable on this cache. H3 is
therefore untested, not weakly supported.

**The event-communication clause is currently unmeasurable.** `readout=:hybrid_vr` builds features
from time-averaged voltage and gate; upward crossings never enter the readout or the loss, so
reducing events costs the objective nothing. The research question's "using less event
communication" needs an event-carrying readout (`:hybrid_zr`, or `learning_mode=:surrogate` with
`:spike_count`) before it can be tested at all. Until then event counts are diagnostics.

**Matched families now exist.** `--model` selects `heterogeneous`, `ensemble` (four populations at
the bank's mean parameters), or `homogeneous` (one population carrying the whole hidden budget).
All three hold total hidden state equal with effective parameter counts within 63 of each other.
`ensemble` is the control that separates a heterogeneity effect from a plain ensembling effect, and
it is the comparison H2 actually rests on.

## Immediate next actions

1. Aggregate the matched heterogeneous/ensemble/homogeneous triple over three seeds. If
   heterogeneous does not beat `ensemble` at matched budget, H2 has no support on this cache.
2. Check that regime separation survives training, not only initialization; the first pilot's
   ordering was already inverted at the end of three epochs.
3. Add an event-carrying readout so the event-communication clause becomes testable at all.
4. Re-run the homeostasis pairing non-vacuously, with reachable bands and
   `homeostasis_effective` true, before H3 is discussed.
5. Add ODE/discrete parity and explicit gate-release, depolarization-block, and **saturation**
   tests; the current screen catches block but not saturation.
6. Add matched Julia LIF/PLIF/ALIF controls.
7. Recover the byte-identical N-MNIST and DVS-Gesture caches; do not substitute regenerated files.
8. Only after recognition gates pass, create the bounded residual interface to the P3 flight-control
   simulator and replace the reference projection with a monitored QP safety filter.

### A prior question for the portfolio

Every recognition hypothesis here rests on populations occupying genuinely different temporal
regimes. On a 20-bin cache the whole four-regime bank now fits inside 0.002–0.022 crossings per
neuron-step, that is, between roughly 0.05 and 0.44 crossings per neuron per sequence. That is a
narrow band in which to demonstrate that regime diversity does useful work. Before committing the
Stage 3 confirmation budget it is worth deciding whether SHD at 20 bins can carry this claim at
all, or whether a longer-horizon cache is a precondition rather than a replication.

## Sources

[^1]: Nicolas Perez-Nieves et al., “[Neural heterogeneity promotes robust learning](https://doi.org/10.1038/s41467-021-26022-3),” *Nature Communications*, 2021.
[^2]: Richard Gast et al., “[Neural heterogeneity controls computations in spiking neural networks](https://doi.org/10.1073/pnas.2311885121),” *PNAS*, 2024.
[^3]: Yann Sweeney, Jeanette Hellgren Kotaleski, and Matthias H. Hennig, “[A Diffusive Homeostatic Signal Maintains Neural Heterogeneity and Responsiveness in Cortical Networks](https://doi.org/10.1371/journal.pcbi.1004389),” *PLOS Computational Biology*, 2015.
[^4]: Benjamin Strohmer et al., “[Integrating Non-spiking Interneurons in Spiking Neural Networks](https://doi.org/10.3389/fnins.2021.633945),” *Frontiers in Neuroscience*, 2021.
[^5]: Anju Pulikkakudi Johnson et al., “[Homeostatic Fault Tolerance in Spiking Neural Networks: A Dynamic Hardware Perspective](https://doi.org/10.1109/TCSI.2017.2726763),” *IEEE Transactions on Circuits and Systems I*, 2018.
[^6]: Ana Maryada et al., “[Stable recurrent dynamics in heterogeneous neuromorphic computing systems using excitatory and inhibitory plasticity](https://doi.org/10.1038/s41467-025-60697-2),” *Nature Communications*, 2025.
[^7]: Zhang et al., “[Homeostatic dendritic neuron based on co-integrated volatile and non-volatile memristors for neuromorphic processing](https://doi.org/10.1038/s41467-026-73669-x),” *Nature Communications*, 2026.
[^8]: “[SpikeAEC: a neuromodulation-based spiking controller for explore-exploit balancing in mobile robots](https://doi.org/10.3389/fnbot.2026.1757795),” *Frontiers in Neurorobotics*, 2026.
[^9]: Mehdi Keramati and Boris Gutkin, “[Homeostatic reinforcement learning for integrating reward collection and physiological stability](https://doi.org/10.7554/eLife.04811),” *eLife*, 2014.
[^10]: Paolo La Rocca et al., “[VBOC: Learning the Viability Boundary of a Robot Manipulator Using Optimal Control](https://doi.org/10.1109/LRA.2023.3313921),” *IEEE Robotics and Automation Letters*, 2023.
[^11]: Aaron D. Ames et al., “[Control Barrier Function Based Quadratic Programs for Safety Critical Systems](https://doi.org/10.1109/TAC.2016.2638961),” *IEEE Transactions on Automatic Control*, 2017.
[^12]: Jaime F. Fisac et al., “[A General Safety Framework for Learning-Based Control in Uncertain Robotic Systems](https://doi.org/10.1109/TAC.2018.2876389),” *IEEE Transactions on Automatic Control*, 2019.
[^13]: Friedemann Zenke, Guillaume Hennequin, and Wulfram Gerstner, “[Synaptic Plasticity in Neural Networks Needs Homeostasis with a Fast Rate Detector](https://doi.org/10.1371/journal.pcbi.1003330),” *PLOS Computational Biology*, 2013.
[^14]: Benjamin Cramer et al., “[The Heidelberg Spiking Data Sets for the Systematic Evaluation of Spiking Neural Networks](https://doi.org/10.1109/TNNLS.2020.3044364),” *IEEE Transactions on Neural Networks and Learning Systems*, 2020.
[^15]: Garrick Orchard et al., “[Converting Static Image Datasets to Spiking Neuromorphic Datasets Using Saccades](https://doi.org/10.3389/fnins.2015.00437),” *Frontiers in Neuroscience*, 2015.

