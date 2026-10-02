$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Paper = Join-Path $Root 'paper'
$Tex = 'acc2027_neuromorphic_gate_residual_draft.tex'
$Pdf = 'acc2027_neuromorphic_gate_residual_draft.pdf'
$OutputDir = Join-Path $Root 'output\pdf'
$BuildDir = Join-Path $Root 'tmp\paper_build'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$BuildStem = "acc2027_cmg_build_$Stamp"
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

Push-Location $Paper
try {
    $OutputDirectoryArg = "-output-directory=$BuildDir"
    $JobNameArg = "-jobname=$BuildStem"
    & pdflatex '-interaction=nonstopmode' '-halt-on-error' `
        $OutputDirectoryArg $JobNameArg $Tex
    if ($LASTEXITCODE -ne 0) { throw "First pdflatex pass failed with exit code $LASTEXITCODE" }
    & pdflatex '-interaction=nonstopmode' '-halt-on-error' `
        $OutputDirectoryArg $JobNameArg $Tex
    if ($LASTEXITCODE -ne 0) { throw "Second pdflatex pass failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$SourcePdf = Join-Path $BuildDir "$BuildStem.pdf"
$CanonicalPdf = Join-Path $OutputDir $Pdf
try {
    Copy-Item -LiteralPath $SourcePdf -Destination $CanonicalPdf -Force -ErrorAction Stop
    Write-Output "Built $CanonicalPdf"
}
catch [System.IO.IOException] {
    $FallbackPdf = Join-Path $OutputDir "acc2027_cmg_residual_draft_$Stamp.pdf"
    Copy-Item -LiteralPath $SourcePdf -Destination $FallbackPdf -ErrorAction Stop
    Write-Warning "The canonical output PDF is open or locked; wrote $FallbackPdf instead."
}
