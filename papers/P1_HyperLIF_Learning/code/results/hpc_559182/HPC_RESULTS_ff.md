# HPC event-vision results — Adaptive HyperLIF (HyperLIF_Learning)

Registry: `/fs1/scratch/gandhico/HyperLIF_Learning/results/_registry.csv` — 1170 runs, 5 datasets, 54 configs.

Columns: accuracy = mean ± std over seeds; events = mean events/sample; stable = fraction of seeds with no NaN.

## dvsg32_wide

_provenance: dvsg32_wide.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| conv.hyperlif.membrane | 0.8521 ± 0.0157 | 5 | 315.3 | 100% |
| conv.hyperlif.hybrid_vr | 0.8236 ± 0.0083 | 5 | 432.0 | 100% |
| delay.hyperlif.spike_count | 0.8236 ± 0.0180 | 5 | 4427.7 | 100% |
| conv.adaptive.membrane | 0.8229 ± 0.0394 | 5 | 120.6 | 100% |
| conv.hyperlif.hybrid_vr_conductance | 0.8229 ± 0.0074 | 5 | 436.3 | 100% |
| conv.hyperlif.gate | 0.8221 ± 0.0276 | 5 | 519.6 | 100% |
| delay.hyperlif.membrane | 0.8221 ± 0.0083 | 5 | 3556.8 | 100% |
| conv.hyperlif.spike_count | 0.8121 ± 0.0188 | 5 | 718.5 | 100% |
| delay.hyperlif.hybrid_vr_conductance | 0.8100 ± 0.0208 | 5 | 4415.2 | 100% |
| conv.adaptive.hybrid_vr | 0.8093 ± 0.0133 | 5 | 159.8 | 100% |
| delay.hyperlif.hybrid_gr | 0.8086 ± 0.0228 | 5 | 4400.2 | 100% |
| conv.adaptive.hybrid_vr_conductance | 0.8071 ± 0.0387 | 5 | 175.4 | 100% |
| rsnn.hyperlif.spike_count | 0.8064 ± 0.0238 | 5 | 4418.0 | 100% |
| delay.hyperlif.hybrid_vr | 0.8050 ± 0.0137 | 5 | 4348.8 | 100% |
| rsnn.hyperlif.hybrid_gr | 0.8036 ± 0.0265 | 5 | 4334.1 | 100% |
| delay.hyperlif.gate | 0.7971 ± 0.0192 | 5 | 4445.2 | 100% |
| conv.hyperlif.hybrid_gr | 0.7957 ± 0.0118 | 5 | 518.3 | 100% |
| rsnn.hyperlif.hybrid_vr_conductance | 0.7936 ± 0.0156 | 5 | 4351.9 | 100% |
| rsnn.hyperlif.gate | 0.7886 ± 0.0253 | 5 | 4440.5 | 100% |
| rsnn.hyperlif.hybrid_vr | 0.7850 ± 0.0190 | 5 | 4329.5 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.7771 ± 0.0463 | 5 | 2543.6 | 100% |
| rsnn.adaptive.hybrid_vr | 0.7736 ± 0.0352 | 5 | 2574.2 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.7729 ± 0.0121 | 5 | 2604.9 | 100% |
| delay.adaptive.hybrid_vr | 0.7714 ± 0.0134 | 5 | 2551.9 | 100% |
| rsnn.hyperlif.membrane | 0.7643 ± 0.0278 | 5 | 3750.1 | 100% |
| delay.adaptive.hybrid_gr | 0.7614 ± 0.0104 | 5 | 2612.0 | 100% |
| conv.lif.hybrid_vr | 0.7593 ± 0.0133 | 5 | 1740.8 | 100% |
| conv.lif.membrane | 0.7593 ± 0.0144 | 5 | 1790.7 | 100% |
| delay.adaptive.membrane | 0.7593 ± 0.0121 | 5 | 2594.7 | 100% |
| conv.lif.hybrid_vr_conductance | 0.7514 ± 0.0211 | 5 | 1807.8 | 100% |
| rsnn.adaptive.membrane | 0.7500 ± 0.0146 | 5 | 2525.4 | 100% |
| rsnn.adaptive.hybrid_gr | 0.7464 ± 0.0230 | 5 | 2544.3 | 100% |
| rsnn.adaptive.spike_count | 0.7329 ± 0.0234 | 5 | 2584.9 | 100% |
| delay.adaptive.gate | 0.7193 ± 0.0273 | 5 | 2582.3 | 100% |
| conv.adaptive.gate | 0.7186 ± 0.0361 | 5 | 204.6 | 100% |
| delay.adaptive.spike_count | 0.7129 ± 0.0303 | 5 | 2590.2 | 100% |
| conv.adaptive.hybrid_gr | 0.7079 ± 0.0557 | 5 | 182.5 | 100% |
| rsnn.adaptive.gate | 0.7029 ± 0.0310 | 5 | 2571.1 | 100% |
| delay.lif.spike_count | 0.6821 ± 0.0201 | 5 | 3772.3 | 100% |
| rsnn.lif.spike_count | 0.6750 ± 0.0203 | 5 | 3822.9 | 100% |
| conv.adaptive.spike_count | 0.6643 ± 0.0450 | 5 | 385.9 | 100% |
| conv.lif.spike_count | 0.6500 ± 0.0423 | 5 | 2170.1 | 100% |
| rsnn.lif.hybrid_vr | 0.6250 ± 0.0120 | 5 | 3765.0 | 100% |
| delay.lif.hybrid_vr | 0.6207 ± 0.0138 | 5 | 3778.8 | 100% |
| rsnn.lif.hybrid_vr_conductance | 0.6186 ± 0.0162 | 5 | 3818.1 | 100% |
| rsnn.lif.membrane | 0.6186 ± 0.0107 | 5 | 3834.9 | 100% |
| delay.lif.hybrid_vr_conductance | 0.6179 ± 0.0106 | 5 | 3778.8 | 100% |
| delay.lif.membrane | 0.6129 ± 0.0103 | 5 | 3781.3 | 100% |
| conv.lif.gate | 0.1429 ± 0.0000 | 5 | 1770.5 | 100% |
| conv.lif.hybrid_gr | 0.1429 ± 0.0000 | 5 | 1774.7 | 100% |
| delay.lif.gate | 0.1314 ± 0.0229 | 5 | 3781.7 | 100% |
| delay.lif.hybrid_gr | 0.1314 ± 0.0229 | 5 | 3781.7 | 100% |
| rsnn.lif.gate | 0.1314 ± 0.0229 | 5 | 3781.6 | 100% |
| rsnn.lif.hybrid_gr | 0.1314 ± 0.0229 | 5 | 3781.6 | 100% |

