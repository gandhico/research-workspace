# Watch helix; add -Headless to run without a viewer.
[CmdletBinding()]
param(
    [switch]$Headless,
    [string]$Output,
    [string]$Python,
    [switch]$DryRun
)
& (Join-Path $PSScriptRoot 'run.ps1') -Mission 'helix' @PSBoundParameters
exit $LASTEXITCODE
