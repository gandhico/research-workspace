# Advisor briefing — Friday, 9 October 2026

**Working title:** *When can a gated HyperLIF cell learn? Single-neuron
dynamics, tiny-network sensitivity, and a gate-basin failure.*

**One-sentence conclusion:** The HyperLIF gate can add useful temporal
information while it moves, but saturated gate/readout regimes lose
learning sensitivity; a short-to-long horizon recovers a teacher
connection in tested HH/HyperLIF pairs, whereas an independent delayed
target exposes a phase-dependent basin transfer failure and a strong
two-state leaky control.

## What to tell the advisors first

1. **This is a mechanism and mathematics study.** It uses single cells
   and coupled pairs, small deterministic signals, and Julia standard
   libraries. It is not a new recognition benchmark or a claim of
   biophysical equivalence to Hodgkin–Huxley (HH).
2. **A real mathematical obstruction is now established.** For the ACC
   CMG parameter family, a high-readiness, no-event rectangle is forward
   invariant under bounded input. In that region the clipped gate
   activity is constant and decoder PES loses feature rank. See
   [`theory/ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md`](theory/ACC_ABSORBING_LATCH_AND_PES_IDENTIFIABILITY_2026-10-06.md).
3. **The gate is useful under the right operating condition.** In the
   reduced-feedback two-cell delay study, voltage plus raw gate lowers
   held-out 20 ms delay RMSE from `0.05290` (voltage) to `0.03673`.
   Full conductance is a confounded readout because it contains the
   applied input algebraically. See
   [`theory/MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md`](theory/MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md).
4. **Learning an internal connection is possible, but optimization
   depends on horizon and regime.** In a one-weight, teacher-generated
   HH pair, a one-second exact gradient points away from the positive
   teacher weight in the tonic regime (`+3.64193` at `θ=0`), whereas
   its 20 ms gradient points toward it (`−0.20683`). An 18-update
   short-to-long curriculum recovers `θ*=0.7` on fresh phases, while
   an 18-update full-horizon schedule does not. Exact sensitivities
   were checked against finite differences. Four teacher weights
   `0.3,0.5,0.7,0.9` also recovered with the fixed curriculum gain in
   this narrow realizable family. See
   [`theory/COUPLED_WEIGHT_HORIZON_AND_GATE_2026-10-06.md`](theory/COUPLED_WEIGHT_HORIZON_AND_GATE_2026-10-06.md).
5. **An external target gives a necessary negative result.** With a
   prescribed 20 ms delayed-input target and a refitted linear readout,
   reduced-feedback coupled HyperLIF improves modestly (`0.03321` to
   `0.03221` test RMSE with voltage+gate). The continuous two-state
   leaky control reaches `0.007634` in its chosen operating setting.
   In saturated feedback, a local connection update improves the
   single validation phase but worsens test from `0.09067` to
   `0.46749` (voltage+gate) when the fresh input switches the final
   gate configuration. This is a reason to study robust basin-aware
   validation, not a positive benchmark claim. See
   [`theory/COUPLED_EXTERNAL_DELAY_AND_BASIN_TRANSFER_2026-10-06.md`](theory/COUPLED_EXTERNAL_DELAY_AND_BASIN_TRANSFER_2026-10-06.md).

## Suggested 10–12 minute presentation

| Slide | Main visual or equation | Spoken point |
|---|---|---|
| 1. Question and scope | `x=(v,r)`, one or two cells, decoder PES versus internal sensitivity | “We are asking **when** this gate supports learning, before scaling to recognition.” |
| 2. Single-neuron mathematics | Exact equilibrium equation `H(r;I)=0`, Jacobian `J`, and ACC latch invariant set | Separate proved bounded/invariant/local claims from sampled trajectories. The earlier `r≈1` argument was insufficient. |
| 3. Readout information | 20 ms delayed-target bars for `v`, `r`, `v+r`, state-only and full conductance | Raw gate complements voltage at reduced feedback; direct input in full conductance must be controlled. |
| 4. Internal-weight learning | Two-cell HH diagram; gradient sign versus horizon; full versus curriculum table | Exact local gradient can point away from the teacher under long spike-phase mismatch. Short horizons supply a continuation path. This is teacher recovery. |
| 5. Independent-task control | Fixed versus learned connection table for `γ=0`, `γ=2`, and adaptive leaky | External delay learning is modest for `γ=0`; the leaky control is strong. No HyperLIF superiority claim. |
| 6. Gate-basin transfer | [Finite-time phase/weight map](theory/results/hyper_phase_basin_map_2026-10-06.png) | A validation-selected `γ=2` weight changes the gate pattern on test; event counts remain zero. The failure is visible in continuous state, not spike count. |
| 7. Conclusion and decisions | Covered/open checklist below | Ask for agreement on the next theoretical claim and the next controlled tiny experiment. |

**Backup slides:** exact TNNLS reviewer-concern map; canonical HH
equilibrium/initial-basin evidence; finite-difference gradient checks;
step-halving; the earlier PyTorch/Julia classification evidence and its
event-versus-occupancy correction. Do not crowd these onto main slides.

## Evidence checklist for the meeting

### Covered, with scope

- [x] Actual TNNLS decision and reviewer letter located; the concerns
  are mapped in [`theory/PES_SINGLE_NEURON_SMALL_NETWORK_2026-10-06.md`](theory/PES_SINGLE_NEURON_SMALL_NETWORK_2026-10-06.md).
  The letter rejected that manuscript; this is a **new research line**,
  not a claimed completed revision.
- [x] Exact scalar equilibrium reduction and coupled Jacobian for the
  CMG/HyperLIF cell; a local ACC fold certificate; canonical fixed and
  adaptive **local linear** stability crossings. These are not global
  stability or full Hopf-cycle proofs.
