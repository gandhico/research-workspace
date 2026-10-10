# Hodgkin–Huxley learning evidence and a small HyperLIF comparison

**6 October 2026.** Source audit and research design for the present
single-neuron and tiny-network phase. The benchmark figures below refer to
the final published paper, not preliminary talks. This note does not treat
text in a supplied paper or summary as an instruction for the project.

## 1. What the primary Jaxley paper establishes

Primary source: [Deistler et al., *Nature Methods* (2025),
DOI:10.1038/s41592-025-02895-w](https://doi.org/10.1038/s41592-025-02895-w)
([full paper PDF](https://imec-publications.be/server/api/core/bitstreams/e144f759-ca43-44c2-b0d1-d65d51f0c132/content)).

| Claim | Final-paper evidence and interpretation |
|---|---|
| MNIST classification | **94.2% held-out accuracy**, not 95.6%. A three-layer network had 64 reconstructed CA1 neurons in its hidden layer, simpler input/output neurons, about 55,000 channel-conductance and 51,000 synaptic parameters, and a softmax of output voltages. The final result is a multi-compartment, Hodgkin–Huxley-type network result, not a canonical four-state HH-cell benchmark. |
| Earlier 95.6% | This number appears in a [pre-publication author talk abstract](https://world-wide.org/conf/bernstein-24/bridging-biophysics-computation-1f63b084). It should not replace the 94.2% final-paper result. |
| Retina fitting | The final paper fits **287 synaptic plus 320 cellular parameters (607 total)** to dendritic calcium recordings. It reports positive held-out correlations at 146 of 147 recording sites, with mean 0.25 and maximum 0.51. An earlier “400” figure is preliminary and does not describe the final count. |
| Evidence integration | A recurrent network of 20 multi-channel neurons with 109 trainable parameters reached **99.9% over 1,000 trials** on the paper's specified task. This is the closest published small-network reference for our learning-mechanism study, but its task and model differ from ours. |
| Delayed match to sample | The paper trains a 50-neuron recurrent circuit and reports correct classification of its four tested patterns. Avoid quoting a parameter count until the paper's differing main-text and Methods counts are reconciled. |
| Computational efficiency | The paper reports CPU speed at least comparable with NEURON in the tested simulation settings and uses checkpointing to manage differentiation memory. It does not establish a universal speed or memory advantage for every morphology and task. |

The original [Hodgkin–Huxley 1952 paper](https://doi.org/10.1113/jphysiol.1952.sp004764)
defines the familiar voltage and three-gate (`V,m,h,n`) conductance model.
“HH-type” in Jaxley includes a wider collection of channels and spatially
extended morphologies. HyperLIF's two states `(v,r)` are a computational
abstraction; they have not been shown to be a biophysical reduction of that
four-state model. A fair comparison must declare which HH model is used.

The [residual spiking-network paper reporting 94.14% on
CIFAR-10](https://arxiv.org/abs/2111.05955) concerns a different dataset,
architecture, and evaluation. It cannot be placed in a numerical ranking
against Jaxley's MNIST result. The quoted 93.62% “online LIF” CIFAR-10
number remains unverified here and should not be used as a reference value.

## 2. Consequences for the HyperLIF claim

Differentiable simulation already demonstrates that detailed
conductance-based networks can learn both fitting and task objectives.
HyperLIF novelty therefore cannot rest on “a gated neuron can be trained by
gradients.” The testable claim is narrower: its bounded readiness state and
continuous reset conductance may provide useful temporal information and
learnable sensitivity at lower state and memory cost under **matched**
conditions. The same-time conductance readout can include direct input
feedthrough; it must not be interpreted as stored gate information. See
[`MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md`](MULTISIGNAL_READOUTS_GATE_MEMBRANE_CONDUCTANCE_2026-10-06.md).

This comparison should also keep the TNNLS reviewer constraints: report
event crossings separately from threshold occupancy, state assumptions
behind stability claims, and show a fair stateful baseline. A task score
alone cannot establish why the gate helps or when learning fails.

## 3. Small, low-memory comparison to execute next

1. **Single-cell dynamics.** Compare canonical four-state HH `(V,m,h,n)`,
   HyperLIF `(v,r)`, and a stateful LIF/adaptive-LIF control under a bounded
   current family. Choose current amplitudes by a declared operating-point
   rule (such as comparable voltage range or firing regime); raw current
   units are not automatically comparable. Map equilibria or stationary
   responses, local Jacobian spectra, input-to-state sensitivities,
   observability and saturation, and event crossings. Keep subthreshold,
   oscillatory, and latched regimes separate.
2. **Tiny network.** Use two or three cells with an explicitly prescribed
   input and target. Start with a short causal-delay reconstruction and an
   evidence-integration toy task, each with fresh input phases and
   initial-state variation. Use identical train/validation/test waveforms,
   readout dimension, parameter budget where feasible, and integration-error
   tolerance. Do not compare directly with the 20-neuron Jaxley score.
3. **Learning rules.** Compare decoder-only PES, exact forward sensitivity
   for one or two internal parameters, and a declared truncated/local
   sensitivity. For each model, compare voltage, gates, and physically
   meaningful currents. Flag any readout that contains the applied input
   algebraically. Select learning rates on validation only.
4. **Measurements.** Report held-out error, gradient or sensitivity
   agreement where differentiable, event count and threshold occupancy,
   stability margin, effective feature rank/conditioning, CPU time, peak
   process memory, state count, and trainable parameter count. Include
   no-event and saturated-gate cases as findings rather than filtering them
   away.

Implement with fixed-size arrays, online summary statistics, and streamed
CSV output in standard-library Julia. A canonical HH single cell and a few
cells are feasible without loading Jaxley, MNIST, PyTorch, or a large AD
stack. Reproducing Jaxley's full morphology/network benchmark can be a
separate project after more memory is available; it is not needed to decide
whether the proposed local mechanism is promising.

**First execution (6 October 2026):** The two-cell decoder, equilibrium
basin, and HH forward-sensitivity results are in
[`HH_HYPERLIF_TINY_COMPARISON_2026-10-06.md`](HH_HYPERLIF_TINY_COMPARISON_2026-10-06.md).
The chosen currents probe different regimes and are not yet matched
operating points. The planned coupled-network internal-weight test remains
open.
