param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$QuanserPython = "C:\Quanser\0_libraries\python",
    [string]$QuanserApiWheelDir = "C:\Program Files\Quanser\QUARC\python"
)

$ErrorActionPreference = "Stop"
$VenvPath = Join-Path $ProjectRoot ".venv"

if (-not (Test-Path -LiteralPath $VenvPath)) {
    throw "Virtual environment not found at $VenvPath. Run .\scripts\setup_env.ps1 first."
}

$env:QUANSER_PYTHON = $QuanserPython
$env:QUANSER_API_WHEEL_DIR = $QuanserApiWheelDir
$srcPath = Join-Path $ProjectRoot "src"
$env:PYTHONPATH = "$srcPath;$QuanserPython;$env:PYTHONPATH"

. (Join-Path $VenvPath "Scripts\Activate.ps1")
