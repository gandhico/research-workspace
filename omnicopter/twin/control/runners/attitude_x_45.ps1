# Watch attitude_x_45; add -Headless to run without a viewer.
[CmdletBinding()]
param(
    [switch]$Headless,
    [string]$Output,
    [string]$Python,
    [switch]$DryRun
)
& (Join-Path $PSScriptRoot 'run.ps1') -Mission 'attitude_x_45' @PSBoundParameters
exit $LASTEXITCODE
