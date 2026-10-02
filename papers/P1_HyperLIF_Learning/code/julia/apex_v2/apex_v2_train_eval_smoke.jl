# APEX-v2 bounded train/eval smoke over real SHD train/test batches.
#
# This is G4 for the PyTorch-parity APEX-v2 ladder. The recurrent/delay trunk is
# kept fixed after the shared-weight forward gate; only the readout head is
# trained. This tests whether portable HyperLIF/Adaptive HyperLIF features can
# support stable multi-batch learning in Julia/APEX-v2 before any full trunk
# training or paper-grade multi-seed claim.

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
arg_list(name::AbstractString, default::AbstractString) = filter(!isempty, strip.(split(lowercase(arg_value(name, default)), ",")))

Pkg.activate(arg_value("apex-root", DEFAULT_APEX_ROOT))

using CUDA
using Dates
using HDF5
using Printf
using Random
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

function load_split_h5(cache_path::AbstractString, split::AbstractString)
    x_key = split == "train" ? "X_train" : "X_test"
    y_key = split == "train" ? "y_train" : "y_test"
    local x_raw, y_raw
    h5open(cache_path, "r") do fid
        x_raw = Float32.(read(fid, x_key))
        y_raw = Int.(read(fid, y_key))
    end
    return x_raw, y_raw
end

function make_batch(x_raw, idxs::UnitRange{Int})
    x_view = view(x_raw, :, :, idxs)
    return CuArray(permutedims(Float32.(x_view), (1, 3, 2)))
end

function make_labels(y_raw, idxs::UnitRange{Int})
    return y_raw[collect(idxs)]
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

function count_correct(logits, labels::Vector{Int})
    logits_cpu = Array(logits)
    correct = 0
    for b in 1:length(labels)
        pred = findmax(view(logits_cpu, :, b))[2] - 1
        correct += pred == labels[b] ? 1 : 0
    end
    return correct
end

function batch_indices(total::Int, batch_size::Int, max_batches::Int)
    n_batches = min(max_batches, total ÷ batch_size)
    return [((b - 1) * batch_size + 1):(b * batch_size) for b in 1:n_batches]
end

function run_pass!(model::ParityModel, config::ParityConfig, x_raw, y_raw;
                   n_classes::Int, batch_size::Int, max_batches::Int,
                   train::Bool, lr::Float32)
    total_loss = 0.0
    total_correct = 0
    total_seen = 0
    total_events = 0.0
    total_gate = 0.0
    nan_batches = 0
    batches = batch_indices(length(y_raw), batch_size, max_batches)

    for idxs in batches
        x_batch = make_batch(x_raw, idxs)
        labels = make_labels(y_raw, idxs)
        targets = one_hot(labels, n_classes)
        summary = forward_summary!(model, x_batch, config)
        features = batchnorm_features(summary.features)
        logits = model.W_head * features
        logits .+= reshape(model.B_head, :, 1)
        loss, probs = loss_and_probs(logits, targets)
        finite = summary.finite && isfinite(loss)
        nan_batches += finite ? 0 : 1
        finite || continue

        total_loss += loss
        total_correct += count_correct(logits, labels)
        total_seen += length(labels)
        total_events += summary.events_per_sample
        total_gate += summary.gate_mean

        if train
            err = (probs .- targets) ./ Float32(length(labels))
            grad_W = err * transpose(features)
            grad_B = sum(err; dims=2)
            model.W_head .-= lr .* grad_W
            model.B_head .-= lr .* reshape(grad_B, :)
        end
    end

    n = length(batches)
    return (
        batches = n,
        loss = n == 0 ? NaN : total_loss / n,
        accuracy = total_seen == 0 ? NaN : total_correct / total_seen,
        correct = total_correct,
        seen = total_seen,
        events_per_sample = n == 0 ? NaN : total_events / n,
        gate_mean = n == 0 ? NaN : total_gate / n,
        nan_batches = nan_batches,
        stable = nan_batches == 0 && total_seen > 0,
    )
end

