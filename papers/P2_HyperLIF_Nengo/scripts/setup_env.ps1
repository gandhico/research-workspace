# Create a local virtual environment and install dependencies.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
$venv = Join-Path $root ".venv"

if (-not (Test-Path $venv)) {
    Write-Host "Creating virtual environment at $venv" -ForegroundColor Cyan
    python -m venv $venv
}
$py = Join-Path $venv "Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $root "requirements.txt")
Write-Host "Environment ready. Python:" -ForegroundColor Green
& $py --version
& $py -c "import numpy, matplotlib, nengo; print('numpy', numpy.__version__); print('matplotlib', matplotlib.__version__); print('nengo', nengo.__version__)"