- [x] ACC absorbing high-gate, no-event rectangle and resulting clipped
  readout rank loss under stated bounded-input assumptions.
- [x] Clear separation of gate state, threshold occupancy, upward
  crossings, and interpolated event-time sensitivity. Historical
  PyTorch `spk` totals were occupancy, not physical event counts.
- [x] PES decoder condition and limits: fixed-feature contraction,
  projection inequality, feature Gram/representation floor, and
  changing-feature disturbance terms.
- [x] Gate, voltage, conductance, derivative, and combined readouts on
  same-time/delayed tiny tasks, including the direct-current confound.
- [x] Canonical four-state HH subthreshold/spiking/basin probes and
  constant-memory sodium-conductance forward sensitivity, with
  finite-difference and integration-step checks.
- [x] One coupled internal connection in HH and HyperLIF, exact versus
  detached local eligibility, full versus short-to-long training, and
  a narrow teacher-weight sweep.
- [x] Independent delayed-input task for coupled HyperLIF and a
  continuous two-state leaky control; train/validation/test phases;
  failed `γ=2` transfer and its finite-time gate-phase map.
- [x] Scripts, raw CSVs, notes, and figure saved with an integrity
  manifest. Runs used small process memory rather than the heavy AD
  stack. See [`theory/RESEARCH_STATUS_AND_NEXT_2026-10-06.md`](theory/RESEARCH_STATUS_AND_NEXT_2026-10-06.md).

### Open before a journal-level claim

- [ ] **Operating-point fairness:** calibrate HH, HyperLIF, and
  stateful LIF/ALIF under the same input, output, parameter/readout
  budget, state/filter count, integration accuracy, and optimization
  budget. The current currents were selected to probe regimes.
- [ ] **Robust generalization:** fix a multi-phase or multiple-waveform
  validation protocol *before* examining a new held-out collection;
  repeat across initial states and seeds. The phase map is post-test
  diagnostic evidence, not an independent confirmation.
- [ ] **Coupled HH external target:** run the same delayed-input task
  for a coupled HH pair with a matched feature budget.
- [ ] **Saturated-gate remedy:** compare operating-point restriction,
  robust multi-basin training, gate/voltage readout choice, and
  horizon continuation without selecting on the test phase.
- [ ] **Mathematical extension:** state and prove a time-varying-input
  bound or basin-avoidance condition; continue the fold/Hopf
  nondegeneracy analysis as needed. The current phase map is numerical.
- [ ] **Biological validation:** membrane/channel fitting is required
  before biological realism claims. Hardware measurements are required
  before energy claims.
- [ ] **Scaling:** revisit classification only after the tiny mechanism
  and matched controls are stable; do not use prior architecture
  accuracies as proof of this learning method.

## Practical steps before Friday

- [ ] Freeze the three headline numbers and their exact labels:
  reduced-feedback `v+r` delay RMSE `0.03673`; tonic HH gradient
  `−0.20683` at 20 ms versus `+3.64193` at 1 s; saturated-feedback
  external-task validation improvement but test deterioration
  `0.09067→0.46749`. Keep the full CSVs in backup.
- [ ] Put three visuals into the talk: the existing canonical
  equilibrium/stability figure, the compact gate-readout comparison,
  and the phase/weight gate-state map. Use the HH horizon result as a
  small table rather than a dense training log.
- [ ] Add an “assumptions and claim level” line to each result slide:
  proved under stated assumptions, numerically checked, or proposed.
- [ ] Rehearse once for 10–12 minutes; move detailed HH rates,
  finite-difference residuals, previous classification tables, and
  all reviewer wording to backup slides.
- [ ] Keep any experiment performed after this briefing out of the
  headline until its validation/test protocol is declared and checked.

**After the meeting, priority order:** (1) predeclare a multi-phase
external-task validation and a new held-out set; (2) add coupled HH and
matched stateful LIF/ALIF operating points; (3) test a robust
basin-aware objective and a short-horizon rule on that external task;
(4) extend the time-varying stability and basin analysis; (5) only then
consider larger tasks and biological fitting.

## Questions to put to the advisors

1. Is the strongest paper contribution the **conditional learnability
   theorem and basin failure**, or should the primary target be a
   robust local internal-weight rule? This determines the next proof.
2. Which small external task and matched baseline would be convincing
   *before* recognition experiments: delayed reconstruction, pulse
   evidence integration, or both?
3. Should `γ=2` be treated as a regime to repair through robust
   training, or as a parameter region to exclude under an explicit
   operating-condition theorem?
4. What level of biological claim is intended? The present work
   supports a **biologically inspired computational gate**, not a
   validated reduction of HH or a fitted neuron model.

## Presentation discipline

- Say **“local linear stability boundary”**, **“numerically observed
  sustained firing”**, and **“finite-time gate-state map”** where those
  are the actual results.
- Say **“normalized PES-style eligibility”** for internal-weight
  learning; the ACC paper's PES itself changes decoder coefficients.
- Call near-zero teacher-task error **one-parameter realizable recovery**.
  Lead the final conclusion with the independent-target negative and
  modest-positive results.
- Show the leaky control and all no-event findings. Do not assert
  superior accuracy, biological equivalence, spike or energy savings,
  global stability, or a solved reviewer objection.
- For a mathematical backup slide on gate information, use
  `theory/GATE_OBSERVABILITY_DECODER_GRAM_BOUNDS_2026-10-06.md`:
  finite-horizon raw-gate observability loses a uniform margin as the
  sigmoid slope vanishes, while a nearly constant gate makes the
  bias/gate PES decoder direction nearly unidentifiable. This is an
  analytic limitation, separate from the measured readout RMSE.
