# P1 Final Statistics Audit

Generated: 2026-07-19T19:35:16

## Inputs

- triage root: `C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage`
- output directory: `C:\Users\gandhico\OneDrive - New Mexico State University\Documents\HyperLIF_Nengo\08_HyperLIF_Architectures\results\final_stats`
- registries: full 450-run FF sweep, roster60 architecture-transfer sweep, N-MNIST tiny FF, SHD-wide FF, SHD-wide RSNN/delay shortlist

## Decision

The existing registries are sufficient to compute per-seed descriptive statistics, CI95 values, paired deltas, and failure counts for the main feedforward table, the architecture-transfer table, and the current reviewer-baseline table. They are not sufficient for a strict two-sided nonparametric significance claim at p<0.05 because each cell has only five seeds; the exact sign-flip lower bound is 0.0625 when all five paired differences agree.

Recommended manuscript stance: report mean/std and failure counts in the main table, keep paired tests in supplement or methods notes, and describe the PLIF/ALIF result as a reviewer-baseline shortlist rather than as a fully powered statistical benchmark. A larger seed run is only needed if advisors want formal nonparametric p<0.05 claims.

## Selected Configurations

| Scope | Dataset | Arch | Neuron/readout | Accuracy mean/std | CI95 | Failures | Events mean |
|---|---|---|---|---:|---:|---:|---:|
| full_arch_transfer_roster60 | dvsg32_wide | conv | adaptive membrane | 0.8536 +/- 0.0268 | 0.0333 | 0 | 130.1094 |
| full_arch_transfer_roster60 | dvsg32_wide | conv | hyperlif membrane | 0.8514 +/- 0.0157 | 0.0195 | 0 | 307.3281 |
| full_arch_transfer_roster60 | dvsg32_wide | conv | lif membrane | 0.7693 +/- 0.0100 | 0.0124 | 0 | 1801.2250 |
| full_arch_transfer_roster60 | dvsg32_wide | delay | adaptive hybrid_vr_conductance | 0.7979 +/- 0.0155 | 0.0192 | 0 | 2542.8969 |
| full_arch_transfer_roster60 | dvsg32_wide | delay | hyperlif spike_count | 0.8343 +/- 0.0109 | 0.0135 | 0 | 4468.7219 |
| full_arch_transfer_roster60 | dvsg32_wide | delay | lif spike_count | 0.6857 +/- 0.0145 | 0.0180 | 0 | 3669.0375 |
| full_arch_transfer_roster60 | dvsg32_wide | rsnn | adaptive hybrid_vr_conductance | 0.8121 +/- 0.0253 | 0.0315 | 0 | 2462.1906 |
| full_arch_transfer_roster60 | dvsg32_wide | rsnn | hyperlif hybrid_gr | 0.8143 +/- 0.0141 | 0.0175 | 0 | 4364.7594 |
| full_arch_transfer_roster60 | dvsg32_wide | rsnn | lif spike_count | 0.6893 +/- 0.0308 | 0.0383 | 0 | 3915.1188 |
| full_arch_transfer_roster60 | dvsg48_wide | conv | adaptive membrane | 0.7850 +/- 0.0105 | 0.0131 | 0 | 54.7437 |
| full_arch_transfer_roster60 | dvsg48_wide | conv | hyperlif membrane | 0.7757 +/- 0.0174 | 0.0216 | 0 | 52.7750 |
| full_arch_transfer_roster60 | dvsg48_wide | conv | lif hybrid_vr_conductance | 0.7593 +/- 0.0206 | 0.0256 | 0 | 1667.3312 |
| full_arch_transfer_roster60 | dvsg48_wide | delay | adaptive hybrid_vr | 0.8050 +/- 0.0325 | 0.0404 | 0 | 1500.0750 |
| full_arch_transfer_roster60 | dvsg48_wide | delay | hyperlif hybrid_vr | 0.7971 +/- 0.0260 | 0.0323 | 0 | 2766.5062 |
| full_arch_transfer_roster60 | dvsg48_wide | delay | lif spike_count | 0.7121 +/- 0.0253 | 0.0315 | 0 | 3794.3094 |
| full_arch_transfer_roster60 | dvsg48_wide | rsnn | adaptive hybrid_vr | 0.7693 +/- 0.0277 | 0.0344 | 0 | 1455.5125 |
| full_arch_transfer_roster60 | dvsg48_wide | rsnn | hyperlif hybrid_vr_conductance | 0.7864 +/- 0.0292 | 0.0362 | 0 | 2869.2531 |
| full_arch_transfer_roster60 | dvsg48_wide | rsnn | lif spike_count | 0.7136 +/- 0.0201 | 0.0250 | 0 | 3655.4781 |
| full_arch_transfer_roster60 | nmnist_wide | conv | adaptive membrane | 0.9335 +/- 0.0113 | 0.0140 | 0 | 6.6125 |
| full_arch_transfer_roster60 | nmnist_wide | conv | hyperlif membrane | 0.9390 +/- 0.0080 | 0.0100 | 0 | 19.7656 |
| full_arch_transfer_roster60 | nmnist_wide | conv | lif hybrid_vr_conductance | 0.9320 +/- 0.0054 | 0.0067 | 0 | 1576.5969 |
| full_arch_transfer_roster60 | nmnist_wide | delay | adaptive membrane | 0.8980 +/- 0.0057 | 0.0071 | 0 | 788.5688 |
| full_arch_transfer_roster60 | nmnist_wide | delay | hyperlif membrane | 0.9085 +/- 0.0038 | 0.0047 | 0 | 1007.9719 |
| full_arch_transfer_roster60 | nmnist_wide | delay | lif spike_count | 0.8990 +/- 0.0142 | 0.0176 | 0 | 2978.0312 |
| full_arch_transfer_roster60 | nmnist_wide | rsnn | adaptive membrane | 0.9025 +/- 0.0068 | 0.0085 | 0 | 790.9406 |
| full_arch_transfer_roster60 | nmnist_wide | rsnn | hyperlif membrane | 0.9115 +/- 0.0063 | 0.0078 | 0 | 1003.6625 |
| full_arch_transfer_roster60 | nmnist_wide | rsnn | lif spike_count | 0.8860 +/- 0.0140 | 0.0174 | 0 | 3300.3219 |
| full_arch_transfer_roster60 | shd_wide_T20 | delay | adaptive membrane | 0.6552 +/- 0.0093 | 0.0115 | 0 | 971.1000 |
| full_arch_transfer_roster60 | shd_wide_T20 | delay | hyperlif membrane | 0.7025 +/- 0.0091 | 0.0113 | 0 | 1608.2656 |
| full_arch_transfer_roster60 | shd_wide_T20 | delay | lif hybrid_vr_conductance | 0.6548 +/- 0.0081 | 0.0100 | 0 | 2124.3781 |
| full_arch_transfer_roster60 | shd_wide_T20 | rsnn | adaptive hybrid_vr_conductance | 0.5880 +/- 0.0268 | 0.0333 | 0 | 901.2094 |
| full_arch_transfer_roster60 | shd_wide_T20 | rsnn | hyperlif spike_count | 0.6743 +/- 0.0086 | 0.0107 | 0 | 2045.4969 |
| full_arch_transfer_roster60 | shd_wide_T20 | rsnn | lif hybrid_vr_conductance | 0.5360 +/- 0.0145 | 0.0180 | 0 | 2344.3844 |
| full_arch_transfer_roster60 | ssc_wide_T20 | delay | adaptive membrane | 0.2579 +/- 0.0099 | 0.0124 | 0 | 901.3906 |
| full_arch_transfer_roster60 | ssc_wide_T20 | delay | hyperlif membrane | 0.3079 +/- 0.0148 | 0.0183 | 0 | 1128.5625 |
| full_arch_transfer_roster60 | ssc_wide_T20 | delay | lif membrane | 0.1380 +/- 0.0097 | 0.0121 | 0 | 2027.4344 |
| full_arch_transfer_roster60 | ssc_wide_T20 | rsnn | adaptive hybrid_vr | 0.2107 +/- 0.0076 | 0.0095 | 0 | 837.1938 |
| full_arch_transfer_roster60 | ssc_wide_T20 | rsnn | hyperlif membrane | 0.2299 +/- 0.0091 | 0.0113 | 0 | 876.1094 |
| full_arch_transfer_roster60 | ssc_wide_T20 | rsnn | lif membrane | 0.1163 +/- 0.0043 | 0.0054 | 0 | 2341.2781 |
| full_ff_temporal_450 | dvsg32_wide | ff | adaptive hybrid_vr_conductance | 0.7900 +/- 0.0096 | 0.0119 | 0 | 2563.4875 |
| full_ff_temporal_450 | dvsg32_wide | ff | hyperlif spike_count | 0.8179 +/- 0.0200 | 0.0249 | 0 | 4433.5500 |
| full_ff_temporal_450 | dvsg32_wide | ff | lif spike_count | 0.6979 +/- 0.0103 | 0.0128 | 0 | 3763.6406 |
| full_ff_temporal_450 | dvsg48_wide | ff | adaptive membrane | 0.7514 +/- 0.0163 | 0.0202 | 0 | 1453.7281 |
| full_ff_temporal_450 | dvsg48_wide | ff | hyperlif spike_count | 0.7864 +/- 0.0295 | 0.0366 | 0 | 3024.1188 |
| full_ff_temporal_450 | dvsg48_wide | ff | lif spike_count | 0.7193 +/- 0.0155 | 0.0192 | 0 | 3685.8187 |
| full_ff_temporal_450 | nmnist_wide | ff | adaptive membrane | 0.9040 +/- 0.0058 | 0.0071 | 0 | 786.8656 |
| full_ff_temporal_450 | nmnist_wide | ff | hyperlif membrane | 0.9075 +/- 0.0066 | 0.0082 | 0 | 1015.8906 |
| full_ff_temporal_450 | nmnist_wide | ff | lif spike_count | 0.8945 +/- 0.0091 | 0.0113 | 0 | 3021.0906 |
| full_ff_temporal_450 | shd_wide_T20 | ff | adaptive hybrid_vr_conductance | 0.5810 +/- 0.0161 | 0.0200 | 0 | 916.3156 |
| full_ff_temporal_450 | shd_wide_T20 | ff | hyperlif hybrid_vr | 0.6368 +/- 0.0158 | 0.0196 | 0 | 2014.3906 |
| full_ff_temporal_450 | shd_wide_T20 | ff | lif spike_count | 0.4835 +/- 0.0078 | 0.0097 | 0 | 2395.4563 |
| full_ff_temporal_450 | ssc_wide_T20 | ff | adaptive membrane | 0.2120 +/- 0.0098 | 0.0122 | 0 | 875.3500 |
| full_ff_temporal_450 | ssc_wide_T20 | ff | hyperlif hybrid_vr_conductance | 0.2149 +/- 0.0102 | 0.0127 | 0 | 1631.7469 |
| full_ff_temporal_450 | ssc_wide_T20 | ff | lif membrane | 0.1277 +/- 0.0081 | 0.0101 | 0 | 2194.0781 |
| nmnist_tiny_ff_best_readout | nmnist_tiny_T20 | ff | adaptive hybrid_vr_conductance | 0.8767 +/- 0.0116 | 0.0144 | 0 | 224.4750 |
| nmnist_tiny_ff_best_readout | nmnist_tiny_T20 | ff | alif hybrid_vr_conductance | 0.8967 +/- 0.0192 | 0.0238 | 0 | 323.3062 |
| nmnist_tiny_ff_best_readout | nmnist_tiny_T20 | ff | hyperlif hybrid_vr | 0.8975 +/- 0.0070 | 0.0087 | 0 | 342.8562 |
| nmnist_tiny_ff_best_readout | nmnist_tiny_T20 | ff | lif hybrid_vr | 0.8742 +/- 0.0123 | 0.0153 | 0 | 578.5375 |
| nmnist_tiny_ff_best_readout | nmnist_tiny_T20 | ff | plif hybrid_vr | 0.8750 +/- 0.0106 | 0.0132 | 0 | 581.8750 |
| shd_wide_arch_shortlist | shd_wide_T20 | delay | adaptive hybrid_vr_conductance | 0.4577 +/- 0.0227 | 0.0282 | 0 | 474.4031 |
| shd_wide_arch_shortlist | shd_wide_T20 | delay | alif hybrid_vr_conductance | 0.5650 +/- 0.0209 | 0.0260 | 0 | 840.6063 |
| shd_wide_arch_shortlist | shd_wide_T20 | delay | hyperlif hybrid_vr | 0.5593 +/- 0.0154 | 0.0191 | 0 | 1033.2000 |
| shd_wide_arch_shortlist | shd_wide_T20 | delay | lif hybrid_vr | 0.4945 +/- 0.0215 | 0.0267 | 0 | 1185.7250 |
| shd_wide_arch_shortlist | shd_wide_T20 | delay | plif hybrid_vr | 0.4940 +/- 0.0228 | 0.0284 | 0 | 1191.0625 |
| shd_wide_arch_shortlist | shd_wide_T20 | rsnn | adaptive hybrid_vr_conductance | 0.4823 +/- 0.0159 | 0.0198 | 0 | 471.0250 |
| shd_wide_arch_shortlist | shd_wide_T20 | rsnn | alif hybrid_vr_conductance | 0.5473 +/- 0.0179 | 0.0223 | 0 | 818.8312 |
| shd_wide_arch_shortlist | shd_wide_T20 | rsnn | hyperlif hybrid_vr | 0.5695 +/- 0.0172 | 0.0214 | 0 | 1034.9875 |
| shd_wide_arch_shortlist | shd_wide_T20 | rsnn | lif hybrid_vr | 0.4640 +/- 0.0091 | 0.0113 | 0 | 1186.7219 |
| shd_wide_arch_shortlist | shd_wide_T20 | rsnn | plif hybrid_vr | 0.4637 +/- 0.0096 | 0.0119 | 0 | 1189.3156 |
| shd_wide_ff_shortlist | shd_wide_T20 | ff | adaptive hybrid_vr_conductance | 0.4785 +/- 0.0191 | 0.0238 | 0 | 464.6156 |
| shd_wide_ff_shortlist | shd_wide_T20 | ff | alif hybrid_vr_conductance | 0.5570 +/- 0.0199 | 0.0247 | 0 | 830.2031 |
| shd_wide_ff_shortlist | shd_wide_T20 | ff | hyperlif hybrid_vr | 0.5475 +/- 0.0227 | 0.0282 | 0 | 1042.2281 |
| shd_wide_ff_shortlist | shd_wide_T20 | ff | lif hybrid_vr | 0.4238 +/- 0.0133 | 0.0165 | 0 | 1208.6813 |
| shd_wide_ff_shortlist | shd_wide_T20 | ff | plif hybrid_vr | 0.4235 +/- 0.0119 | 0.0148 | 0 | 1210.3375 |

