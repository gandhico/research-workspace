param([double]$Duration = 10.0, [double]$Beta = 0.5)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Base = Join-Path $Root "results\runs\$Stamp`_cross_platform"
foreach ($Platform in @('pendulum','hover3dof','qcar')) {
    foreach ($Controller in @('classical','fixed-residual','adaptive-residual','online-pes-fixed','online-pes-adaptive')) {
        & $Py -m gra_control.cli simulate --platform $Platform --controller $Controller `
            --duration $Duration --beta $Beta --output (Join-Path $Base ($Platform+'\'+$Controller))
    }
}
Write-Output "Cross-platform integration matrix saved under $Base"

