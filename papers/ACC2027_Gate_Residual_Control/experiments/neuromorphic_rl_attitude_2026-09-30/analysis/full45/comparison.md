# Exploratory RL replay on the paper's 45-s missions

Trained for six 10-s episodes on Full3/Hard45, then frozen. Positive is lower true-state mean quaternion error.
Archived baseline: `experiments/final_robustness_gating_2026-09-20/results/final_nominal.csv`, classical `pdff_rho3` rows.

| Platform | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean |
|---|---:|---:|---:|---:|---:|---:|
| x2 | -1.20% | -0.79% | -4.10% | -0.52% | -0.96% | -1.50% |
| cf2-rotor | -0.03% | -1.05% | -0.33% | -0.11% | -0.13% | -0.33% |

One training seed; descriptive only. Full3/Hard45 were used for training; Roll/Hardstep/Yaw360 were held out.
