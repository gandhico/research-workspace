# P2 Claim-Artifact Audit - 2026-07-20

Active manuscript:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.tex`

Active PDF:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\paper\main.pdf`

Build status:

- `main.pdf`: 27 pages, 858119 bytes.
- `main.log`: no undefined references/citations and no overfull boxes.
- `main.blg`: `warning$ -- 0`.

## Main Claim Surface

| Claim | Manuscript location | Evidence | Status |
|---|---|---|---|
| Standalone and Nengo HyperLIF/Adaptive stepping agree exactly. | Abstract, Nengo Implementation, parity result | `07_python_vs_nengo.csv`, `07_parity_metrics.csv`, `fig:parity`, `tab:parity`, shared kernel in `src/neurons/nengo_hyperlif.py` | Paper-ready |
| Fixed-gain HyperLIF DB onset is predicted by `J_DB=(v_thresh-gamma)(1+tau G_b)=2.4`. | Abstract, formulation, FI/DB results | `03_db_analysis.csv`, `03_current_sweep.csv`, `fig:fi`, `fig:db`, `tab:sweep` | Paper-ready |
| Latched voltage at `J=4` is predicted and observed as `1.3333`. | Abstract, formulation, FI results | `03_db_analysis.csv`, `03_current_sweep.csv` | Paper-ready |
| Adaptive conductance keeps the high-drive equilibrium bounded below the gate knee under the stated sufficient condition. | Abstract, adaptive formulation, FI results | `03_db_analysis.csv`, `03_equilibria.csv`, `03_current_sweep.csv` | Paper-ready with parameter-dependent caveat |
| Exponential stepping is stable where explicit Euler can overshoot. | Integration section | `06_integration_accuracy.csv`, `06_stability.csv`, `fig:integration`, `tab:integration` | Paper-ready |
| Single-neuron reset-gate state is decodable as readiness. | Gate-state decoding and readiness sections | `05_gate_state_decoding.csv`, `05_decoding_metrics.csv`, `fig:decode`, `tab:decoding` | Paper-ready as illustrative single-neuron result |
| Static `theta_event=0.95` improves useful event availability without changing dynamics. | Readout adaptation section | `09_theta_static_event_threshold_summary.csv` and copied adaptive-threshold project evidence | Paper-ready as readout-adaptation result |
| HyperLIF covers the breadth of the Nengo suite in NengoCore after calibration. | Capability section | `13_hyperlif_nengo_capability_matrix.csv`, `fig:capability`, `tab:capability-calib`, `NENGO_CAPABILITY_FINDINGS.md` | Paper-ready with NengoCore-only scope |
| Seeded core capability preflight completes 84/84 simulations with zero failures. | Capability section | `17_capability_seed_sweep.csv`, `17_capability_seed_sweep_summary.csv`, `results/logs/17_capability_seed_sweep_preflight_20260719.log`, `tab:capability-seeded` | Paper-ready methods evidence |
| PES weakness is a firing-rate trade, not a fixed dynamics failure. | Capability trade section | `15_pes_rate_matched.csv`, `fig:capability`, `tab:capability-calib` | Paper-ready for matched-time PES channel |
| Backend portability is currently limited to NengoCore for this custom continuous-gate neuron. | Backend section | `14_backend_portability_probe.py`, `NENGO_CAPABILITY_FINDINGS.md`, `tab:backend` | Paper-ready limitation |
| Five-seed scalar NEF decoder-ablation validates low-rate state readouts. | Capability decoder-ablation section | `18_nef_decoder_state_ablation.csv`, `18_nef_decoder_state_ablation_summary.csv`, `results/logs/18_nef_decoder_state_ablation.txt`, `tab:nef-decoder-ablation` | Paper-ready as scalar NEF result |
| Gate-state residual control is a future-work bridge, not a closed-loop result. | Readiness, bridge, limitations, future work | Conceptual link to P3/P4 fused control work | Correctly limited |

## Submission Risks Still Open

| Risk | Current state | Required action |
|---|---|---|
| IEEEtran package is stale. | `paper/main_ieee.tex` is an old June draft and lacks the new Nengo capability and decoder-ablation results. | Regenerate IEEEtran source from current `paper/main.tex`. |
| Author and metadata are placeholders. | Author block is project-level, not submission-ready. | Add author names, affiliations, ORCID if desired, corresponding author, acknowledgments, funding, and data/code availability statement. |
| Table density is high. | Current article PDF is 27 pages and has several wide tables. | In IEEEtran, decide main text versus appendix/supplement placement for long tables. |
| Journal target is undecided. | TNNLS rejected the old paper; this P2 is a different implementation/NEF paper. | Pick target venue before final formatting so length and supplement policy are known. |
| Advisor approval pending. | Scientific claim surface is now organized but not advisor-approved. | Send P2 package with this audit and ask whether they prefer another decoder expansion or submission polish. |

## Readiness Decision

After this audit, P2 is at 91%.

The scientific core is strong. The remaining 9% is not mainly experiments. It is
submission mechanics: current IEEEtran conversion, table economy, metadata,
advisor copyedit, and final Overleaf package.