## dvsg48_wide

_provenance: dvsg48_wide.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| delay.hyperlif.membrane | 0.7950 ± 0.0182 | 5 | 1649.1 | 100% |
| delay.hyperlif.hybrid_vr | 0.7943 ± 0.0215 | 5 | 2776.8 | 100% |
| delay.hyperlif.hybrid_vr_conductance | 0.7893 ± 0.0152 | 5 | 2854.3 | 100% |
| delay.hyperlif.spike_count | 0.7879 ± 0.0097 | 5 | 2964.3 | 100% |
| conv.adaptive.membrane | 0.7850 ± 0.0203 | 5 | 64.4 | 100% |
| rsnn.hyperlif.gate | 0.7821 ± 0.0155 | 5 | 2921.9 | 100% |
| rsnn.hyperlif.hybrid_vr_conductance | 0.7807 ± 0.0223 | 5 | 2873.5 | 100% |
| delay.hyperlif.gate | 0.7779 ± 0.0162 | 5 | 2945.7 | 100% |
| delay.hyperlif.hybrid_gr | 0.7771 ± 0.0205 | 5 | 2888.3 | 100% |
| rsnn.hyperlif.spike_count | 0.7757 ± 0.0138 | 5 | 2928.3 | 100% |
| conv.hyperlif.membrane | 0.7721 ± 0.0086 | 5 | 62.4 | 100% |
| conv.adaptive.hybrid_vr_conductance | 0.7707 ± 0.0047 | 5 | 66.3 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.7693 ± 0.0083 | 5 | 1475.6 | 100% |
| rsnn.hyperlif.hybrid_gr | 0.7693 ± 0.0146 | 5 | 2943.7 | 100% |
| rsnn.adaptive.hybrid_vr | 0.7657 ± 0.0250 | 5 | 1454.5 | 100% |
| rsnn.hyperlif.hybrid_vr | 0.7636 ± 0.0080 | 5 | 2792.0 | 100% |
| conv.adaptive.hybrid_vr | 0.7621 ± 0.0144 | 5 | 99.4 | 100% |
| conv.lif.hybrid_vr_conductance | 0.7564 ± 0.0154 | 5 | 1676.6 | 100% |
| rsnn.hyperlif.membrane | 0.7550 ± 0.0273 | 5 | 1881.2 | 100% |
| conv.hyperlif.spike_count | 0.7521 ± 0.0161 | 5 | 330.3 | 100% |
| delay.adaptive.membrane | 0.7514 ± 0.0265 | 5 | 1424.9 | 100% |
| conv.hyperlif.hybrid_vr_conductance | 0.7479 ± 0.0211 | 5 | 174.1 | 100% |
| conv.hyperlif.hybrid_vr | 0.7471 ± 0.0076 | 5 | 191.4 | 100% |
| conv.lif.hybrid_vr | 0.7471 ± 0.0131 | 5 | 1581.0 | 100% |
| delay.adaptive.hybrid_vr | 0.7471 ± 0.0180 | 5 | 1467.3 | 100% |
| delay.adaptive.hybrid_gr | 0.7436 ± 0.0332 | 5 | 1475.5 | 100% |
| rsnn.adaptive.membrane | 0.7414 ± 0.0236 | 5 | 1455.6 | 100% |
| conv.lif.membrane | 0.7407 ± 0.0083 | 5 | 1556.0 | 100% |
| rsnn.adaptive.hybrid_gr | 0.7407 ± 0.0257 | 5 | 1473.8 | 100% |
| conv.hyperlif.hybrid_gr | 0.7386 ± 0.0147 | 5 | 340.4 | 100% |
| rsnn.lif.spike_count | 0.7329 ± 0.0073 | 5 | 3591.1 | 100% |
| conv.hyperlif.gate | 0.7307 ± 0.0261 | 5 | 312.7 | 100% |
| conv.adaptive.spike_count | 0.7286 ± 0.0283 | 5 | 241.8 | 100% |
| delay.lif.spike_count | 0.7250 ± 0.0246 | 5 | 3679.3 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.7236 ± 0.0332 | 5 | 1467.2 | 100% |
| rsnn.adaptive.spike_count | 0.7200 ± 0.0125 | 5 | 1409.1 | 100% |
| delay.adaptive.gate | 0.7164 ± 0.0261 | 5 | 1470.4 | 100% |
| delay.adaptive.spike_count | 0.7086 ± 0.0231 | 5 | 1435.5 | 100% |
| conv.adaptive.gate | 0.7071 ± 0.0264 | 5 | 122.4 | 100% |
| conv.adaptive.hybrid_gr | 0.7043 ± 0.0178 | 5 | 104.6 | 100% |
| rsnn.adaptive.gate | 0.7014 ± 0.0224 | 5 | 1408.3 | 100% |
| conv.lif.spike_count | 0.6686 ± 0.0184 | 5 | 2161.4 | 100% |
| rsnn.lif.membrane | 0.6279 ± 0.0097 | 5 | 3572.1 | 100% |
| rsnn.lif.hybrid_vr | 0.6243 ± 0.0086 | 5 | 3616.3 | 100% |
| rsnn.lif.hybrid_vr_conductance | 0.6229 ± 0.0105 | 5 | 3578.7 | 100% |
| delay.lif.hybrid_vr_conductance | 0.6057 ± 0.0095 | 5 | 3600.2 | 100% |
| delay.lif.hybrid_vr | 0.5979 ± 0.0144 | 5 | 3638.0 | 100% |
| delay.lif.membrane | 0.5921 ± 0.0122 | 5 | 3632.3 | 100% |
| conv.lif.hybrid_gr | 0.1429 ± 0.0000 | 5 | 1654.1 | 100% |
| delay.lif.gate | 0.1429 ± 0.0000 | 5 | 3553.0 | 100% |
| rsnn.lif.gate | 0.1429 ± 0.0000 | 5 | 3552.8 | 100% |
| rsnn.lif.hybrid_gr | 0.1429 ± 0.0000 | 5 | 3552.8 | 100% |
| conv.lif.gate | 0.1314 ± 0.0229 | 5 | 1679.7 | 100% |
| delay.lif.hybrid_gr | 0.1314 ± 0.0229 | 5 | 3553.0 | 100% |

