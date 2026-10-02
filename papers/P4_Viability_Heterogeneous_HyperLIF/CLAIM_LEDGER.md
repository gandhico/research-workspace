# Claim ledger

## Safe

- The P4 Julia package constructs multiple HyperLIF populations from one canonical P1 equation.
- The current code distinguishes upward crossings from threshold occupancy.
- Viability-box geometry, risk routing, heterogeneous gradients, slow threshold homeostasis,
  plasticity gating, and CBF halfspace projection have executable tests.
- A label-free SHD training-input calibration produced four different initial activity rates.
- The exact local SHD cache has the recorded SHA-256 and dimensions in `PROGRESS_REGISTER.md`.

## Qualified

- The proposed cross-level architecture appears unreported in the primary sources reviewed here.
  Say “to our knowledge” and require a formal database search before submission.
- The synthetic high-reactivity candidate avoided block only over the screened constant-current grid.
- The tiny SHD runs demonstrate an end-to-end pipeline, not classification quality or homeostatic
  benefit.
- The reference safety shield certifies only its returned linear inequalities to tolerance; it does
  not establish a real robot's global safety.

## Exploratory

- Low-event continuous states may complement higher-event evidence.
- Population-specific homeostasis may preserve functional heterogeneity during task learning.
- Viability-dependent routing may reduce nominal events and disturbance recovery time.
- The benefit may be larger on temporally rich audio/gesture data than on N-MNIST.

## Unsafe

- “First heterogeneous SNN,” “first mixed spiking/non-spiking network,” “first homeostatic robot,”
  or “first safe neuromorphic controller.”
- “High-spiking population” based only on threshold, gain, or occupancy.
- Any claim that the three-epoch pilot improves accuracy or proves homeostasis.
- Hardware energy savings inferred from crossings, occupancy, or wall time.
- Forward-invariance or viability-kernel claims without the required system and solver assumptions.
- Exact image-dataset replication until the original cache binary and hash are recovered.
- HyperLIF priority based solely on absence of a web-search result.


## Falsified on 2026-09-10 (second session)

- "A label-free SHD training-input calibration produced four different initial activity
  rates." The four rates differ, but they do not correspond to four firing regimes: at those
  gains the regular and burst populations are saturated, and sweeping the gain by a further
  16× barely moves their crossing rate. See `reachable_rate_envelope.csv`.
- "The synthetic high-reactivity candidate avoided block over the screened constant-current
  grid." True as stated, but it does not transfer: the same parameters on SHD input reach
  roughly one crossing per neuron per sequence regardless of gain.
- "Paired three-epoch pilots with and without homeostasis ... final training rate-band penalty
  3.21e-5 versus 3.43e-5." The two runs are byte-identical on the test split; the compared
  penalties come from checkpoints that were never selected. No comparison was made.

## Safe (added)

- On `shd_wide_T20`, every regime's upward-crossing rate saturates near one crossing per
  neuron per 20-step sequence as input gain grows, while occupancy keeps rising.
- Under synthetic constant current at the same 20-step horizon the burst regime reaches 8
  crossings per neuron, so the horizon does not explain the saturation.
- At a shared input gain of 1.4 the four regimes measure 0.0024 / 0.0057 / 0.0116 / 0.0221
  upcrossings per neuron-step in the intended order with burst occupancy 0.037.
- The heterogeneous, ensemble, and homogeneous families hold total hidden state equal and
  effective parameter counts within 63 of each other.

## Unsafe (added)

- Any statement that the four populations occupy distinct firing regimes on SHD under the
  per-regime gain profile `shd_calibrated_regimes`.
- Any energy or event-communication claim while the readout is `:hybrid_vr`; upward crossings
  do not enter the readout or the loss, so event count is a diagnostic only.
- Any homeostasis comparison that does not report `homeostasis_effective` as true.
