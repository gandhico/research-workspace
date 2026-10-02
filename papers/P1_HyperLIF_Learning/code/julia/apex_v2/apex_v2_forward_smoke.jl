# APEX-v2 PyTorch-parity forward smoke.
#
# This is the first validation ladder gate for the new parity layer. It does not
# train yet; it confirms that the Julia/CUDA forward path can reproduce the
# PyTorch architecture families and readout feature shapes on the same SHD cache.

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

function csv_escape(x)
    s = string(x)
    return occursin(",", s) ? "\"" * replace(s, "\"" => "\"\"") * "\"" : s
end

function main()
    cache_path = arg_value("cache", DEFAULT_CACHE)
    isfile(cache_path) || error("Cache not found: $(cache_path)")
    CUDA.functional() || error("CUDA is not functional; APEX-v2 smoke expects CUDA.")

    batch_size = arg_int("batch-size", 32)
    hidden_dim = arg_int("hidden-dim", 64)
    seeds = arg_int("seeds", 1)
    input_scale = arg_float("input-scale", 16.0f0)
    dt = arg_float("dt", 0.001f0)
    gamma = arg_float("gamma", 0.2f0)
    delay_kernel_size = arg_int("delay-kernel-size", 7)
    architectures = normalize_architecture.(arg_list("architectures", "dense,recurrent,delay"))
    neurons = arg_list("neurons", "lif,hyperlif")
    readouts = arg_list("readouts", "spike_count,membrane,gate,hybrid_gr,hybrid_vr,hybrid_vr_conductance")

    println("="^78)
    println("APEX-v2 PYTORCH-PARITY FORWARD SMOKE")
    println("="^78)
    println("CACHE=", cache_path)
    @printf("batch=%d hidden=%d seeds=%d dt=%.6f input_scale=%.3f gamma=%.3f delay_kernel=%d\n",
            batch_size, hidden_dim, seeds, dt, input_scale, gamma, delay_kernel_size)
    println("architectures=", join(architectures, "+"))
    println("neurons=", join(neurons, "+"))
    println("readouts=", join(readouts, "+"))

    x_fbt, y_batch, n_classes = load_first_batch_h5(cache_path, batch_size)
    n_input = size(x_fbt, 1)
    actual_batch = size(x_fbt, 2)
    time_steps = size(x_fbt, 3)
    @printf("loaded x_fbt=[%d,%d,%d] labels=%d classes=%d\n",
            n_input, actual_batch, time_steps, length(y_batch), n_classes)

    config = ParityConfig(dt=dt, input_scale=input_scale, gamma=gamma,
                          delay_kernel_size=delay_kernel_size)

    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    results_dir = joinpath(dirname(dirname(@__DIR__)), "results", "apex_v2")
    mkpath(results_dir)
    csv_path = joinpath(results_dir, "apex_v2_forward_smoke_$(timestamp).csv")

    rows = String["framework,dataset,architecture,neuron,readout,seed,batch_size,n_input,hidden_dim,time_steps,feature_dim,logit_rows,logit_cols,events_per_sample,gate_mean,voltage_mean,conductance_mean,finite,provenance"]
    total = 0
    failures = 0

    for seed in 1:seeds
        for architecture in architectures
            architecture in APEXV2Parity.ARCHITECTURES || error("Unknown architecture: $(architecture)")
            for neuron in neurons
                neuron in APEXV2Parity.NEURONS || error("Unknown neuron: $(neuron)")
                for readout in readouts
                    haskey(APEXV2Parity.READOUT_MULT, readout) || error("Unknown readout: $(readout)")
                    model = init_model(n_input, hidden_dim, n_classes, actual_batch;
                                       architecture=architecture, neuron=neuron,
                                       readout=readout, seed=seed, config=config)
                    summary = forward_summary!(model, x_fbt, config)
                    total += 1
                    failures += summary.finite ? 0 : 1
                    @printf("seed=%d arch=%s neuron=%s readout=%s feature_dim=%d logits=%dx%d finite=%s ev/sample=%.3f gate=%.5f\n",
                            seed, architecture, neuron, readout, summary.feature_dim,
                            summary.logit_rows, summary.logit_cols, string(summary.finite),
                            summary.events_per_sample, summary.gate_mean)
                    push!(rows, join(csv_escape.([
                        "apex_v2", "shd_wide_T20", architecture, neuron, readout, seed,
                        actual_batch, n_input, hidden_dim, time_steps, summary.feature_dim,
                        summary.logit_rows, summary.logit_cols, summary.events_per_sample,
                        summary.gate_mean, summary.voltage_mean, summary.conductance_mean,
                        summary.finite, cache_path,
                    ]), ","))
                end
            end
        end
    end

    open(csv_path, "w") do io
        for row in rows
            println(io, row)
        end
    end

    println("CSV=", csv_path)
    @printf("APEX_V2_FORWARD_SMOKE total=%d failures=%d\n", total, failures)
    failures == 0 || error("APEX-v2 forward smoke produced non-finite outputs.")
    println("APEX_V2_FORWARD_SMOKE_OK")
end

main()

