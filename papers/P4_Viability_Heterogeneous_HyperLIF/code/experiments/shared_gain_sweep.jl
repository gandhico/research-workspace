#!/usr/bin/env julia

"""Does a single shared input gain separate the four regimes on a real cache?

A usable gain must satisfy four conditions at once: the intended rate ordering
holds, the busiest population is not saturating (occupancy below 0.10), the
quietest population is still measurably active (a ratio earned by silencing one
population is an artifact, not a regime), and the separation ratio is as large
as those constraints allow.

`reachable_rate_envelope.jl` shows that per-regime input gain is the wrong lever:
above roughly gain 8 every regime saturates near one upward crossing per neuron
per sequence regardless of its intrinsic parameters. This script sweeps a single
*shared* gain across the low, unsaturated range and reports, for each gain, the
four measured crossing rates, their max/min separation ratio, whether the
intended ordering subthreshold < sparse < regular < burst holds, and the burst
occupancy as a saturation guard.

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

function main(args=ARGS)
    isempty(args) && error("usage: shared_gain_sweep.jl CACHE.h5 [OUTPUT.csv]")
    cache = abspath(args[1])
    output = length(args) >= 2 ? abspath(args[2]) :
        abspath(joinpath(@__DIR__, "..", "results", "shared_gain_sweep.csv"))
    mkpath(dirname(output))

    x_train, _, _, _, n_classes = ExistingHarness.load_cache(cache)
    calibration_count = min(96, size(x_train, 3))
    input = ExistingHarness.input_batch(x_train, collect(1:calibration_count))
    time_steps = size(input, 3)
    hidden = 12
    seeds = (7101, 7102, 7103)

    regimes = default_regimes()
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    scales = Float32[0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0,
                     1.2, 1.4, 1.7, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0]

    rows = NamedTuple[]
    println("shared_gain,", join(string.(getproperty.(regimes, :name)), ","),
            ",separation_ratio,ordering_holds,burst_occupancy")
    for scale in scales
        rates = Float32[]
        occupancies = Float32[]
        for regime in regimes
            config = only(build_population_configs(
                base, (ViabilityHyperLIF._replace_input_scale(regime, scale),)))
            per_seed_rate = Float32[]
            per_seed_occupancy = Float32[]
            for seed in seeds
                parameters = init_parameters(MersenneTwister(seed), size(x_train, 1),
                                             hidden, n_classes, config)
                _, auxiliary = forward(parameters, input, config)
                activity = population_activity(auxiliary, hidden, time_steps)
                push!(per_seed_rate, activity.event_rate)
                push!(per_seed_occupancy, activity.occupancy_rate)
            end
            push!(rates, mean(per_seed_rate))
            push!(occupancies, mean(per_seed_occupancy))
        end
        separation = minimum(rates) > 0f0 ? maximum(rates) / minimum(rates) : Inf32
        ordering = issorted(rates)
        push!(rows, (shared_gain=scale, subthreshold=rates[1], sparse=rates[2],
                     regular=rates[3], burst=rates[4],
                     separation_ratio=separation, ordering_holds=ordering,
                     burst_occupancy=occupancies[4]))
        println(join((scale, rates..., separation, ordering, occupancies[4]), ','))
    end

    open(output, "w") do io
        println(io, join(keys(rows[1]), ','))
        for row in rows
            println(io, join(values(row), ','))
        end
    end
    println()
    println("RESULT $output")
    # A separation ratio earned by silencing the quietest population is an
    # artifact, not a regime. The subthreshold band must stay measurably alive.
    usable = filter(row -> row.ordering_holds && isfinite(row.separation_ratio) &&
                           row.burst_occupancy < 0.10f0 &&
                           row.subthreshold >= 0.002f0, rows)
    if isempty(usable)
        println("VERDICT no shared gain gives ordered, separated, unsaturated regimes")
    else
        best = usable[argmax(getproperty.(usable, :separation_ratio))]
        println("VERDICT best shared gain=$(best.shared_gain) " *
                "separation=$(round(best.separation_ratio; digits=2)) " *
                "burst_occupancy=$(round(best.burst_occupancy; digits=4))")
    end
end

main()
