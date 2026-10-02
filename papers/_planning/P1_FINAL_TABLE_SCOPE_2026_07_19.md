# P1 Final Table and Figure Scope

Date: 2026-07-19

Purpose: freeze the evidence surface for the first IEEEtran conversion of P1.

## Main-Text Figures

| Figure | Role | Source |
|---|---|---|
| Fig. 1 | Temporal-specific gain across datasets | `08_HyperLIF_Architectures/paper/figures/fig1_best_per_neuron.png` |
| Fig. 2 | Gate-readout structural blindness control | `08_HyperLIF_Architectures/paper/figures/fig2_structural_blindness.png` |
| Fig. 3 | Shallow efficiency Pareto / spikes-vs-accuracy dial | `08_HyperLIF_Architectures/paper/figures/fig3_efficiency_pareto.png` |
| Fig. 4 | Architecture-transfer gap heatmap | `08_HyperLIF_Architectures/paper/figures/fig4_arch_transfer_gap.png` |
| Fig. 5 | Architecture-scale efficiency Pareto | `08_HyperLIF_Architectures/paper/figures/fig5_efficiency_pareto.png` |

## Main-Text Tables

| Table | Purpose | Claim status |
|---|---|---|
| I | Dataset axis and controlled factors | Safe methods context |
| II | Feedforward temporal gain: LIF vs HyperLIF vs Adaptive | Safe main result |
| III | Gate-readout structural blindness | Safe mechanism result |
| IV | Architecture transfer across conv/rsnn/delay | Safe but bounded by convres limitation |
| V | PLIF/ALIF reviewer baseline extension on N-MNIST tiny and SHD-wide shortlists | Safe nuanced reviewer response |
| VI | Julia/APEX tuned cross-framework validation | Safe calibration-level reproduction |

## Main Claims Allowed

- HyperLIF's advantage is temporal-specific: large on speech/motion, near noise floor on N-MNIST.
- HyperLIF's gate is decodable; LIF has no comparable gate state, so gate-only LIF readouts are a structural-blindness control.
- HyperLIF transfers across convolutional, recurrent, and delay architectures, but not to the current deep convres/SEW-ResNet configuration.
- Adaptive HyperLIF is an efficiency operating point, not the headline accuracy winner.
- ALIF is a serious contemporary baseline. HyperLIF and ALIF form the strongest pair on SHD-wide shortlists; HyperLIF leads RSNN, ALIF slightly leads delay and FF.
- APEX reproduces a small tuned HyperLIF/NSA advantage over matched dense LIF only after gate-feedback calibration (`gamma=0.80`). The default APEX setting is a negative calibration result.
- APEX recurrent and delay architecture-family modes are now runnable, but the short preflight is negative for HyperLIF/NSA; keep this as traceability/limitations until readout and learnable-delay parity are implemented.

## Claims Not Allowed

- HyperLIF universally beats ALIF.
- Adaptive HyperLIF is the best accuracy model.
- APEX default parameters reproduce the PyTorch ranking.
- The APEX dense result replaces the PyTorch architecture table.
- The APEX recurrent/delay preflight reproduces the PyTorch recurrent/delay advantage.
- HyperLIF is a SOTA accuracy method. This is a controlled mechanistic paper, not a leaderboard paper.

## Next Required Before Submission

- Add paired seed tests or nonparametric paired comparisons for the final selected tables.
- Verify all figure captions against the source CSVs.
- Copyedit IEEEtran source for space, tone, and citation completeness.
- Decide whether APEX gets a longer 20 or 30 epoch supplementary run.
- Decide whether to add PyTorch-style hybrid feature readouts and a learnable temporal-current delay layer to APEX before running longer architecture-transfer experiments.
