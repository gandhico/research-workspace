param(
    [double]$Duration = 45.0,
    [double]$Dt = 0.0005,
    [string]$Methods = 'classical,fixed_gate,online_pes,eprop_anneal'
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$LegacyDir = 'C:\Research\papers\P3_Gate_Residual\learned\code\experiments\controller_benchmarks'
$LegacyScript = Join-Path $LegacyDir 'learned_gate_experiment.py'
if (-not (Test-Path -LiteralPath $LegacyScript)) {
    throw "Historical learned runner not found: $LegacyScript"
}
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$OutputDir = Join-Path $ProjectRoot "results\legacy\$Stamp`_skydio_learned_blend"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$OutputJson = Join-Path $OutputDir 'results.json'
Push-Location $LegacyDir
try {
    & $Py $LegacyScript --quad skydio_x2 --mission hard45 --sim-time $Duration --dt $Dt `
        --methods $Methods --lr 0.0008 --k-err 8.0 --k-rate 0.0 --leak 0.0 --out $OutputJson
}
finally {
    Pop-Location
}
Get-FileHash -Algorithm SHA256 -LiteralPath $LegacyScript,$OutputJson |
    Format-Table -AutoSize | Out-String | Set-Content -LiteralPath (Join-Path $OutputDir 'sha256.txt')
@'
This reproduces the historical Skydio learned NEURAL-BLENDING experiment.
It uses xfrc_applied rather than the X2 rotor actuator path and adapts online on
the evaluation trajectory. Do not label this result actuator-faithful residual
augmentation. Use it as legacy evidence while the additive rotor-path matrix runs.
'@ | Set-Content -LiteralPath (Join-Path $OutputDir 'LIMITATIONS.txt')
Write-Output "Saved legacy reproduction under $OutputDir"

