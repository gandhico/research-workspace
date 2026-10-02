#!/usr/bin/env julia

"""
Train one Julia HyperLIF experiment from the portable HDF5 contract.

The script deliberately distinguishes three observables:
  * upward crossings (events),
  * above-threshold occupancy (not an event count), and
  * the smooth readiness gate used by continuous-state learning.

The test split is evaluated once, after selecting the checkpoint on a held-out
validation subset.  No energy claim is made: wall time and event/occupancy
proxies are reported, while hardware energy remains explicitly unmeasured.
"""

using CUDA
using Dates
using HDF5
using HyperLIFLearning
using JSON
using Optimisers
using Random
using SHA
using Serialization
using Statistics
using Zygote

const DEFAULTS = Dict(
    "cache" => "",
    "architecture" => "dense",
    "cell" => "hyperlif",
    "learning-mode" => "continuous",
    "readout" => "mode_default",
    "delay-mode" => "causal",
    "seed" => "1",
    "epochs" => "20",
    "hidden" => "128",
    "batch-size" => "32",
    "lr" => "0.001",
    "weight-decay" => "0.0001",
    "validation-fraction" => "0.10",
    "patience" => "6",
    "max-train" => "0",
    "max-test" => "0",
    "device" => "auto",
    "results-root" => "results/julia_learning",
    "skip-existing" => "false",
    "smoke" => "false",
)

function usage()
    println("""
Usage:
  julia --project=. train_hpc.jl --cache DATA.h5 [options]

Core options:
  --architecture dense|recurrent|delay
  --cell hyperlif|adaptive|next
  --learning-mode continuous|surrogate|event_time
  --readout mode_default|membrane|gate|conductance|spike_count|
            first_event_time|hybrid_vr|hybrid_zr|hybrid_time_vr|hybrid_next
  --device auto|cpu|cuda
  --epochs N --hidden N --batch-size N --lr X --seed N
  --validation-fraction X --patience N --max-train N --max-test N
  --results-root DIR --skip-existing --smoke
""")
end

function parse_cli(args)
    options = copy(DEFAULTS)
    i = 1
    while i <= length(args)
        token = args[i]
        token in ("-h", "--help") && (usage(); exit(0))
        startswith(token, "--") || error("unexpected positional argument: $token")
        item = token[3:end]
        if occursin('=', item)
            key, value = split(item, '='; limit=2)
            haskey(options, key) || error("unknown option --$key")
            options[key] = value
        else
            haskey(options, item) || error("unknown option --$item")
            if item in ("skip-existing", "smoke")
                options[item] = "true"
            else
                i == length(args) && error("missing value for --$item")
                i += 1
                options[item] = args[i]
            end
        end
        i += 1
    end
    isempty(options["cache"]) && error("--cache is required")
    return options
end

parse_bool(value) = lowercase(value) in ("1", "true", "yes", "on")
parse_symbol(value) = Symbol(replace(lowercase(value), '-' => '_'))

function normalize_layout(x, labels, split)
    ndims(x) == 3 || error("$split input must be rank three, got $(size(x))")
    n = length(labels)
    if size(x, 3) == n
        return Float32.(x)                 # HDF5.jl: features × time × samples
    elseif size(x, 1) == n
        return Float32.(permutedims(x, (3, 2, 1)))
    end
    error("cannot identify sample axis for $split: X=$(size(x)), y=$n")
end

function normalize_labels(y)
    labels = Int.(vec(y))
    minimum(labels) == 0 && (labels .+= 1)
    minimum(labels) >= 1 || error("labels must be zero- or one-based nonnegative integers")
    return labels
end

function load_cache(path)
    isfile(path) || error("cache does not exist: $path")
    raw = h5open(path, "r") do file
        required = ("X_train", "y_train", "X_test", "y_test")
        all(haskey(file, key) for key in required) ||
            error("HDF5 cache must contain $(join(required, ", "))")
        (read(file["X_train"]), read(file["y_train"]),
         read(file["X_test"]), read(file["y_test"]))
    end
    y_train, y_test = normalize_labels(raw[2]), normalize_labels(raw[4])
    x_train = normalize_layout(raw[1], y_train, "train")
    x_test = normalize_layout(raw[3], y_test, "test")
    size(x_train)[1:2] == size(x_test)[1:2] ||
        error("train/test feature-time shapes disagree")
    n_classes = max(maximum(y_train), maximum(y_test))
    return x_train, y_train, x_test, y_test, n_classes
end

