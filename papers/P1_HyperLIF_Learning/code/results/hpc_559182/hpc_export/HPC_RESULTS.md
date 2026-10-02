# HPC event-vision results — Adaptive HyperLIF (HyperLIF_Learning)

Registry: `/fs1/scratch/gandhico/HyperLIF_Learning/results/_registry.csv` — 450 runs, 5 datasets, 18 configs.

Columns: accuracy = mean ± std over seeds; events = mean events/sample; stable = fraction of seeds with no NaN.

## dvsg32_wide

_provenance: dvsg32_wide.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| hyperlif.spike_count | 0.8179 ± 0.0179 | 5 | 4433.6 | 100% |
| hyperlif.hybrid_vr_conductance | 0.8029 ± 0.0167 | 5 | 4284.1 | 100% |
| hyperlif.hybrid_vr | 0.7957 ± 0.0201 | 5 | 4308.9 | 100% |
| adaptive.hybrid_vr_conductance | 0.7900 ± 0.0086 | 5 | 2563.5 | 100% |
| hyperlif.membrane | 0.7843 ± 0.0140 | 5 | 3593.8 | 100% |
| hyperlif.hybrid_gr | 0.7821 ± 0.0128 | 5 | 4382.6 | 100% |
| hyperlif.gate | 0.7764 ± 0.0165 | 5 | 4383.2 | 100% |
| adaptive.hybrid_vr | 0.7693 ± 0.0107 | 5 | 2543.0 | 100% |
| adaptive.membrane | 0.7614 ± 0.0183 | 5 | 2516.4 | 100% |
| adaptive.hybrid_gr | 0.7486 ± 0.0140 | 5 | 2563.5 | 100% |
| adaptive.spike_count | 0.7336 ± 0.0182 | 5 | 2571.9 | 100% |
| adaptive.gate | 0.7300 ± 0.0440 | 5 | 2537.5 | 100% |
| lif.spike_count | 0.6979 ± 0.0092 | 5 | 3763.6 | 100% |
| lif.hybrid_vr_conductance | 0.6279 ± 0.0183 | 5 | 3808.1 | 100% |
| lif.membrane | 0.6243 ± 0.0222 | 5 | 3806.9 | 100% |
| lif.hybrid_vr | 0.6207 ± 0.0152 | 5 | 3771.9 | 100% |
| lif.gate | 0.1314 ± 0.0229 | 5 | 3781.7 | 100% |
| lif.hybrid_gr | 0.1200 ± 0.0280 | 5 | 3781.7 | 100% |

## dvsg48_wide

_provenance: dvsg48_wide.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| hyperlif.spike_count | 0.7864 ± 0.0264 | 5 | 3024.1 | 100% |
| hyperlif.gate | 0.7850 ± 0.0221 | 5 | 2952.1 | 100% |
| hyperlif.hybrid_vr_conductance | 0.7793 ± 0.0174 | 5 | 2804.1 | 100% |
| hyperlif.hybrid_gr | 0.7779 ± 0.0145 | 5 | 2876.4 | 100% |
| hyperlif.hybrid_vr | 0.7779 ± 0.0127 | 5 | 2723.7 | 100% |
| hyperlif.membrane | 0.7650 ± 0.0216 | 5 | 1824.2 | 100% |
| adaptive.membrane | 0.7514 ± 0.0146 | 5 | 1453.7 | 100% |
| adaptive.hybrid_vr_conductance | 0.7500 ± 0.0260 | 5 | 1444.9 | 100% |
| adaptive.hybrid_vr | 0.7486 ± 0.0097 | 5 | 1438.1 | 100% |
| adaptive.gate | 0.7207 ± 0.0225 | 5 | 1449.4 | 100% |
| lif.spike_count | 0.7193 ± 0.0139 | 5 | 3685.8 | 100% |
| adaptive.hybrid_gr | 0.7057 ± 0.0209 | 5 | 1475.4 | 100% |
| adaptive.spike_count | 0.7057 ± 0.0086 | 5 | 1405.3 | 100% |
| lif.membrane | 0.6143 ± 0.0045 | 5 | 3525.5 | 100% |
| lif.hybrid_vr_conductance | 0.6100 ± 0.0157 | 5 | 3524.8 | 100% |
| lif.hybrid_vr | 0.6029 ± 0.0149 | 5 | 3546.9 | 100% |
| lif.hybrid_gr | 0.1314 ± 0.0229 | 5 | 3553.0 | 100% |
| lif.gate | 0.1200 ± 0.0280 | 5 | 3553.0 | 100% |

