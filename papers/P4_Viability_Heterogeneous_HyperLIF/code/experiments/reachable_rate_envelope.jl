#!/usr/bin/env julia

"""Reachable upward-crossing envelope for each regime on a real input cache.

`calibrate_dataset_activity.jl` selected one `input_scale` per regime by matching
target rate bands whose values were chosen from the *synthetic constant-current*
atlas. This script asks the prior question that calibration assumed: on the real
training input distribution, what event rate can each regime reach at all?

For every regime it sweeps `input_scale` over a wide log grid and records the
upcrossing rate, occupancy, and a block indicator. The reported maximum over the
grid is the regime's reachable ceiling on this cache. A target band whose lower
edge exceeds that ceiling is unreachable, and any homeostatic rule pointed at it
will drive its threshold offset to the clamp instead of regulating activity.

Training inputs only; no labels, no test examples, no accuracy.
"""

using HDF5
using HyperLIFLearning
using Random
using Statistics
using ViabilityHyperLIF

module ExistingHarness
include(joinpath(@__DIR__, "..", "..", "..", "P1_HyperLIF_Learning",
                 "code", "julia", "learning", "train_hpc.jl"))
end

function replace_scale(regime::RegimeSpec, scale)
    names = fieldnames(RegimeSpec)
    source = NamedTuple{names}(Tuple(getfield(regime, name) for name in names))
    return RegimeSpec(; merge(source, (input_scale=Float32(scale),))...)
end

"""Blocked means the membrane sits above threshold while almost never re-crossing."""
is_blocked(activity) = activity.occupancy_rate > 0.50f0 && activity.event_rate < 0.01f0

function main(args=ARGS)
    isempty(args) && error("usage: reachable_rate_envelope.jl CACHE.h5 [OUTPUT.csv]")
    cache = abspath(args[1])
    output = length(args) >= 2 ? abspath(args[2]) :
        abspath(joinpath(@__DIR__, "..", "results", "reachable_rate_envelope.csv"))
    mkpath(dirname(output))

    x_train, y_train, _, _, n_classes = ExistingHarness.load_cache(cache)
    calibration_count = min(96, size(x_train, 3))
    input = ExistingHarness.input_batch(x_train, collect(1:calibration_count))
    time_steps = size(input, 3)
    hidden = 12
    seeds = (7101, 7102, 7103)

    regimes = default_regimes()
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    scales = Float32[0.5, 1, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]

    rows = NamedTuple[]
    for regime in regimes, scale in scales
        config = only(build_population_configs(base, (replace_scale(regime, scale),)))
        for seed in seeds
            rng = MersenneTwister(seed)
            parameters = init_parameters(rng, size(x_train, 1), hidden, n_classes, config)
            _, auxiliary = forward(parameters, input, config)
            activity = population_activity(auxiliary, hidden, time_steps)
            push!(rows, (regime=regime.name, input_scale=scale, seed=seed,
                         event_rate=activity.event_rate,
                         occupancy_rate=activity.occupancy_rate,
                         gate_mean=activity.gate_mean,
                         no_event_fraction=activity.no_event_fraction,
                         blocked=is_blocked(activity)))
        end
    end

    open(output, "w") do io
        println(io, join(keys(rows[1]), ','))
        for row in rows
            println(io, join(values(row), ','))
        end
    end
    println("RESULT $output")
    println()
    println("cache=$cache")
    println("batch=$calibration_count time_steps=$time_steps hidden=$hidden seeds=$(collect(seeds))")
    println()
    println("regime,target_min,target_max,ceiling_rate,ceiling_scale,target_reachable,ceiling_blocked")
    for regime in regimes
        candidates = filter(row -> row.regime == regime.name && !row.blocked, rows)
        # Mean over seeds at each scale, then the best scale.
        by_scale = Dict{Float32,Vector{Float32}}()
        for row in candidates
            push!(get!(by_scale, row.input_scale, Float32[]), row.event_rate)
        end
        if isempty(by_scale)
            println("$(regime.name),$(regime.target_rate_min),$(regime.target_rate_max),0,NA,false,true")
            continue
        end
        best_scale = argmax(scale -> mean(by_scale[scale]), collect(keys(by_scale)))
        ceiling = mean(by_scale[best_scale])
        reachable = ceiling >= regime.target_rate_min
        blocked_at_top = any(row -> row.regime == regime.name &&
                             row.input_scale == maximum(scales) && row.blocked, rows)
        println("$(regime.name),$(regime.target_rate_min),$(regime.target_rate_max)," *
                "$(round(ceiling; digits=5)),$(best_scale),$(reachable),$(blocked_at_top)")
    end
end

main()
