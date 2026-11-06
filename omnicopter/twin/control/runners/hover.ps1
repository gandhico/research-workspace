# Watch hover; add -Headless to run without a viewer.
[CmdletBinding()]
param(
    [switch]$Headless,
    [string]$Output,
    [string]$Python,
    [switch]$DryRun
)
& (Join-Path $PSScriptRoot 'run.ps1') -Mission 'hover' @PSBoundParameters
exit $LASTEXITCODE
