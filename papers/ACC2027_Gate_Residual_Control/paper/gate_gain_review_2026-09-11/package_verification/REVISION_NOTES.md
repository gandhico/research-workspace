# Technical response to the supplied reviews

This revision preserves the frozen main performance matrix and all nine existing figures. New experiments are stored separately. Agent-generated review scores are opinions, not actual ACC decisions.

| Review point | Decision | Evidence / action |
|---|---|---|
| What does CMG add beyond PES? | Central question; accept | Gain/chi sensitivity, weaker-threshold-feedback tests, matched-input neuron ramp, paired-linear and constant-feature PES controls. Report unfavorable findings. |
| Conductance is inactive because it is tiny | Reject that explanation as general | Fresh canonical X2 Full3 has raw gates >.9 for 97.7% of unit-samples and mean conductance/leak 7.08. Readout saturation and persistent high-gate states hide membrane changes. |
| Conductance modulation equals all CMG dynamics | Correct the distinction | chi=0 retains g0 r^2 shunting, membrane integration and threshold feedback. Only the added input-dependent conductance term is removed. |
| Random-feature interpretation | Do not use | The stateful features are deterministic. Under constant activity and inactive projection, derive the exact reduced PES recursion instead. |
| Neuron-family normalization | Accept; retain explicit mathematical accounting | Existing Eq. familyscale already derives eta*S_f in normalized coordinates and the S_f^2 correction. Do not silently relabel old data as corrected. Figure caption becomes explicitly exploratory. |
| Local ISS proof certifies the experiments | Reject | Preserve constant-reference, local, continuous-time scope and the uncertified experimental beta=.5 smallness condition. Present as a sufficient robustness condition, not a new global flight theorem. |
| Noise proves true-state robustness | Reject | Preserve explicit corrupted-feedback metric disclosure. A ground-truth/noise rerun is a separate missing test, not something that prose can repair. |
| Motor lag omitted | Accept as limitation | Model/interface table already states algebraic forces, no motor/battery dynamics and historical step-response context. No synthetic motor-lag results invented. |
| Actuator-bound occupancy proves infeasibility | Reject | Occupancy is post-clipping boundary contact, not requested-wrench mismatch magnitude. |
| Results prove scale-independent control | Reject | PD gains and torque limits depend on model principal moments; normalized design partially rescales the dynamics. |
| Long disturbance run proves memory reuse | Reject causal wording | Learning/leak remain active and burst phases differ. Keep reset/frozen-decoder experiment as future work. |
| New novelty relative to PES UAV PID | Clarify, do not erase prior work | Fixed quaternion PD plus bounded torque residual and explicit allocation interface, rather than self-tuning spiking PID. |
| Abstract overburdened by caveats | Accept selectively | Lead with architecture/results; consolidate the principal scope limits into the final sentence. Keep necessary qualifications in the body. |
| Hardware is preliminary | Accept | Keep the three matched Roll pairs and their different Euler-coordinate metric; do not imply full mission validation. |
| Better baseline controllers | Partially address | New simple residual controls test the mechanism. Concurrent integral/geometric/optimization-controller experiments are not appropriated or merged without a separate audit. |

## Completed revision

71 new MuJoCo cases are complete and audited; the complete original 148-cell factorial was not run. There are eight Nengo cross-checks and 67 full-rate neural/basis archives. All canonical controller source hashes remained unchanged. Full results, negative outcomes, exact case definitions and the data freeze manifest are in `experiments/gate_gain_sweep_2026-09-11` under the project root.

The manuscript retains all nine figures and the unchanged ten-case main matrix. New Table V gives the direct-backend simple-basis controls. New Eq. (36) is the exact constant-activity decoder recursion. The neuron-family normalization equation is now Eq. (37); its mathematical correction was already present, and its old benchmark is not relabelled as a corrected experiment.

The key finding is not a new superior conductance regime. Constant-basis/PES reductions are 57.78%, 56.98%, and 18.38% in X2 Roll, X2 Full3, and CF2 Hardstep, versus canonical CMG 17.36%, 56.56%, and 18.37%. Weakening threshold feedback and shifting input bias reveals conductance sensitivity, but none of the 24 development cases improves on canonical CMG in its mission.

The abstract and conclusion now state that CMG is a tested continuous neuromorphic realization, not an experimentally necessary cause of these improvements. A compact gain-sweep summary and unfavorable development results are included. The larger plots remain in the supporting audit rather than adding new full-page figures.

## Iterative assessment, not a prediction of peer review

1. **Before the new controls:** the text was transparent, but the implied distinctive role of the CMG basis had not been directly tested. A favorable score based only on presentation would have been premature.
2. **After the mechanism audit:** technical clarity and evidential transparency improve. Conductance is not generally small; persistent gates/readout saturation and the reduced PES dynamics provide a better explanation. The simple-control results weaken CMG-specific novelty.
3. **Delivered version:** approximately **8.5/10 for clarity/reproducibility**, **4.5/10 for demonstrated CMG-specific performance novelty**, and **6.5–7/10 overall readiness for a competitive ACC review**. These are editorial judgments, not acceptance probabilities. I would not inflate the overall score simply because the manuscript has been edited again.

The unresolved contribution question is a distinctive benefit over matched-bandwidth classical dynamic residuals, not merely whether CMG/PES can beat the original PD baseline. The next comparison should match authority, teacher, effective learning bandwidth and task conditions before seeking a neuron-specific advantage.

## Page and submission status

The revised PDF compiles to **10 pages** with all existing figures retained, as requested for this advisor-review stage. It is about **3.09 MB**, so it is not upload-ready. ACC 2027's official author information limits initial regular/invited papers to **8 pages** and uploaded PDFs to **2 MB**: https://acc2027.a2c2.org/1710-2/ (checked 2026-09-11).

For the later eight-page version, first consider moving the exploratory neuron-family dashboard and its unequal-normalization discussion to supporting material, reducing duplicated tracking/neuron panels, and retaining the new simple-basis control. Do not save space by deleting assumptions or hiding the unfavorable control results. No such figure removal is performed in this revision.
