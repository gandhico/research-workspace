param(
    [double]$Duration = 30.0,
    [double]$BalanceDuration = 20.0,
    [double]$MaxDuration = 90.0,
    [int]$Trials = 3,
    [double]$ResidualCapV = 0.35,
    [string]$Label = "paper_nominal"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $root "runners\twin_acc2027_gate_residual.py"
$pythonCandidates = @(
    "C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe",
    (Join-Path $root ".venv\Scripts\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $python) {
    throw "No compatible Python was found. The Quanser environment is required."
}

$controllers = @(
    "classical",
    "fixed-residual",
    "adaptive-residual",
    "online-pes-fixed",
    "online-pes-adaptive"
)

Write-Host "QLabs must be running with the QUBE Servo 3 pendulum scene."
Write-Host "Every run uses hardware=0 and terminates at zero voltage."
for ($trial = 1; $trial -le $Trials; $trial++) {
    foreach ($controller in $controllers) {
        $runLabel = "${Label}_trial${trial}"
        Write-Host "[$trial/$Trials] $controller"
        & $python $runner `
            --controller $controller `
            --duration $Duration `
            --balance-duration $BalanceDuration `
            --max-duration $MaxDuration `
            --residual-cap-v $ResidualCapV `
            --label $runLabel
        if ($LASTEXITCODE -ne 0) {
            throw "Runner failed for $controller, trial $trial."
        }
    }
}

Write-Host "Matrix complete. Aggregate with:"
Write-Host "  python .\tools\summarize_acc2027_twin.py --label $Label"
