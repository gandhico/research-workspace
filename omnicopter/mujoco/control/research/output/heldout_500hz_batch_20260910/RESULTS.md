# Lote retenido CMG-PES del omnicóptero

Fecha: 2026-09-10. Simulación MuJoCo a 500 Hz; semillas retenidas 10, 11 y 12.

Este lote usa incertidumbre sintética de masa, inercia, ganancia/retardo de motor y fuerza/par externo. No representa todavía aerodinámica identificada ni validación de hardware.

## Misiones

| Misión | Propósito | Duración | Repeticiones por controlador |
|---|---|---:|---:|
| `hover_push` | Hover con impulso de velocidad a los 4 s; mide rechazo y recuperación. | 20 s | 3 |
| `attitude_x_45` | Giro +45° alrededor de X, mantenimiento y retorno; mide reorientación grande. | 28 s | 3 |
| `yaw_360_6s` | Giro completo de yaw en 6 s; mide seguimiento rápido y límites de actuación. | 16 s | 3 |

## Resultado por misión

Valores: media ± desviación estándar entre semillas.

| Misión | Controlador | Posición RMSE [m] | Actitud RMSE [°] | Completadas | Saturación máxima |
|---|---|---:|---:|---:|---:|
| `hover_push` | PD + feedforward | 0.2189 ± 0.0699 | 4.729 ± 1.353 | 3/3 | 0.0% |
| `hover_push` | CMG-PES actual (12) | 0.0927 ± 0.0273 | 3.666 ± 1.074 | 3/3 | 0.0% |
| `hover_push` | CMG-PES revisado (12) | 0.0899 ± 0.0271 | 3.403 ± 1.000 | 3/3 | 0.0% |
| `attitude_x_45` | PD + feedforward | 0.2224 ± 0.0859 | 4.694 ± 0.887 | 3/3 | 30.5% |
| `attitude_x_45` | CMG-PES actual (12) | 0.0940 ± 0.0343 | 3.637 ± 0.689 | 3/3 | 29.4% |
| `attitude_x_45` | CMG-PES revisado (12) | 0.1171 ± 0.0772 | 3.549 ± 0.671 | 3/3 | 27.8% |
| `yaw_360_6s` | PD + feedforward | 0.2134 ± 0.0718 | 4.592 ± 1.349 | 3/3 | 0.0% |
| `yaw_360_6s` | CMG-PES actual (12) | 0.0922 ± 0.0275 | 3.605 ± 1.057 | 3/3 | 0.0% |
| `yaw_360_6s` | CMG-PES revisado (12) | 0.0878 ± 0.0282 | 3.332 ± 0.990 | 3/3 | 0.0% |

## Resultado global

| Controlador | Posición RMSE [m] | Actitud RMSE [°] | Completadas | Casos con saturación |
|---|---:|---:|---:|---:|
| PD + feedforward | 0.2182 ± 0.0661 | 4.672 ± 1.055 | 9/9 | 1/9 |
| CMG-PES actual (12) | 0.0930 ± 0.0259 | 3.636 ± 0.829 | 9/9 | 1/9 |
| CMG-PES revisado (12) | 0.0983 ± 0.0456 | 3.428 ± 0.786 | 9/9 | 1/9 |

## Lectura

- Frente al PD, el CMG-PES revisado reduce el RMSE medio global de posición en 55.0% y el de actitud en 26.6%.
- Frente al CMG-PES actual, aumenta el RMSE medio global de posición en 5.7% y reduce el de actitud en 5.7%.
- Gana frente al PD en 9/9 casos de posición y 9/9 de actitud.
- Gana frente al CMG-PES actual en 8/9 casos de posición y 8/9 de actitud.
- Excepción importante: en semilla 10, `attitude_x_45`, el CMG-PES revisado fue peor que el actual; el PD y ambos residuales alcanzaron saturación. Esto apunta a introducir anti-windup/aprendizaje condicionado por autoridad antes de aumentar neuronas.

> **Definición de completada:** sin caída por altura, contacto ni valores no finitos. No significa que haya aprobado los umbrales nominales de seguimiento.

La conclusión es preliminar: tres semillas retenidas permiten detectar tendencias y fallos, pero no sostienen todavía una afirmación estadística ni una conclusión de vuelo.
