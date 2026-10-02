#!/usr/bin/env julia

"""Train a HyperLIF recognition model on the exact P1 HDF5 contract.

This runner is deliberately CPU-only. It reuses the P1 cache loader and class-stratified split
implementation, selects a checkpoint only on validation accuracy, and touches the test split once.

`--model` selects one of three budget-matched families built from the same regime bank:

  heterogeneous  four regimes, `hidden-per-population` neurons each
  ensemble       four populations that all carry the bank's mean parameters
  homogeneous    one population carrying the whole hidden budget at mean parameters

All three hold total hidden state equal and, for the dense/`:hyperlif` contract, agree on
effective parameter count to within the handful of extra readout biases and mixer logits that the
multi-population families require. `ensemble` is the control that separates a heterogeneity effect
from a plain ensembling effect; `homogeneous` is the single-population null. Julia LIF/PLIF/ALIF
controls remain a separate required experiment.
"""

using Dates
using HDF5
using HyperLIFLearning
using JSON
using Optimisers
using Random
using SHA
using Serialization
using Statistics
using ViabilityHyperLIF
using Zygote

module ExistingHarness
include(joinpath(@__DIR__, "..", "..", "..", "P1_HyperLIF_Learning",
                 "code", "julia", "learning", "train_hpc.jl"))
end

const DEFAULTS = Dict(
    "cache" => "",
    "seed" => "1",
    "epochs" => "5",
    "hidden-per-population" => "16",
    "batch-size" => "16",
    "lr" => "0.001",
    "weight-decay" => "0.0001",
    "validation-fraction" => "0.10",
    "patience" => "3",
    "max-train" => "0",
    "max-test" => "0",
    "results-root" => "results/recognition",
    "regime-profile" => "auto",
    "model" => "heterogeneous",
    "homeostasis" => "true",
    "homeostasis-interval" => "0",
    "homeostasis-rate" => "1.0",
    "homeostasis-ema" => "0.5",
    "smoke" => "false",
)

parse_bool(value) = lowercase(value) in ("1", "true", "yes", "on")

function parse_cli(args)
    options = copy(DEFAULTS)
    i = 1
    while i <= length(args)
        token = args[i]
        startswith(token, "--") || error("unexpected positional argument: $token")
        item = token[3:end]
        if occursin('=', item)
            key, value = split(item, '='; limit=2)
            haskey(options, key) || error("unknown option --$key")
            options[key] = value
        elseif item == "smoke"
            options[item] = "true"
        else
            haskey(options, item) || error("unknown option --$item")
            i == length(args) && error("missing value for --$item")
            i += 1
            options[item] = args[i]
        end
        i += 1
    end
    isempty(options["cache"]) && error("--cache is required")
    if parse_bool(options["smoke"])
        merge!(options, Dict("epochs" => "1", "hidden-per-population" => "3",
                             "batch-size" => "8", "max-train" => "48",
                             "max-test" => "40", "patience" => "1"))
    end
    return options
end

function copy_parameters(parameters)
    populations = Tuple(NamedTuple{keys(population)}(map(copy, values(population)))
                        for population in parameters.populations)
    return (populations=populations, mix_logits=copy(parameters.mix_logits))
end

function parameter_count(parameters)
    return sum(HyperLIFLearning.parameter_count, parameters.populations) +
           length(parameters.mix_logits)
end

"""Parameters that the declared architecture actually reads in the forward pass.

`init_parameters` always allocates the recurrent, delay, and dendritic blocks, so the raw count
scales with the square of the hidden width even under `:dense`, where `W_rec` is never touched.
Budget matching between a wide single population and several narrow ones is only meaningful on the
parameters that are used.
"""
function effective_parameter_count(parameters, configs)
    total = 0
    for (population, config) in zip(parameters.populations, configs)
        total += length(population.W_in) + length(population.b_in) +
                 length(population.W_head) + length(population.b_head)
        config.architecture == :recurrent && (total += length(population.W_rec))
        config.architecture == :delay && (total += length(population.delay_kernel))
        config.cell == :next && (total += length(population.dendritic_mix))
    end
    return total + length(parameters.mix_logits)
end

"""Resolve the regime bank and per-population width for a budget-matched family."""
function model_family(name, bank, hidden_per_population)
    populations = length(bank)
    name == "heterogeneous" && return bank, hidden_per_population
    averaged = mean_regime(bank)
    if name == "ensemble"
        indexed = Tuple(ViabilityHyperLIF._replace_fields(averaged, NamedTuple())
                        for _ in 1:populations)
        return indexed, hidden_per_population
    end
    name == "homogeneous" &&
        return (averaged,), hidden_per_population * populations
    error("model must be heterogeneous, ensemble, or homogeneous")
