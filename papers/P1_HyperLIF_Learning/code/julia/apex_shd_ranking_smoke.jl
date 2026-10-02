# Bounded APEX SHD-wide ranking smoke for P1.
#
# This validates the Julia/APEX training path on the same SHD cache used by the
# PyTorch shortlist. It is smoke-grade by default: increase --epochs,
# --max-train-batches, --max-test-batches, and --seeds for paper-grade runs.

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

function arg_set(name::AbstractString, default::AbstractString)
    return Set(filter(!isempty, strip.(split(lowercase(arg_value(name, default)), ","))))
end

function selected_architectures(raw_architectures::Set{SubString{String}})
    architecture_alias = Dict(
        "ff" => "dense",
        "feedforward" => "dense",
        "rsnn" => "recurrent",
        "eprop" => "recurrent",
        "axonal_delay" => "delay",
    )
    all_architectures = ["dense", "recurrent", "delay"]
    if "all" in raw_architectures
        return all_architectures
    end

    selected = String[]
    for raw in raw_architectures
        arch = get(architecture_alias, String(raw), String(raw))
        if !(arch in all_architectures)
            error("Unknown architecture '$(raw)'. Use dense, recurrent/rsnn, delay, or all.")
        end
        if !(arch in selected)
            push!(selected, arch)
        end
    end
    isempty(selected) && error("No architectures selected. Use --architectures=dense,recurrent,delay or --architectures=all.")
    return selected
end

apex_root = arg_value("apex-root", DEFAULT_APEX_ROOT)
cache_path = arg_value("cache", DEFAULT_CACHE)

Pkg.activate(apex_root)

using CUDA
using Dates
using Printf
using Random
using Statistics

include(joinpath(apex_root, "src", "APEXEngine.jl"))
using .APEXEngine

include(joinpath(@__DIR__, "apex_load_cache_h5_adapter.jl"))

function build_readout(trunk_dim::Int, n_classes::Int, batch_size::Int,
                       readout_hidden::Int, dt_macro::Float32, lr::Float32)
    return V11ReadoutLayer(trunk_dim, readout_hidden, n_classes, 4, 4, batch_size, dt_macro;
                              lr=lr, use_predictive_coding=false)
end

function build_workspace(batch_size::Int, time_steps::Int, n_classes::Int, trunk_dim::Int,
                         readout_hidden::Int, n_input::Int)
    return SequentialWorkspace(batch_size, time_steps, n_classes, trunk_dim;
                               k_traces_out=4, n_hid_v11=readout_hidden,
                               k_branches=4, n_frac=trunk_dim, n_input=n_input)
end

function build_dense_model(name::AbstractString, use_nsa::Bool, n_input::Int, n_classes::Int,
                           batch_size::Int, time_steps::Int, hidden_dim::Int,
                           readout_hidden::Int, dt_macro::Float32, lr::Float32,
                           max_delay::Int)
    dense = DenseLIFLayer(n_input, hidden_dim, batch_size; lr=lr, use_nsa=use_nsa)
    readout = build_readout(hidden_dim, n_classes, batch_size, readout_hidden, dt_macro, lr)
    model = SequentialSNN(nothing, dense, readout)
    workspace = build_workspace(batch_size, time_steps, n_classes, hidden_dim, readout_hidden, n_input)
    return (name=name, model=model, workspace=workspace)
end

function build_recurrent_model(name::AbstractString, use_nsa::Bool, n_input::Int, n_classes::Int,
                               batch_size::Int, time_steps::Int, hidden_dim::Int,
                               readout_hidden::Int, dt_macro::Float32, lr::Float32,
                               max_delay::Int)
    recurrent = EPropHyperLIFLayer(n_input, hidden_dim, batch_size, true, dt_macro; lr=lr, use_nsa=use_nsa)
    readout = build_readout(hidden_dim, n_classes, batch_size, readout_hidden, dt_macro, lr)
    model = SequentialSNN(nothing, recurrent, readout)
    workspace = build_workspace(batch_size, time_steps, n_classes, hidden_dim, readout_hidden, n_input)
    return (name=name, model=model, workspace=workspace)
