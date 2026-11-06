# Protocolo publicable de conexión y validación físico--virtual

## Pregunta científica

La validación no intenta demostrar que el modelo y el vehículo tienen números
idénticos. Intenta establecer, con incertidumbre trazable, que un conjunto de
parámetros identificado en ensayos independientes permite al gemelo predecir
datos físicos retenidos dentro de tolerancias pre-registradas.

Se separan tres afirmaciones:

1. **Conformidad geométrica:** marcos, posiciones, signos y numeración coinciden.
2. **Conformidad de software:** implementaciones directas y Nengo producen la
   misma orden para la misma entrada.
3. **Validez predictiva:** el gemelo reproduce trayectorias físicas no usadas
   para identificar parámetros.

La conformidad de software no demuestra validez física, y ajustar parámetros
con las mismas trayectorias utilizadas para evaluarlos no constituye validación.

## Arquitecturas que deben compararse

| Identificador | Ley PD | Residual CMG | PES | Propósito experimental |
|---|---|---|---|---|
| `pd` | Python/NumPy exacta | No | No | Línea base clásica. |
| `cmg-pes` | Python/NumPy exacta | CMG directa, 12 células | Actualización directa | Efecto del residual. |
| `nengo-pd` | Nodo Nengo exacto | No | No | Conformidad del backend Nengo. |
| `nengo-cmg-pes` | Nodo Nengo exacto | `NeuronType` CMG | `nengo.PES` nativo | Realización neuromórfica de la arquitectura completa. |

Los cuatro controladores comparten referencias, estados, ganancias, matriz de
actuación, asignador acotado, límites y frecuencia. Las comparaciones científicas
son PD contra CMG-PES. Las comparaciones directo contra Nengo son pruebas de
equivalencia de implementación, no cuatro leyes de control independientes.

## Conexión recomendada

```text
              reloj sincronizado + manifiesto de revisión
                              |
sensores físicos -> estimador -> interfaz común -> controlador seleccionado
      |                            |                    |
      +------ log sin editar ------+            wrench corporal
                                                        |
                             asignador 6x8 compartido/replicado
                                                        |
                     monitor de seguridad independiente -> ESC/motores
                              |
            mismas entradas y estado inicial -> MuJoCo en sombra
                              |
               logs físicos y virtuales en contrato común
```

La primera conexión debe ser **shadow mode**: MuJoCo recibe la condición inicial,
referencia y comandos reales, pero no manda comandos al vehículo. Después sigue
hardware-in-the-loop con motores desarmados o carga segura. El control cerrado en
vuelo sólo comienza cuando signos, escalas, tiempo, asignación y abortos han sido
verificados de forma independiente.

La capa de transporte puede ser MAVLink, ROS 2, UDP o la interfaz existente del
autopiloto. No debe entrar en las ecuaciones del controlador. Debe proporcionar:

- estado con timestamp de adquisición;
- referencia con identificador de misión;
- ocho órdenes y, cuando sea posible, RPM/empuje estimado por motor;
- voltaje/corriente, saturación y estado de armado;
- secuencia, pérdida de paquetes y timestamp de recepción;
- hash del conjunto de parámetros y versión del controlador.

## Marcos de coordenadas

MuJoCo usa el mundo de su XML y el cuerpo `drone`. La telemetría física debe
transformarse explícitamente a esos marcos antes de comparar:

```text
p^M = R^M_H (p^H - p^H_0)
R^M_BM = R^M_H R^H_BH R^BH_BM
omega^BM = R^BM_BH omega^BH
```

`R^M_H` transforma coordenadas del mundo de medición al mundo MuJoCo;
`R^BH_BM` registra el cuerpo MuJoCo con el cuerpo de IMU/autopiloto. Se obtienen mediante un
artefacto de calibración y varias poses estáticas, se congelan antes de las
misiones y deben tener determinante +1. No se permite escoger inversiones de eje
observando cuál trayectoria “se ve mejor”.

## Tiempo

Todos los datos deben conservar el timestamp de adquisición monotónico. Si el
autopiloto utiliza MAVLink, `TIMESYNC` permite estimar el offset entre relojes;
también se conserva el round-trip time. Para otro transporte se utiliza un
mecanismo equivalente. El retardo sensor--estimador--control--actuador se mide
por separado mediante excitación registrada.

El offset confirmatorio se obtiene del sincronizador, no ajustando las curvas.
La correlación posterior puede detectar problemas de tiempo, pero se etiqueta
como diagnóstico y no puede reemplazar el valor pre-registrado.

## Identificación de parámetros

