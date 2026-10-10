# ACC 2027 QLabs pendulum aggregate

Selection label: `closure_matched20`. Metrics use the final five seconds of each run.

| Controller | n | alpha RMS (deg) | Improvement | residual RMS (V) | Tail balanced | Faults/stalls |
|---|---:|---:|---:|---:|:---:|---:|
| classical | 3 | 1.0581 +/- 0.0012 | +0.00% | 0.0000 | yes | 0/0 |
| fixed-residual | 3 | 1.0590 +/- 0.0020 | -0.08% | 0.0798 | yes | 0/0 |
| adaptive-residual | 3 | 1.1170 +/- 0.1003 | -5.57% | 0.0748 | yes | 0/0 |
| online-pes-fixed | 3 | 1.0566 +/- 0.0011 | +0.15% | 0.0482 | yes | 0/0 |
| online-pes-adaptive | 3 | 1.0570 +/- 0.0015 | +0.10% | 0.0415 | yes | 0/0 |

Interpret repeated-trial statistics only when n >= 3. Capture time is not a matched metric because the QLabs arm state is not reset between processes.
