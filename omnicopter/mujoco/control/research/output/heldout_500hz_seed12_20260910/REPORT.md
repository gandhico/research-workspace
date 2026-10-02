# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 3/3 | 0.15210 ± 0.01202 | 4.012 ± 0.106 | 0.270 | 5.23 | 8.43 |
| legacy_12 | 12 | 3/3 | 0.06803 ± 0.00527 | 3.135 ± 0.103 | 0.150 | 4.59 | 8.47 |
| cmg_12 | 12 | 3/3 | 0.06319 ± 0.00503 | 2.900 ± 0.095 | 0.139 | 4.22 | 8.48 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