## nmnist_wide

_provenance: nmnist_wide.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| conv.hyperlif.membrane | 0.9390 ± 0.0058 | 5 | 23.6 | 100% |
| conv.adaptive.membrane | 0.9330 ± 0.0097 | 5 | 6.8 | 100% |
| conv.lif.hybrid_vr | 0.9270 ± 0.0103 | 5 | 1520.6 | 100% |
| conv.adaptive.hybrid_vr | 0.9260 ± 0.0124 | 5 | 10.6 | 100% |
| conv.lif.hybrid_vr_conductance | 0.9255 ± 0.0066 | 5 | 1588.4 | 100% |
| conv.hyperlif.hybrid_vr | 0.9245 ± 0.0081 | 5 | 57.0 | 100% |
| conv.lif.membrane | 0.9235 ± 0.0120 | 5 | 1527.3 | 100% |
| conv.hyperlif.gate | 0.9180 ± 0.0076 | 5 | 148.2 | 100% |
| conv.hyperlif.hybrid_vr_conductance | 0.9165 ± 0.0075 | 5 | 86.5 | 100% |
| conv.adaptive.hybrid_vr_conductance | 0.9160 ± 0.0093 | 5 | 22.7 | 100% |
| conv.hyperlif.spike_count | 0.9120 ± 0.0062 | 5 | 203.8 | 100% |
| conv.hyperlif.hybrid_gr | 0.9095 ± 0.0137 | 5 | 124.7 | 100% |
| rsnn.hyperlif.membrane | 0.9095 ± 0.0080 | 5 | 1016.1 | 100% |
| rsnn.hyperlif.spike_count | 0.9070 ± 0.0056 | 5 | 1269.7 | 100% |
| delay.hyperlif.membrane | 0.9050 ± 0.0052 | 5 | 1024.5 | 100% |
| rsnn.hyperlif.hybrid_vr | 0.9045 ± 0.0104 | 5 | 1116.5 | 100% |
| delay.hyperlif.hybrid_vr | 0.9025 ± 0.0045 | 5 | 1152.3 | 100% |
| delay.hyperlif.spike_count | 0.9005 ± 0.0048 | 5 | 1287.2 | 100% |
| delay.adaptive.membrane | 0.8995 ± 0.0019 | 5 | 786.0 | 100% |
| rsnn.adaptive.hybrid_vr | 0.8990 ± 0.0080 | 5 | 793.0 | 100% |
| rsnn.adaptive.membrane | 0.8990 ± 0.0064 | 5 | 791.1 | 100% |
| rsnn.hyperlif.hybrid_vr_conductance | 0.8990 ± 0.0072 | 5 | 1158.0 | 100% |
| delay.adaptive.hybrid_vr | 0.8960 ± 0.0044 | 5 | 783.3 | 100% |
| rsnn.hyperlif.gate | 0.8945 ± 0.0124 | 5 | 1243.9 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.8935 ± 0.0080 | 5 | 792.1 | 100% |
| rsnn.adaptive.spike_count | 0.8935 ± 0.0087 | 5 | 856.3 | 100% |
| delay.hyperlif.hybrid_vr_conductance | 0.8930 ± 0.0043 | 5 | 1197.1 | 100% |
| conv.adaptive.gate | 0.8925 ± 0.0147 | 5 | 48.1 | 100% |
| conv.lif.spike_count | 0.8925 ± 0.0057 | 5 | 1689.6 | 100% |
| delay.lif.spike_count | 0.8925 ± 0.0123 | 5 | 2984.2 | 100% |
| delay.hyperlif.gate | 0.8895 ± 0.0110 | 5 | 1278.1 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.8895 ± 0.0071 | 5 | 791.6 | 100% |
| delay.adaptive.spike_count | 0.8890 ± 0.0111 | 5 | 858.4 | 100% |
| conv.adaptive.spike_count | 0.8875 ± 0.0079 | 5 | 130.6 | 100% |
| rsnn.hyperlif.hybrid_gr | 0.8840 ± 0.0121 | 5 | 1238.2 | 100% |
| rsnn.lif.spike_count | 0.8840 ± 0.0062 | 5 | 3309.8 | 100% |
| delay.adaptive.gate | 0.8830 ± 0.0143 | 5 | 809.8 | 100% |
| conv.adaptive.hybrid_gr | 0.8825 ± 0.0254 | 5 | 34.4 | 100% |
| rsnn.adaptive.gate | 0.8795 ± 0.0121 | 5 | 808.2 | 100% |
| delay.hyperlif.hybrid_gr | 0.8795 ± 0.0100 | 5 | 1248.1 | 100% |
| rsnn.lif.hybrid_vr_conductance | 0.8790 ± 0.0070 | 5 | 3191.2 | 100% |
| rsnn.lif.membrane | 0.8780 ± 0.0058 | 5 | 3138.7 | 100% |
| delay.adaptive.hybrid_gr | 0.8765 ± 0.0101 | 5 | 810.0 | 100% |
| rsnn.adaptive.hybrid_gr | 0.8750 ± 0.0141 | 5 | 817.0 | 100% |
| rsnn.lif.hybrid_vr | 0.8720 ± 0.0033 | 5 | 3124.5 | 100% |
| delay.lif.hybrid_vr | 0.8630 ± 0.0046 | 5 | 2945.7 | 100% |
| delay.lif.hybrid_vr_conductance | 0.8595 ± 0.0051 | 5 | 2991.9 | 100% |
| delay.lif.membrane | 0.8545 ± 0.0048 | 5 | 2939.4 | 100% |
| conv.lif.gate | 0.1000 ± 0.0000 | 5 | 1542.4 | 100% |
| conv.lif.hybrid_gr | 0.1000 ± 0.0000 | 5 | 1642.2 | 100% |
| delay.lif.gate | 0.1000 ± 0.0000 | 5 | 3004.3 | 100% |
| delay.lif.hybrid_gr | 0.1000 ± 0.0000 | 5 | 3004.3 | 100% |
| rsnn.lif.gate | 0.1000 ± 0.0000 | 5 | 3010.4 | 100% |
| rsnn.lif.hybrid_gr | 0.1000 ± 0.0000 | 5 | 3010.4 | 100% |

