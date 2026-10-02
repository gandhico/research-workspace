# Exploratory RL pilot comparison

Positive reduction means lower true-state quaternion-angle error.

| Platform | Duration | Arm | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| x2 | 15 s | CMG direct | -400.87% | -4.86% | -13.50% | -0.00% | -54.26% | -55.86% |
| x2 | 15 s | CMG envelope | -3.05% | -2.38% | -4.43% | -0.63% | -0.48% | -2.19% |
| x2 | 15 s | LIFRate envelope | -3.12% | -0.90% | -1.44% | +1.87% | -1.15% | -0.93% |
| x2 | 15 s | Paired-current envelope | -0.69% | -0.91% | -1.02% | +0.32% | -0.23% | -0.50% |

Development missions: Full3 and Hard45. Held-out missions: Roll, Hardstep and Yaw360.
This table is a pilot, not a paper comparison or statistical result.
