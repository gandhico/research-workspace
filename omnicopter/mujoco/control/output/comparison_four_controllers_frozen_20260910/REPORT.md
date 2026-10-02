# Comparación pareada de cuatro controladores

| Controlador | Misiones aprobadas | RMSE posición media [m] | RMSE actitud media [°] | Saturación media |
|---|---:|---:|---:|---:|
| PD directo | 25/25 | 0.001029 | 0.0260 | 0.000% |
| CMG-PES directo | 25/25 | 0.011579 | 0.0629 | 0.000% |
| Nengo-PD | 25/25 | 0.001029 | 0.0260 | 0.000% |
| Nengo-CMG-PES | 25/25 | 0.011579 | 0.0629 | 0.000% |

## Conformidad de backend

| Par | Máx. Δ RMSE posición [m] | Máx. Δ RMSE actitud [°] | Máx. Δ pico motor [N] |
|---|---:|---:|---:|
| `pd_vs_nengo-pd` | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| `cmg-pes_vs_nengo-cmg-pes` | 9.762e-09 | 3.653e-07 | 2.047e-08 |

PD/Nengo-PD and CMG-PES/Nengo-CMG-PES are backend-conformance pairs. Controller benefit must be assessed between PD and CMG-PES, not inferred from backend equivalence.
