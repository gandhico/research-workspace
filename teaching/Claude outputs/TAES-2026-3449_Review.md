# Review — TAES-2026-3449
**"PH-GRN: A Predictive Hierarchical Gene Regulatory Network Framework for UAV Swarm Cooperative Entrapment"**
Fan, Huang, Wang, Zhang & Wang — Dalian University of Technology

**Recommendation: Major Revision**

---

# PART A — CONFIDENTIAL COMMENTS TO THE EDITOR

## Recommendation
Major Revision. The manuscript is technically competent and the architecture is coherent, but three issues prevent a positive assessment in its present form, and one of them is potentially decisive.

## The decisive issue: the headline result does not survive inspection
The abstract's central claim — an **84.33 % improvement in average escape distance** — is, per Fig. 12(c), the ratio 0.1576 m / 0.0855 m. The absolute difference is **7.2 cm**, in a 20 m × 20 m workspace, against an inter-UAV safety radius of 1.5 m, on a *signed* metric whose per-trial values span roughly −0.7 m to +0.7 m. A percentage computed on a signed quantity whose mean sits near zero is numerically unstable and rhetorically inflated.

Worse, the same figure shows the predictive variant is marginally **worse** on the other two metrics (uniformity 0.5990 vs 0.5943; movement distance 0.2944 vs 0.2860 — both "lower is better"). The manuscript reports a percentage only for the metric that improved and describes the two that regressed as "competitive." In the plotted bars the two variants are visually near-identical across all 100 trials on all three metrics.

I do not read this as misconduct — the data are shown honestly and the differences are small in both directions. But the framing overstates what the evidence supports, and the abstract, contributions, and conclusion all rest on it. This must be corrected with paired statistics, confidence intervals, and an entrapment success rate before the contribution can be judged.

## Novelty concern requiring editorial attention
Reference **[39]** (Wen *et al.*, "Time-varying target predictive entrapment based on gene regulatory network and sliding mode control," *IEEE IoT J.*, 2025) appears to be the nearest prior art — GRN-based entrapment with target prediction — and is the closest analogue to this paper's first claimed contribution. It is cited once in the Introduction and never compared against, nor is any delta stated. Separately, the construction of the GRN perception layer itself is deferred to the authors' prior work [36] ("More details … can be found in Fan *et al.* [36]"), leaving the paper not self-contained as a Regular Paper. I would ask the authors to state explicitly what is new relative to [36] and [39], and to add [39] as a baseline.

## Scope-fit question for TAES
The evaluation is a 2-D point-mass MATLAB simulation: 20 m arena, UAV maximum speed 0.4 m/s, target 0.35 m/s, Δt = 1 s, inter-UAV safety distance 1.5 m. These are ground-robot-swarm testbed parameters, not aerospace ones. There is no vehicle dynamics model, no attitude loop, no non-holonomic or actuator constraint, no wind/disturbance, and no hardware or HIL validation. The abstract's claims of generalization to 3-D and to "underwater cooperative entrapment" are asserted with zero supporting derivation or experiment. The editor may wish to consider whether the contribution is better matched to a swarm-robotics venue unless the authors add UAV-realistic dynamics and scales.

## Suggested scoring (adjust to your judgement)
- Originality — moderate; contingent on the [36]/[39] delta being established
- Technical quality / soundness — below threshold as submitted (unverified claims, unproved safety, parameter inconsistencies)
- Significance — moderate
- Presentation — acceptable, with a number of correctable errors
- Confidence — high on the numerical and editorial findings; moderate on GRN-specific prior art

## Short summary for the decision letter
> The manuscript proposes PH-GRN, a three-layer framework integrating LSTM target prediction, inertia-aware Hungarian capture-point assignment, and an improved artificial potential field with vortex obstacle avoidance and adaptive damping. The architecture is coherent and the evaluation is reasonably broad. However, the headline 84.33 % improvement corresponds to a 7 cm absolute difference on a signed metric and is accompanied by small regressions on the other two metrics; the LSTM component is undocumented and unbenchmarked against trivial predictive baselines; the claimed contributions other than prediction are never ablated; collision avoidance is neither proved nor measured; the stated velocity constraint appears not to be enforced by the equations; and the novelty relative to references [36] and [39] is not established. Major revision is recommended.

