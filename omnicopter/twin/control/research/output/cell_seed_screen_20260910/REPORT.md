# Omnicopter CMG cell/seed screening

Synthetic mass, inertia, motor-lag/gain and external-wrench mismatch; controller actuation remains exclusively through the eight rotor controls.

| Controller | Cells | Runs passed | Position RMSE m | Attitude RMSE deg | Worst position m | Worst attitude deg | Max motor N |
|---|---:|---:|---:|---:|---:|---:|---:|
| pd | 0 | 6/6 | 0.13610 ± 0.02830 | 4.859 ± 0.234 | 0.235 | 6.69 | 6.90 |
| legacy_12 | 12 | 6/6 | 0.06530 ± 0.01295 | 3.810 ± 0.190 | 0.139 | 5.54 | 6.91 |
| cmg_12 | 12 | 6/6 | 0.09393 ± 0.01894 | 4.344 ± 0.211 | 0.176 | 6.15 | 6.92 |
| cmg_24 | 24 | 6/6 | 0.09385 ± 0.01903 | 4.344 ± 0.211 | 0.177 | 6.15 | 6.92 |
| cmg_48 | 48 | 6/6 | 0.09389 ± 0.01882 | 4.344 ± 0.211 | 0.176 | 6.16 | 6.92 |
| cmg_96 | 96 | 6/6 | 0.09391 ± 0.01890 | 4.344 ± 0.211 | 0.176 | 6.16 | 6.92 |
| cmg_192 | 192 | 6/6 | 0.09390 ± 0.01891 | 4.344 ± 0.211 | 0.176 | 6.16 | 6.92 |

This screen selects hypotheses for a larger held-out study; it is not evidence of aerodynamic or hardware performance.