end

function prediction_accuracy(logits, labels)
    predictions = [argmax(view(logits, :, column)) for column in axes(logits, 2)]
    return Float32(mean(predictions .== labels))
end

"""Per-population activity for one already-materialized batch."""
function batch_activity(parameters, input, configs, hidden)
    _, auxiliary = heterogeneous_forward(parameters, input, configs)
    return [population_activity(auxiliary.populations[index], hidden, size(input, 3))
            for index in eachindex(configs)]
end

function batch_metrics(parameters, input, labels, targets, configs, hidden)
    logits, auxiliary = heterogeneous_forward(parameters, input, configs)
    shifted = logits .- maximum(logits; dims=1)
    log_probabilities = shifted .- log.(sum(exp.(shifted); dims=1))
    loss = -sum(targets .* log_probabilities) / Float32(size(input, 2))
    activities = [population_activity(auxiliary.populations[index], hidden, size(input, 3))
                  for index in eachindex(configs)]
    population_accuracies = [prediction_accuracy(auxiliary.population_logits[index], labels)
                             for index in eachindex(configs)]
    return (loss=Float32(loss), accuracy=prediction_accuracy(logits, labels),
            weights=Float32.(auxiliary.weights), activities=activities,
            population_accuracies=population_accuracies)
end

function evaluate(parameters, x, labels, indices, n_classes, configs, hidden, batch_size)
    count = 0
    loss_sum = 0.0
    accuracy_sum = 0.0
    weights_sum = zeros(Float64, length(configs))
    population_accuracy_sum = zeros(Float64, length(configs))
    activity_sums = [Dict("event_rate" => 0.0, "occupancy_rate" => 0.0,
                          "gate_mean" => 0.0, "no_event_fraction" => 0.0)
                     for _ in configs]
    for start in 1:batch_size:length(indices)
        selected = indices[start:min(start + batch_size - 1, length(indices))]
        input = ExistingHarness.input_batch(x, selected)
        targets = ExistingHarness.one_hot(labels[selected], n_classes)
        metrics = batch_metrics(parameters, input, labels[selected], targets, configs, hidden)
        n = length(selected)
        count += n
        loss_sum += metrics.loss * n
        accuracy_sum += metrics.accuracy * n
        weights_sum .+= metrics.weights .* n
        population_accuracy_sum .+= metrics.population_accuracies .* n
        for index in eachindex(configs)
            for name in keys(activity_sums[index])
                activity_sums[index][name] += getproperty(metrics.activities[index], Symbol(name)) * n
            end
        end
    end
    populations = [Dict(name => value / count for (name, value) in activity_sums[index])
                   for index in eachindex(configs)]
    for index in eachindex(populations)
        populations[index]["standalone_accuracy"] = population_accuracy_sum[index] / count
    end
    return Dict{String,Any}(
        "loss" => loss_sum / count,
        "accuracy" => accuracy_sum / count,
        "mix_weights" => weights_sum ./ count,
        "populations" => populations,
    )
end

const CALIBRATION_NOTES = Dict(
    "generic" => "uncalibrated generic priors",
    "shd_training_calibrated" =>
        "per-regime training-only input-gain calibration; see results/dataset_activity_calibration.csv. " *
        "Superseded: two of its four gains are search-grid boundaries and the regular/burst " *
        "populations saturate on this cache (results/reachable_rate_envelope.csv).",
    "shd_shared_gain" =>
        "single shared input gain in the unsaturated window; intrinsic parameters set the regime. " *
        "See results/shared_gain_sweep.csv.",
)

