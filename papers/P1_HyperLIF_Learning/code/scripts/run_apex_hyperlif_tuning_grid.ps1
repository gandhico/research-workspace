$ErrorActionPreference = "Stop"

$Root = "C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures"
$Runner = Join-Path $Root "julia\apex_shd_ranking_smoke.jl"
$ResultsDir = Join-Path $Root "results\apex"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Manifest = Join-Path $ResultsDir "apex_hyperlif_tuning_grid_$Stamp.csv"
"config,beta,gamma,summary_csv,epoch_csv,raw_csv" | Set-Content -LiteralPath $Manifest

$Configs = @(
    @{ Name = "beta010_gamma050_baseline"; Beta = "0.10"; Gamma = "0.50" },
    @{ Name = "beta005_gamma050_low_conductance"; Beta = "0.05"; Gamma = "0.50" },
    @{ Name = "beta020_gamma050_high_conductance"; Beta = "0.20"; Gamma = "0.50" },
    @{ Name = "beta010_gamma030_weak_gate"; Beta = "0.10"; Gamma = "0.30" },
    @{ Name = "beta010_gamma080_strong_gate"; Beta = "0.10"; Gamma = "0.80" }
)

foreach ($Config in $Configs) {
    Write-Host ("=" * 78)
    Write-Host "APEX HyperLIF tuning: $($Config.Name)"
    Write-Host ("=" * 78)

    $Output = & julia $Runner `
        --epochs=3 `
        --max-train-batches=31 `
        --max-test-batches=12 `
        --batch-size=64 `
        --hidden-dim=128 `
        --readout-hidden=64 `
        --seeds=3 `
        --models=hyperlif `
        --beta=$($Config.Beta) `
        --gamma=$($Config.Gamma) 2>&1

    $Output | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) {
        throw "APEX tuning config failed: $($Config.Name)"
    }

    $RawCsv = (($Output | Select-String -Pattern '^CSV=' | Select-Object -Last 1).Line -replace '^CSV=', '').Trim()
    $EpochCsv = (($Output | Select-String -Pattern '^EPOCH_CSV=' | Select-Object -Last 1).Line -replace '^EPOCH_CSV=', '').Trim()
    $SummaryCsv = (($Output | Select-String -Pattern '^SUMMARY_CSV=' | Select-Object -Last 1).Line -replace '^SUMMARY_CSV=', '').Trim()

    "$($Config.Name),$($Config.Beta),$($Config.Gamma),$SummaryCsv,$EpochCsv,$RawCsv" | Add-Content -LiteralPath $Manifest
}

Write-Host "MANIFEST=$Manifest"
