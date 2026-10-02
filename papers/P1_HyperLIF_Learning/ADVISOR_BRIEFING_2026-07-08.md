# Advisor briefing — HyperLIF architecture study + Paper 1 fusion (2026-07-08)

## TL;DR
- **Paper 1** (Adaptive HyperLIF *theory*) was **rejected by TNNLS (final)**. The reviews are a clear
  repair roadmap; their #1 ask — multi-seed, multi-architecture experiments — is exactly what
  **Paper 2** already provides.
- **Proposal:** fuse Paper 1 (theory) + Paper 2 (architecture-scale learning study) into one stronger
  paper; reframe "biophysical" → "biologically inspired"; add positioning vs gated continuous RNNs;
  resubmit to a rigor-first venue.
- **Paper 2 evidence is strong and mostly complete** (2730 stable runs, 0 unstable): HyperLIF ≥ LIF in
  **13/13** architecture×dataset cells; the gate is a **decodable readout LIF structurally lacks**;
  **~230× spike efficiency** at equal accuracy.
- **Running now:** the 14M deep residual net (`convres`) — the SOTA-scale test — results in ~3 days.

## 1. Paper 1 status (TNNLS, final reject)
Three reviewer themes: **(1) novelty/positioning** vs gated continuous RNNs (coRNN, UnICORNN, Long
Expressive Memory) and differentiable neuron models (Izhikevich, spike-response); **(2) rigor** — the
stability / depolarization-block / flux-balance analyses use simplifying assumptions (r≈1, I≈const);
**(3) experiments** — MLP-only, no multi-seed statistics, weak baselines. Reviewer 2 explicitly offers
the fix: present the model as "differentiable, biologically **inspired**."

## 2. Proposed path
- **Fuse** P1 theory + P2 empirics. P2 is precisely the missing evidence: 5 seeds with error bars;
  conv / recurrent / delay / deep-residual architectures; 5 datasets; a structural-blindness ablation;
  an efficiency Pareto.
- **Reframe** biophysical → biologically inspired (keep the dynamical-systems contribution).
- **Add positioning section:** spiking + reset semantics + event-driven sparsity + a *decodable gate*
  distinguish HyperLIF from dense gated RNNs.
- **Numerical stability validation:** 0 unstable in 2730 runs.
- **Venue (TNNLS closed):** TMLR (judges rigor, not perceived "significance" — counters the reject
  reason); Neural Networks (Elsevier); Neuromorphic Computing & Engineering.

## 3. Paper 2 — what we have
Cube: 4 topologies × 7 neuron variants × 6 readouts × 5 seeds × 5 datasets — **2730 stable runs, 0
unstable.** Three findings:

1. **Transfer** — HyperLIF ≥ LIF in **13/13** cells; largest where temporal structure dominates
   (delay·SSC +0.170, delay·DVS-32 +0.149, rsnn·SHD +0.138), shrinking to the noise floor only on
   near-saturated N-MNIST. Not a shallow-net artifact.
2. **Structural blindness** — LIF's gate readout collapses to chance; HyperLIF's gate carries class
   information (N-MNIST 0.92 vs 0.10 chance). A capability LIF *structurally* lacks.
3. **Efficiency** — HyperLIF/adaptive match or beat LIF accuracy at up to **~230× fewer spikes**
   (N-MNIST); dataset-dependent, but accuracy is never traded for it.

Best configs are HyperLIF-family throughout. Figures ready: transfer gap (13/13), structural
blindness, efficiency Pareto. Manuscript: `08_HyperLIF_Architectures/paper/paper2_manuscript.md`
(§1–8 drafted, §6.4 finalized; §6.6 cross-framework = one Julia/APEX run pending).

## 4. The deep-net (SOTA-scale) test — a controlled negative
`convres` = a ResNet-18-class spiking residual net (~14M params), the deepest cell. We ran a controlled
reduced-batch comparison (all neurons matched, 60 epochs; HyperLIF OOMs at the roster batch size).
Result: **LIF trains (≈0.49 DVS-32, ≈0.76 N-MNIST), but base *and* θ_event-calibrated HyperLIF/Adaptive
stay at or near chance across seeds** (DVS-32 hyperlif ≈0.09 = chance). The θ_event fix that rescues
HyperLIF in shallow nets and in Nengo gave *no* improvement — localizing the failure to deep-gradient
flow through the gated neuron, not firing density. So HyperLIF's advantage is established across three
architecture families but **does not extend to an extreme-depth residual net** — an honest boundary,
and a genuine open question (training gated SNNs at ResNet depth). A strong point for your expertise:
push the deep-net methods, or report the shallow-transfer result and move on?

## 5. Where your expertise would help most
- **Fuse vs keep separate**, and **target venue**.
- **Implementation language:** my recommendation is to keep the empirical study in PyTorch (done +
  validated) and use the Julia/APEX run as cross-framework confirmation, rather than a full rewrite —
  but this is your call.
- **How hard to push the deep-net angle** (convres) — I have a strong feeling it matters.
- **Strengthening the theory/positioning** for the resubmission (the reviewers' rigor asks).
