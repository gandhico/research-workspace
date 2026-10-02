$ErrorActionPreference = "Stop"

$Root = "C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures"
$Runner = Join-Path $Root "julia\apex_shd_ranking_smoke.jl"

Write-Host ("=" * 78)
Write-Host "APEX architecture-transfer preflight: recurrent + delay"
Write-Host ("=" * 78)

& julia $Runner `
    --epochs=3 `
    --max-train-batches=31 `
    --max-test-batches=12 `
    --batch-size=64 `
    --hidden-dim=128 `
    --readout-hidden=64 `
    --seeds=3 `
    --architectures=recurrent,delay `
    --models=lif,hyperlif `
    --beta=0.10 `
    --gamma=0.80 `
    --max-delay=3

if ($LASTEXITCODE -ne 0) {
    throw "APEX architecture-transfer preflight failed."
}