end

function build_delay_model(name::AbstractString, use_nsa::Bool, n_input::Int, n_classes::Int,
                           batch_size::Int, time_steps::Int, hidden_dim::Int,
                           readout_hidden::Int, dt_macro::Float32, lr::Float32,
                           max_delay::Int)
    dense = DenseLIFLayer(n_input, hidden_dim, batch_size; lr=lr, use_nsa=use_nsa)
    delay = SpikingDelayLayer(hidden_dim, max_delay, batch_size)
    readout = build_readout(hidden_dim, n_classes, batch_size, readout_hidden, dt_macro, lr)
    model = SequentialSNN(nothing, dense, delay, readout)
    workspace = build_workspace(batch_size, time_steps, n_classes, hidden_dim, readout_hidden, n_input)
    return (name=name, model=model, workspace=workspace)
end

const ARCHITECTURE_BUILDERS = Dict(
    "dense" => build_dense_model,
    "recurrent" => build_recurrent_model,
    "delay" => build_delay_model,
)

function build_specs(architectures::Vector{String}, model_filter::Set{SubString{String}})
    specs = NamedTuple[]
    for architecture in architectures
        if "lif" in model_filter || "all" in model_filter
            push!(specs, (architecture=architecture, name="$(architecture)_lif_control", use_nsa=false))
        end
        if "hyperlif" in model_filter || "all" in model_filter
            push!(specs, (architecture=architecture, name="$(architecture)_hyperlif_nsa", use_nsa=true))
        end
    end
    isempty(specs) && error("No models selected. Use --models=lif,hyperlif, --models=hyperlif, --models=lif, or --models=all.")
    return specs
end

function run_limited_epoch!(model, ws, loader, p, epoch::Int, burn_in::Int, is_train::Bool,
                            max_batches::Int, loss_fn)
    time_steps = size(loader.X_cpu, 3)
    eval_steps = max(1, time_steps - p.EVAL_START_STEP)
    total_loss = 0.0f0
    total_correct = 0
    total_seen = 0
    batches = 0

    for (batch_idx, (x_batch, y_batch)) in enumerate(loader)
        batch_idx > max_batches && break
        fill!(ws.readout.err, 0.0f0)
        result = train_batch!(model, ws, x_batch, y_batch, p, loader.batch_size, time_steps,
                              epoch, burn_in, is_train, loss_fn)
        total_loss += Float32(result.loss)
        total_correct += result.correct
        total_seen += loader.batch_size
        batches += 1

        if is_train && batch_idx % 10 == 0
            GC.gc(true)
            CUDA.reclaim()
        end
    end

    accuracy = total_seen == 0 ? 0.0f0 : Float32(total_correct / total_seen)
    mean_loss = batches == 0 ? 0.0f0 : Float32(total_loss / (batches * eval_steps))
    return (loss=mean_loss, accuracy=accuracy, correct=total_correct, seen=total_seen, batches=batches)
end

function mean_and_std(values)
    vals = Float64.(collect(values))
    isempty(vals) && return (NaN, NaN)
    spread = length(vals) > 1 ? std(vals) : 0.0
    return (mean(vals), spread)
end

