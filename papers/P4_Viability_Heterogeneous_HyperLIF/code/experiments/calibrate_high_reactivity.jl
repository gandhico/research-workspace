#!/usr/bin/env julia

"""Screen HyperLIF parameters for a high-reactivity regime without early depolarization block.

This is a mechanism calibration on synthetic constant currents, never a task-accuracy search.
Candidates must later be retested on training-current quantiles from each dataset.
"""

using HyperLIFLearning
include(joinpath(@__DIR__, "regime_probe.jl"))

function main(args=ARGS)
    output = isempty(args) ?
        abspath(joinpath(@__DIR__, "..", "results", "high_reactivity_calibration.csv")) :
        abspath(args[1])
    mkpath(dirname(output))
    drives = collect(0.5f0:0.1f0:3f0)
    rows = NamedTuple[]
    for threshold in (0.75f0, 0.90f0, 1.05f0),
        reset_gain in (100f0, 200f0, 400f0),
        tau_r in (0.0005f0, 0.001f0, 0.002f0),
        gamma in (0.05f0, 0.10f0, 0.20f0),
        alpha in (30f0, 60f0, 100f0)
        config = HyperConfig(cell=:hyperlif, architecture=:dense,
                             learning_mode=:continuous, readout=:hybrid_vr,
                             tau_v=0.012f0, tau_r=tau_r, gamma=gamma, alpha=alpha,
                             v_threshold=threshold, event_threshold=threshold,
                             reset_gain=reset_gain)
        results = [simulate(config, drive; neurons=1, steps=300) for drive in drives]
        event_rates = getproperty.(results, :event_rate)
        occupancy_rates = getproperty.(results, :occupancy_rate)
        peak, peak_index = findmax(event_rates)
        block_fraction = mean((event_rates .<= 0.005f0) .& (occupancy_rates .>= 0.90f0))
        active_fraction = mean((event_rates .>= 0.04f0) .& (event_rates .<= 0.30f0))
        score = peak + 0.10f0 * active_fraction - 0.20f0 * block_fraction
        push!(rows, (score=score, threshold=threshold, reset_gain=reset_gain,
                     tau_r=tau_r, gamma=gamma, alpha=alpha,
                     peak_event_rate=peak, peak_drive=drives[peak_index],
                     active_fraction=active_fraction, block_fraction=block_fraction))
    end
    sort!(rows; by=row -> row.score, rev=true)
    open(output, "w") do io
        println(io, join(keys(rows[1]), ','))
        for row in rows
            println(io, join(values(row), ','))
        end
    end
    println("RESULT $output")
    println("BEST $(rows[1])")
end

main()

