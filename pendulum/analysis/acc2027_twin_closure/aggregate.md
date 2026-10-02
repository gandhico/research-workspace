# ACC 2027 QLabs pendulum aggregate

Selection label: `closure_nominal`. Metrics use the final five seconds of each run.

| Controller | n | alpha RMS (deg) | Improvement | residual RMS (V) | Tail balanced | Faults/stalls |
|---|---:|---:|---:|---:|:---:|---:|
| classical | 1 | 1.2371 +/- 0.0000 | +0.00% | 0.0000 | yes | 0/0 |
| fixed-residual | 1 | 1.0565 +/- 0.0000 | +14.60% | 0.0156 | yes | 0/0 |
| adaptive-residual | 1 | 1.0597 +/- 0.0000 | +14.34% | 0.1784 | yes | 0/0 |
| online-pes-fixed | 1 | 1.0570 +/- 0.0000 | +14.55% | 0.0309 | yes | 0/0 |
| online-pes-adaptive | 1 | 1.0617 +/- 0.0000 | +14.17% | 0.0288 | yes | 0/0 |

Interpret repeated-trial statistics only when n >= 3. Capture time is not a matched metric because the QLabs arm state is not reset between processes.
