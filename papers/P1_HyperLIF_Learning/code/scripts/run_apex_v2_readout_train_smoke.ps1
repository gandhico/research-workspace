$ErrorActionPreference = "Stop"

$Root = "C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures"
$Runner = Join-Path $Root "julia\apex_v2\apex_v2_readout_train_smoke.jl"

Write-Host ("=" * 78)
Write-Host "APEX-v2 readout-head training smoke"
Write-Host ("=" * 78)

& julia $Runner `
    --architecture=recurrent `
    --neuron=hyperlif `
    --readout=hybrid_vr `
    --batch-size=64 `
    --hidden-dim=64 `
    --seed=1 `
    --steps=20 `
    --lr=0.05

if ($LASTEXITCODE -ne 0) {
    throw "APEX-v2 readout-head training smoke failed."
}