| Grupo | Ensayo | Parámetros | Entra en MuJoCo como |
|---|---|---|---|
| Geometría | CAD, calibre y registro de marcos | posiciones, orientación IMU/rotores | `pos`, `quat/xyaxes` |
| Masa | báscula calibrada | masa total | `mass` o `inertial` |
| Centro de masa | suspensión en ≥3 orientaciones | vector COM y covarianza | `ipos` |
| Inercia | péndulo bifilar/trifilar o CAD reconciliado | tensor y ejes principales | `fullinertia`/`diaginertia` + `iquat` |
| Propulsión | barrido bidireccional por cada motor | fuerza, par, deadband, dispersión | ganancia/actuador identificado |
| Dinámica de motor | escalones y PRBS seguros | constante de tiempo, retardo | `filterexact`, delay o plugin |
| Sensores | reposo y excitación conocida | bias, ruido, escala, bandwidth | sensores y modelo del estimador |
| Aerodinámica | ventilador/túnel, varios ángulos y velocidades | arrastre y momento | elipsoide o wrench personalizado |

Cada fila del registro incluye revisión física, unidad, incertidumbre estándar,
método, condiciones, archivo fuente, hash, fecha y operador. El ajuste utiliza
un conjunto de identificación; la validación usa ensayos distintos.

## Cómo decidir si “tienen los mismos parámetros”

Para un parámetro directamente medible se reporta el estimado físico
`theta_h ± u_h` y el valor compilado `theta_m`. La aceptación requiere:

```text
|theta_m - theta_h| <= tolerancia(theta)
```

La tolerancia no es universal: combina incertidumbre de medida y sensibilidad
del controlador. Se perturba cada parámetro dentro de su incertidumbre y se mide
cuánto cambia la métrica de misión. Los parámetros de alta sensibilidad reciben
tolerancias más estrictas y prioridad de identificación.

Para parámetros no identificables individualmente, se valida la predicción del
modelo: aceleración, actitud, tasa y respuesta de motor deben caer dentro de la
banda predictiva en datos retenidos. Dos parámetros correlacionados no deben
declararse “correctos” sólo porque una trayectoria coincide.

## Secuencia para la próxima semana

| Fase | Vehículo | Control aplicado | Criterio para avanzar |
|---|---|---|---|
| 0 | Desarmado | Ninguno | Revisión física, firmware, hélices, signos y E-stop congelados. |
| 1 | Desarmado | Comandos mínimos individuales | Correspondencia 1--8, signo, eje, telemetría y límites confirmados. |
| 2 | Banco | Barridos/escalones | Curvas bidireccionales y retardos con repetibilidad e incertidumbre. |
| 3 | Estructura sujeta | PD, amplitud reducida | Marcos, asignador y sentidos de wrench confirmados. |
| 4 | Sombra | Los cuatro calculan; sólo PD gobierna | Equivalencia temporal y de comandos; residual observado y acotado. |
| 5 | Vuelo sujeto | PD; CMG con pesos congelados y autoridad mínima | Abortos, saturación y envolvente verificados. |
| 6 | Vuelo sujeto | CMG-PES online limitado | Mejora pareada sin degradar seguridad ni saturación. |
| 7 | Retenido | Orden aleatorizado y repeticiones | Datos de validación no usados para ajuste. |

El monitor de seguridad debe estar fuera de Nengo/PES y poder sustituir la orden
por cero/aterrizaje seguro ante pérdida de enlace, geocerca, actitud, tasa,
voltaje, saturación sostenida o comando no finito. No se arma si el empuje
reversible real, sus signos o sus límites no han sido comprobados.

## Diseño estadístico

- Pre-registrar hipótesis, misiones, métricas, exclusiones y límites antes de
  inspeccionar los ensayos confirmatorios.
- Usar bloques pareados: misma batería/voltaje, misión, condición de viento y
  perturbación; aleatorizar el orden de los controladores dentro de cada bloque.
- Separar pilotos de ajuste y repeticiones confirmatorias.
- Reportar cada repetición, diferencia pareada, intervalo de confianza, tamaño de
  efecto, saturación, energía, latencia, abortos y datos ausentes.
- No reutilizar pesos adaptados entre controladores o repeticiones salvo que ésa
  sea una hipótesis predefinida de transferencia.

Los límites de `hardware/provisional_validation_gates.json` son sólo para el
shakedown inicial. Los límites de publicación se congelan después de medir el
piso de ruido y la repetibilidad, pero antes de ejecutar el lote retenido.

## Artefactos reproducibles

- `physics/omnicopter_parameters.json`: registro canónico del gemelo.
- `physics/identification/parameter_measurements.csv`: resultados de identificación.
- `validation/COMMON_LOG_SCHEMA.md`: contrato común de datos.
- `hardware/validate_paired_logs.py`: comparación sincronizada físico--virtual.
- `control/verify_nengo_equivalence.py`: conformidad directa--Nengo.
- `control/compare_four_controllers.py`: campaña pareada de cuatro ejecuciones.

El paquete final de cada ensayo debe contener datos crudos inmutables, datos
convertidos, manifiesto, hashes, parámetros, código, ambiente, criterio de
aceptación, resultados y cualquier desviación del protocolo.
