$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$Platforms = @('cf2', 'cf2-rotor', 'x2', 'pendulum', 'hover3dof', 'qcar')
foreach ($Platform in $Platforms) {
    & $Py -m gra_control.cli simulate --platform $Platform --controller adaptive-residual --mission hover --duration 0.5
}
