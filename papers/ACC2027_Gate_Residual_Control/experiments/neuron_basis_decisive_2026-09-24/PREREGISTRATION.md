# Preregistered decision rules

Date: 2026-09-24. These rules were written before inspecting the new full-run
results.

## Fixed interface

- Baseline: the paper's final `rho=3` quaternion PD plus desired-rate
  feedforward controller.
- Missions: Roll, Full3, Hard45, Hardstep, and Yaw360, 45 s each.
- Plants: X2 at model authority; CF2 at the disclosed 1.5x rotor design.
- Residual authority: beta=0.5 (X2), beta=0.2 (CF2).
- Teacher: k_error=8, k_rate=0; direct-equivalent eta=8e-4.
- Six signed channels, W0=[I3,-I3], identical decoder leak/projection.
- Conventional-family Nengo PES is normalized with
  eta_N=eta*N/(dt*S^2), so the normalized decoder update exactly matches CMG.
  The archived eta*N/(dt*S) setting is not used for confirmatory conclusions.
- Same saturation-opposition output gate for every residual arm.
- Primary metric: true-state mean quaternion angle error.
- Secondary mechanism metrics: normalized residual RMS, activity occupancy,
  decoder rail occupancy, output-gate duty, and allocation saturation.

## Questions and decisions

1. **Strict family result.** A family is useful without retuning if its
   five-mission geometric-mean error is below the classical baseline and it
   does not catastrophically degrade Roll or Yaw360 (>100% error increase).
2. **CMG specificity.** CMG has evidence of a dynamics-specific advantage only
   if it outperforms both no-neuron controls in tracking/effort and the gap is
   not explained solely by activity occupancy.
3. **Operating-point hypothesis.** For LIF, ALIF, and LIFRate, vary only
   current bias/gain and feature-filter time constant. Bias+gain remains 2.0,
   preserving the archived maximum-current calibration. For Izhikevich, the
   lower-bias candidates test whether tonic spiking caused the low-error floor.
4. **Selection without mission leakage.** Select one setting per family using
   a 15 s X2 Roll and Hard45 screen only, then confirm the selected setting on
   the complete 45 s development missions. Minimize

       geometric_mean(error / baseline_error) * (1 + mean residual_NRMS).

   Reject a candidate if either development mission exceeds 10x its baseline.
   Candidate ratios use separately executed 15 s classical baselines, not the
   45 s confirmatory summaries.
   Then freeze it and validate on X2 Full3/Hardstep/Yaw360 and all five CF2
   missions. No mission-specific retuning is allowed.
5. **Controller expansion gate.** Do not start PID/MPC/NMPC/Backstepping/SMC
   replication until this study identifies whether the transferable object is
   the CMG dynamics, a persistent continuous basis, or PES residual learning
   independent of the basis.

No-neuron controls are analytic mechanism ablations and must not be described
as neuromorphic controllers.
