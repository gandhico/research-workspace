# Regenerate every publication figure (PNG + PDF) from the results CSVs.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py (Join-Path $root "figures\make_figures.py")