function capped_indices(rng, labels, maximum_count)
    n = length(labels)
    count = maximum_count <= 0 ? n : min(n, maximum_count)
    count == n && return collect(1:n)
    classes = sort(unique(labels))
    groups = [findall(==(class), labels) for class in classes]
    ideal = [count * length(group) / n for group in groups]
    quotas = floor.(Int, ideal)
    remaining = count - sum(quotas)
    order = sortperm(ideal .- quotas; rev=true)
    for group_index in order[1:remaining]
        quotas[group_index] += 1
    end
    selected = Int[]
    for (group, quota) in zip(groups, quotas)
        shuffled = group[randperm(rng, length(group))]
        append!(selected, shuffled[1:quota])
    end
    return selected[randperm(rng, length(selected))]
end

function train_validation_split(rng, indices, labels, fraction)
    0f0 < fraction < 0.5f0 || error("validation-fraction must lie in (0, 0.5)")
    training, validation = Int[], Int[]
    for class in sort(unique(labels[indices]))
        group = indices[findall(==(class), labels[indices])]
        shuffled = group[randperm(rng, length(group))]
        n_validation = length(group) == 1 ? 0 :
            clamp(round(Int, length(group) * fraction), 1, length(group) - 1)
        append!(validation, shuffled[1:n_validation])
        append!(training, shuffled[n_validation+1:end])
    end
    isempty(validation) && error("validation split is empty; increase --max-train")
    return training[randperm(rng, length(training))],
           validation[randperm(rng, length(validation))]
end

function input_batch(x, indices)
    return permutedims(view(x, :, :, indices), (1, 3, 2))
end

function one_hot(labels, n_classes)
    targets = zeros(Float32, n_classes, length(labels))
    for (column, label) in enumerate(labels)
        targets[label, column] = 1f0
    end
    return targets
end

function device_choice(requested)
    requested in ("auto", "cpu", "cuda") || error("device must be auto, cpu, or cuda")
    available = try
        CUDA.functional()
    catch exception
        @warn "CUDA probe failed; CPU remains available" exception=(exception, catch_backtrace())
        false
    end
    requested == "cuda" && !available && error("--device=cuda requested, but CUDA.functional() is false")
    return requested == "cpu" || (requested == "auto" && !available) ? :cpu : :cuda
end

to_device(x, ::Val{:cpu}) = x
to_device(x, ::Val{:cuda}) = CUDA.cu(x)

function parameters_to_device(parameters, device)
    converted = map(value -> to_device(value, Val(device)), values(parameters))
    return NamedTuple{keys(parameters)}(converted)
end

copy_parameters(parameters) = NamedTuple{keys(parameters)}(map(copy, values(parameters)))
cpu_parameters(parameters) = NamedTuple{keys(parameters)}(map(Array, values(parameters)))

function host_scalar(value)
    value isa Number && return Float64(value)
    return Float64(only(Array(value)))
end

function finite_or_nothing(value)
    number = host_scalar(value)
    return isfinite(number) ? number : nothing
end

function evaluate(parameters, x, labels, indices, n_classes, batch_size, config, device)
    total_loss = 0.0
    total_correct = 0.0
    total_examples = 0
    weighted = Dict(
        "upcrossings_per_sample" => 0.0,
        "occupancy_per_sample" => 0.0,
        "gate_mean" => 0.0,
        "voltage_mean" => 0.0,
        "no_event_neuron_fraction" => 0.0,
        "grazing_among_event_neurons" => 0.0,
    )
    minimum_speed = Inf
    for start in 1:batch_size:length(indices)
        selected = indices[start:min(start + batch_size - 1, length(indices))]
        xb = to_device(input_batch(x, selected), Val(device))
        yb = labels[selected]
        tb = to_device(one_hot(yb, n_classes), Val(device))
        loss, accuracy, aux = loss_and_accuracy(parameters, xb, tb, yb, config)
        count = length(selected)
        total_loss += host_scalar(loss) * count
        total_correct += Float64(accuracy) * count
        total_examples += count
        metric_values = (
            upcrossings_per_sample=aux.crossings_per_sample,
            occupancy_per_sample=aux.occupancy_per_sample,
            gate_mean=aux.gate_mean,
            voltage_mean=aux.voltage_mean,
            no_event_neuron_fraction=aux.no_event_fraction,
            grazing_among_event_neurons=aux.grazing_fraction,
        )
        for (name, value) in pairs(metric_values)
            weighted[string(name)] += host_scalar(value) * count
        end
        candidate = finite_or_nothing(aux.minimum_event_speed)
        candidate !== nothing && (minimum_speed = min(minimum_speed, candidate))
    end
    metrics = Dict{String,Any}(key => value / total_examples for (key, value) in weighted)
    metrics["loss"] = total_loss / total_examples
    metrics["accuracy"] = total_correct / total_examples
    metrics["minimum_crossing_speed"] = isfinite(minimum_speed) ? minimum_speed : nothing
    metrics["event_definition"] = "upward threshold crossing"
    metrics["occupancy_definition"] = "neuron-time states at or above threshold"
    return metrics
