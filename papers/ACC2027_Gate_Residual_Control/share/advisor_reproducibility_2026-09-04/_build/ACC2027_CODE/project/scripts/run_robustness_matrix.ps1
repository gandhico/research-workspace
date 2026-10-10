param([double]$Duration = 45.0, [double]$Dt = 0.0005, [double]$Beta = 0.5)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Base = Join-Path $Root "results\runs\$Stamp`_robustness"
$Controllers = @('classical','online-pes-fixed','online-pes-adaptive')
foreach ($Seed in @(1,2,3,4,5)) {
    foreach ($Controller in $Controllers) {
        & $Py -m gra_control.cli simulate --platform x2 --controller $Controller `
            --mission hard45 --duration $Duration --dt $Dt --beta $Beta `
            --initial-angle-deg 10 --disturbance-torque 0.01 `
            --attitude-noise-std 0.002 --rate-noise-std 0.01 --seed $Seed `
            --output (Join-Path $Base ("x2\seed_$Seed\$Controller"))
        & $Py -m gra_control.cli simulate --platform cf2-rotor --controller $Controller `
            --mission hard45 --duration $Duration --dt $Dt --beta $Beta --actuator-scale 1.5 `
            --initial-angle-deg 10 --disturbance-torque 0.00001 `
            --attitude-noise-std 0.002 --rate-noise-std 0.01 --seed $Seed `
            --output (Join-Path $Base ("cf2_rotor\seed_$Seed\$Controller"))
    }
}
Write-Output "Robustness matrix saved under $Base"

