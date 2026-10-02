# APEX-v2 shared-weight value-level comparison against a PyTorch fixture.
#
# Loads exact PyTorch-initialized weights/features/logits from HDF5, injects
# those weights into the Julia/APEX-v2 forward layer, and checks numerical
# agreement on the same SHD first batch.

using Pkg

const DEFAULT_APEX_ROOT = raw"C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2"
const DEFAULT_CACHE = raw"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5"
const DEFAULT_FIXTURE = raw"C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\results\apex_v2\pytorch_apex_v2_fixture_recurrent_hyperlif_hybrid_vr_seed1.h5"

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

function load_fixture(path::AbstractString)
    h5open(path, "r") do fid
        data = Dict{String,Any}()
        for name in keys(fid)
            data[String(name)] = read(fid, name)
        end
        return data
    end
end

function inject_fixture_weights!(model::ParityModel, fixture::Dict{String,Any})
    copyto!(model.W_in, CuArray(Float32.(fixture["fc_in_weight"])))
    copyto!(model.B_in, CuArray(Float32.(fixture["fc_in_bias"])))
    copyto!(model.W_head, CuArray(Float32.(fixture["head_weight"])))
    copyto!(model.B_head, CuArray(Float32.(fixture["head_bias"])))
    if model.architecture == "recurrent"
        haskey(fixture, "fc_rec_weight") || error("Fixture missing recurrent weights.")
        copyto!(model.W_rec, CuArray(Float32.(fixture["fc_rec_weight"])))
    elseif model.architecture == "delay"
        haskey(fixture, "delay_kernel") || error("Fixture missing delay kernel.")
        copyto!(model.delay_kernel, CuArray(Float32.(fixture["delay_kernel"])))
    end
    return nothing
end

function compare_arrays(actual, expected)
    delta = abs.(actual .- expected)
    return (
        max_abs = Float64(maximum(delta)),
        mean_abs = Float64(mean(delta)),
        rmse = Float64(sqrt(mean(delta .^ 2))),
    )
end

function main()
    cache_path = arg_value("cache", DEFAULT_CACHE)
    fixture_path = arg_value("fixture", DEFAULT_FIXTURE)
    isfile(cache_path) || error("Cache not found: $(cache_path)")
    isfile(fixture_path) || error("Fixture not found: $(fixture_path)")
    CUDA.functional() || error("CUDA is not functional; shared-weight compare expects CUDA.")

    batch_size = arg_int("batch-size", 32)
    hidden_dim = arg_int("hidden-dim", 64)
    seed = arg_int("seed", 1)
    architecture = normalize_architecture(arg_value("architecture", "recurrent"))
    neuron = lowercase(arg_value("neuron", "hyperlif"))
    readout = lowercase(arg_value("readout", "hybrid_vr"))
    dt = arg_float("dt", 0.001f0)
    input_scale = arg_float("input-scale", 16.0f0)
    gamma = arg_float("gamma", 0.2f0)
    delay_kernel_size = arg_int("delay-kernel-size", 7)
    feature_tol = Float64(arg_float("feature-tol", 1.0f-4))
    logit_tol = Float64(arg_float("logit-tol", 1.0f-3))

    println("="^78)
    println("APEX-v2 SHARED-WEIGHT PYTORCH VALUE COMPARE")
    println("="^78)
    println("CACHE=", cache_path)
    println("FIXTURE=", fixture_path)
    @printf("arch=%s neuron=%s readout=%s batch=%d hidden=%d seed=%d\n",
            architecture, neuron, readout, batch_size, hidden_dim, seed)

    x_fbt, _y_batch, n_classes = load_first_batch_h5(cache_path, batch_size)
    fixture = load_fixture(fixture_path)
    n_input = size(x_fbt, 1)
    actual_batch = size(x_fbt, 2)

    config = ParityConfig(dt=dt, input_scale=input_scale, gamma=gamma,
                          delay_kernel_size=delay_kernel_size)
    model = init_model(n_input, hidden_dim, n_classes, actual_batch;
                       architecture=architecture, neuron=neuron,
                       readout=readout, seed=seed, config=config)
    inject_fixture_weights!(model, fixture)
    summary = forward_summary!(model, x_fbt, config)
    summary.finite || error("APEX-v2 shared-weight forward produced non-finite values.")

    actual_features = Array(summary.features)
    actual_logits = Array(summary.logits)
    expected_features = Float32.(fixture["expected_features_bt"])
    expected_logits = Float32.(fixture["expected_logits_bc"])
    size(actual_features) == size(expected_features) || error("Feature shape mismatch: $(size(actual_features)) vs $(size(expected_features))")
    size(actual_logits) == size(expected_logits) || error("Logit shape mismatch: $(size(actual_logits)) vs $(size(expected_logits))")

    feat = compare_arrays(actual_features, expected_features)
    logit = compare_arrays(actual_logits, expected_logits)
    feature_ok = feat.max_abs <= feature_tol
    logit_ok = logit.max_abs <= logit_tol
    passed = feature_ok && logit_ok

    @printf("feature max_abs=%.9g mean_abs=%.9g rmse=%.9g tol=%.3g ok=%s\n",
            feat.max_abs, feat.mean_abs, feat.rmse, feature_tol, string(feature_ok))
    @printf("logit   max_abs=%.9g mean_abs=%.9g rmse=%.9g tol=%.3g ok=%s\n",
            logit.max_abs, logit.mean_abs, logit.rmse, logit_tol, string(logit_ok))

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    results_dir = joinpath(dirname(dirname(@__DIR__)), "results", "apex_v2")
    mkpath(results_dir)
    csv_path = joinpath(results_dir, "apex_v2_shared_weight_trace_compare_$(timestamp).csv")
    open(csv_path, "w") do io
        println(io, "framework_pair,dataset,architecture,neuron,readout,seed,batch_size,n_input,hidden_dim,feature_max_abs,feature_mean_abs,feature_rmse,feature_tol,feature_ok,logit_max_abs,logit_mean_abs,logit_rmse,logit_tol,logit_ok,passed,fixture")
        println(io, join((
            "pytorch_apex_v2", "shd_wide_T20", architecture, neuron, readout, seed,
            actual_batch, n_input, hidden_dim,
            feat.max_abs, feat.mean_abs, feat.rmse, feature_tol, feature_ok,
            logit.max_abs, logit.mean_abs, logit.rmse, logit_tol, logit_ok,
            passed, fixture_path,
        ), ","))
    end

    println("CSV=", csv_path)
    passed || error("APEX-v2 shared-weight value comparison exceeded tolerance.")
    println("APEX_V2_SHARED_WEIGHT_TRACE_COMPARE_OK")
end

main()