---

# PART B — COMMENTS TO THE AUTHORS

## Summary of the submission
The paper proposes PH-GRN, a three-layer architecture for multi-UAV entrapment of multiple noncooperative moving targets. The perception layer uses an LSTM to forecast target motion and maps predicted targets and obstacles into a morphogen field whose isoline defines a Predictive Entrapment Pattern (PEP). The decision layer discretizes the PEP into uniformly distributed capture points and assigns UAVs via a Hungarian solver on a cost matrix modified by an inertia factor that penalizes reassignment. The execution layer computes velocity commands from a weighted sum of target attraction, inter-UAV repulsion, vortex obstacle avoidance, and a damped capture-point attraction. Evaluation is by MATLAB simulation against AGENT, CH-GRN, and RE-GRN, plus 100-trial randomized comparisons with and without prediction at three mission scales.

## Strengths
The three-layer decomposition is clean and each layer addresses a genuine and well-identified failure mode: reactive lag, assignment chattering, and APF stagnation. Treating these jointly rather than in isolation is the paper's real contribution.

The evaluation goes beyond a single illustrative run. The 100-trial randomized experiments at three mission scales, and particularly the time-domain proportion analysis of Fig. 13 — which separates transient from steady-state behaviour rather than averaging a signed metric over the whole run — show good methodological awareness. That analysis is the most convincing evidence in the paper and deserves more prominence than the 84.33 % figure.

The escape-distance metric of Eq. (32) and Table II, with its sign convention tied to convex-hull membership and its explicit handling of the 1-UAV, 2-UAV, and collinear degenerate cases, is well-conceived and more informative than formation-error metrics alone.

The capture-point generation machinery — proportional-fairness allocation (12), Shoelace-based orientation normalization (13), and temporal smoothing (14) — is a thoughtful treatment of an underappreciated problem, namely that a naively re-sampled contour produces spurious reassignment.

---

## Major concerns

### M1. The principal quantitative claim is not supported by the data as presented
The 84.33 % improvement in average escape distance corresponds, per Fig. 12(c), to 0.1576 m versus 0.0855 m — an absolute difference of 7.2 cm in a 20 m workspace, on a signed metric whose per-trial values range from approximately −0.7 m to +0.7 m. A ratio of two near-zero signed means is not a stable effect size.

In the same figure, the predictive variant is *worse* on the other two metrics: entrapment uniformity 0.5990 versus 0.5943, and average movement distance 0.2944 versus 0.2860, both defined as "lower is better." Reporting a percentage improvement for the one metric that improved while describing the two regressions as "competitive" is not an even-handed presentation.

Please: (i) report mean ± standard deviation or 95 % confidence intervals for all three metrics; (ii) apply a paired test (the trials appear to be matched with and without prediction, so a paired *t*-test or Wilcoxon signed-rank test is appropriate and will be considerably more powerful); (iii) report the effect for all three metrics symmetrically, including the two regressions; (iv) replace or supplement the ratio with an absolute difference and a paired difference distribution. Note that the counts in Table III (56/32, 65/28, 63/22) are individually significant under a sign test — that is a stronger and more defensible result than the 84.33 % figure, and I would encourage you to lead with it.

Additionally, mean escape distances of 0.086–0.158 m are far below the 1.5 m inter-UAV safety distance, which implies that on average the target sits essentially on the convex-hull boundary, and a substantial fraction of trials are negative (not entrapped at all). Please report the **entrapment success rate** — the fraction of trials achieving and holding I_esc > 0 — and the time to first successful entrapment. Without these, it is difficult to establish that the method entraps targets at all, as distinct from entrapping them slightly more often than the ablated variant.

### M2. Novelty relative to [36] and [39] is not established
Reference [39] (Wen *et al.*, 2025) combines GRN-based entrapment with target prediction for time-varying targets — essentially the first claimed contribution of this paper. It is cited in passing in the Introduction and never revisited. Please state explicitly and technically what PH-GRN does that [39] does not, and include [39] as a baseline in the comparative simulations.

