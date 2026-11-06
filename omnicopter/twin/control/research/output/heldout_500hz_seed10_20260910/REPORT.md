# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 3/3 | 0.30054 ± 0.00995 | 3.984 ± 0.496 | 0.360 | 6.84 | 10.00 |
| legacy_12 | 12 | 3/3 | 0.12563 ± 0.00404 | 3.080 ± 0.381 | 0.156 | 5.72 | 10.00 |
| cmg_12 | 12 | 3/3 | 0.14780 ± 0.04912 | 3.027 ± 0.664 | 0.359 | 6.42 | 10.00 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
