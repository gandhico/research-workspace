# Run stages 0 through 7 headlessly; stop escalation on the first nonpass.
[CmdletBinding()]
param(
    [ValidateSet('pd', 'cmg-pes')]
    [string]$Controller = 'pd',
    [double]$Beta = 0.05,
    [double]$LearningRate = 0.0008,
    [double]$Leak = 0.000001,
    [string]$Output,
    [string]$Python,
    [switch]$DryRun
)
& (Join-Path $PSScriptRoot 'run.ps1') -Campaign -MaxStage 7 @PSBoundParameters
exit $LASTEXITCODE