Relatedly, Section III-B defers the construction of the GRN structure to [36] ("More details on the construction of the GRN-based perception layer can be found in Fan *et al.* [36]"). For a Regular Paper the perception layer should be reproducible from this manuscript alone. Please include the GRN topology, the genetic-programming-derived structure or its result, and the parameters needed to reconstruct the morphogen field.

### M3. The LSTM is entirely undocumented and unbenchmarked
The manuscript states that an LSTM predictor is used and defines its inputs, but I could not locate: the architecture (layers, hidden units), history length *H*, prediction horizon *q*, training data generation procedure, number of trajectories, train/validation/test split, loss, optimizer, learning rate, epochs, normalization, or any prediction-error statistic (RMSE, ADE/FDE) at the horizon actually used.

This matters disproportionately because the entire large-scale evaluation of Section IV-E is an ablation of exactly this component. Two specific requests:

First, please state the target motion model used at test time. If the targets follow smooth random trajectories, and the LSTM was trained on the same generative process, the evaluation is in-distribution and optimistic.

Second, please compare the LSTM against a constant-velocity extrapolator and a constant-acceleration or Kalman-filter predictor under identical conditions. Given how small the measured differences are (M1), it is entirely plausible that the benefit comes from having *any* short-horizon prediction, not from the LSTM specifically. If a constant-velocity baseline matches the LSTM, the paper's framing should change accordingly — which would not diminish the architecture, but would correctly locate the contribution.

### M4. Only one of three claimed contributions is ablated
The paper claims three innovations: predictive pattern formation, inertia-aware allocation, and the improved APF with vortex avoidance and adaptive damping. The large-scale evaluation ablates only the first. Please add, at minimum: PH-GRN with η = 1 (inertia disabled), PH-GRN with η_tan = 0 (vortex term removed), and PH-GRN with λ_kd = 0 (adaptive damping removed), each measured on task-switching frequency, trajectory oscillation, and convergence time as appropriate. Without these, the claimed contributions are architectural assertions rather than demonstrated ones.

I would add one further ablation. The resultant force (24) weights the morphogen-derived target attraction at w_tar = 0.3 while the capture-point term is weighted w_cap = 1.0, and Eq. (21) is a proportional-derivative law toward an assigned waypoint. On these weights, the execution layer is dominated by PD-to-waypoint plus standard APF repulsion, and the gene-regulatory field appears to act mainly as a *generator* of the contour from which capture points are extracted rather than as a driver of motion. Please run the framework with w_tar = 0 to establish how much the morphogen term contributes to closed-loop behaviour, and if the contribution is small, reposition the bio-inspired framing accordingly.

### M5. Safety is neither guaranteed nor measured
Collision avoidance is central to the method but appears nowhere in the results. Please report: minimum inter-UAV separation over each run, minimum UAV–obstacle clearance, and the number and rate of safety violations (r_ij < r_imp, or penetration of an obstacle).

On the analytical side, the radial repulsion in (20) is bounded, and the velocity increment is then clamped by (26) to Δv_limit = 0.4. A bounded repulsive acceleration subject to a saturation cannot in general guarantee that r_ij ≥ r_imp is maintained; safety therefore depends on the parameter regime rather than on the construction. Please either provide a forward-invariance or Lyapunov argument for the safe set under the stated bounds, or state plainly that safety is empirical and support it with the metrics above. A full stability proof for the switched, gain-scheduled, saturated closed loop may be more than is reasonable to demand, but the current complete absence of both proof and measurement is not tenable for a control contribution.

Two specific mechanisms deserve scrutiny here. The obstacle sensing radius is r_obs = 0.8 m, obstacle radii are drawn from [0.8, 1.2] m, and a UAV travels up to 0.4 m per step — so a UAV receives roughly **two time steps** of warning before contact. Second, Δt = 1 s with forward-Euler integration is very coarse for a potential-field controller at these length scales. I would ask you to verify that the reported oscillation and overshoot — which the adaptive damping is introduced to suppress — are not substantially artifacts of the integration step. A step-size refinement study (Δt = 0.1 s, 0.05 s) would settle this and would materially strengthen the damping contribution if the behaviour persists.

