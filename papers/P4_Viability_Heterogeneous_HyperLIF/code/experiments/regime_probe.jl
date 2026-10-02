#!/usr/bin/env julia

using HyperLIFLearning
using Statistics
using ViabilityHyperLIF

function simulate(config, drive; neurons=32, steps=500)
    template = zeros(Float32, neurons, 1)
    state = initial_state(template, neurons, 1, Float32(steps) * config.dt + config.dt)
    mix = zeros(Float32, neurons, 3)
    crossings = 0f0
    occupancy = 0f0
    gate_sum = 0f0
    voltage_sum = 0f0
    for step in 1:steps
        current = fill(Float32(drive), neurons, 1)
        state, output = neuron_step(state, current, config, mix;
                                    step_start=Float32(step - 1) * config.dt)
        crossings += sum(output.event)
        occupancy += sum(output.occupancy)
        gate_sum += sum(output.gate)
        voltage_sum += sum(output.voltage)
    end
    denominator = Float32(neurons * steps)
    return (event_rate=crossings / denominator,
            occupancy_rate=occupancy / denominator,
            gate_mean=gate_sum / denominator,
            voltage_mean=voltage_sum / denominator)
end

function main(args=ARGS)
    output = isempty(args) ?
        abspath(joinpath(@__DIR__, "..", "results", "regime_atlas.csv")) :
        abspath(args[1])
    mkpath(dirname(output))
    regimes = default_regimes()
    base = HyperConfig(cell=:hyperlif, architecture=:dense,
                       learning_mode=:continuous, readout=:hybrid_vr)
    configs = build_population_configs(base, regimes)
    drives = collect(0f0:0.10f0:4f0)
    open(output, "w") do io
        println(io, "regime,drive,event_rate,occupancy_rate,gate_mean,voltage_mean")
        for (regime, config) in zip(regimes, configs), drive in drives
            metrics = simulate(config, drive)
            println(io, join((regime.name, drive, metrics.event_rate,
                              metrics.occupancy_rate, metrics.gate_mean,
                              metrics.voltage_mean), ','))
        end
    end
    println("RESULT $output")
end

if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    main()
end
