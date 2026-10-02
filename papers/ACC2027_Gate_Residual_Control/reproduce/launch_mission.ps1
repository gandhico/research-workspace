# Launch one paper mission with the live MuJoCo viewer (or all ten nominal cells headless).
# Uses the project environment directly; no activation needed. Runs from the repository root.
#
#   powershell -ExecutionPolicy Bypass -File reproduce\launch_mission.ps1 -Platform x2 -Mission hard45 -Arm cmg
#   powershell -ExecutionPolicy Bypass -File reproduce\launch_mission.ps1 -Platform cf2 -Mission hover -Arm cmg -Disturbance x1
#   powershell -ExecutionPolicy Bypass -File reproduce\launch_mission.ps1 -Platform x2 -Mission full3 -Noise realistic -Seed 3
#   powershell -ExecutionPolicy Bypass -File reproduce\launch_mission.ps1 -AllNominal       # 20 runs headless, each checked vs the paper
param(
    [ValidateSet('x2', 'cf2')] [string]$Platform = 'x2',
    [ValidateSet('roll', 'full3', 'hard45', 'hardstep', 'yaw360', 'hover')] [string]$Mission = 'hard45',
    [ValidateSet('pdff', 'cmg')] [string]$Arm = 'cmg',
    [ValidateSet('none', 'moderate', 'realistic')] [string]$Noise = 'none',
    [int]$Seed = 1,
    [ValidateSet('none', 'x0.5', 'x1', 'x2')] [string]$Disturbance = 'none',
    [double]$Duration = 45,
    [double]$Realtime = 1,
    [switch]$NoViewer,
    [switch]$AllNominal
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { throw "Python environment not found: $py" }
Set-Location $root

function Invoke-Mission([string[]]$extra) {
    & $py (Join-Path $root 'reproduce\run_mission_viewer.py') @extra
    if ($LASTEXITCODE -ne 0) { throw "Run failed: $($extra -join ' ')" }
}

if ($AllNominal) {
    foreach ($p in @('x2', 'cf2')) {
        foreach ($m in @('roll', 'full3', 'hard45', 'hardstep', 'yaw360')) {
            foreach ($a in @('pdff', 'cmg')) {
                Write-Output "=== $p $m $a"
                Invoke-Mission @('--platform', $p, '--mission', $m, '--arm', $a, '--no-viewer')
            }
        }
    }
    return
}

$argsList = @('--platform', $Platform, '--mission', $Mission, '--arm', $Arm, '--noise', $Noise, '--seed', "$Seed",
              '--disturbance', $Disturbance, '--duration', "$Duration", '--realtime', "$Realtime")
if ($NoViewer) { $argsList += '--no-viewer' }
Invoke-Mission $argsList
