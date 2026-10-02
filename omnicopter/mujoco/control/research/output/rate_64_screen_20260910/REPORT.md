# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| cmg_12 | 12 | 6/6 | 0.09306 ± 0.01896 | 4.342 ± 0.211 | 0.173 | 6.11 | 6.92 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
