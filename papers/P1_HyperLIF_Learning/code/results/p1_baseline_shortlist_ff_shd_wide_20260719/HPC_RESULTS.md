# HPC event-vision results — Adaptive HyperLIF (HyperLIF_Learning)

Registry: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_baseline_shortlist_ff_shd_wide_20260719\_registry.csv` — 25 runs, 1 datasets, 5 configs.

Columns: accuracy = mean ± std over seeds; events = mean events/sample; stable = fraction of seeds with no NaN.

## shd_wide_T20

_provenance: shd_wide_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| ff.alif.hybrid_vr_conductance | 0.5570 ± 0.0178 | 5 | 830.2 | 100% |
| ff.hyperlif.hybrid_vr | 0.5475 ± 0.0203 | 5 | 1042.2 | 100% |
| ff.adaptive.hybrid_vr_conductance | 0.4785 ± 0.0171 | 5 | 464.6 | 100% |
| ff.lif.hybrid_vr | 0.4238 ± 0.0119 | 5 | 1208.7 | 100% |
| ff.plif.hybrid_vr | 0.4235 ± 0.0106 | 5 | 1210.3 | 100% |

## Cross-dataset (mean accuracy)

| config | shd_wide_T20 | mean |
|---|---:|---:|
| ff.alif.hybrid_vr_conductance | 0.5570 | 0.5570 |
| ff.hyperlif.hybrid_vr | 0.5475 | 0.5475 |
| ff.adaptive.hybrid_vr_conductance | 0.4785 | 0.4785 |
| ff.lif.hybrid_vr | 0.4238 | 0.4238 |
| ff.plif.hybrid_vr | 0.4235 | 0.4235 |