### M6. The stated velocity constraint does not appear to be enforced
Eq. (26) constrains the *velocity increment* ‖Δv_i‖ to Δv_limit, and Eq. (27) then accumulates it into v_i(t+1) with no saturation on ‖v_i(t+1)‖. Table I nonetheless describes Δv_limit = 0.4 m/s as "Maximum UAV speed," and Assumption 3 and Section IV-A both rely on a 0.4 m/s cap relative to the 0.35 m/s target. As written, Δv_limit is a per-step acceleration bound, and the actual speed is limited only implicitly by the damping term −K_d·v_i in (21). Please correct the table entry, add an explicit speed saturation if one was used in the implementation, and confirm whether the reported results need regenerating. If the UAVs in fact exceed 0.35 m/s by more than "slightly," the comparison against targets is affected.

### M7. Centralization is understated relative to the self-organization framing
Assumption 1 grants every UAV the positions of all UAVs, targets, and obstacles; the decision layer builds a global N × N cost matrix and solves it with the Hungarian algorithm. This is a centralized or fully-connected-communication architecture, which sits uneasily with the repeated framing as "decentralized self-organization" and "each UAV acts as an artificial cell." The Conclusion acknowledges this, but the acknowledgement arrives too late to correct the impression built over the preceding twelve pages.

Please state the communication and computation architecture explicitly in Section II, report the O(N³) assignment cost with measured wall-clock timings versus swarm size, and discuss behaviour under directed or range-limited communication graphs, packet loss, and localized sensing. The proportional-fairness allocation (12) in particular requires every agent to know every PEP perimeter, which is a strong global requirement.

### M8. Scale, dynamics, and unsupported generalization claims
The UAV model is a planar point mass. There is no attitude dynamics, no non-holonomic or under-actuation constraint, no actuator saturation beyond the increment clamp, and no disturbance. The parameter set — 20 m arena, 0.4 m/s, 1.5 m safety radius, Δt = 1 s — corresponds to a ground-robot testbed rather than to aerial vehicles, whose operating speeds are one to two orders of magnitude higher and for whom turn-rate limits dominate pursuit geometry.

This is acceptable for a high-level guidance contribution if stated as such, but the manuscript makes broader claims. The abstract asserts the framework is "inherently generalizable to three-dimensional scenarios" and shows "great application potential for underwater cooperative entrapment." Neither is demonstrated. Concretely, the vortex direction factor σ_i and the Shoelace-based clockwise ordering (13) are intrinsically planar constructions; in 3-D the tangential direction is not determined by a sign but by a choice of vector in a tangent plane, and there is no canonical cyclic ordering of capture points on a closed surface. Please either provide the 3-D derivation and at least one 3-D simulation, or narrow these claims to what is shown. The underwater claim should be removed unless supported.

### M9. Parameter sensitivity, and the compounding of four lag mechanisms
Table I lists roughly twenty tuned parameters with no justification for their values and no sensitivity analysis. Please report how performance and stability vary with at least the inertia factor η, the close-range damping gain λ_kd, the smoothing factors γ and β, and the prediction weights α_i.

I would draw particular attention to an interaction the paper does not discuss. Prediction is introduced to remove reactive lag, but the pipeline then inserts four separate lag-inducing mechanisms: the temporal coherence blend γ (4), the capture-point smoothing β (14), the assignment inertia η (17), and the velocity damping K_d (21). Each is individually well-motivated, but their lags compound, and at γ = 0.5, β = 0.4, and η = 0.25 the net phase lag may well consume much of the lead time that the LSTM provides. This is a plausible explanation for why the measured benefit in Fig. 12(c) is so small, and it is the most interesting open question in the paper. An analysis or empirical characterization of net effective lead time — predicted horizon minus accumulated filter lag — would substantially strengthen the work.

### M10. Baselines and their tuning
All three baselines (AGENT [37], CH-GRN [35], RE-GRN [38]) are GRN-family methods, two of them closely related to the authors' own prior work, and AGENT [37] is an unrefereed arXiv preprint. The Introduction surveys leader–follower, virtual-structure, consensus, and reinforcement-learning approaches, yet none is compared against. Please add at least one contemporary non-GRN predictive or multi-agent control baseline, and state how all baseline parameters were tuned and whether every method operated under identical velocity, sensing, obstacle, and communication constraints. A baseline tuned less carefully than the proposed method is not a fair comparison, and readers cannot currently assess this.

