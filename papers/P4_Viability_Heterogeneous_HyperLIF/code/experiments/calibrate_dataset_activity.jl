#!/usr/bin/env julia

"""Label-free activity calibration on a training-only HDF5 batch.

The script selects only `input_scale` for each fixed intrinsic regime by
matching upward-crossing bands. It never uses test inputs, class labels, or
accuracy during calibration.
"""

using HDF5
using HyperLIFLearning
using Random
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

function main(args=ARGS)
    isempty(args) && error("usage: calibrate_dataset_activity.jl CACHE.h5 [OUTPUT.csv]")
    cache = abspath(args[1])
    output = length(args) >= 2 ? abspath(args[2]) :
        abspath(joinpath(@__DIR__, "..", "results", "dataset_activity_calibration.csv"))
    mkpath(dirname(output))
    x_train, y_train, _, _, n_classes = ExistingHarness.load_cache(cache)
    calibration_count = min(96, size(x_train, 3))
    input = ExistingHarness.input_batch(x_train, collect(1:calibration_count))
    regimes = default_regimes()
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    scales = Float32[0.5, 1, 2, 4, 6, 8, 10, 12, 16, 20, 24, 32]
    rows = NamedTuple[]
    for (regime_index, regime) in enumerate(regimes), scale in scales
        candidate = replace_scale(regime, scale)
        config = only(build_population_configs(base, (candidate,)))
        rng = MersenneTwister(7100 + regime_index)
        parameters = init_parameters(rng, size(x_train, 1), 12, n_classes, config)
        _, auxiliary = forward(parameters, input, config)
        activity = population_activity(auxiliary, 12, size(input, 3))
        target = max(1f-4, (regime.target_rate_min + regime.target_rate_max) / 2f0)
        log_error = abs(log10(activity.event_rate + 1f-5) - log10(target + 1f-5))
        block_penalty = activity.occupancy_rate > 0.80f0 && activity.event_rate < 0.01f0 ? 5f0 : 0f0
        score = log_error + block_penalty
        push!(rows, (regime=regime.name, input_scale=scale,
                     event_rate=activity.event_rate,
                     occupancy_rate=activity.occupancy_rate,
                     gate_mean=activity.gate_mean,
                     no_event_fraction=activity.no_event_fraction,
                     target_rate=target, score=score))
    end
    open(output, "w") do io
        println(io, join(keys(rows[1]), ','))
        for row in rows
            println(io, join(values(row), ','))
        end
    end
    println("RESULT $output")
    for regime in regimes
        candidates = filter(row -> row.regime == regime.name, rows)
        best = candidates[argmin(getproperty.(candidates, :score))]
        println("RECOMMEND $(regime.name) input_scale=$(best.input_scale) " *
                "event_rate=$(round(best.event_rate; digits=5)) " *
                "occupancy=$(round(best.occupancy_rate; digits=5))")
    end
end

main()
