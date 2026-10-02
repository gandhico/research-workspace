# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| cmg_12 | 12 | 1/1 | 0.08422 ± 0.00000 | 4.189 ± 0.000 | 0.141 | 4.71 | 6.76 |
| cmg_48 | 48 | 1/1 | 0.08372 ± 0.00000 | 4.192 ± 0.000 | 0.139 | 4.76 | 6.76 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
