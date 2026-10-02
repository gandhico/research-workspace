# Representative paired mission metrics

Same seed, uncertainty draw, gusts, reference, controller and actuator limits.
The left outer elevon is jammed at zero at 32 s.

| Architecture | Attitude RMSE [deg] | Peak error [deg] | Post-fault RMSE [deg] | Allocation RMSE [deg/s^2] | Surface RMS [-] | Total variation [-] |
|---|---:|---:|---:|---:|---:|---:|
| Thesis grouped ACS | 2.1583 | 5.9031 | 2.4409 | 0.3204 | 0.02964 | 4.8992 |
| Distributed elevon QP | 2.1159 | 5.8421 | 2.3702 | 0.1683 | 0.02749 | 4.4288 |

> Evidence boundary: the control-effectiveness matrix is a synthetic research prior,
> not an identified EHEKATL, X-Plane, wind-tunnel or flight-test model.
