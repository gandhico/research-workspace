$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Runner = Join-Path $Root "julia\apex_v2\apex_v2_shared_weight_trace_compare.jl"

julia $Runner `
    --architecture=recurrent `
    --neuron=hyperlif `
    --readout=hybrid_vr `
    --batch-size=32 `
    --hidden-dim=64 `
    --seed=1 `
    --feature-tol=1e-4 `
    --logit-tol=1e-3