## nmnist_wide

_provenance: nmnist_wide.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| hyperlif.membrane | 0.9075 ± 0.0059 | 5 | 1015.9 | 100% |
| adaptive.membrane | 0.9040 ± 0.0051 | 5 | 786.9 | 100% |
| hyperlif.spike_count | 0.9000 ± 0.0050 | 5 | 1232.7 | 100% |
| hyperlif.hybrid_vr | 0.8995 ± 0.0083 | 5 | 1115.1 | 100% |
| adaptive.hybrid_vr | 0.8980 ± 0.0029 | 5 | 780.3 | 100% |
| hyperlif.hybrid_vr_conductance | 0.8950 ± 0.0101 | 5 | 1154.8 | 100% |
| lif.spike_count | 0.8945 ± 0.0081 | 5 | 3021.1 | 100% |
| adaptive.spike_count | 0.8940 ± 0.0075 | 5 | 854.5 | 100% |
| hyperlif.gate | 0.8890 ± 0.0051 | 5 | 1225.1 | 100% |
| adaptive.hybrid_vr_conductance | 0.8885 ± 0.0072 | 5 | 788.6 | 100% |
| adaptive.gate | 0.8835 ± 0.0147 | 5 | 805.3 | 100% |
| hyperlif.hybrid_gr | 0.8775 ± 0.0067 | 5 | 1238.3 | 100% |
| adaptive.hybrid_gr | 0.8760 ± 0.0034 | 5 | 798.8 | 100% |
| lif.hybrid_vr | 0.8555 ± 0.0040 | 5 | 2807.5 | 100% |
| lif.membrane | 0.8550 ± 0.0072 | 5 | 2819.5 | 100% |
| lif.hybrid_vr_conductance | 0.8500 ± 0.0071 | 5 | 2823.4 | 100% |
| lif.gate | 0.1000 ± 0.0000 | 5 | 3004.3 | 100% |
| lif.hybrid_gr | 0.1000 ± 0.0000 | 5 | 3004.3 | 100% |

## shd_wide_T20

_provenance: shd_wide_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| hyperlif.hybrid_vr | 0.6368 ± 0.0141 | 5 | 2014.4 | 100% |
| hyperlif.hybrid_vr_conductance | 0.6282 ± 0.0038 | 5 | 2011.3 | 100% |
| hyperlif.spike_count | 0.6175 ± 0.0113 | 5 | 2022.8 | 100% |
| hyperlif.hybrid_gr | 0.6035 ± 0.0145 | 5 | 2015.0 | 100% |
| hyperlif.gate | 0.5945 ± 0.0204 | 5 | 2006.5 | 100% |
| adaptive.hybrid_vr_conductance | 0.5810 ± 0.0144 | 5 | 916.3 | 100% |
| hyperlif.membrane | 0.5785 ± 0.0113 | 5 | 1737.5 | 100% |
| adaptive.membrane | 0.5655 ± 0.0132 | 5 | 923.5 | 100% |
| adaptive.hybrid_vr | 0.5613 ± 0.0166 | 5 | 925.6 | 100% |
| adaptive.hybrid_gr | 0.5222 ± 0.0131 | 5 | 924.5 | 100% |
| adaptive.spike_count | 0.5172 ± 0.0093 | 5 | 965.1 | 100% |
| adaptive.gate | 0.4895 ± 0.0303 | 5 | 912.2 | 100% |
| lif.spike_count | 0.4835 ± 0.0070 | 5 | 2395.5 | 100% |
| lif.hybrid_vr | 0.4570 ± 0.0104 | 5 | 2278.5 | 100% |
| lif.hybrid_vr_conductance | 0.4555 ± 0.0061 | 5 | 2317.1 | 100% |
| lif.membrane | 0.4462 ± 0.0128 | 5 | 2297.3 | 100% |
| lif.gate | 0.0500 ± 0.0000 | 5 | 2443.1 | 100% |
| lif.hybrid_gr | 0.0500 ± 0.0000 | 5 | 2443.1 | 100% |

## ssc_wide_T20

_provenance: ssc_wide_T20.pt_

