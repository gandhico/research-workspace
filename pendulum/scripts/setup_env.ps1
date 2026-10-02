param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$QuanserPython = "C:\Quanser\0_libraries\python",
    [string]$QuanserApiWheelDir = "C:\Program Files\Quanser\QUARC\python",
    [switch]$SkipQuanserApi,
    [switch]$InstallRequirements
)

$ErrorActionPreference = "Stop"
$VenvPath = Join-Path $ProjectRoot ".venv"

if (-not (Test-Path -LiteralPath $VenvPath)) {
    python -m venv --system-site-packages $VenvPath
}

$env:QUANSER_PYTHON = $QuanserPython
$srcPath = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = "$srcPath;$QuanserPython;$env:PYTHONPATH"

if ((-not $SkipQuanserApi) -and (Test-Path -LiteralPath $QuanserApiWheelDir)) {
    & (Join-Path $VenvPath "Scripts\python.exe") -m pip install --no-index --find-links $QuanserApiWheelDir quanser_api
}

if ($InstallRequirements) {
    & (Join-Path $VenvPath "Scripts\python.exe") -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
}

Write-Host "Environment ready."
Write-Host "Activate with:"
Write-Host "  .\scripts\activate_env.ps1"
Write-Host "Then try:"
Write-Host "  python .\runners\run_offline_benchmark.py --duration 5"
Write-Host "  python .\runners\run_online_qube.py --mode sensor_check --hardware 0 --duration 5"
