# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 3/3 | 0.20206 ± 0.01166 | 6.019 ± 0.331 | 0.291 | 7.41 | 8.44 |
| legacy_12 | 12 | 3/3 | 0.08520 ± 0.00385 | 4.693 ± 0.276 | 0.141 | 6.15 | 8.47 |
| cmg_12 | 12 | 3/3 | 0.08378 ± 0.00447 | 4.357 ± 0.256 | 0.145 | 5.77 | 8.48 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
