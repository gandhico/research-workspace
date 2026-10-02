| run | reward | arm (line) | steps (M) | train gates/ep (final) | crash (final) | 1st eval gate (M) | past split-S (M) | 1st lap (M) | best eval gates | best lap (s) | MuJoCo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v2pilot_mlp_s1 | v2 | mlp (control) | 5.0 | 0.07 | 0.3 | None | None | None | 0 | None | -- |
| v2pilot_cmg_acc_s1 | v2 | cmg_acc (non-spiking) | 5.0 | 0.11 | 0.48 | None | None | None | 0 | None | -- |
| v3A_mlp_bonus10 | v3 (sweep A) | mlp (control) | 5.0 | 0.36 | 0.97 | 3.3 | None | None | 1 | None | -- |
| v3B_mlp_bonus10_crash5_smooth001 | sweep B | mlp (control) | 5.0 | 0.41 | 0.96 | None | None | None | 0 | None | -- |
| v3_mlp_s1 | v3 | mlp (control) | 20.0 | 4.12 | 0.3 | 6.6 | 14.4 | 15.7 | 14 | 14.88 | 7 gates, 0 coll., lap 14.98 s |
| v3_cmg_acc_s1 | v3 | cmg_acc (non-spiking) | 20.0 | 1.32 | 0.62 | 5.2 | None | None | 3 | None | 3 gates, 0 coll., time_limit |
| v3_hyperlif_spike_s1 | v3 | hyperlif_spike (spiking) | 20.0 | 2.6 | 0.16 | 5.9 | None | None | 3 | None | 3 gates, 0 coll., time_limit |
| v4_mlp_s1 | v4 | mlp (control) | 20.0 | 7.47 | 0.28 | 5.2 | 9.8 | 9.8 | 14 | 9.5 | 7 gates, 0 coll., lap 9.42 s |
| v4_cmg_acc_s1 | v4 | cmg_acc (non-spiking) | 20.0 | 1.11 | 1.0 | 5.2 | None | None | 2 | None | 2 gates, 1 coll., collision |
| v4_hyperlif_spike_s1 | v4 | hyperlif_spike (spiking) | 20.0 | 1.92 | 0.85 | 2.6 | None | None | 1 | None | 0 gates, 0 coll., time_limit |

| run | det. official | det. distributed | stoch. official | stoch. distributed |
|---|---|---|---|---|
| v3_mlp_s1 | 6.0 gates, lap 0%, crash 0% | 3.86 gates, lap 3%, crash 27% | 5.97 gates, lap 16%, crash 9% | 3.53 gates, lap 1%, crash 35% |
| v3_cmg_acc_s1 | 3.0 gates, lap 0%, crash 0% | 0.84 gates, lap 0%, crash 79% | 2.97 gates, lap 0%, crash 1% | 0.85 gates, lap 0%, crash 73% |
| v3_hyperlif_spike_s1 | 3.0 gates, lap 0%, crash 0% | 2.48 gates, lap 1%, crash 22% | 2.91 gates, lap 0%, crash 5% | 2.46 gates, lap 1%, crash 22% |
| v4_mlp_s1 | 10.0 gates, lap 100%, crash 0% | 7.51 gates, lap 76%, crash 24% | 8.78 gates, lap 82%, crash 22% | 6.88 gates, lap 67%, crash 34% |
| v4_cmg_acc_s1 | 2.0 gates, lap 0%, crash 100% | 0.8 gates, lap 0%, crash 98% | 1.98 gates, lap 0%, crash 95% | 0.95 gates, lap 0%, crash 98% |
| v4_hyperlif_spike_s1 | 0.0 gates, lap 0%, crash 0% | 3.01 gates, lap 2%, crash 57% | 0.09 gates, lap 0%, crash 54% | 2.7 gates, lap 1%, crash 68% |

| run | feature mean | saturated | silent | event rate (Hz/unit) | active units |
|---|---|---|---|---|---|
| v2pilot_cmg_acc_s1 | 0.847 | 0.759 | 0.011 | 0.11 | 0.138 |
| v3_cmg_acc_s1 | 0.93 | 0.895 | 0.012 | 0.12 | 0.151 |
| v3_hyperlif_spike_s1 | 0.668 | 0.293 | 0.184 | 53.39 | 0.931 |
| v4_cmg_acc_s1 | 0.875 | 0.814 | 0.021 | 0.21 | 0.263 |
| v4_hyperlif_spike_s1 | 0.657 | 0.284 | 0.189 | 52.55 | 0.959 |