---

## Minor comments and technical corrections

**C1.** Eq. (2): the quantifier ranges over targets *j*, but the expression involves UAV index *i* and capture-point index *k*. The indices appear inconsistent. Also, a limit that is asserted to be ≤ ε should be a limit superior, since the limit itself may not exist for a moving target.

**C2.** Eq. (16): the two one-to-one constraints use the same summation index. For each UAV *i* the sum should run over capture points *k*; for each capture point *k* the sum should run over UAVs *i*. As printed, both sum over the same index.

**C3.** Section III-B states that γ is typically selected in [0.7, 0.9]; Table I uses γ = 0.5. Please reconcile.

**C4.** Table I: Δv_limit = 0.4 is described as "Maximum UAV speed" but is used in (26) as a bound on the velocity *increment*. See M6.

**C5.** The history length *H* and prediction horizon *q* are never reported numerically. Table I gives only α_1 and α_2, from which q = 2 can be inferred, but this should be stated. Please also report Δt's role in the prediction horizon — q = 2 with Δt = 1 s is a 2 s lookahead against a target moving at 0.35 m/s, i.e. a 0.7 m lead, which is worth stating explicitly as it bears directly on M1.

**C6.** The directional factor σ_i in (20) is illustrated geometrically in Fig. 6 but never defined by a formula or selection rule. In particular, the condition under which σ_i = 0 (Fig. 6(c), no tangential guidance) is not specified. This is a reproducibility gap in the vortex mechanism.

**C7.** Eq. (4) is described as a mechanism that "recursively smooth[s]" the prediction sequence, but it is a one-step convex blend of the current measured velocity and the weighted prediction; it does not involve V^pred at the previous step and is therefore not recursive. Either correct the description or, if an exponential moving average was intended, correct the equation.

**C8.** Fig. 1 and Fig. 2 carry the identical caption "Flowchart of the PH-GRN algorithm." Fig. 2 depicts the layered GRN architecture and should be captioned accordingly.

**C9.** Section IV-C, p. 11: "AGENT AGENT achieves rapid initial entrapment" — duplicated word.

**C10.** Section IV-E denotes the complete predictive method "GRN" in the running text while Table III labels the same method "PH-GRN." Since "GRN" is also used throughout the paper as the generic term for the model class, this is genuinely confusing. I suggest retaining PH-GRN and H-GRN consistently.

**C11.** In all three subplots of Fig. 12(c) the horizontal axis is labelled "Time" but spans 100 independent trials. Please relabel as "Trial."

**C12.** Fig. 11: please state whether each box aggregates 100 independent randomized experiments or time samples from a single run. The two carry very different meanings.

**C13.** Table III: please define what constitutes "Equal" for a continuous time-domain proportion P_t^+. Between 7 % and 15 % exact ties on a continuous quantity suggests either a rounding rule or a set of degenerate trials (e.g. both variants at 0), which should be explained. Please also report a sign test or McNemar test on these counts — they support you.

**C14.** Eq. (31): I_move is the mean per-step displacement (mean speed × Δt) at a single time instant, not a cumulative path length. "Average movement distance" invites misreading; consider "mean instantaneous step length" or report cumulative path length instead, which is the quantity readers will associate with energy consumption.

**C15.** Eq. (12): proportional-fairness allocation permits a target to be assigned fewer than three UAVs, in which case Table II makes the escape distance negative by construction regardless of controller performance. Please state whether n_q ≥ 3 is enforced, and how such trials were treated in the averages of Fig. 12(c). If they were included, they may account for a meaningful share of the negative values.

**C16.** Eq. (17): the inertia term multiplies the previously-assigned entry by η = 0.25, i.e. a reassignment requires the alternative to be four times cheaper. This is a large hysteresis, and because the discount is multiplicative and applied to one entry per row, the Hungarian solution no longer minimizes the true cost. Please characterize the resulting suboptimality (empirically is sufficient: report true assignment cost with and without the inertia modification) and justify the magnitude of η.

**C17.** Eq. (18): the target attractive force is asymmetric about the desired contour — its magnitude is bounded by (1 − φ_ref) = 0.25 from inside and by φ_ref = 0.75 from outside, and it vanishes at the contour, giving asymptotically slow final convergence. Please comment on whether this asymmetry is intentional.

