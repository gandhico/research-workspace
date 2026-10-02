#!/usr/bin/env julia

"""Is the 20-bin cache horizon what prevents repeated upward crossings?

`reachable_rate_envelope.jl` shows every regime saturating near one crossing per neuron per
20-step SHD sequence. Two explanations compete: the horizon is too short for a second crossing,
or the input statistics do not sustain one. This script removes the input from the question by
driving each regime with constant current at four horizons. If a regime crosses repeatedly at
20 steps under constant drive, the horizon is not the limiter and the cause lies in the data.

Evidence for finding F2 in `PROGRESS_REGISTER.md`. Synthetic currents only; no cache is read.
"""

using HyperLIFLearning
using Statistics
using ViabilityHyperLIF

function simulate(config, drive; neurons=64, steps=500)
    template = zeros(Float32, neurons, 1)
    state = initial_state(template, neurons, 1, Float32(steps) * config.dt + config.dt)
    mix = zeros(Float32, neurons, 3)
    crossings, occupancy = 0f0, 0f0
    for step in 1:steps
        state, output = neuron_step(state, fill(Float32(drive), neurons, 1), config, mix;
                                    step_start=Float32(step - 1) * config.dt)
        crossings += sum(output.event)
        occupancy += sum(output.occupancy)
    end
    return (event_rate=crossings / Float32(neurons * steps),
            occupancy_rate=occupancy / Float32(neurons * steps),
            per_neuron=crossings / Float32(neurons))
end

function main(args=ARGS)
    output = isempty(args) ?
        abspath(joinpath(@__DIR__, "..", "results", "horizon_probe.csv")) : abspath(args[1])
    mkpath(dirname(output))
    regimes = default_regimes()
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    configs = build_population_configs(base, regimes)
    horizons = (20, 50, 100, 500)
    drives = 0f0:0.10f0:4f0

    rows = NamedTuple[]
    println("regime,horizon,best_event_rate,crossings_per_neuron,best_drive")
    for (regime, config) in zip(regimes, configs), steps in horizons
        best = (event_rate=-1f0, occupancy_rate=0f0, per_neuron=0f0)
        best_drive = 0f0
        for drive in drives
            metrics = simulate(config, drive; steps=steps)
            if metrics.event_rate > best.event_rate
                best, best_drive = metrics, drive
            end
        end
        push!(rows, (regime=regime.name, horizon=steps, event_rate=best.event_rate,
                     crossings_per_neuron=best.per_neuron, drive=best_drive))
        println(join((regime.name, steps, round(best.event_rate; digits=4),
                      round(best.per_neuron; digits=2), best_drive), ','))
    end

    open(output, "w") do io
        println(io, join(keys(rows[1]), ','))
        for row in rows
            println(io, join(values(row), ','))
        end
    end
    println()
    println("RESULT $output")
    short = filter(row -> row.horizon == 20, rows)
    repeaters = filter(row -> row.crossings_per_neuron >= 2f0, short)
    if isempty(repeaters)
        println("VERDICT at 20 steps no regime crosses repeatedly even under constant drive; " *
                "the horizon is a genuine limiter")
    else
        names = join(string.(getproperty.(repeaters, :regime)), ", ")
        println("VERDICT at 20 steps these regimes still cross repeatedly under constant drive: " *
                "$names. The horizon is not the limiter; the input statistics are.")
    end
end

main()