end

function train(parameters, x, labels, train_indices, validation_indices,
               n_classes, config, options, device)
    epochs = parse(Int, options["epochs"])
    batch_size = parse(Int, options["batch-size"])
    learning_rate = parse(Float32, options["lr"])
    weight_decay = parse(Float32, options["weight-decay"])
    patience = parse(Int, options["patience"])
    rng = MersenneTwister(parse(Int, options["seed"]) + 101)
    rule = Optimisers.AdamW(learning_rate, (0.9f0, 0.999f0), weight_decay)
    optimizer_state = Optimisers.setup(rule, parameters)
    best_parameters = copy_parameters(parameters)
    best_accuracy = -Inf
    best_epoch = 0
    trace = Vector{Dict{String,Any}}()
    stopped_early = false

    for epoch in 1:epochs
        order = train_indices[randperm(rng, length(train_indices))]
        train_loss = 0.0
        train_examples = 0
        epoch_start = time()
        for start in 1:batch_size:length(order)
            selected = order[start:min(start + batch_size - 1, length(order))]
            xb = to_device(input_batch(x, selected), Val(device))
            targets = to_device(one_hot(labels[selected], n_classes), Val(device))
            loss, pullback = Zygote.withgradient(parameters) do candidate
                classification_loss(candidate, xb, targets, config)
            end
            gradients = pullback[1]
            isfinite(host_scalar(loss)) || error("non-finite training loss at epoch $epoch")
            optimizer_state, parameters = Optimisers.update(optimizer_state, parameters, gradients)
            train_loss += host_scalar(loss) * length(selected)
            train_examples += length(selected)
        end
        validation = evaluate(parameters, x, labels, validation_indices,
                              n_classes, batch_size, config, device)
        record = Dict{String,Any}(
            "epoch" => epoch,
            "train_loss" => train_loss / train_examples,
            "validation_loss" => validation["loss"],
            "validation_accuracy" => validation["accuracy"],
            "seconds" => time() - epoch_start,
        )
        push!(trace, record)
        shown_train_loss = round(record["train_loss"]; digits=5)
        shown_validation_loss = round(record["validation_loss"]; digits=5)
        shown_validation_accuracy = round(record["validation_accuracy"]; digits=4)
        println("epoch=$epoch train_loss=$shown_train_loss " *
                "val_loss=$shown_validation_loss " *
                "val_accuracy=$shown_validation_accuracy")
        if validation["accuracy"] > best_accuracy
            best_accuracy = validation["accuracy"]
            best_epoch = epoch
            best_parameters = copy_parameters(parameters)
        elseif patience > 0 && epoch - best_epoch >= patience
            stopped_early = true
            break
        end
    end
    return best_parameters, trace, best_epoch, best_accuracy, stopped_early
end

function config_from(options)
    config = HyperConfig(
        architecture=parse_symbol(options["architecture"]),
        cell=parse_symbol(options["cell"]),
        learning_mode=parse_symbol(options["learning-mode"]),
        readout=parse_symbol(options["readout"]),
        delay_mode=parse_symbol(options["delay-mode"]),
    )
    return validate_config(config)
end

function gradient_semantics(mode)
    mode == :continuous && return "reverse-mode derivative of the discretized piecewise-smooth voltage/readiness path; hard crossings are diagnostic"
    mode == :surrogate && return "hard upward crossings in forward pass; declared fast-sigmoid pseudo-derivative in backward pass"
    return "within-step interpolated first-crossing time under fixed event topology; undefined/grazing cases are diagnosed"
end

function experiment_id(cache, config, readout, seed, options)
    identity_settings = join((options["epochs"], options["hidden"], options["batch-size"],
                              options["lr"], options["weight-decay"], options["max-train"],
                              options["max-test"], options["validation-fraction"],
                              options["patience"], options["device"]), '|')
    settings_digest = bytes2hex(sha1(identity_settings))[1:10]
    parts = (splitext(basename(cache))[1], string(config.architecture), string(config.cell),
             string(config.learning_mode), string(readout), "seed$(seed)",
             "cfg$settings_digest")
    return join(parts, "__")
end

