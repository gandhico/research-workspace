# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 1/1 | 0.11953 ± nan | 4.674 ± nan | 0.179 | 5.28 | 6.79 |
| legacy_12 | 12 | 1/1 | 0.05875 ± nan | 3.717 ± nan | 0.108 | 4.26 | 6.75 |
| cmg_12 | 12 | 1/1 | 0.08449 ± nan | 4.192 ± nan | 0.142 | 4.78 | 6.76 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
