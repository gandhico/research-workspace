param([double]$Dt = 0.0005, [double]$Beta = 0.5)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Base = Join-Path $Root "results\runs\$Stamp`_x2_paper_matrix"
$Missions = @(
    @{Name='hard45'; Duration=45.0},
    @{Name='full3'; Duration=20.0},
    @{Name='roll'; Duration=20.0},
    @{Name='hardstep'; Duration=45.0}
)
$Controllers = @('classical','fixed-residual','adaptive-residual','online-pes-fixed','online-pes-adaptive')
foreach ($Mission in $Missions) {
    foreach ($Controller in $Controllers) {
        $Out = Join-Path $Base ($Mission.Name + '\' + $Controller)
        & $Py -m gra_control.cli simulate --platform x2 --controller $Controller `
            --mission $Mission.Name --duration $Mission.Duration --dt $Dt --beta $Beta `
            --learning-rate 0.0008 --k-error 8 --k-rate 0 --output $Out
    }
}
Write-Output "X2 matrix saved under $Base"

