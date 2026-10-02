# APEX-v2 one-batch readout-head training smoke.
#
# This is G3 in the parity ladder. It freezes the forward architecture features
# and verifies that a PyTorch-style readout feature tensor can drive a finite,
# decreasing cross-entropy update through a linear head.

using Pkg

const DEFAULT_APEX_ROOT = raw"C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2"
const DEFAULT_CACHE = raw"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5"

function arg_value(name::AbstractString, default::AbstractString)
    prefix = "--$(name)="
    for arg in ARGS
        startswith(arg, prefix) && return arg[length(prefix)+1:end]
    end
    return default
end

arg_int(name::AbstractString, default::Integer) = parse(Int, arg_value(name, string(default)))
arg_float(name::AbstractString, default::Real) = parse(Float32, arg_value(name, string(default)))

Pkg.activate(arg_value("apex-root", DEFAULT_APEX_ROOT))

using CUDA
using Dates
using HDF5
using Printf
using Statistics

include(joinpath(@__DIR__, "APEXV2Parity.jl"))
using .APEXV2Parity

function normalize_architecture(arch::AbstractString)
    arch = lowercase(String(arch))
    arch == "ff" && return "dense"
    arch == "feedforward" && return "dense"
    arch == "rsnn" && return "recurrent"
    return arch
end

function load_first_batch_h5(cache_path::AbstractString, batch_size::Int)
    local x_raw, y_raw
    h5open(cache_path, "r") do fid
        x_raw = read(fid, "X_train")
        y_raw = Int.(read(fid, "y_train"))
    end
    n = min(batch_size, size(x_raw, 3))
    x_fbt = permutedims(Float32.(x_raw[:, :, 1:n]), (1, 3, 2))
    y = y_raw[1:n]
    n_classes = maximum(y_raw) + 1
    return CuArray(x_fbt), y, n_classes
end

function one_hot(labels::Vector{Int}, n_classes::Int)
    targets = zeros(Float32, n_classes, length(labels))
    for (b, label) in enumerate(labels)
        targets[label + 1, b] = 1.0f0
    end
    return CuArray(targets)
end

function batchnorm_features(features)
    mu = mean(features; dims=2)
    centered = features .- mu
    sigma = sqrt.(mean(centered .^ 2; dims=2) .+ 1.0f-5)
    return centered ./ sigma
end

function loss_and_probs(logits, targets)
    shifted = logits .- maximum(logits; dims=1)
    exps = exp.(shifted)
    probs = exps ./ sum(exps; dims=1)
    p_true = sum(probs .* targets; dims=1)
    loss = -sum(log.(p_true .+ 1.0f-8)) / Float32(size(logits, 2))
    return Float64(loss), probs
end

function main()
    cache_path = arg_value("cache", DEFAULT_CACHE)
    isfile(cache_path) || error("Cache not found: $(cache_path)")
    CUDA.functional() || error("CUDA is not functional; APEX-v2 smoke expects CUDA.")

    batch_size = arg_int("batch-size", 64)
    hidden_dim = arg_int("hidden-dim", 64)
    seed = arg_int("seed", 1)
    steps = arg_int("steps", 20)
    lr = arg_float("lr", 0.05f0)
    architecture = normalize_architecture(arg_value("architecture", "recurrent"))
    neuron = lowercase(arg_value("neuron", "hyperlif"))
    readout = lowercase(arg_value("readout", "hybrid_vr"))
    input_scale = arg_float("input-scale", 16.0f0)
    dt = arg_float("dt", 0.001f0)
    gamma = arg_float("gamma", 0.2f0)
    delay_kernel_size = arg_int("delay-kernel-size", 7)

    println("="^78)
    println("APEX-v2 READOUT TRAINING SMOKE")
    println("="^78)
    println("CACHE=", cache_path)
    @printf("arch=%s neuron=%s readout=%s batch=%d hidden=%d seed=%d steps=%d lr=%.5f\n",
            architecture, neuron, readout, batch_size, hidden_dim, seed, steps, lr)

    x_fbt, y_batch, n_classes = load_first_batch_h5(cache_path, batch_size)
    n_input = size(x_fbt, 1)
    actual_batch = size(x_fbt, 2)
    time_steps = size(x_fbt, 3)
    targets = one_hot(y_batch, n_classes)

    config = ParityConfig(dt=dt, input_scale=input_scale, gamma=gamma,
                          delay_kernel_size=delay_kernel_size)
    model = init_model(n_input, hidden_dim, n_classes, actual_batch;
                       architecture=architecture, neuron=neuron,
                       readout=readout, seed=seed, config=config)
    summary = forward_summary!(model, x_fbt, config)
    summary.finite || error("Forward features are not finite.")
    features = batchnorm_features(summary.features)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    results_dir = joinpath(dirname(dirname(@__DIR__)), "results", "apex_v2")
    mkpath(results_dir)
    csv_path = joinpath(results_dir, "apex_v2_readout_train_smoke_$(timestamp).csv")
    rows = String["step,loss,finite"]

    initial_loss = NaN
    final_loss = NaN
    for step in 0:steps
        logits = model.W_head * features
        logits .+= reshape(model.B_head, :, 1)
        loss, probs = loss_and_probs(logits, targets)
        finite = isfinite(loss)
        step == 0 && (initial_loss = loss)
        step == steps && (final_loss = loss)
        @printf("step=%02d loss=%.6f finite=%s\n", step, loss, string(finite))
        push!(rows, join((step, loss, finite), ","))
        finite || error("Non-finite readout loss at step $(step).")

        if step < steps
            err = (probs .- targets) ./ Float32(actual_batch)
            grad_W = err * transpose(features)
            grad_B = sum(err; dims=2)
            model.W_head .-= lr .* grad_W
            model.B_head .-= lr .* reshape(grad_B, :)
        end
    end

    open(csv_path, "w") do io
        for row in rows
            println(io, row)
        end
    end

    improved = final_loss < initial_loss
    println("CSV=", csv_path)
    @printf("APEX_V2_READOUT_TRAIN_SMOKE initial_loss=%.6f final_loss=%.6f improved=%s\n",
            initial_loss, final_loss, string(improved))
    improved || error("Readout training smoke did not decrease loss.")
    println("APEX_V2_READOUT_TRAIN_SMOKE_OK")
end

main()

