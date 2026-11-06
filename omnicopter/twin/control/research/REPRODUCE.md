# Reproducción de las misiones y lotes CMG-PES

Ejecutar en PowerShell. Cada directorio indicado en `--output` debe ser nuevo.

```powershell
Set-Location 'C:\Research\omnicopter\twin'
$Python = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$Missions = 'C:\Research\omnicopter\twin\control\missions.py'
$Study = 'C:\Research\omnicopter\twin\control\research\run_cell_seed_study.py'
$Summarize = 'C:\Research\omnicopter\twin\control\research\summarize_heldout_batch.py'
```

## Visualizar una misión nominal

```powershell
& $Python $Missions --mission hover_push --controller pd --view
& $Python $Missions --mission attitude_x_45 --controller cmg-pes --view
& $Python $Missions --mission yaw_360_6s --controller cmg-pes --view
```

## Campaña nominal completa de 25 misiones

```powershell
& $Python $Missions --controller pd --output '.\control\output\pd_reproduction'
& $Python $Missions --controller cmg-pes --output '.\control\output\cmg_pes_reproduction'
& $Python $Missions --controller nengo-pd --output '.\control\output\nengo_pd_reproduction'
& $Python $Missions --controller nengo-cmg-pes --output '.\control\output\nengo_cmg_pes_reproduction'
```

Verifique primero la equivalencia directa--Nengo:

```powershell
& $Python '.\control\verify_nengo_equivalence.py' `
    --steps 1000 `
    --output '.\control\output\nengo_equivalence.json'
```

Después consolide las cuatro campañas, en este orden:

```powershell
& $Python '.\control\compare_four_controllers.py' `
    '.\control\output\pd_reproduction' `
    '.\control\output\cmg_pes_reproduction' `
    '.\control\output\nengo_pd_reproduction' `
    '.\control\output\nengo_cmg_pes_reproduction' `
    --output '.\control\output\four_controller_comparison'
```

## Comparación de logs físicos y virtuales

Los dos CSV deben cumplir `validation/COMMON_LOG_SCHEMA.md` y estar convertidos a
los mismos marcos. El offset debe venir de la sincronización de relojes.

```powershell
& $Python '.\hardware\validate_paired_logs.py' `
    '.\hardware\data\physical_common.csv' `
    '.\hardware\data\twin_common.csv' `
    --time-offset-s 0.000000 `
    --warmup-s 2 `
    --gates '.\hardware\provisional_validation_gates.json' `
    --output '.\hardware\output\paired_validation'
```

## Lote retenido publicado en RESULTS.md

El runner compara automáticamente PD, CMG-PES canónico de 12 células y CMG-PES
revisado de 12 células.

```powershell
foreach ($Seed in 10, 11, 12) {
    & $Python $Study `
        --cells 12 `
        --seeds $Seed `
        --missions hover_push attitude_x_45 yaw_360_6s `
        --learning-rate 8 `
        --beta 0.75 `
        --timestep 0.002 `
        --output ".\control\research\output\reproduction_seed$Seed"
}
```

Consolidación:

```powershell
& $Python $Summarize `
    '.\control\research\output\reproduction_seed10' `
    '.\control\research\output\reproduction_seed11' `
    '.\control\research\output\reproduction_seed12' `
    --output '.\control\research\output\reproduction_batch'
```

## Verificación nominal a 500 Hz

Comprueba que la arquitectura revisada sea exactamente nula en equilibrio y no
degrade la línea base sin incertidumbre.

```powershell
& $Python $Study `
    --cells 12 `
    --seeds 0 `
    --missions hover yaw_360_6s `
    --learning-rate 8 `
    --beta 0.75 `
    --timestep 0.002 `
    --nominal `
    --output '.\control\research\output\nominal_reproduction'
```

## Barrido del número de células

Esta pantalla es rápida (200 Hz) y sólo selecciona hipótesis; cualquier finalista
debe repetirse a 500 Hz y con semillas retenidas.

```powershell
& $Python $Study `
    --cells 12 24 48 96 192 `
    --seeds 0 1 2 3 4 `
    --missions hover_push yaw_360_12s `
    --learning-rate 8 `
    --beta 0.75 `
    --timestep 0.005 `
    --output '.\control\research\output\cell_count_reproduction'
```
