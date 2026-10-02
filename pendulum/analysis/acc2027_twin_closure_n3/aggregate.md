# ACC 2027 QLabs pendulum aggregate

Selection label: `closure`. Metrics use the final five seconds of each run.

| Controller | n | alpha RMS (deg) | Improvement | residual RMS (V) | Tail balanced | Faults/stalls |
|---|---:|---:|---:|---:|:---:|---:|
| classical | 3 | 1.2349 +/- 0.0030 | +0.00% | 0.0000 | yes | 0/0 |
| fixed-residual | 3 | 1.0587 +/- 0.0040 | +14.27% | 0.1135 | yes | 0/0 |
| adaptive-residual | 3 | 1.0582 +/- 0.0021 | +14.31% | 0.1215 | yes | 0/0 |
| online-pes-fixed | 3 | 1.1161 +/- 0.1032 | +9.62% | 0.0404 | yes | 0/0 |
| online-pes-adaptive | 3 | 1.0602 +/- 0.0028 | +14.15% | 0.0265 | yes | 0/0 |

Interpret repeated-trial statistics only when n >= 3. Capture time is not a matched metric because the QLabs arm state is not reset between processes.
