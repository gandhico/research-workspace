# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 6/6 | 0.13610 ± 0.02830 | 4.859 ± 0.234 | 0.235 | 6.69 | 6.90 |
| legacy_12 | 12 | 6/6 | 0.06530 ± 0.01295 | 3.810 ± 0.190 | 0.139 | 5.54 | 6.91 |
| cmg_12 | 12 | 6/6 | 0.05742 ± 0.01173 | 3.580 ± 0.181 | 0.126 | 5.22 | 6.95 |
| cmg_48 | 48 | 6/6 | 0.05744 ± 0.01170 | 3.582 ± 0.178 | 0.124 | 5.20 | 6.96 |
| cmg_192 | 192 | 6/6 | 0.05753 ± 0.01152 | 3.582 ± 0.179 | 0.123 | 5.26 | 6.92 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
