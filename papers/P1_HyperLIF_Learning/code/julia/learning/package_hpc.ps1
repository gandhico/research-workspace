param(
    [string]$Output = ""
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
if ([string]::IsNullOrWhiteSpace($Output)) {
    $Output = Join-Path $ProjectRoot 'hyperlif_julia_hpc_20260909.zip'
}
$Output = [IO.Path]::GetFullPath($Output)
$Staging = Join-Path ([IO.Path]::GetTempPath()) ('hyperlif_julia_hpc_' + [guid]::NewGuid().ToString('N'))
$Destination = Join-Path $Staging 'code\julia\learning'

try {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    foreach ($Name in @('Project.toml', 'Manifest.toml', 'README.md', 'train_hpc.jl', 'grid.jl',
                         'run_bundle.jl', 'preflight.jl', 'aggregate_results.jl', 'submit.sh',
                         'run_array.slurm')) {
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination $Destination
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'src') -Destination $Destination -Recurse
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'test') -Destination $Destination -Recurse

    $HpcDestination = Join-Path $Staging 'code\hpc'
    New-Item -ItemType Directory -Path $HpcDestination -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $ProjectRoot 'code\hpc\export_hdf5.py') -Destination $HpcDestination

    foreach ($Name in @('AGENTS.md',
                         'HYPERLIF_THEORY_LEARNING_AND_RESEARCH_PROGRAM_2026-09-09.md',
                         'THREE_LEARNING_MODES_MATHEMATICAL_NOTE_2026-09-09.md',
                         'THREE_STAGE_DEVELOPMENT_REPORT_2026-09-09.md',
                         'HPC_UPLOAD_AND_RUN_2026-09-09.md')) {
        Copy-Item -LiteralPath (Join-Path $ProjectRoot $Name) -Destination $Staging
    }

    if (Test-Path -LiteralPath $Output) {
        Remove-Item -LiteralPath $Output -Force
    }
    tar.exe -a -c -f $Output -C $Staging .
    if ($LASTEXITCODE -ne 0) { throw "tar.exe failed with exit code $LASTEXITCODE" }
    $SizeMiB = [math]::Round((Get-Item -LiteralPath $Output).Length / 1MB, 2)
    Write-Output "Created $Output ($SizeMiB MiB)"
}
finally {
    if (Test-Path -LiteralPath $Staging) {
        Remove-Item -LiteralPath $Staging -Recurse -Force
    }
}