| config | accuracy | seeds | events/sample | stable |
|---|---:|---:|---:|---:|
| hyperlif.hybrid_vr_conductance | 0.2149 ± 0.0091 | 5 | 1631.7 | 100% |
| hyperlif.hybrid_vr | 0.2130 ± 0.0070 | 5 | 1592.5 | 100% |
| adaptive.membrane | 0.2120 ± 0.0088 | 5 | 875.4 | 100% |
| adaptive.hybrid_vr_conductance | 0.2103 ± 0.0130 | 5 | 847.5 | 100% |
| hyperlif.spike_count | 0.2094 ± 0.0070 | 5 | 1675.1 | 100% |
| adaptive.hybrid_vr | 0.2047 ± 0.0073 | 5 | 853.5 | 100% |
| hyperlif.gate | 0.1970 ± 0.0049 | 5 | 1657.1 | 100% |
| adaptive.spike_count | 0.1927 ± 0.0126 | 5 | 886.9 | 100% |
| hyperlif.hybrid_gr | 0.1920 ± 0.0087 | 5 | 1671.9 | 100% |
| hyperlif.membrane | 0.1837 ± 0.0076 | 5 | 1242.3 | 100% |
| adaptive.hybrid_gr | 0.1823 ± 0.0056 | 5 | 855.5 | 100% |
| adaptive.gate | 0.1709 ± 0.0042 | 5 | 886.6 | 100% |
| lif.membrane | 0.1277 ± 0.0073 | 5 | 2194.1 | 100% |
| lif.hybrid_vr | 0.1261 ± 0.0043 | 5 | 2192.8 | 100% |
| lif.hybrid_vr_conductance | 0.1214 ± 0.0052 | 5 | 2194.5 | 100% |
| lif.spike_count | 0.1023 ± 0.0076 | 5 | 2284.5 | 100% |
| lif.gate | 0.0286 ± 0.0000 | 5 | 2375.2 | 100% |
| lif.hybrid_gr | 0.0286 ± 0.0000 | 5 | 2375.2 | 100% |

## Cross-dataset (mean accuracy)

| config | dvsg32_wide | dvsg48_wide | nmnist_wide | shd_wide_T20 | ssc_wide_T20 | mean |
|---|---:|---:|---:|---:|---:|---:|
| hyperlif.spike_count | 0.8179 | 0.7864 | 0.9000 | 0.6175 | 0.2094 | 0.6662 |
| hyperlif.hybrid_vr | 0.7957 | 0.7779 | 0.8995 | 0.6368 | 0.2130 | 0.6646 |
| hyperlif.hybrid_vr_conductance | 0.8029 | 0.7793 | 0.8950 | 0.6282 | 0.2149 | 0.6641 |
| hyperlif.gate | 0.7764 | 0.7850 | 0.8890 | 0.5945 | 0.1970 | 0.6484 |
| hyperlif.hybrid_gr | 0.7821 | 0.7779 | 0.8775 | 0.6035 | 0.1920 | 0.6466 |
| adaptive.hybrid_vr_conductance | 0.7900 | 0.7500 | 0.8885 | 0.5810 | 0.2103 | 0.6440 |
| hyperlif.membrane | 0.7843 | 0.7650 | 0.9075 | 0.5785 | 0.1837 | 0.6438 |
| adaptive.membrane | 0.7614 | 0.7514 | 0.9040 | 0.5655 | 0.2120 | 0.6389 |
| adaptive.hybrid_vr | 0.7693 | 0.7486 | 0.8980 | 0.5613 | 0.2047 | 0.6364 |
| adaptive.spike_count | 0.7336 | 0.7057 | 0.8940 | 0.5172 | 0.1927 | 0.6087 |
| adaptive.hybrid_gr | 0.7486 | 0.7057 | 0.8760 | 0.5222 | 0.1823 | 0.6070 |
| adaptive.gate | 0.7300 | 0.7207 | 0.8835 | 0.4895 | 0.1709 | 0.5989 |
| lif.spike_count | 0.6979 | 0.7193 | 0.8945 | 0.4835 | 0.1023 | 0.5795 |
| lif.membrane | 0.6243 | 0.6143 | 0.8550 | 0.4462 | 0.1277 | 0.5335 |
| lif.hybrid_vr_conductance | 0.6279 | 0.6100 | 0.8500 | 0.4555 | 0.1214 | 0.5330 |
| lif.hybrid_vr | 0.6207 | 0.6029 | 0.8555 | 0.4570 | 0.1261 | 0.5324 |
| lif.gate | 0.1314 | 0.1200 | 0.1000 | 0.0500 | 0.0286 | 0.0860 |
| lif.hybrid_gr | 0.1200 | 0.1314 | 0.1000 | 0.0500 | 0.0286 | 0.0860 |
