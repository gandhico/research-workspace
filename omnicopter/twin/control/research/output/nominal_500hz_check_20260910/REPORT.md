# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 2/2 | 0.00000 ± 0.00000 | 0.006 ± 0.008 | 0.000 | 0.03 | 5.48 |
| legacy_12 | 12 | 2/2 | 0.00288 ± 0.00041 | 0.312 ± 0.442 | 0.011 | 1.71 | 5.48 |
| cmg_12 | 12 | 2/2 | 0.00000 ± 0.00000 | 0.006 ± 0.008 | 0.000 | 0.03 | 5.48 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
