[CmdletBinding()]
param(
    [double]$Beta = 0.05,
    [double]$LearningRate = 0.0008,
    [double]$Leak = 0.000001,
    [string]$Output,
    [string]$Python,
    [switch]$DryRun
)
& (Join-Path $PSScriptRoot 'run.ps1') -Campaign -MaxStage 7 -Controller cmg-pes @PSBoundParameters
exit $LASTEXITCODE
