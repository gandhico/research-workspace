$ErrorActionPreference = "Stop"

$Root = "C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures"
$Runner = Join-Path $Root "julia\apex_v2\apex_v2_train_eval_smoke.jl"

Write-Host ("=" * 78)
Write-Host "APEX-v2 three-seed train/eval preflight"
Write-Host ("=" * 78)

& julia $Runner `
    --architectures=recurrent,delay `
    --neurons=hyperlif,adaptive `
    --readout=hybrid_vr `
    --batch-size=64 `
    --hidden-dim=64 `
    --seed=1 `
    --seeds=3 `
    --epochs=2 `
    --max-train-batches=4 `
    --max-test-batches=2 `
    --lr=0.05

if ($LASTEXITCODE -ne 0) {
    throw "APEX-v2 three-seed train/eval preflight failed."
}
