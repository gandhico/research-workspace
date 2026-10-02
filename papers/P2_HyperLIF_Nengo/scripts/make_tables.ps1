# Regenerate every LaTeX table from the results CSVs and parameter dataclasses.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
& $py (Join-Path $root "tables\make_tables.py")
