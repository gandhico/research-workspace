# Build the paper: pdflatex -> bibtex -> pdflatex x2.
# Locates pdflatex on PATH, or in a user-scope MiKTeX install.
$ErrorActionPreference = "Stop"

function Find-PdfLatex {
    $cmd = Get-Command pdflatex -ErrorAction SilentlyContinue
    if ($cmd) { return (Split-Path $cmd.Source) }
    $cands = @(
        "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin\x64",
        "$env:LOCALAPPDATA\Programs\MiKTeX\miktex\bin"
    )
    foreach ($c in $cands) { if (Test-Path (Join-Path $c 'pdflatex.exe')) { return $c } }
    $hit = Get-ChildItem "$env:LOCALAPPDATA\Programs\MiKTeX" -Filter pdflatex.exe -Recurse `
        -ErrorAction SilentlyContinue -File | Select-Object -First 1
    if ($hit) { return $hit.Directory.FullName }
    throw "pdflatex not found. Install MiKTeX (winget install MiKTeX.MiKTeX) or TeX Live."
}

$bin = Find-PdfLatex
if ($env:Path -notlike "*$bin*") { $env:Path = "$bin;$env:Path" }

$paperDir = Join-Path $PSScriptRoot "..\paper"
Push-Location $paperDir
try {
    Write-Host "Building paper in $((Resolve-Path .).Path) using $bin" -ForegroundColor Cyan
    pdflatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
    bibtex main | Out-Null
    pdflatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
    pdflatex -interaction=nonstopmode -halt-on-error main.tex | Out-Null
    if (Test-Path "main.pdf") {
        $pdf = (Resolve-Path "main.pdf").Path
        Write-Host "OK -> $pdf" -ForegroundColor Green
    } else {
        throw "main.pdf was not produced; inspect paper/main.log"
    }
}
finally {
    Pop-Location
}
