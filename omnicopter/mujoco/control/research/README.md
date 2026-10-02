# Investigación de control residual neuromórfico del omnicóptero

Este directorio mantiene las extensiones de investigación separadas del
controlador CMG-PES canónico. El objetivo es comparar arquitecturas bajo el
mismo modelo, las mismas perturbaciones y semillas pareadas.

## Principios de la arquitectura transferible

1. El PD geométrico y el feedforward siguen siendo la línea base estable.
2. El aprendizaje sólo añade un wrench corporal residual de seis dimensiones.
3. Las entradas neuronales se centran en el equilibrio; el residual es exactamente
   cero cuando el error es cero.
4. Las células positivas/negativas están pareadas y la tasa PES se normaliza por
   número de células.
5. El residual se proyecta sobre el margen real de los ocho motores antes de
   aplicarse; no puede exigir una actuación físicamente imposible.
6. Las comparaciones usan semillas pareadas y separan selección de hiperparámetros
   de validación retenida.
7. Una perturbación sintética sirve para probar robustez de software, no para
   afirmar fidelidad aerodinámica ni preparación de vuelo.

## Programa de misiones

| Familia | Misiones actuales | Propiedad evaluada |
|---|---|---|
| Equilibrio nominal | `hover`, `quaternion_sign` | Preservación de la línea base y continuidad quaternion. |
| Traslación | `translate_x/y/z` | Control independiente de posición. |
| Actitud | `attitude_x/y/z_15`, `attitude_x/y_45`, `attitude_y_90`, `attitude_x_180` | Reorientación pequeña y grande. |
| Rotación completa | `yaw_360`, `yaw_minus_360`, `spin_x/y_360` | Maniobrabilidad omnidireccional. |
| Trayectorias | `circle`, `figure_eight`, `helix`, `circle_yaw_360` | Seguimiento acoplado de posición y actitud. |
| Perturbación | `hover_push`, `circle_yaw_push` | Rechazo y recuperación. |
| Envolvente de tasa | `yaw_360_24s/12s/6s` | Efecto de velocidad y saturación. |

## Evidencia mínima necesaria para una publicación sólida

- Congelar XML, código, unidades, límites de motor y criterios de aceptación.
- Identificar en banco empuje/RPM, par de reacción, constante de tiempo y dispersión
  entre motores; identificar masa, centro de masa e inercia del vehículo.
- Reemplazar el viento sintético por un modelo validado o datos de túnel/ventilador.
- Ejecutar al menos 30 semillas de desarrollo y 30 semillas retenidas, pareadas
  entre controladores, sobre el conjunto completo de misiones.
- Reportar intervalos de confianza, tamaño de efecto, fallos, saturación, energía,
  tiempo de cómputo y recuperación, no sólo RMSE promedio.
- Hacer ablaciones: PES congelado, centrado de equilibrio, pares de células,
  heterogeneidad, proyección de margen y conteo de células.
- Validar progresivamente: software-in-the-loop, hardware-in-the-loop, vehículo
  sujeto y finalmente vuelo, con límites y abortos independientes del aprendizaje.

La evidencia actual indica que aumentar células por sí solo no mejora este problema:
12, 48 y 192 células dieron resultados casi iguales en la pantalla inicial. La
prioridad técnica es tratar saturación, enriquecer las señales con estado de motor y
modelar la aerodinámica identificada; después se vuelve a estudiar la capacidad.
