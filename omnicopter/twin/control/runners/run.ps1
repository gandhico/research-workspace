# Self-contained launcher. Single missions open the viewer; campaigns are headless.
[CmdletBinding(DefaultParameterSetName = 'Mission')]
param(
    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = 'Mission')]
    [ValidateSet('hover', 'quaternion_sign', 'translate_x', 'translate_y', 'translate_z', 'attitude_x_15', 'attitude_y_15', 'attitude_z_15', 'attitude_x_45', 'attitude_y_45', 'attitude_y_90', 'attitude_x_180', 'yaw_360', 'yaw_minus_360', 'spin_x_360', 'spin_y_360', 'circle', 'figure_eight', 'helix', 'circle_yaw_360', 'hover_push', 'circle_yaw_push', 'yaw_360_24s', 'yaw_360_12s', 'yaw_360_6s')]
    [string]$Mission,

    [Parameter(Mandatory = $true, ParameterSetName = 'Campaign')]
    [switch]$Campaign,

    [Parameter(ParameterSetName = 'Campaign')]
    [ValidateRange(0, 7)]
    [int]$MaxStage = 7,

    [Parameter(Mandatory = $true, ParameterSetName = 'List')]
    [switch]$List,

    [Parameter(ParameterSetName = 'Mission')]
    [switch]$Headless,

    [ValidateSet('pd', 'cmg-pes')]
    [string]$Controller = 'pd',
    [ValidateRange(0.0, 1.0)]
    [double]$Beta = 0.05,
    [ValidateRange(0.0, [double]::MaxValue)]
    [double]$LearningRate = 0.0008,
    [ValidateRange(0.0, [double]::MaxValue)]
    [double]$Leak = 0.000001,
    [string]$Output,
    [string]$Python = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$missionScript = Join-Path (Split-Path -Parent $PSScriptRoot) 'missions.py'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python not found: $Python. Supply -Python with a MuJoCo-enabled python.exe."
}
if (-not (Test-Path -LiteralPath $missionScript -PathType Leaf)) {
    throw "Mission script not found: $missionScript"
}
$pythonArguments = @($missionScript)
switch ($PSCmdlet.ParameterSetName) {
    'Mission' {
        $pythonArguments += @('--mission', $Mission)
        if (-not $Headless) { $pythonArguments += '--view' }
    }
    'Campaign' { $pythonArguments += @('--max-stage', [string]$MaxStage) }
    'List' { $pythonArguments += '--list' }
}
$pythonArguments += @('--controller', $Controller)
if ($Controller -eq 'cmg-pes') {
    $pythonArguments += @('--beta', [string]$Beta,
                          '--learning-rate', [string]$LearningRate,
                          '--leak', [string]$Leak)
}
if ($Output) { $pythonArguments += @('--output', $Output) }
if ($DryRun) {
    $quotedArguments = @($Python) + $pythonArguments | ForEach-Object {
        "'" + ([string]$_).Replace("'", "''") + "'"
    }
    Write-Output ('& ' + ($quotedArguments -join ' '))
    exit 0
}
& $Python @pythonArguments
exit $LASTEXITCODE