**C18.** Assumption 2 (base-station deployment and recall of UAVs) is stated but never exercised in any simulation. Either demonstrate it or remove it.

**C19.** The simulation animations are hosted on an external video platform (bilibili). Reviewers and future readers may not be able to access this, and the link is unlikely to persist. Please submit the animations as supplementary material through the IEEE portal, and ensure the paper's claims are fully supported by the figures in the manuscript itself.

**C20.** Please consolidate into Table I everything currently missing: *H*, *q*, the full LSTM configuration, the target motion model and its parameters, the obstacle-count distribution, initial-condition randomization ranges, the number of Monte Carlo trials per configuration, and the baseline parameter settings.

**C21.** Section III-D is presented as the "execution layer," but Eqs. (21)–(23) constitute gain-scheduled PD control toward a waypoint. Positioning it explicitly in those terms would help readers place the contribution — the novelty is in the scheduling law and its coupling to the vortex term, not in the control structure — and would also clarify why the stability question in M5 arises.

---

## Closing assessment

### What the paper gets right
The problem is real and correctly diagnosed. Reactive lag, assignment chattering, and APF stagnation are the three failure modes that actually break dynamic entrapment in practice, and the decision to attack them jointly — rather than publishing another single-mechanism improvement — is the right instinct and the paper's genuine contribution. The three-layer decomposition is clean, each layer is matched to the failure mode it addresses, and the interfaces between layers are well defined.

Several individual pieces are better than they need to be. The capture-point machinery of Section III-C — proportional-fairness allocation, Shoelace-based orientation normalization, and temporal smoothing — solves a problem most papers in this area do not even notice, namely that naively re-sampling a deforming contour manufactures spurious reassignment. The escape-distance metric of Eq. (32) and Table II, with its sign convention tied to convex-hull membership and its explicit treatment of the degenerate 1-UAV, 2-UAV, and collinear cases, is more informative than the formation-error metrics this literature usually reports. And the time-domain proportion analysis of Fig. 13, which separates transient from steady-state rather than averaging a signed metric across an entire run, shows real methodological care. That analysis, not the 84.33 % headline, is the most convincing evidence in the paper.

The manuscript is also well organized and readable, and the figures are generally clear. The work behind it is substantial. My concerns below are about what the evidence currently establishes, not about the quality of the engineering.

### What must change
1. **Replace the headline claim with defensible statistics.** The 84.33 % figure is a 7 cm absolute difference on a signed metric, accompanied by small regressions on the other two metrics. Report paired tests, confidence intervals, all three metrics symmetrically, and an entrapment success rate. Lead with the Table III counts — they are significant and they support you. (M1)
2. **Ablate the contributions you claim.** Only prediction is currently ablated. Add inertia-off, vortex-off, and damping-off variants, and benchmark the LSTM against constant-velocity and Kalman predictors. Given how small the measured differences are, the possibility that any short-horizon predictor would do is live and must be closed. (M3, M4)
3. **Measure safety, and fix the velocity constraint.** Report minimum inter-UAV separation, obstacle clearance, and violation counts. Correct the Δv_limit mislabel and confirm whether a speed saturation was in fact implemented — as written, Assumption 3 is not enforced by the equations. (M5, M6)
4. **Establish the delta against [36] and [39].** Reference [39] is GRN entrapment with target prediction; it is the nearest prior art and is neither compared against nor differentiated. The novelty claim does not stand until this is addressed. (M2)
5. **Match the claims to the evidence.** Remove or demonstrate the 3-D and underwater generalizations, state the communication architecture plainly in Section II rather than in the Conclusion, and either justify the ground-robot-scale parameters for an aerospace venue or re-run at UAV-realistic speeds. (M7, M8)

One further question I would genuinely like answered, offered as an opportunity rather than a demand: prediction is introduced to remove lag, and then four lag-inducing filters are stacked on top of it (γ, β, η, K_d). If the compounded lag is consuming the lead time the LSTM provides, that would explain the small measured benefit — and characterizing it would turn a weak result into an interesting one. (M9)

I would be glad to review a revised version.
