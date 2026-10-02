# Run stages 0 through 6 headlessly; stop escalation on the first nonpass.
[CmdletBinding()]
param(
    [string]$Output,
    [string]$Python,
    [switch]$DryRun
)
& (Join-Path $PSScriptRoot 'run.ps1') -Campaign -MaxStage 6 @PSBoundParameters
exit $LASTEXITCODE
