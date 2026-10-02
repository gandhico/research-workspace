# Comparación pareada de cuatro controladores

| Controlador | Misiones aprobadas | RMSE posición media [m] | RMSE actitud media [°] | Saturación media |
|---|---:|---:|---:|---:|
| PD directo | 25/25 | 0.001029 | 0.0260 | 0.000% |
| CMG-PES directo | 25/25 | 0.011579 | 0.0629 | 0.000% |
| Nengo-PD | 25/25 | 0.001029 | 0.0260 | 0.000% |
| Nengo-CMG-PES | 25/25 | 0.011579 | 0.0629 | 0.000% |

PD/Nengo-PD and CMG-PES/Nengo-CMG-PES are backend-conformance pairs. Controller benefit must be assessed between PD and CMG-PES, not inferred from backend equivalence.

> **Provenance note:** the Nengo runs began before a telemetry-only addition (body rates and simulated sensor fields) to `missions.py`; therefore their mission-source hash differs from the two direct runs. Model, controller core, gains, gates and serialized mission definitions match. This batch is an engineering conformance result; rerun all four after the code freeze for the publication release.