function cache_sha256(path)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function main(args=ARGS)
    options = parse_cli(args)
    parse_bool(options["smoke"]) && merge!(options, Dict(
        "epochs" => "1", "hidden" => "24", "batch-size" => "16",
        "max-train" => "96", "max-test" => "64", "patience" => "1"))
    config = config_from(options)
    cache = abspath(options["cache"])
    seed = parse(Int, options["seed"])
    id = experiment_id(cache, config, HyperLIFLearning._readout_symbol(config), seed, options)
    run_directory = abspath(joinpath(options["results-root"], id))
    summary_path = joinpath(run_directory, "summary.json")
    if parse_bool(options["skip-existing"]) && isfile(summary_path)
        println("SKIP existing $summary_path")
        return
    end
    mkpath(run_directory)
    started_at = now(UTC)
    wall_start = time()
    rng = MersenneTwister(seed)
    x_train, y_train, x_test, y_test, n_classes = load_cache(cache)
    selected_train = capped_indices(rng, y_train, parse(Int, options["max-train"]))
    selected_test = capped_indices(rng, y_test, parse(Int, options["max-test"]))
    train_indices, validation_indices = train_validation_split(
        rng, selected_train, y_train, parse(Float32, options["validation-fraction"]))
    device = device_choice(lowercase(options["device"]))
    parameters = init_parameters(rng, size(x_train, 1), parse(Int, options["hidden"]),
                                 n_classes, config)
    parameters = parameters_to_device(parameters, device)
    println("experiment=$id device=$device train=$(length(train_indices)) " *
            "validation=$(length(validation_indices)) test=$(length(selected_test))")
    best_parameters, trace, best_epoch, best_validation, stopped_early = train(
        parameters, x_train, y_train, train_indices, validation_indices,
        n_classes, config, options, device)
    test_metrics = evaluate(best_parameters, x_test, y_test, selected_test,
                            n_classes, parse(Int, options["batch-size"]), config, device)
    checkpoint_path = joinpath(run_directory, "checkpoint.jls")
    serialize(checkpoint_path, Dict(
        "parameters" => cpu_parameters(best_parameters),
        "config" => config,
        "experiment_id" => id,
        "best_epoch" => best_epoch,
    ))
    summary = Dict{String,Any}(
        "schema_version" => 1,
        "status" => "complete",
        "experiment_id" => id,
        "started_at_utc" => string(started_at),
        "finished_at_utc" => string(now(UTC)),
        "wall_seconds" => time() - wall_start,
        "dataset" => Dict(
            "path" => cache,
            "sha256" => cache_sha256(cache),
            "layout_in_memory" => "features x time x samples",
            "input_features" => size(x_train, 1),
            "time_steps" => size(x_train, 2),
            "classes" => n_classes,
            "train_used" => length(train_indices),
            "validation_used" => length(validation_indices),
            "test_used" => length(selected_test),
            "subset_selection" => "class-stratified deterministic sampling from seed",
        ),
        "model" => Dict(
            "architecture" => string(config.architecture),
            "cell" => string(config.cell),
            "learning_mode" => string(config.learning_mode),
            "readout" => string(HyperLIFLearning._readout_symbol(config)),
            "delay_mode" => string(config.delay_mode),
            "hidden" => parse(Int, options["hidden"]),
            "parameter_count" => parameter_count(best_parameters),
            "event_semantics" => "upward threshold crossing",
            "gradient_semantics" => gradient_semantics(config.learning_mode),
        ),
        "optimization" => Dict(
            "optimizer" => "AdamW",
            "learning_rate" => parse(Float64, options["lr"]),
            "weight_decay" => parse(Float64, options["weight-decay"]),
            "epochs_requested" => parse(Int, options["epochs"]),
            "epochs_completed" => length(trace),
            "best_epoch_by_validation_accuracy" => best_epoch,
            "best_validation_accuracy" => best_validation,
            "stopped_early" => stopped_early,
            "seed" => seed,
        ),
        "test" => test_metrics,
        "trace" => trace,
        "compute" => Dict(
            "device" => string(device),
            "julia_version" => string(VERSION),
            "hardware_energy" => nothing,
            "energy_claim" => "not measured; event and occupancy statistics are activity proxies only",
        ),
        "checkpoint" => checkpoint_path,
        "command_line" => copy(args),
    )
    open(summary_path, "w") do io
        JSON.print(io, summary, 2)
    end
    println("RESULT $summary_path")
    shown_test_accuracy = round(test_metrics["accuracy"]; digits=4)
    shown_crossings = round(test_metrics["upcrossings_per_sample"]; digits=3)
    shown_occupancy = round(test_metrics["occupancy_per_sample"]; digits=3)
    println("test_accuracy=$shown_test_accuracy " *
            "upcrossings_per_sample=$shown_crossings occupancy_per_sample=$shown_occupancy")
end

if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    main()
end