## shd_wide_T20

_provenance: shd_wide_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| delay.hyperlif.membrane | 0.7005 ± 0.0084 | 5 | 1678.0 | 100% |
| delay.hyperlif.spike_count | 0.6783 ± 0.0230 | 5 | 2019.7 | 100% |
| delay.hyperlif.hybrid_vr | 0.6743 ± 0.0141 | 5 | 2011.6 | 100% |
| delay.hyperlif.hybrid_vr_conductance | 0.6635 ± 0.0071 | 5 | 2003.8 | 100% |
| rsnn.hyperlif.spike_count | 0.6590 ± 0.0138 | 5 | 2037.9 | 100% |
| delay.lif.hybrid_vr | 0.6560 ± 0.0085 | 5 | 2139.0 | 100% |
| delay.lif.membrane | 0.6517 ± 0.0117 | 5 | 2158.1 | 100% |
| delay.lif.hybrid_vr_conductance | 0.6515 ± 0.0049 | 5 | 2157.6 | 100% |
| rsnn.hyperlif.gate | 0.6482 ± 0.0086 | 5 | 2011.8 | 100% |
| rsnn.hyperlif.hybrid_vr | 0.6475 ± 0.0061 | 5 | 2056.4 | 100% |
| rsnn.hyperlif.hybrid_vr_conductance | 0.6472 ± 0.0137 | 5 | 2016.5 | 100% |
| rsnn.hyperlif.membrane | 0.6468 ± 0.0131 | 5 | 1707.2 | 100% |
| delay.hyperlif.gate | 0.6460 ± 0.0159 | 5 | 2010.1 | 100% |
| delay.adaptive.membrane | 0.6408 ± 0.0104 | 5 | 953.4 | 100% |
| delay.hyperlif.hybrid_gr | 0.6355 ± 0.0170 | 5 | 1954.8 | 100% |
| rsnn.hyperlif.hybrid_gr | 0.6280 ± 0.0085 | 5 | 1948.1 | 100% |
| delay.adaptive.hybrid_vr | 0.6272 ± 0.0140 | 5 | 926.3 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.6142 ± 0.0117 | 5 | 913.9 | 100% |
| delay.adaptive.spike_count | 0.6050 ± 0.0132 | 5 | 950.8 | 100% |
| rsnn.adaptive.hybrid_vr | 0.5995 ± 0.0102 | 5 | 900.9 | 100% |
| rsnn.adaptive.membrane | 0.5938 ± 0.0058 | 5 | 907.7 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.5930 ± 0.0151 | 5 | 908.6 | 100% |
| delay.adaptive.hybrid_gr | 0.5730 ± 0.0164 | 5 | 941.4 | 100% |
| delay.adaptive.gate | 0.5627 ± 0.0183 | 5 | 920.4 | 100% |
| rsnn.adaptive.hybrid_gr | 0.5520 ± 0.0094 | 5 | 899.8 | 100% |
| rsnn.adaptive.spike_count | 0.5465 ± 0.0147 | 5 | 951.5 | 100% |
| rsnn.lif.hybrid_vr_conductance | 0.5393 ± 0.0106 | 5 | 2326.7 | 100% |
| rsnn.lif.membrane | 0.5300 ± 0.0165 | 5 | 2370.4 | 100% |
| rsnn.lif.hybrid_vr | 0.5295 ± 0.0145 | 5 | 2303.9 | 100% |
| delay.lif.spike_count | 0.5248 ± 0.0253 | 5 | 2407.3 | 100% |
| rsnn.lif.spike_count | 0.4982 ± 0.0198 | 5 | 2390.2 | 100% |
| rsnn.adaptive.gate | 0.4950 ± 0.0237 | 5 | 929.6 | 100% |
| delay.lif.gate | 0.0500 ± 0.0000 | 5 | 2443.1 | 100% |
| delay.lif.hybrid_gr | 0.0500 ± 0.0000 | 5 | 2443.1 | 100% |
| rsnn.lif.gate | 0.0500 ± 0.0000 | 5 | 2444.8 | 100% |
| rsnn.lif.hybrid_gr | 0.0500 ± 0.0000 | 5 | 2444.8 | 100% |

