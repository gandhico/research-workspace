param([double]$Duration = 5.0, [double]$Dt = 0.0005, [double]$Beta = 0.5)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Base = Join-Path $Root "results\runs\$Stamp`_cf2_authority_sweep"
foreach ($Scale in @(1.0,1.1,1.2,1.25,1.3,1.4,1.5,2.0)) {
    foreach ($Controller in @('classical','online-pes-fixed','online-pes-adaptive')) {
        & $Py -m gra_control.cli simulate --platform cf2-rotor --controller $Controller `
            --mission hard45 --duration $Duration --dt $Dt --beta $Beta `
            --actuator-scale $Scale --learning-rate 0.0008 --k-error 8 `
            --output (Join-Path $Base ("scale_$Scale\$Controller"))
    }
}
Write-Output "CF2 authority sweep saved under $Base"