## HyperLIF-Centered Paired Comparisons

| Scope | Arch | Model A | Model B | Mean diff A-B | t p | sign-flip p | Wins A/B |
|---|---|---|---|---:|---:|---:|---:|
| shd_wide_ff_shortlist | ff | hyperlif/hybrid_vr | plif/hybrid_vr | 0.1240 | 0.0000 | 0.0625 | 5/0 |
| shd_wide_ff_shortlist | ff | hyperlif/hybrid_vr | lif/hybrid_vr | 0.1237 | 0.0000 | 0.0625 | 5/0 |
| shd_wide_ff_shortlist | ff | adaptive/hybrid_vr_conductance | hyperlif/hybrid_vr | -0.0690 | 0.0003 | 0.0625 | 0/5 |
| shd_wide_ff_shortlist | ff | alif/hybrid_vr_conductance | hyperlif/hybrid_vr | 0.0095 | 0.1617 | 0.1875 | 4/1 |
| shd_wide_arch_shortlist | rsnn | hyperlif/hybrid_vr | plif/hybrid_vr | 0.1058 | 0.0005 | 0.0625 | 5/0 |
| shd_wide_arch_shortlist | rsnn | hyperlif/hybrid_vr | lif/hybrid_vr | 0.1055 | 0.0005 | 0.0625 | 5/0 |
| shd_wide_arch_shortlist | rsnn | adaptive/hybrid_vr_conductance | hyperlif/hybrid_vr | -0.0873 | 0.0008 | 0.0625 | 0/5 |
| shd_wide_arch_shortlist | rsnn | alif/hybrid_vr_conductance | hyperlif/hybrid_vr | -0.0222 | 0.0357 | 0.0625 | 0/5 |
| shd_wide_arch_shortlist | delay | adaptive/hybrid_vr_conductance | hyperlif/hybrid_vr | -0.1015 | 0.0001 | 0.0625 | 0/5 |
| shd_wide_arch_shortlist | delay | hyperlif/hybrid_vr | plif/hybrid_vr | 0.0653 | 0.0076 | 0.0625 | 5/0 |
| shd_wide_arch_shortlist | delay | hyperlif/hybrid_vr | lif/hybrid_vr | 0.0648 | 0.0071 | 0.0625 | 5/0 |
| shd_wide_arch_shortlist | delay | alif/hybrid_vr_conductance | hyperlif/hybrid_vr | 0.0057 | 0.6169 | 0.6250 | 3/2 |

## Output Files

- `C:\Users\gandhico\OneDrive - New Mexico State University\Documents\HyperLIF_Nengo\08_HyperLIF_Architectures\results\final_stats\p1_final_stats_summary_20260719.csv`
- `C:\Users\gandhico\OneDrive - New Mexico State University\Documents\HyperLIF_Nengo\08_HyperLIF_Architectures\results\final_stats\p1_final_paired_tests_20260719.csv`

## Claim Impact

- Safe: descriptive mean/std/CI and failure-count reporting for the current shortlist.
- Safe: paired directional deltas as exploratory/statistical-context evidence.
- Unsafe: strict nonparametric p<0.05 claims from the five-seed shortlist.
- Open: decide whether to place paired-test p-values in supplement only, or add a compact statement in Methods.