## ssc_wide_T20

_provenance: ssc_wide_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| delay.hyperlif.membrane | 0.3153 ± 0.0105 | 5 | 1222.2 | 100% |
| delay.hyperlif.hybrid_vr | 0.2961 ± 0.0068 | 5 | 1661.0 | 100% |
| delay.hyperlif.spike_count | 0.2916 ± 0.0101 | 5 | 1723.2 | 100% |
| delay.adaptive.membrane | 0.2761 ± 0.0031 | 5 | 908.8 | 100% |
| delay.hyperlif.hybrid_vr_conductance | 0.2750 ± 0.0069 | 5 | 1623.6 | 100% |
| delay.hyperlif.gate | 0.2629 ± 0.0089 | 5 | 1709.1 | 100% |
| delay.hyperlif.hybrid_gr | 0.2473 ± 0.0165 | 5 | 1672.4 | 100% |
| delay.adaptive.hybrid_vr | 0.2440 ± 0.0100 | 5 | 880.3 | 100% |
| delay.adaptive.spike_count | 0.2417 ± 0.0104 | 5 | 902.0 | 100% |
| delay.adaptive.hybrid_vr_conductance | 0.2403 ± 0.0074 | 5 | 853.7 | 100% |
| rsnn.hyperlif.spike_count | 0.2370 ± 0.0107 | 5 | 1600.5 | 100% |
| rsnn.hyperlif.membrane | 0.2316 ± 0.0058 | 5 | 945.4 | 100% |
| rsnn.hyperlif.hybrid_vr | 0.2301 ± 0.0055 | 5 | 1513.4 | 100% |
| delay.adaptive.hybrid_gr | 0.2273 ± 0.0068 | 5 | 875.7 | 100% |
| rsnn.hyperlif.hybrid_vr_conductance | 0.2261 ± 0.0056 | 5 | 1582.8 | 100% |
| rsnn.adaptive.hybrid_vr | 0.2240 ± 0.0042 | 5 | 862.3 | 100% |
| rsnn.hyperlif.gate | 0.2214 ± 0.0082 | 5 | 1606.0 | 100% |
| rsnn.adaptive.membrane | 0.2211 ± 0.0067 | 5 | 843.5 | 100% |
| rsnn.adaptive.hybrid_vr_conductance | 0.2183 ± 0.0140 | 5 | 836.9 | 100% |
| delay.adaptive.gate | 0.2149 ± 0.0099 | 5 | 880.9 | 100% |
| rsnn.hyperlif.hybrid_gr | 0.2106 ± 0.0137 | 5 | 1557.5 | 100% |
| rsnn.adaptive.spike_count | 0.2031 ± 0.0124 | 5 | 901.8 | 100% |
| rsnn.adaptive.hybrid_gr | 0.2004 ± 0.0048 | 5 | 854.2 | 100% |
| rsnn.adaptive.gate | 0.1910 ± 0.0149 | 5 | 880.7 | 100% |
| delay.lif.membrane | 0.1677 ± 0.0061 | 5 | 2032.6 | 100% |
| delay.lif.hybrid_vr | 0.1617 ± 0.0061 | 5 | 2030.6 | 100% |
| delay.lif.hybrid_vr_conductance | 0.1614 ± 0.0102 | 5 | 2031.7 | 100% |
| rsnn.lif.membrane | 0.1299 ± 0.0045 | 5 | 2362.3 | 100% |
| delay.lif.spike_count | 0.1286 ± 0.0104 | 5 | 2276.7 | 100% |
| rsnn.lif.hybrid_vr_conductance | 0.1251 ± 0.0090 | 5 | 2352.2 | 100% |
| rsnn.lif.hybrid_vr | 0.1211 ± 0.0067 | 5 | 2352.6 | 100% |
| rsnn.lif.spike_count | 0.1010 ± 0.0086 | 5 | 2364.8 | 100% |
| delay.lif.gate | 0.0286 ± 0.0000 | 5 | 2375.2 | 100% |
| delay.lif.hybrid_gr | 0.0286 ± 0.0000 | 5 | 2375.2 | 100% |
| rsnn.lif.gate | 0.0286 ± 0.0000 | 5 | 2376.9 | 100% |
| rsnn.lif.hybrid_gr | 0.0286 ± 0.0000 | 5 | 2376.9 | 100% |

