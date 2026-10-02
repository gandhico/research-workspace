# Comparación pareada de cuatro controladores

| Controlador | Misiones aprobadas | RMSE posición media [m] | RMSE actitud media [°] | Saturación media |
|---|---:|---:|---:|---:|
| PD directo | 25/25 | 0.001029 | 0.0260 | 0.000% |
| CMG-PES canónico directo | 25/25 | 0.011579 | 0.0629 | 0.000% |
| Nengo-PD | 25/25 | 0.001029 | 0.0260 | 0.000% |
| Nengo-CMG-PES canónico | 25/25 | 0.011579 | 0.0629 | 0.000% |

## Conformidad de backend

| Par | Máx. Δ RMSE posición [m] | Máx. Δ RMSE actitud [°] | Máx. Δ pico motor [N] |
|---|---:|---:|---:|
| `pd_vs_nengo-pd` | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| `cmg-pes_vs_nengo-cmg-pes` | 9.762e-09 | 3.653e-07 | 2.047e-08 |

PD/Nengo-PD y CMG-PES canónico/Nengo-CMG-PES son pares de conformidad entre backends. El beneficio del controlador debe evaluarse comparando PD con CMG-PES; no se deduce de la equivalencia entre backends.

## Límite de interpretación

Esta tabla corresponde a una campaña nominal con coincidencia exacta entre modelo y planta; no constituye una clasificación universal de controladores. La media agregada incluye el transitorio de arranque del CMG-PES canónico. El rechazo de perturbaciones debe informarse en una ventana posterior a la perturbación, y la robustez ante incertidumbre de planta debe evaluarse con la campaña *held-out* de semillas. La arquitectura de investigación revisada, centrada en el equilibrio, no forma parte de las cuatro variantes de esta tabla.