function main()
    if !CUDA.functional()
        error("CUDA is not functional. APEX ranking smoke requires a CUDA-capable Julia session.")
    end
    if !isfile(cache_path)
        error("SHD cache not found: $(cache_path)")
    end

    batch_size = arg_int("batch-size", 64)
    epochs = arg_int("epochs", 1)
    max_train_batches = arg_int("max-train-batches", 2)
    max_test_batches = arg_int("max-test-batches", 2)
    hidden_dim = arg_int("hidden-dim", 128)
    readout_hidden = arg_int("readout-hidden", 64)
    eval_start = arg_int("eval-start", 5)
    seeds = arg_int("seeds", 1)
    lr = arg_float("lr", 0.005f0)
    dt_macro = arg_float("dt-macro", 5.0f0)
    rec_dropout = arg_float("rec-dropout", 0.10f0)
    g_base = arg_float("g-base", 1.0f0)
    beta = arg_float("beta", 0.10f0)
    gamma = arg_float("gamma", 0.50f0)
    tau_r = arg_float("tau-r", 2.0f0)
    tau_soma = arg_float("tau-soma", 5.0f0)
    num_micro = arg_int("num-micro", 5)
    max_delay = arg_int("max-delay", 3)
    model_filter = arg_set("models", "lif,hyperlif")
    architectures = selected_architectures(arg_set("architectures", "dense"))

    println("="^78)
    println("APEX SHD-WIDE RANKING SMOKE")
    println("="^78)
    println("APEX_ROOT=", apex_root)
    println("CACHE=", cache_path)
    @printf("batch=%d epochs=%d max_train_batches=%d max_test_batches=%d hidden=%d readout_hidden=%d seeds=%d\n",
            batch_size, epochs, max_train_batches, max_test_batches, hidden_dim, readout_hidden, seeds)
    @printf("lr=%.5f rec_dropout=%.3f dt=%.3f num_micro=%d g_base=%.3f beta=%.3f gamma=%.3f tau_r=%.3f tau_soma=%.3f max_delay=%d models=%s architectures=%s\n",
            lr, rec_dropout, dt_macro, num_micro, g_base, beta, gamma, tau_r, tau_soma, max_delay,
            join(sort(collect(model_filter)), "+"), join(architectures, "+"))
    if "delay" in architectures
        println("NOTE: APEX delay mode uses SpikingDelayLayer fixed causal axonal delays after the hidden neuron; PyTorch delay used a learnable depthwise temporal-current kernel.")
    end
    if "recurrent" in architectures
        println("NOTE: APEX recurrent mode uses EPropHyperLIFLayer with the native exact/NSA toggle; it is an APEX-family RSNN validation, not a byte-identical PyTorch module port.")
    end

    train_loader, test_loader = load_cache_h5(cache_path, batch_size; shuffle_train=true, shuffle_test=false)
    n_input = size(train_loader.X_cpu, 1)
    time_steps = size(train_loader.X_cpu, 3)
    n_classes = max(maximum(train_loader.Y_cpu), maximum(test_loader.Y_cpu)) + 1

    p = APEXParameters(N_INPUT=n_input, N_CLASSES=n_classes, DT_MACRO=dt_macro,
                       EVAL_START_STEP=eval_start, TRAIN_RES=false,
                       FREEZE_TRUNK=false, REC_DROPOUT=rec_dropout,
                       G_BASE=g_base, BETA=beta, GAMMA=gamma,
                       TAU_R=tau_r, TAU_SOMA=tau_soma, NUM_MICRO=num_micro)
    loss_fn = APEXCrossEntropy()

    result_rows = String["seed,architecture,model,use_nsa,epochs,train_batches,test_batches,train_loss,train_accuracy,test_loss,test_accuracy,correct_test,seen_test"]
    epoch_rows = String["seed,architecture,model,use_nsa,epoch,train_batches,test_batches,train_loss,train_accuracy,test_loss,test_accuracy,correct_test,seen_test"]
    records = NamedTuple[]
    timestamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    results_dir = joinpath(dirname(@__DIR__), "results", "apex")
    mkpath(results_dir)
    csv_path = joinpath(results_dir, "apex_shd_ranking_smoke_$(timestamp).csv")
    epoch_csv_path = joinpath(results_dir, "apex_shd_ranking_smoke_$(timestamp)_epochs.csv")
    summary_path = joinpath(results_dir, "apex_shd_ranking_smoke_$(timestamp)_summary.csv")

    for seed in 1:seeds
        Random.seed!(seed)
        CUDA.seed!(seed)

        specs = build_specs(architectures, model_filter)

        for spec in specs
            Random.seed!(seed)
            CUDA.seed!(seed)

            cell = ARCHITECTURE_BUILDERS[spec.architecture](
                spec.name, spec.use_nsa, n_input, n_classes, batch_size,
                time_steps, hidden_dim, readout_hidden, dt_macro, lr, max_delay)

            train_metrics = (loss=0.0f0, accuracy=0.0f0, correct=0, seen=0, batches=0)
            test_metrics = (loss=0.0f0, accuracy=0.0f0, correct=0, seen=0, batches=0)

            for epoch in 1:epochs
                train_metrics = run_limited_epoch!(cell.model, cell.workspace, train_loader, p,
                                                   epoch, 0, true, max_train_batches, loss_fn)
                test_metrics = run_limited_epoch!(cell.model, cell.workspace, test_loader, p,
                                                  epoch, 0, false, max_test_batches, loss_fn)
                @printf("seed=%d architecture=%s model=%s epoch=%d train_acc=%.4f test_acc=%.4f train_loss=%.6f test_loss=%.6f\n",
                        seed, spec.architecture, spec.name, epoch, train_metrics.accuracy, test_metrics.accuracy,
                        train_metrics.loss, test_metrics.loss)
                push!(epoch_rows,
                      join((seed, spec.architecture, spec.name, spec.use_nsa, epoch, train_metrics.batches,
                            test_metrics.batches, train_metrics.loss, train_metrics.accuracy,
                            test_metrics.loss, test_metrics.accuracy, test_metrics.correct,
                            test_metrics.seen), ","))
            end

            push!(result_rows,
                  join((seed, spec.architecture, spec.name, spec.use_nsa, epochs, train_metrics.batches,
                        test_metrics.batches, train_metrics.loss, train_metrics.accuracy,
                        test_metrics.loss, test_metrics.accuracy, test_metrics.correct,
                        test_metrics.seen), ","))

            push!(records, (
                seed=seed,
                architecture=spec.architecture,
                model=spec.name,
                use_nsa=spec.use_nsa,
                train_batches=train_metrics.batches,
                test_batches=test_metrics.batches,
                train_loss=Float64(train_metrics.loss),
                train_accuracy=Float64(train_metrics.accuracy),
                test_loss=Float64(test_metrics.loss),
                test_accuracy=Float64(test_metrics.accuracy),
                correct_test=test_metrics.correct,
                seen_test=test_metrics.seen,
            ))

            cell = nothing
            GC.gc(true)
            CUDA.reclaim()
        end
    end

    summary_rows = String["architecture,model,use_nsa,n,train_accuracy_mean,train_accuracy_std,test_accuracy_mean,test_accuracy_std,train_loss_mean,train_loss_std,test_loss_mean,test_loss_std,correct_test_total,seen_test_total"]
    summary_keys = unique([(r.architecture, r.model) for r in records])
    for key in summary_keys
        architecture, model_name = key
        subset = [r for r in records if r.architecture == architecture && r.model == model_name]
        train_acc = mean_and_std(r.train_accuracy for r in subset)
        test_acc = mean_and_std(r.test_accuracy for r in subset)
        train_loss = mean_and_std(r.train_loss for r in subset)
        test_loss = mean_and_std(r.test_loss for r in subset)
        correct_total = sum(r.correct_test for r in subset)
        seen_total = sum(r.seen_test for r in subset)
        use_nsa = first(subset).use_nsa

        push!(summary_rows,
              join((architecture, model_name, use_nsa, length(subset), train_acc[1], train_acc[2],
                    test_acc[1], test_acc[2], train_loss[1], train_loss[2],
                    test_loss[1], test_loss[2], correct_total, seen_total), ","))
    end

    open(csv_path, "w") do io
        for row in result_rows
            println(io, row)
        end
    end

    open(epoch_csv_path, "w") do io
        for row in epoch_rows
            println(io, row)
        end
    end

    open(summary_path, "w") do io
        for row in summary_rows
            println(io, row)
        end
    end

    println("SUMMARY")
    for row in summary_rows[2:end]
        println(row)
    end

    println("CSV=", csv_path)
    println("EPOCH_CSV=", epoch_csv_path)
    println("SUMMARY_CSV=", summary_path)
    println("APEX_SHD_RANKING_SMOKE_OK")
end

main()
