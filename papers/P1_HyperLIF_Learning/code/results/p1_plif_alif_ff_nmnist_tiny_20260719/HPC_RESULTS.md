# HPC event-vision results — Adaptive HyperLIF (HyperLIF_Learning)

Registry: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\results\p1_plif_alif_ff_nmnist_tiny_20260719\_registry.csv` — 150 runs, 1 datasets, 30 configs.

Columns: accuracy = mean ± std over seeds; events = mean events/sample; stable = fraction of seeds with no NaN.

## nmnist_tiny_T20

_provenance: nmnist_tiny_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| ff.hyperlif.hybrid_vr | 0.8975 ± 0.0062 | 5 | 342.9 | 100% |
| ff.hyperlif.hybrid_vr_conductance | 0.8975 ± 0.0125 | 5 | 341.8 | 100% |
| ff.alif.hybrid_vr_conductance | 0.8967 ± 0.0172 | 5 | 323.3 | 100% |
| ff.hyperlif.membrane | 0.8900 ± 0.0150 | 5 | 279.9 | 100% |
| ff.alif.hybrid_vr | 0.8858 ± 0.0068 | 5 | 314.5 | 100% |
| ff.adaptive.hybrid_vr_conductance | 0.8767 ± 0.0104 | 5 | 224.5 | 100% |
| ff.adaptive.membrane | 0.8758 ± 0.0085 | 5 | 207.2 | 100% |
| ff.plif.hybrid_vr | 0.8750 ± 0.0095 | 5 | 581.9 | 100% |
| ff.lif.hybrid_vr | 0.8742 ± 0.0110 | 5 | 578.5 | 100% |
| ff.hyperlif.spike_count | 0.8725 ± 0.0125 | 5 | 349.8 | 100% |
| ff.lif.hybrid_vr_conductance | 0.8717 ± 0.0116 | 5 | 563.4 | 100% |
| ff.plif.hybrid_vr_conductance | 0.8717 ± 0.0116 | 5 | 565.5 | 100% |
| ff.hyperlif.hybrid_gr | 0.8708 ± 0.0139 | 5 | 360.8 | 100% |
| ff.lif.membrane | 0.8708 ± 0.0139 | 5 | 530.0 | 100% |
| ff.plif.membrane | 0.8708 ± 0.0139 | 5 | 531.9 | 100% |
| ff.adaptive.hybrid_vr | 0.8675 ± 0.0189 | 5 | 226.2 | 100% |
| ff.alif.membrane | 0.8650 ± 0.0107 | 5 | 292.5 | 100% |
| ff.alif.hybrid_gr | 0.8633 ± 0.0148 | 5 | 313.0 | 100% |
| ff.hyperlif.gate | 0.8483 ± 0.0299 | 5 | 350.7 | 100% |
| ff.alif.gate | 0.8475 ± 0.0086 | 5 | 305.9 | 100% |
| ff.lif.spike_count | 0.8450 ± 0.0318 | 5 | 563.2 | 100% |
| ff.plif.spike_count | 0.8417 ± 0.0290 | 5 | 571.5 | 100% |
| ff.adaptive.hybrid_gr | 0.8283 ± 0.0133 | 5 | 214.7 | 100% |
| ff.alif.spike_count | 0.8225 ± 0.0180 | 5 | 288.8 | 100% |
| ff.adaptive.spike_count | 0.8125 ± 0.0087 | 5 | 225.1 | 100% |
| ff.adaptive.gate | 0.7900 ± 0.0198 | 5 | 219.2 | 100% |
| ff.lif.gate | 0.1667 ± 0.0000 | 5 | 585.0 | 100% |
| ff.lif.hybrid_gr | 0.1667 ± 0.0000 | 5 | 585.0 | 100% |
| ff.plif.gate | 0.1667 ± 0.0000 | 5 | 587.7 | 100% |
| ff.plif.hybrid_gr | 0.1667 ± 0.0000 | 5 | 587.7 | 100% |

## Cross-dataset (mean accuracy)

| config | nmnist_tiny_T20 | mean |
|---|---:|---:|
| ff.hyperlif.hybrid_vr | 0.8975 | 0.8975 |
| ff.hyperlif.hybrid_vr_conductance | 0.8975 | 0.8975 |
| ff.alif.hybrid_vr_conductance | 0.8967 | 0.8967 |
| ff.hyperlif.membrane | 0.8900 | 0.8900 |
| ff.alif.hybrid_vr | 0.8858 | 0.8858 |
| ff.adaptive.hybrid_vr_conductance | 0.8767 | 0.8767 |
| ff.adaptive.membrane | 0.8758 | 0.8758 |
| ff.plif.hybrid_vr | 0.8750 | 0.8750 |
| ff.lif.hybrid_vr | 0.8742 | 0.8742 |
| ff.hyperlif.spike_count | 0.8725 | 0.8725 |
| ff.lif.hybrid_vr_conductance | 0.8717 | 0.8717 |
| ff.plif.hybrid_vr_conductance | 0.8717 | 0.8717 |
| ff.hyperlif.hybrid_gr | 0.8708 | 0.8708 |
| ff.lif.membrane | 0.8708 | 0.8708 |
| ff.plif.membrane | 0.8708 | 0.8708 |
| ff.adaptive.hybrid_vr | 0.8675 | 0.8675 |
| ff.alif.membrane | 0.8650 | 0.8650 |
| ff.alif.hybrid_gr | 0.8633 | 0.8633 |
| ff.hyperlif.gate | 0.8483 | 0.8483 |
| ff.alif.gate | 0.8475 | 0.8475 |
| ff.lif.spike_count | 0.8450 | 0.8450 |
| ff.plif.spike_count | 0.8417 | 0.8417 |
| ff.adaptive.hybrid_gr | 0.8283 | 0.8283 |
| ff.alif.spike_count | 0.8225 | 0.8225 |
| ff.adaptive.spike_count | 0.8125 | 0.8125 |
| ff.adaptive.gate | 0.7900 | 0.7900 |
| ff.lif.gate | 0.1667 | 0.1667 |
| ff.lif.hybrid_gr | 0.1667 | 0.1667 |
| ff.plif.gate | 0.1667 | 0.1667 |
| ff.plif.hybrid_gr | 0.1667 | 0.1667 |
