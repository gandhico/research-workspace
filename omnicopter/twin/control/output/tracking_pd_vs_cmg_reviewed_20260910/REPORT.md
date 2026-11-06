# Señales de seguimiento PD vs CMG-PES

Las ventanas de las misiones con impulso comienzan en el instante del impulso; las demás usan la misión completa.

| Misión/ventana | Posición PD [m] | Posición CMG [m] | Cambio | Actitud PD [°] | Actitud CMG [°] | Cambio |
|---|---:|---:|---:|---:|---:|---:|
| `hover` (completa) | 0.000000 | 0.015564 | n/a | 0.0000 | 0.0000 | n/a |
| `hover_push` (desde 4 s) | 0.018088 | 0.010551 | +41.7% | 0.4412 | 0.2929 | +33.6% |
| `circle_yaw_push` (desde 22 s) | 0.012024 | 0.006276 | +47.8% | 0.2941 | 0.1967 | +33.1% |
| `yaw_360_6s` (completa) | 0.000000 | 0.014688 | n/a | 0.0110 | 0.5842 | -5228.5% |

Un cambio positivo significa reducción de error con CMG-PES; uno negativo, degradación. `n/a` indica que el error PD está por debajo del piso numérico elegido, por lo que un cociente porcentual sería engañoso.
