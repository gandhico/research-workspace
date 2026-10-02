# Figure and Table Map

Date: 2026-07-19

## Figures

| Label | File | Manuscript role | Source/provenance |
|---|---|---|---|
| `fig:temporal-gain` | `figures/fig1_best_per_neuron.png` | Feedforward temporal gain | P1 architecture paper figures |
| `fig:gate-state` | `figures/fig2_structural_blindness.png` | Gate-readout structural blindness | P1 architecture paper figures |
| `fig:efficiency-shallow` | `figures/fig3_efficiency_pareto.png` | Shallow spikes-vs-accuracy dial | P1 architecture paper figures |
| `fig:architecture-gap` | `figures/fig4_arch_transfer_gap.png` | Architecture transfer gap | P1 architecture paper figures |
| `fig:efficiency-arch` | `figures/fig5_efficiency_pareto.png` | Architecture-scale efficiency | P1 architecture paper figures |

## Tables

| Label | Data source | Notes |
|---|---|---|
| `tab:datasets` | Manuscript design ledger | Methods context |
| `tab:ff-temporal` | `results/final_stats/p1_final_stats_summary_20260719.csv`, `07_AdHyperLIF_Triage/results/hpc_559182/hpc_export/_registry.csv` | Main temporal-specific result; mean plus sample std over five seeds; selected rows had zero failures |
| `tab:gate-readout` | `paper/paper2_manuscript.md`, Fig. 2 aggregate | Mechanism / structural-blindness control |
| `tab:arch-transfer` | `results/final_stats/p1_final_stats_summary_20260719.csv`, `07_AdHyperLIF_Triage/results/roster60/_registry.csv` | Main architecture-transfer result; mean plus sample std over five seeds; selected rows had zero failures |
| `tab:baseline-shortlist` | `results/final_stats/p1_final_stats_summary_20260719.csv`, `P1_FF_NMNIST_TINY_PREFLIGHT_SUMMARY.md`, `P1_FF_SHD_WIDE_SHORTLIST_SUMMARY.md`, `P1_SHD_WIDE_ARCH_SHORTLIST_SUMMARY.md` | Reviewer baseline extension with PLIF/ALIF; mean plus sample std over five seeds; selected rows had zero failures |
| `tab:apex-validation` | `results/apex/apex_shd_ranking_smoke_20260719_143719_summary.csv`, `P1_APEX_MULTI_SEED_TUNING_2026_07_19.md` | Tuned APEX cross-framework validation |
| `tab:apex-v2-traceability` | `results/apex_v2/apex_v2_forward_smoke_20260719_174512.csv`, `results/apex_v2/apex_v2_shared_weight_trace_compare_20260719_183254.csv`, `results/apex_v2/apex_v2_shared_weight_trace_compare_20260719_183913.csv`, `results/apex_v2/apex_v2_train_eval_smoke_20260719_190105_summary.csv`, `P1_APEX_V2_THREE_SEED_PREFLIGHT_2026_07_19.md` | Supplementary traceability only; not paper-grade accuracy |

## Open Verification

- Paired-test audit exists for feedforward and reviewer-baseline tables: `results/final_stats/p1_final_paired_tests_20260719.csv`.
- Architecture-transfer per-seed provenance is `07_AdHyperLIF_Triage/results/roster60/_registry.csv`; paired-test context is in `results/final_stats/p1_final_paired_tests_20260719.csv`.
- Re-check all cited source CSV paths before submission.
- Replace placeholder author metadata before Overleaf submission.
- Decide with advisor whether APEX-v2 traceability table stays in the main text or moves to supplementary material.
