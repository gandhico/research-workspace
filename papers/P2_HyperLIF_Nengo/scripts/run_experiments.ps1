# Run all numbered experiments, regenerating every CSV and log in results/.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py (Join-Path $root "experiments\run_all.py")
