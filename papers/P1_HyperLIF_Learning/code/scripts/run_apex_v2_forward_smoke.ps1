$ErrorActionPreference = "Stop"

$Root = "C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures"
$Runner = Join-Path $Root "julia\apex_v2\apex_v2_forward_smoke.jl"

Write-Host ("=" * 78)
Write-Host "APEX-v2 PyTorch-parity forward smoke"
Write-Host ("=" * 78)

& julia $Runner `
    --batch-size=32 `
    --hidden-dim=64 `
    --seeds=1 `
    --architectures=dense,recurrent,delay `
    --neurons=lif,hyperlif,adaptive `
    --readouts=spike_count,membrane,gate,hybrid_gr,hybrid_vr,hybrid_vr_conductance `
    --delay-kernel-size=7

if ($LASTEXITCODE -ne 0) {
    throw "APEX-v2 forward smoke failed."
}
