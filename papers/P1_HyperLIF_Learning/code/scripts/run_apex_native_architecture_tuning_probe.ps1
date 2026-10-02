$ErrorActionPreference = "Stop"

$Root = "C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures"
$Runner = Join-Path $Root "julia\apex_shd_ranking_smoke.jl"
$ResultsDir = Join-Path $Root "results\apex"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Manifest = Join-Path $ResultsDir "apex_native_architecture_tuning_probe_$Stamp.csv"
"config,beta,gamma,architectures,summary_csv,epoch_csv,raw_csv" | Set-Content -LiteralPath $Manifest

$Configs = @(
    @{ Name = "beta010_gamma050_default"; Beta = "0.10"; Gamma = "0.50" },
    @{ Name = "beta010_gamma080_dense_best"; Beta = "0.10"; Gamma = "0.80" },
    @{ Name = "beta010_gamma120_stronger_gate"; Beta = "0.10"; Gamma = "1.20" },
    @{ Name = "beta005_gamma080_low_conductance"; Beta = "0.05"; Gamma = "0.80" },
    @{ Name = "beta020_gamma080_high_conductance"; Beta = "0.20"; Gamma = "0.80" }
)

foreach ($Config in $Configs) {
    Write-Host ("=" * 78)
    Write-Host "Native APEX architecture tuning probe: $($Config.Name)"
    Write-Host ("=" * 78)

    $Output = & julia $Runner `
        --epochs=3 `
        --max-train-batches=31 `
        --max-test-batches=12 `
        --batch-size=64 `
        --hidden-dim=128 `
        --readout-hidden=64 `
        --seeds=1 `
        --architectures=recurrent,delay `
        --models=hyperlif `
        --beta=$($Config.Beta) `
        --gamma=$($Config.Gamma) `
        --max-delay=3 2>&1

    $Output | ForEach-Object { Write-Host $_ }
    if ($LASTEXITCODE -ne 0) {
        throw "Native APEX architecture tuning probe failed: $($Config.Name)"
    }

    $RawCsv = (($Output | Select-String -Pattern '^CSV=' | Select-Object -Last 1).Line -replace '^CSV=', '').Trim()
    $EpochCsv = (($Output | Select-String -Pattern '^EPOCH_CSV=' | Select-Object -Last 1).Line -replace '^EPOCH_CSV=', '').Trim()
    $SummaryCsv = (($Output | Select-String -Pattern '^SUMMARY_CSV=' | Select-Object -Last 1).Line -replace '^SUMMARY_CSV=', '').Trim()

    "$($Config.Name),$($Config.Beta),$($Config.Gamma),recurrent+delay,$SummaryCsv,$EpochCsv,$RawCsv" | Add-Content -LiteralPath $Manifest
}

Write-Host "MANIFEST=$Manifest"
