# Generic launcher for the Aero2 residual runner. Passes all CLI args through.
# Uses the recovered HyperLIF/Quanser environment and resolves this repository
# relative to the script, so the launcher remains valid if the repo moves.
#   .\scripts\run_residual.ps1 --controller smc --variant yawboost --residual-mode gate ...
$ErrorActionPreference = "Stop"
$proj = Split-Path -Parent $PSScriptRoot
$python = "C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Recovered HyperLIF Python was not found: $python"
}

$cleanCandidates = @(
    $env:AERO2_CLEAN,
    "C:\Research\aero2_clean",
    "C:\02_Research\01_Robotics_Quanser\01_Aero2\aero2_clean",
    "D:\NMSU_backups\Backup\02_Research\01_Robotics_Quanser\01_Aero2\aero2_clean"
) | Where-Object { $_ }

$clean = $cleanCandidates | Where-Object {
    $probe = [System.IO.Path]::Combine($_, "M7_Aero2_Linear_Controllers", "src", "M7_aero2_simulink_2dof_pd_replicate.py")
    Test-Path -LiteralPath $probe -ErrorAction SilentlyContinue
} | Select-Object -First 1

if (-not $clean) {
    throw @"
The Aero2 residual runner is present, but its required aero2_clean controller tree is missing.
Expected M7_Aero2_Linear_Controllers and M8_Aero2_Nonlinear_Controllers under one of:
$($cleanCandidates -join "`n")

Reconnect the backup disk or restore aero2_clean, then set:
  `$env:AERO2_CLEAN = 'C:\actual\path\to\aero2_clean'
and rerun this command.
"@
}

$env:AERO2_CLEAN = $clean
$env:PYTHONPATH = (@($proj, $clean, $env:PYTHONPATH) | Where-Object { $_ }) -join ";"

Push-Location -LiteralPath $proj
try {
    & $python -u .\runners\run_aero2_residual.py @args
    if ($LASTEXITCODE -ne 0) {
        throw "Aero2 residual runner exited with code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
