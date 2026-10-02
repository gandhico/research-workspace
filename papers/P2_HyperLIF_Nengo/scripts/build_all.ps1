# End-to-end rebuild: experiments -> figures -> tables -> compile paper.
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
Write-Host "[1/4] Experiments" -ForegroundColor Cyan
& (Join-Path $here "run_experiments.ps1")
Write-Host "[2/4] Figures" -ForegroundColor Cyan
& (Join-Path $here "make_figures.ps1")
Write-Host "[3/4] Tables" -ForegroundColor Cyan
& (Join-Path $here "make_tables.ps1")
Write-Host "[4/4] Paper" -ForegroundColor Cyan
& (Join-Path $here "build_paper.ps1")
Write-Host "All steps complete." -ForegroundColor Green
