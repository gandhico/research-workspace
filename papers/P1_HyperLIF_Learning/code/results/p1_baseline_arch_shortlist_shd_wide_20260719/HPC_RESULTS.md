# HPC event-vision results — Adaptive HyperLIF (HyperLIF_Learning)

Registry: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_baseline_arch_shortlist_shd_wide_20260719\_registry.csv` — 50 runs, 1 datasets, 10 configs.

Columns: accuracy = mean ± std over seeds; events = mean events/sample; stable = fraction of seeds with no NaN.

## shd_wide_T20

_provenance: shd_wide_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| rsnn.hyperlif.hybrid_vr | 0.5695 ± 0.0154 | 5 | 1035.0 | 100% |
| delay.alif.hybrid_vr_conductance | 0.5650 ± 0.0187 | 5 | 840.6 | 100% |
| delay.hyperlif.hybrid_vr | 0.5593 ± 0.0138 | 5 | 1033.2 | 100% |
| rsnn.alif.hybrid_vr_conductance | 0.5473 ± 0.0160 | 5 | 818.8 | 100% |
| delay.lif.hybrid_vr | 0.4945 ± 0.0193 | 5 | 1185.7 | 100% |
| delay.plif.hybrid_vr | 0.4940 ± 0.0204 | 5 | 1191.1 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.4823 ± 0.0142 | 5 | 471.0 | 100% |
| rsnn.lif.hybrid_vr | 0.4640 ± 0.0081 | 5 | 1186.7 | 100% |
| rsnn.plif.hybrid_vr | 0.4637 ± 0.0086 | 5 | 1189.3 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.4577 ± 0.0203 | 5 | 474.4 | 100% |

## Cross-dataset (mean accuracy)

| config | shd_wide_T20 | mean |
|---|---:|---:|
| rsnn.hyperlif.hybrid_vr | 0.5695 | 0.5695 |
| delay.alif.hybrid_vr_conductance | 0.5650 | 0.5650 |
| delay.hyperlif.hybrid_vr | 0.5593 | 0.5593 |
| rsnn.alif.hybrid_vr_conductance | 0.5473 | 0.5473 |
| delay.lif.hybrid_vr | 0.4945 | 0.4945 |
| delay.plif.hybrid_vr | 0.4940 | 0.4940 |
| rsnn.adaptive.hybrid_vr_conductance | 0.4823 | 0.4823 |
| rsnn.lif.hybrid_vr | 0.4640 | 0.4640 |
| rsnn.plif.hybrid_vr | 0.4637 | 0.4637 |
| delay.adaptive.hybrid_vr_conductance | 0.4577 | 0.4577 |
