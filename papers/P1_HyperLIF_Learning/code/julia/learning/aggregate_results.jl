#!/usr/bin/env julia

using JSON
using Statistics

root = abspath(length(ARGS) >= 1 ? ARGS[1] : "results/julia_learning")
output = abspath(length(ARGS) >= 2 ? ARGS[2] : joinpath(root, "summary.csv"))
files = sort(filter(path -> basename(path) == "summary.json",
                    [joinpath(directory, file) for (directory, _, names) in walkdir(root)
                     for file in names]))
isempty(files) && error("no summary.json files found below $root")

columns = ["experiment_id", "dataset", "architecture", "cell", "learning_mode",
           "readout", "seed", "parameters", "best_epoch", "validation_accuracy",
           "test_accuracy", "test_loss", "upcrossings_per_sample",
           "occupancy_per_sample", "no_event_neuron_fraction",
           "minimum_crossing_speed", "wall_seconds", "device", "status"]

function row(summary)
    return Any[
        summary["experiment_id"], basename(summary["dataset"]["path"]),
        summary["model"]["architecture"], summary["model"]["cell"],
        summary["model"]["learning_mode"], summary["model"]["readout"],
        summary["optimization"]["seed"], summary["model"]["parameter_count"],
        summary["optimization"]["best_epoch_by_validation_accuracy"],
        summary["optimization"]["best_validation_accuracy"], summary["test"]["accuracy"],
        summary["test"]["loss"], summary["test"]["upcrossings_per_sample"],
        summary["test"]["occupancy_per_sample"],
        summary["test"]["no_event_neuron_fraction"],
        summary["test"]["minimum_crossing_speed"], summary["wall_seconds"],
        summary["compute"]["device"], summary["status"],
    ]
end

escape_csv(value) = value === nothing ? "" :
    occursin(r"[,\"\n]", string(value)) ? "\"" * replace(string(value), "\"" => "\"\"") * "\"" : string(value)

mkpath(dirname(output))
open(output, "w") do io
    println(io, join(columns, ','))
    for path in files
        summary = JSON.parsefile(path)
        println(io, join(escape_csv.(row(summary)), ','))
    end
end
println("wrote $(length(files)) rows to $output")