## Cross-dataset (mean accuracy)

| config | dvsg32_wide | dvsg48_wide | nmnist_wide | shd_wide_T20 | ssc_wide_T20 | mean |
|---|---:|---:|---:|---:|---:|---:|
| conv.hyperlif.membrane | 0.8521 | 0.7721 | 0.9390 | — | — | 0.8544 |
| conv.adaptive.membrane | 0.8229 | 0.7850 | 0.9330 | — | — | 0.8470 |
| conv.adaptive.hybrid_vr | 0.8093 | 0.7621 | 0.9260 | — | — | 0.8325 |
| conv.hyperlif.hybrid_vr | 0.8236 | 0.7471 | 0.9245 | — | — | 0.8317 |
| conv.adaptive.hybrid_vr_conductance | 0.8071 | 0.7707 | 0.9160 | — | — | 0.8313 |
| conv.hyperlif.hybrid_vr_conductance | 0.8229 | 0.7479 | 0.9165 | — | — | 0.8291 |
| conv.hyperlif.spike_count | 0.8121 | 0.7521 | 0.9120 | — | — | 0.8254 |
| conv.hyperlif.gate | 0.8221 | 0.7307 | 0.9180 | — | — | 0.8236 |
| conv.hyperlif.hybrid_gr | 0.7957 | 0.7386 | 0.9095 | — | — | 0.8146 |
| conv.lif.hybrid_vr | 0.7593 | 0.7471 | 0.9270 | — | — | 0.8111 |
| conv.lif.hybrid_vr_conductance | 0.7514 | 0.7564 | 0.9255 | — | — | 0.8111 |
| conv.lif.membrane | 0.7593 | 0.7407 | 0.9235 | — | — | 0.8078 |
| conv.adaptive.gate | 0.7186 | 0.7071 | 0.8925 | — | — | 0.7727 |
| conv.adaptive.hybrid_gr | 0.7079 | 0.7043 | 0.8825 | — | — | 0.7649 |
| conv.adaptive.spike_count | 0.6643 | 0.7286 | 0.8875 | — | — | 0.7601 |
| conv.lif.spike_count | 0.6500 | 0.6686 | 0.8925 | — | — | 0.7370 |
| delay.hyperlif.membrane | 0.8221 | 0.7950 | 0.9050 | 0.7005 | 0.3153 | 0.7076 |
| delay.hyperlif.spike_count | 0.8236 | 0.7879 | 0.9005 | 0.6783 | 0.2916 | 0.6964 |
| delay.hyperlif.hybrid_vr | 0.8050 | 0.7943 | 0.9025 | 0.6743 | 0.2961 | 0.6944 |
| delay.hyperlif.hybrid_vr_conductance | 0.8100 | 0.7893 | 0.8930 | 0.6635 | 0.2750 | 0.6862 |
| rsnn.hyperlif.spike_count | 0.8064 | 0.7757 | 0.9070 | 0.6590 | 0.2370 | 0.6770 |
| delay.hyperlif.gate | 0.7971 | 0.7779 | 0.8895 | 0.6460 | 0.2629 | 0.6747 |
| delay.hyperlif.hybrid_gr | 0.8086 | 0.7771 | 0.8795 | 0.6355 | 0.2473 | 0.6696 |
| rsnn.hyperlif.hybrid_vr_conductance | 0.7936 | 0.7807 | 0.8990 | 0.6472 | 0.2261 | 0.6693 |
| rsnn.hyperlif.gate | 0.7886 | 0.7821 | 0.8945 | 0.6482 | 0.2214 | 0.6670 |
| rsnn.hyperlif.hybrid_vr | 0.7850 | 0.7636 | 0.9045 | 0.6475 | 0.2301 | 0.6661 |
| delay.adaptive.membrane | 0.7593 | 0.7514 | 0.8995 | 0.6408 | 0.2761 | 0.6654 |
| rsnn.hyperlif.membrane | 0.7643 | 0.7550 | 0.9095 | 0.6468 | 0.2316 | 0.6614 |
| rsnn.hyperlif.hybrid_gr | 0.8036 | 0.7693 | 0.8840 | 0.6280 | 0.2106 | 0.6591 |
| delay.adaptive.hybrid_vr | 0.7714 | 0.7471 | 0.8960 | 0.6272 | 0.2440 | 0.6572 |
| rsnn.adaptive.hybrid_vr | 0.7736 | 0.7657 | 0.8990 | 0.5995 | 0.2240 | 0.6524 |
| rsnn.adaptive.hybrid_vr_conductance | 0.7771 | 0.7693 | 0.8895 | 0.5930 | 0.2183 | 0.6494 |
| delay.adaptive.hybrid_vr_conductance | 0.7729 | 0.7236 | 0.8935 | 0.6142 | 0.2403 | 0.6489 |
| rsnn.adaptive.membrane | 0.7500 | 0.7414 | 0.8990 | 0.5938 | 0.2211 | 0.6411 |
| delay.adaptive.hybrid_gr | 0.7614 | 0.7436 | 0.8765 | 0.5730 | 0.2273 | 0.6364 |
| delay.adaptive.spike_count | 0.7129 | 0.7086 | 0.8890 | 0.6050 | 0.2417 | 0.6314 |
| rsnn.adaptive.hybrid_gr | 0.7464 | 0.7407 | 0.8750 | 0.5520 | 0.2004 | 0.6229 |
| delay.adaptive.gate | 0.7193 | 0.7164 | 0.8830 | 0.5627 | 0.2149 | 0.6193 |
| rsnn.adaptive.spike_count | 0.7329 | 0.7200 | 0.8935 | 0.5465 | 0.2031 | 0.6192 |
| rsnn.adaptive.gate | 0.7029 | 0.7014 | 0.8795 | 0.4950 | 0.1910 | 0.5940 |
| delay.lif.spike_count | 0.6821 | 0.7250 | 0.8925 | 0.5248 | 0.1286 | 0.5906 |
| delay.lif.hybrid_vr | 0.6207 | 0.5979 | 0.8630 | 0.6560 | 0.1617 | 0.5799 |
| delay.lif.hybrid_vr_conductance | 0.6179 | 0.6057 | 0.8595 | 0.6515 | 0.1614 | 0.5792 |
| rsnn.lif.spike_count | 0.6750 | 0.7329 | 0.8840 | 0.4982 | 0.1010 | 0.5782 |
| delay.lif.membrane | 0.6129 | 0.5921 | 0.8545 | 0.6517 | 0.1677 | 0.5758 |
| rsnn.lif.hybrid_vr_conductance | 0.6186 | 0.6229 | 0.8790 | 0.5393 | 0.1251 | 0.5570 |
| rsnn.lif.membrane | 0.6186 | 0.6279 | 0.8780 | 0.5300 | 0.1299 | 0.5569 |
| rsnn.lif.hybrid_vr | 0.6250 | 0.6243 | 0.8720 | 0.5295 | 0.1211 | 0.5544 |
| conv.lif.hybrid_gr | 0.1429 | 0.1429 | 0.1000 | — | — | 0.1286 |
| conv.lif.gate | 0.1429 | 0.1314 | 0.1000 | — | — | 0.1248 |
| delay.lif.gate | 0.1314 | 0.1429 | 0.1000 | 0.0500 | 0.0286 | 0.0906 |
| rsnn.lif.gate | 0.1314 | 0.1429 | 0.1000 | 0.0500 | 0.0286 | 0.0906 |
| rsnn.lif.hybrid_gr | 0.1314 | 0.1429 | 0.1000 | 0.0500 | 0.0286 | 0.0906 |
| delay.lif.hybrid_gr | 0.1314 | 0.1314 | 0.1000 | 0.0500 | 0.0286 | 0.0883 |
