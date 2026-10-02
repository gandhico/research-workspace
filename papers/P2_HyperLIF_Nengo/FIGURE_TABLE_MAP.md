# Figure / Table Map

Every figure and table is a pure function of a CSV file written by an experiment
script. Nothing in `figures/` or `tables/` runs a simulation. This guarantees
traceability: figure ⟶ generating function ⟶ source CSV ⟶ experiment script.

## Figures (`figures/make_figures.py` → `results/figures/` and `paper/figures/`, PNG + PDF)

| Manuscript | File | Function | Source CSV(s) | Experiment |
|---|---|---|---|---|
| Fig. 1 (schematic) | TikZ in `paper/main.tex` | — (drawn in LaTeX) | — | — |
| Fig. 2 | `fig_step` | `fig_step()` | `01_lif_vs_hyperlif.csv` | `01_lif_vs_hyperlif.py` |
| Fig. 3 | `fig_stress` | `fig_stress()` | `02_hyperlif_vs_adaptive.csv` | `02_hyperlif_vs_adaptive.py` |
| Fig. 4 | `fig_fi` | `fig_fi()` | `03_current_sweep.csv` | `03_current_sweep.py` |
| Fig. 5 | `fig_db` | `fig_db()` | `04_depolarization_block.csv` | `04_depolarization_block.py` |
| Fig. 6 | `fig_integration` | `fig_integration()` | `06_integration_accuracy.csv`, `06_stability.csv` | `06_numerical_integration.py` |
| Fig. 7 | `fig_parity` | `fig_parity()` | `07_python_vs_nengo.csv` | `07_python_vs_nengo.py` |
| Fig. 8 | `fig_decode` | `fig_decode()` | `05_gate_state_decoding.csv` | `05_gate_state_decoding.py` |

The constant `DB_ONSET = 2.4` annotated in `fig_fi` matches the analytical value
written to `03_db_analysis.csv` (`hyperlif_db_onset_current`).

## Capability figure (`experiments/make_capability_figure.py` -> `paper/figures/`, PNG + PDF)

| Manuscript | File | Source CSV(s) | Experiment |
|---|---|---|---|
| Fig. 9 (`fig:capability`) | `fig_nengo_capability` | `13_hyperlif_nengo_capability_matrix.csv`, `15_pes_rate_matched.csv` | `13_hyperlif_nengo_capability_matrix.py`, `15_pes_rate_matched.py`, `make_capability_figure.py` |

## Candidate calibration figures (`figures/make_candidate_plots.py` → `results/figures/` and `paper/figures/`, PNG + PDF)

| File | Purpose | Source CSV | Experiment |
|---|---|---|---|
| `fig_candidate_robustness_heatmap` | Per-app normalized penalty heatmap for the ranked priority candidates | `12_origin_aware_calibration_summary.csv` | `11_origin_aware_calibration_sweep.py` |
| `fig_candidate_score_events` | Robustness score versus mean event rate, labeled by candidate family | `12_origin_aware_calibration_summary.csv` | `11_origin_aware_calibration_sweep.py` |
| `fig_candidate_rate_calibration` | Origin-aware `rate_to_current` calibration trend for θ_event=0.95 candidates | `12_origin_aware_calibration_summary.csv` | `11_origin_aware_calibration_sweep.py` |

## Tables (`tables/make_tables.py` → `paper/tables/*.tex`)

| Manuscript | File | Function | Source |
|---|---|---|---|
| Table 1 (notation) | `tab_notation.tex` | `tab_notation()` | static (symbol list) |
| Table 2 (model comparison) | `tab_model_compare.tex` | `tab_model_compare()` | static (qualitative) |
| Table 3 (sweep summary) | `tab_sweep.tex` | `tab_sweep()` | `03_current_sweep.csv` |
| Table 4 (integration) | `tab_integration.tex` | `tab_integration()` | `06_integration_accuracy.csv` |
| Table 5 (parity) | `tab_parity.tex` | `tab_parity()` | `07_parity_metrics.csv` |
| Table 6 (decoding) | `tab_decoding.tex` | `tab_decoding()` | `05_decoding_metrics.csv` |
| Table 7 (parameters) | `tab_params.tex` | `tab_params()` | reflected from `LIFParams`/`HyperLIFParams`/`AdaptiveHyperLIFParams` |

Additional manuscript tables currently written directly in `paper/main.tex`:

| Manuscript | Source |
|---|---|
| NEF app smoke table (`tab:nef-smoke`) | `08_nef_app_smoke.csv` from `experiments/08_nef_app_smoke.py` |
| Core-Nengo capability table (`tab:capability-sweep`) | `10_core_nengo_capability_sweep.csv` from `experiments/09_core_nengo_capability_sweep.py`; includes θ_event and static-origin (`v_reset=-0.6`, `min_voltage=-2.0`) rows |
| θ_event static sweep table (`tab:theta-static`) | `09_theta_static_event_threshold_summary.csv`, copied from `05_Adaptive_Threshold_HyperLIF_Nengo/results/csv/01_static_event_threshold_summary.csv` |
| Calibrated capability table (`tab:capability-calib`) | `13_hyperlif_nengo_capability_matrix.csv` from `experiments/13_hyperlif_nengo_capability_matrix.py` |
| Three-seed core capability table (`tab:capability-seeded`) | `17_capability_seed_sweep_summary.csv` from `experiments/17_capability_seed_sweep.py --preflight`; 84/84 simulations, zero failures |
| Five-seed scalar NEF decoder-ablation table (`tab:nef-decoder-ablation`) | `18_nef_decoder_state_ablation_summary.csv` from `experiments/18_nef_decoder_state_ablation.py --seeds 0,1,2,3,4 --n-neurons 100 --duration 1.2` |
| Backend portability table (`tab:backend`) | `experiments/14_backend_portability_probe.py` plus the recorded backend rejection/status notes |

Additional θ_event text claims are supported by:

- `09_theta_decoder_comparison.csv`
- `09_theta_adaptive_rule_tuning_top.csv`
- `11_full_tuning_candidate_matrix.csv`
- `12_origin_aware_calibration_sweep.csv`
- `12_origin_aware_calibration_summary.csv`

Additional Nengo capability, PES, backend, and seed-preflight text claims are supported by:

- `13_hyperlif_nengo_capability_matrix.csv`
- `14_backend_portability_probe.py`
- `15_pes_rate_matched.csv`
- `17_capability_seed_sweep.csv`
- `17_capability_seed_sweep_summary.csv`
- `results/logs/17_capability_seed_sweep_preflight_20260719.log`

Final scalar NEF decoder-ablation evidence is supported by:

- `18_nef_decoder_state_ablation.csv`
- `18_nef_decoder_state_ablation_summary.csv`
- `results/logs/18_nef_decoder_state_ablation.txt`

> The manuscript float numbers (Table 1..7, Fig. 2..8) are assigned by LaTeX in
> order of appearance; the table above lists them by the `\label` they carry
> (`tab:notation`, `tab:params`, `tab:modelcompare`, `tab:sweep`, `tab:parity`,
> `tab:decoding`, `tab:integration`; `fig:step`, `fig:stress`, `fig:fi`,
> `fig:db`, `fig:integration`, `fig:parity`, `fig:decode`, `fig:schematic`).

## Regeneration

```powershell
scripts\make_figures.ps1   # re-renders all figures from existing CSVs
scripts\make_tables.ps1    # re-writes all .tex tables from existing CSVs/params
```

To regenerate the underlying data first, run `scripts\run_experiments.ps1`.