function main(args=ARGS)
    options = parse_cli(args)
    seed = parse(Int, options["seed"])
    epochs = parse(Int, options["epochs"])
    hidden = parse(Int, options["hidden-per-population"])
    batch_size = parse(Int, options["batch-size"])
    rng = MersenneTwister(seed)
    cache = abspath(options["cache"])
    x_train, y_train, x_test, y_test, n_classes = ExistingHarness.load_cache(cache)
    selected_train = ExistingHarness.capped_indices(
        rng, y_train, parse(Int, options["max-train"]))
    selected_test = ExistingHarness.capped_indices(
        rng, y_test, parse(Int, options["max-test"]))
    train_indices, validation_indices = ExistingHarness.train_validation_split(
        rng, selected_train, y_train, parse(Float32, options["validation-fraction"]))

    profile = lowercase(options["regime-profile"])
    profile in ("auto", "generic", "shd_training_calibrated", "shd_shared_gain") ||
        error("regime-profile must be auto, generic, shd_training_calibrated, or shd_shared_gain")
    is_shd = occursin("shd", lowercase(basename(cache)))
    resolved_profile = profile == "auto" ? (is_shd ? "shd_shared_gain" : "generic") : profile
    bank = resolved_profile == "shd_shared_gain" ? shd_shared_gain_regimes() :
           resolved_profile == "shd_training_calibrated" ? shd_calibrated_regimes() :
           default_regimes()
    model = lowercase(options["model"])
    regimes, hidden = model_family(model, bank, hidden)
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    configs = build_population_configs(base, regimes)
    reference_configs = configs
    parameters = init_heterogeneous_parameters(
        rng, size(x_train, 1), hidden, n_classes, configs)
    optimizer = Optimisers.AdamW(parse(Float32, options["lr"]), (0.9f0, 0.999f0),
                                 parse(Float32, options["weight-decay"]))
    optimizer_state = Optimisers.setup(optimizer, parameters)
    best_parameters = copy_parameters(parameters)
    best_configs = configs
    best_accuracy = -Inf
    best_epoch = 0
    trace = Vector{Dict{String,Any}}()
    homeostatic_state = HomeostaticState(length(regimes))
    use_homeostasis = parse_bool(options["homeostasis"])
    homeostasis_interval = parse(Int, options["homeostasis-interval"])
    patience = parse(Int, options["patience"])
    started = now(UTC)
    wall_start = time()

    for epoch in 1:epochs
        order = train_indices[randperm(rng, length(train_indices))]
        total_loss, total_examples = 0.0, 0
        batch_index = 0
        for start in 1:batch_size:length(order)
            batch_index += 1
            selected = order[start:min(start + batch_size - 1, length(order))]
            input = ExistingHarness.input_batch(x_train, selected)
            targets = ExistingHarness.one_hot(y_train[selected], n_classes)
            loss, back = Zygote.withgradient(parameters) do candidate
                heterogeneous_classification_loss(candidate, input, targets, configs)
            end
            isfinite(loss) || error("non-finite training loss at epoch $epoch")
            optimizer_state, parameters = Optimisers.update(optimizer_state, parameters, back[1])
            total_loss += loss * length(selected)
            total_examples += length(selected)
            # A homeostatic rule that only fires between epochs cannot influence a
            # checkpoint selected at epoch 1, which silently makes paired on/off runs
            # identical. A positive interval lets the slow rule act during the epoch.
            if use_homeostasis && homeostasis_interval > 0 &&
               batch_index % homeostasis_interval == 0
                batch_rates = Float32[activity.event_rate for activity in
                                      batch_activity(parameters, input, configs, hidden)]
                homeostatic_state = update_homeostasis(
                    homeostatic_state, batch_rates, regimes;
                    ema_fraction=parse(Float32, options["homeostasis-ema"]),
                    learning_rate=parse(Float32, options["homeostasis-rate"]), gate=1f0)
                configs = apply_threshold_offsets(reference_configs, homeostatic_state)
            end
        end
        validation = evaluate(parameters, x_train, y_train, validation_indices,
                              n_classes, configs, hidden, batch_size)
        training_activity = evaluate(parameters, x_train, y_train, train_indices,
                                     n_classes, configs, hidden, batch_size)
        observed_rates = Float32[population["event_rate"]
                                 for population in training_activity["populations"]]
        current_penalty = rate_band_penalty(observed_rates, regimes)
        push!(trace, Dict("epoch" => epoch,
                          "train_loss" => total_loss / total_examples,
                          "validation_loss" => validation["loss"],
                          "validation_accuracy" => validation["accuracy"],
                          "training_event_rates" => observed_rates,
                          "rate_band_penalty" => current_penalty,
                          "threshold_offsets" => copy(homeostatic_state.threshold_offsets)))
        shown_train_loss = round(total_loss / total_examples; digits=5)
        shown_validation_accuracy = round(validation["accuracy"]; digits=4)
        println("epoch=$epoch train_loss=$shown_train_loss " *
                "validation_accuracy=$shown_validation_accuracy")
        if validation["accuracy"] > best_accuracy
            best_accuracy = validation["accuracy"]
            best_epoch = epoch
            best_parameters = copy_parameters(parameters)
            best_configs = configs
        elseif patience > 0 && epoch - best_epoch >= patience
            break
        end
        if use_homeostasis
            homeostatic_state = update_homeostasis(
                homeostatic_state, observed_rates, regimes;
                ema_fraction=parse(Float32, options["homeostasis-ema"]),
                learning_rate=parse(Float32, options["homeostasis-rate"]), gate=1f0)
            configs = apply_threshold_offsets(reference_configs, homeostatic_state)
        end
    end

    # A homeostasis=true run whose selected checkpoint still carries the untouched
    # reference thresholds is indistinguishable from homeostasis=false. Record that
    # rather than letting a paired comparison silently compare a model to itself.
    homeostasis_effective = use_homeostasis && any(
        best_configs[index].v_threshold != reference_configs[index].v_threshold
        for index in eachindex(best_configs))
    if use_homeostasis && !homeostasis_effective
        @warn "homeostasis had no effect on the selected checkpoint; this run is " *
              "numerically identical to homeostasis=false" best_epoch=best_epoch
    end

    test = evaluate(best_parameters, x_test, y_test, selected_test,
                    n_classes, best_configs, hidden, batch_size)
    run_id = "$(splitext(basename(cache))[1])__$(model)$(length(regimes))__" *
             "h$(hidden)__$(resolved_profile)__homeo$(use_homeostasis)__seed$(seed)__" *
             Dates.format(now(UTC), "yyyymmddTHHMMSS")
    run_directory = abspath(joinpath(options["results-root"], run_id))
    mkpath(run_directory)
    checkpoint = joinpath(run_directory, "checkpoint.jls")
    serialize(checkpoint, Dict("parameters" => best_parameters, "configs" => best_configs,
                               "regimes" => regimes, "best_epoch" => best_epoch))
    summary = Dict{String,Any}(
        "schema_version" => 1,
        "status" => "exploratory_complete",
        "started_at_utc" => string(started),
        "finished_at_utc" => string(now(UTC)),
        "wall_seconds" => time() - wall_start,
        "dataset" => Dict(
            "path" => cache,
            "sha256" => ExistingHarness.cache_sha256(cache),
            "input_features" => size(x_train, 1),
            "time_steps" => size(x_train, 2),
            "classes" => n_classes,
            "train_used" => length(train_indices),
            "validation_used" => length(validation_indices),
            "test_used" => length(selected_test),
            "split_rule" => "P1 class-stratified seeded cap and validation split",
        ),
        "model" => Dict(
            "family" => model,
            "populations" => length(regimes),
            "regimes" => string.([regime.name for regime in regimes]),
            "hidden_per_population" => hidden,
            "total_hidden" => hidden * length(regimes),
            "parameter_count" => parameter_count(best_parameters),
            "effective_parameter_count" =>
                effective_parameter_count(best_parameters, best_configs),
            "learning_mode" => "continuous",
            "readout" => "hybrid_vr logit ensemble",
            "event_definition" => "upward threshold crossing",
            "readout_uses_events" => false,
            "regime_profile" => resolved_profile,
            "regime_calibration" => CALIBRATION_NOTES[resolved_profile],
            "input_scales" => Float32[regime.input_scale for regime in regimes],
            "target_rate_bands" => [[regime.target_rate_min, regime.target_rate_max]
                                    for regime in regimes],
            "homeostasis" => use_homeostasis,
            "homeostasis_interval_batches" => homeostasis_interval,
            "homeostasis_rule" => "slow population-specific threshold offsets from training upcrossing bands",
            "homeostasis_effective" => homeostasis_effective,
            "final_threshold_offsets" => copy(homeostatic_state.threshold_offsets),
        ),
        "optimization" => Dict(
            "seed" => seed, "epochs_requested" => epochs,
            "epochs_completed" => length(trace), "best_epoch" => best_epoch,
            "best_validation_accuracy" => best_accuracy,
        ),
        "test" => test,
        "trace" => trace,
        "checkpoint" => checkpoint,
        "command_line" => copy(args),
        "claim_boundary" => "single run; a claim requires the matched heterogeneous/ensemble/homogeneous triple over paired seeds",
    )
    summary_path = joinpath(run_directory, "summary.json")
    open(summary_path, "w") do io
        JSON.print(io, summary, 2)
    end
    println("RESULT $summary_path")
    shown_test_accuracy = round(test["accuracy"]; digits=4)
    shown_mix_weights = round.(test["mix_weights"]; digits=3)
    println("test_accuracy=$shown_test_accuracy mix_weights=$shown_mix_weights")
end

main()