function csv_escape(x)
    s = string(x)
    return occursin(",", s) ? "\"" * replace(s, "\"" => "\"\"") * "\"" : s
end

function main()
    cache_path = arg_value("cache", DEFAULT_CACHE)
    isfile(cache_path) || error("Cache not found: $(cache_path)")
    CUDA.functional() || error("CUDA is not functional; APEX-v2 train/eval smoke expects CUDA.")

    batch_size = arg_int("batch-size", 64)
    hidden_dim = arg_int("hidden-dim", 64)
    epochs = arg_int("epochs", 2)
    max_train_batches = arg_int("max-train-batches", 4)
    max_test_batches = arg_int("max-test-batches", 2)
    seed = arg_int("seed", 1)
    seeds = arg_int("seeds", 1)
    lr = arg_float("lr", 0.05f0)
    input_scale = arg_float("input-scale", 16.0f0)
    dt = arg_float("dt", 0.001f0)
    gamma = arg_float("gamma", 0.2f0)
    delay_kernel_size = arg_int("delay-kernel-size", 7)
    architectures = normalize_architecture.(arg_list("architectures", "recurrent,delay"))
    neurons = arg_list("neurons", "hyperlif,adaptive")
    readout = lowercase(arg_value("readout", "hybrid_vr"))

    println("="^78)
    println("APEX-v2 MULTI-BATCH TRAIN/EVAL SMOKE")
    println("="^78)
    println("CACHE=", cache_path)
    @printf("batch=%d hidden=%d seed_start=%d seeds=%d epochs=%d train_batches=%d test_batches=%d lr=%.5f readout=%s\n",
            batch_size, hidden_dim, seed, seeds, epochs, max_train_batches, max_test_batches, lr, readout)
    println("architectures=", join(architectures, "+"))
    println("neurons=", join(neurons, "+"))
    println("NOTE: G4 trains only the PyTorch-parity readout head; the trunk remains fixed after G1-G3/shared-weight gates.")

    x_train, y_train = load_split_h5(cache_path, "train")
    x_test, y_test = load_split_h5(cache_path, "test")
    n_input = size(x_train, 1)
    time_steps = size(x_train, 2)
    n_classes = max(maximum(y_train), maximum(y_test)) + 1
    @printf("loaded train=[%d,%d,%d] test=[%d,%d,%d] classes=%d\n",
            size(x_train, 1), size(x_train, 2), size(x_train, 3),
            size(x_test, 1), size(x_test, 2), size(x_test, 3), n_classes)

    config = ParityConfig(dt=dt, input_scale=input_scale, gamma=gamma,
                          delay_kernel_size=delay_kernel_size)
    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    results_dir = joinpath(dirname(dirname(@__DIR__)), "results", "apex_v2")
    mkpath(results_dir)
    summary_csv = joinpath(results_dir, "apex_v2_train_eval_smoke_$(timestamp)_summary.csv")
    epoch_csv = joinpath(results_dir, "apex_v2_train_eval_smoke_$(timestamp)_epochs.csv")

    summary_rows = String["framework,dataset,architecture,neuron,readout,seed,epochs,batch_size,n_input,hidden_dim,time_steps,train_batches,test_batches,initial_train_loss,final_train_loss,final_train_accuracy,final_test_loss,final_test_accuracy,events_per_sample,gate_mean,stable,nan_batches,provenance"]
    epoch_rows = String["framework,dataset,architecture,neuron,readout,seed,epoch,batch_size,train_batches,test_batches,train_loss,train_accuracy,test_loss,test_accuracy,events_per_sample,gate_mean,stable,nan_batches"]

    for seed_i in seed:(seed + seeds - 1)
        for architecture in architectures
            architecture in APEXV2Parity.ARCHITECTURES || error("Unknown architecture: $(architecture)")
            for neuron in neurons
                neuron in APEXV2Parity.NEURONS || error("Unknown neuron: $(neuron)")
                haskey(APEXV2Parity.READOUT_MULT, readout) || error("Unknown readout: $(readout)")
                Random.seed!(seed_i)
                CUDA.seed!(seed_i)
                model = init_model(n_input, hidden_dim, n_classes, batch_size;
                                   architecture=architecture, neuron=neuron,
                                   readout=readout, seed=seed_i, config=config)

            initial_train = run_pass!(model, config, x_train, y_train;
                                      n_classes=n_classes, batch_size=batch_size,
                                      max_batches=max_train_batches, train=false, lr=lr)
            final_train = initial_train
            final_test = run_pass!(model, config, x_test, y_test;
                                   n_classes=n_classes, batch_size=batch_size,
                                   max_batches=max_test_batches, train=false, lr=lr)
            total_nan = initial_train.nan_batches + final_test.nan_batches
            stable = initial_train.stable && final_test.stable
                @printf("seed=%d arch=%s neuron=%s epoch=0 train_loss=%.6f test_loss=%.6f train_acc=%.4f test_acc=%.4f stable=%s\n",
                    seed_i, architecture, neuron, initial_train.loss, final_test.loss,
                    initial_train.accuracy, final_test.accuracy, string(stable))

            push!(epoch_rows, join(csv_escape.([
                "apex_v2", "shd_wide_T20", architecture, neuron, readout, seed_i, 0,
                batch_size, initial_train.batches, final_test.batches,
                initial_train.loss, initial_train.accuracy,
                final_test.loss, final_test.accuracy,
                final_test.events_per_sample, final_test.gate_mean,
                stable, total_nan,
            ]), ","))

                for epoch in 1:epochs
                    final_train = run_pass!(model, config, x_train, y_train;
                                            n_classes=n_classes, batch_size=batch_size,
                                            max_batches=max_train_batches, train=true, lr=lr)
                    final_test = run_pass!(model, config, x_test, y_test;
                                           n_classes=n_classes, batch_size=batch_size,
                                           max_batches=max_test_batches, train=false, lr=lr)
                    total_nan = final_train.nan_batches + final_test.nan_batches
                    stable = final_train.stable && final_test.stable
                    @printf("seed=%d arch=%s neuron=%s epoch=%d train_loss=%.6f test_loss=%.6f train_acc=%.4f test_acc=%.4f events=%.3f gate=%.5f stable=%s\n",
                            seed_i, architecture, neuron, epoch, final_train.loss, final_test.loss,
                            final_train.accuracy, final_test.accuracy,
                            final_test.events_per_sample, final_test.gate_mean, string(stable))
                    push!(epoch_rows, join(csv_escape.([
                        "apex_v2", "shd_wide_T20", architecture, neuron, readout, seed_i, epoch,
                        batch_size, final_train.batches, final_test.batches,
                        final_train.loss, final_train.accuracy,
                        final_test.loss, final_test.accuracy,
                        final_test.events_per_sample, final_test.gate_mean,
                        stable, total_nan,
                    ]), ","))
                end

                total_nan = initial_train.nan_batches + final_train.nan_batches + final_test.nan_batches
                stable = initial_train.stable && final_train.stable && final_test.stable
                push!(summary_rows, join(csv_escape.([
                    "apex_v2", "shd_wide_T20", architecture, neuron, readout, seed_i, epochs,
                    batch_size, n_input, hidden_dim, time_steps, final_train.batches,
                    final_test.batches, initial_train.loss, final_train.loss,
                    final_train.accuracy, final_test.loss, final_test.accuracy,
                    final_test.events_per_sample, final_test.gate_mean,
                    stable, total_nan, cache_path,
                ]), ","))

                model = nothing
                GC.gc(true)
                CUDA.reclaim()
            end
        end
    end

    open(summary_csv, "w") do io
        for row in summary_rows
            println(io, row)
        end
    end
    open(epoch_csv, "w") do io
        for row in epoch_rows
            println(io, row)
        end
    end

    println("SUMMARY_CSV=", summary_csv)
    println("EPOCH_CSV=", epoch_csv)
    println("APEX_V2_TRAIN_EVAL_SMOKE_OK")
end

main()
