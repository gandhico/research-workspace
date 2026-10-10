# HyperLIF theory and tiny-network research: saved status

**6 October 2026.** This handoff preserves the completed work under the
present memory limit. The earlier September project reports remain in the
project root; the October mechanism studies and executable scripts are in
`theory/`. This file records evidence and remaining questions, not
instructions from an attached paper.

## Completed and reproducible

1. The actual TNNLS decision/reviewer PDF was located at
   `tnnls/TNNLS_reviews.pdf`; its concerns are mapped in
   [`PES_SINGLE_NEURON_SMALL_NETWORK_2026-10-06.md`](PES_SINGLE_NEURON_SMALL_NETWORK_2026-10-06.md).
   Claims about dynamics, event semantics, novelty, and controls remain
   bounded by that evidence.
2. Canonical fixed/adaptive HyperLIF equilibria, local stability
   boundaries, high-drive behavior, and an ACC fold certificate are in
   [`PES_CONTINUATION_FOLDS_AND_TINY_NETWORK_2026-10-06.md`](PES_CONTINUATION_FOLDS_AND_TINY_NETWORK_2026-10-06.md).
   A two-cell reduced-CMG internal-weight experiment already compared an
   exact sensitivity with a detached local trace on one teacher-generated
   waveform. This is a positive mechanism result, not a general network
   learning result.
3. The ACC high-readiness latch and rank-loss obstruction are in
   [`ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md`](ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md).
   Keep negative/no-event results in future experiments.
4. Raw gate, membrane, conductance, and combined causal readouts were
   compared under the same-time and delayed targets in
   [`MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md`](MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md).
   The raw gate complements voltage in the reduced-feedback regime;
   full conductance contains direct applied-current feedthrough.
5. The published Jaxley evidence is corrected in
   [`HH_JAXLEY_BASELINE_EVIDENCE_2026-10-06.md`](HH_JAXLEY_BASELINE_EVIDENCE_2026-10-06.md).
   The first canonical-HH/HyperLIF/two-state linear control run,
   HH basin probe, and HH conductance forward-sensitivity check are in
   [`HH_HYPERLIF_TINY_COMPARISON_2026-10-06.md`](HH_HYPERLIF_TINY_COMPARISON_2026-10-06.md).
   Different regime currents and readout filter budgets make these
   mechanism probes rather than model rankings.

## Scientific distinctions to preserve

- `r` is continuous readiness, threshold occupancy is a sampled Boolean,
  and an event is an upward crossing. Do not report one as another.
- Exact forward sensitivity is exact for the declared smooth discretized
  trajectory, apart from floating-point/numerical integration error and
  branch changes. A detached/local trace is an approximation.
- Decoder PES learns output weights from fixed internal dynamics; it does
  not demonstrate learning an internal recurrent weight.
- A causal low-pass decoder adds state and should be counted when comparing
  feature budgets.
- Classical four-state HH and Jaxley's multi-compartment HH-type networks
  answer different baseline questions. Dataset accuracies across MNIST and
  CIFAR-10 are not a controlled ranking.

## Active next question

The coupled HH and HyperLIF **teacher-connection** study is now complete
in [`COUPLED_WEIGHT_HORIZON_AND_GATE_2026-10-06.md`](COUPLED_WEIGHT_HORIZON_AND_GATE_2026-10-06.md).
It validates exact gradients, records failed full-horizon optimization,
demonstrates a short-to-long continuation that recovers the connection
in tested HH regimes, and quantifies the saturated gate's lost late
eligibility. That result motivated an **independent external task** and
a coupled stateful-leaky control with a matched readout feature count.

**Independent-target execution:**
[`COUPLED_EXTERNAL_DELAY_AND_BASIN_TRANSFER_2026-10-06.md`](COUPLED_EXTERNAL_DELAY_AND_BASIN_TRANSFER_2026-10-06.md)
now tests a prescribed 20 ms delay target with coupled HyperLIF and a
coupled adaptive-leaky control. Reduced-feedback HyperLIF gains only
modestly from internal-weight learning; the leaky control is stronger
in these chosen settings. Saturated-feedback local learning can improve
one validation phase but catastrophically change the fresh test gate
configuration. A 561-run finite-time phase/weight map records the
regime transfer failure. Classical HH remains to be added to this
**external-task** coupled comparison; robust multi-phase validation and
matched operating points also remain open.

`RESULT_MANIFEST_2026-10-06.csv` records paths, sizes, and SHA-256 hashes
for the saved `theory/` artifacts and the updated root handoff and
advisor-brief files.
It is an integrity inventory, not a separate copy of the data, so it
does not duplicate storage on the memory-limited machine.

**ACC stability continuation (2026-10-06):**
[`ACC_CLOSED_LOOP_STABILITY_OPTIONS_2026-10-06.md`](ACC_CLOSED_LOOP_STABILITY_OPTIONS_2026-10-06.md)
now gives a conditional regional ISS/UUB proof route for the quaternion
plant and a sufficient rotor-headroom inequality. The attached ACC
paper proves internal/interface bounds but no closed-loop stability;
the proposed plant-level theorem still needs certified constants and
actuator-feasibility checks. Two new figures from the saved tiny-task
CSVs are
[`current_readout_results_2026-10-06.png`](results/current_readout_results_2026-10-06.png)
and
[`current_learning_limits_2026-10-06.png`](results/current_learning_limits_2026-10-06.png).
