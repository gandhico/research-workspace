#!/usr/bin/env julia

"""Aggregate the budget-matched heterogeneous / ensemble / homogeneous triple.

Reports every run, then the per-family summary, then the seed-paired differences that the
comparison actually rests on. With three seeds this reports effect sizes and ranges only; it
runs no significance test, because three paired seeds do not support one. The confirmation
budget in `RESEARCH_PROGRAM.md` Stage 3 is where inference belongs.

The decisive contrast is heterogeneous versus `ensemble`. Both hold four populations, equal
hidden state, and equal effective parameters; they differ only in whether the populations carry
distinct intrinsic parameters. Heterogeneous versus `homogeneous` alone would confound
heterogeneity with ensembling.
"""

using JSON
using Printf
using Statistics

const FAMILIES = ("heterogeneous", "ensemble", "homogeneous")

function load_runs(root)
    runs = Dict{String,Any}[]
    for (directory, _, files) in walkdir(root)
        "summary.json" in files || continue
        summary = JSON.parsefile(joinpath(directory, "summary.json"))
        push!(runs, summary)
    end
    isempty(runs) && error("no summary.json found under $root")
    return runs
end

key_of(run) = (run["model"]["family"], run["optimization"]["seed"])

function main(args=ARGS)
    root = isempty(args) ? joinpath(@__DIR__, "..", "results", "matched_triple") : args[1]
    runs = load_runs(abspath(root))
    sort!(runs, by=run -> (run["model"]["family"], run["optimization"]["seed"]))

    println("root = $(abspath(root))")
    println("runs = $(length(runs))")
    println()
    @printf("%-14s %5s %7s %7s %9s %9s %11s %s\n",
            "family", "seed", "hidden", "eff_par", "best_val", "test_acc", "test_loss", "population event rates")
    for run in runs
        model, optimization, test = run["model"], run["optimization"], run["test"]
        rates = [round(population["event_rate"]; digits=5) for population in test["populations"]]
        @printf("%-14s %5d %7d %7d %9.4f %9.4f %11.4f %s\n",
                model["family"], optimization["seed"], model["total_hidden"],
                model["effective_parameter_count"], optimization["best_validation_accuracy"],
                test["accuracy"], test["loss"], rates)
    end

    # Guard the premise of the comparison before reporting it.
    hidden = unique(run["model"]["total_hidden"] for run in runs)
    profiles = unique(run["model"]["regime_profile"] for run in runs)
    homeostasis = unique(run["model"]["homeostasis"] for run in runs)
    parameters = [run["model"]["effective_parameter_count"] for run in runs]
    println()
    println("budget check: total_hidden=$hidden profile=$profiles homeostasis=$homeostasis")
    println("budget check: effective parameter spread = $(maximum(parameters) - minimum(parameters)) " *
            "over $(minimum(parameters))")
    length(hidden) == 1 || @warn "families do not share total hidden state; the comparison is not matched"

    println()
    @printf("%-14s %6s %9s %9s %9s\n", "family", "seeds", "test_mean", "test_min", "test_max")
    accuracy = Dict{String,Dict{Int,Float64}}()
    for family in FAMILIES
        selected = filter(run -> run["model"]["family"] == family, runs)
        isempty(selected) && continue
        accuracy[family] = Dict(run["optimization"]["seed"] => run["test"]["accuracy"]
                                for run in selected)
        values = collect(Float64, (run["test"]["accuracy"] for run in selected))
        @printf("%-14s %6d %9.4f %9.4f %9.4f\n",
                family, length(values), mean(values), minimum(values), maximum(values))
    end

    # Regime separation is a premise of the heterogeneity claim, not a by-product:
    # if the populations converge to one rate during training there is no
    # heterogeneity left to credit for any accuracy difference.
    println()
    println("regime separation through training (heterogeneous runs)")
    @printf("%-6s %10s %10s %12s %14s
",
            "seed", "sep_first", "sep_last", "order_kept", "quietest_last")
    for run in filter(run -> run["model"]["family"] == "heterogeneous", runs)
        trace = run["trace"]
        isempty(trace) && continue
        separations = Float64[]
        ordered = 0
        for entry in trace
            rates = Float64.(entry["training_event_rates"])
            push!(separations, maximum(rates) / max(minimum(rates), 1e-9))
            issorted(rates) && (ordered += 1)
        end
        final_rates = Float64.(trace[end]["training_event_rates"])
        @printf("%-6d %10.1f %10.1f %8d/%-3d %14.5f
",
                run["optimization"]["seed"], separations[1], separations[end],
                ordered, length(trace), minimum(final_rates))
    end

    println()
    println("seed-paired differences (positive favours the first family)")
    for (left, right) in (("heterogeneous", "ensemble"), ("heterogeneous", "homogeneous"),
                          ("ensemble", "homogeneous"))
        haskey(accuracy, left) && haskey(accuracy, right) || continue
        shared = sort(collect(intersect(keys(accuracy[left]), keys(accuracy[right]))))
        isempty(shared) && continue
        deltas = [accuracy[left][seed] - accuracy[right][seed] for seed in shared]
        wins = count(>(0), deltas)
        @printf("%-14s - %-14s n=%d mean=%+.4f per-seed=%s wins=%d/%d\n",
                left, right, length(shared), mean(deltas),
                [round(delta; digits=4) for delta in deltas], wins, length(shared))
    end
    println()
    println("No significance test is reported: three paired seeds do not support one.")
    println("Read the heterogeneous-versus-ensemble row first; it is the only contrast that")
    println("isolates heterogeneity from ensembling at matched budget.")
end

main()
