param([double]$ActuatorScale = 1.5, [double]$Dt = 0.0005, [double]$Beta = 0.5)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Base = Join-Path $Root "results\runs\$Stamp`_cf2_rotor_matrix"
$Missions = @(
    @{Name='hard45'; Duration=45.0},
    @{Name='full3'; Duration=20.0},
    @{Name='roll'; Duration=20.0},
    @{Name='hardstep'; Duration=45.0}
)
$Controllers = @('classical','fixed-residual','adaptive-residual','online-pes-fixed','online-pes-adaptive')
foreach ($Mission in $Missions) {
    foreach ($Controller in $Controllers) {
        & $Py -m gra_control.cli simulate --platform cf2-rotor --controller $Controller `
            --mission $Mission.Name --duration $Mission.Duration --dt $Dt --beta $Beta `
            --actuator-scale $ActuatorScale --learning-rate 0.0008 --k-error 8 `
            --output (Join-Path $Base ($Mission.Name+'\'+$Controller))
    }
}
Write-Output "CF2 rotor matrix saved under $Base"

