#!/usr/bin/env julia

"""Deterministic experiment matrices for the Julia HyperLIF learning program."""

function grid_cli(args)
    options = Dict(
        "profile" => "thursday",
        "cache-dir" => get(ENV, "HLL_CACHE", ""),
        "results-root" => get(ENV, "HLL_JULIA_RESULTS", "results/julia_learning"),
        "device" => "auto",
        "index" => "",
        "bundle-index" => "",
        "count" => "false",
        "bundle-count" => "false",
    )
    i = 1
    while i <= length(args)
        token = args[i]
        startswith(token, "--") || error("unexpected argument: $token")
        item = token[3:end]
        if occursin('=', item)
            key, value = split(item, '='; limit=2)
            haskey(options, key) || error("unknown option --$key")
            options[key] = value
        elseif item in ("count", "bundle-count")
            options[item] = "true"
        else
            haskey(options, item) || error("unknown option --$item")
            i == length(args) && error("missing value for --$item")
            i += 1
            options[item] = args[i]
        end
        i += 1
    end
    return options
end

function caches_in(directory)
    isempty(directory) && error("set HLL_CACHE or pass --cache-dir")
    isdir(directory) || error("cache directory does not exist: $directory")
    caches = sort(filter(path -> endswith(lowercase(path), ".h5"),
                         readdir(directory; join=true)))
    isempty(caches) && error("no .h5 caches found in $directory")
    return caches
end

function architecture_variants(profile)
    base = [(architecture="dense", delay_mode="causal"),
            (architecture="recurrent", delay_mode="causal"),
            (architecture="delay", delay_mode="causal")]
    profile == "serious" && push!(base, (architecture="delay", delay_mode="centered"))
    return base
end

function mode_readouts(profile, cell)
    continuous = cell == "next" ? "hybrid_next" : "hybrid_vr"
    if profile in ("smoke", "thursday")
        return [(mode="continuous", readout=continuous),
                (mode="surrogate", readout="hybrid_zr"),
                (mode="event_time", readout="hybrid_time_vr")]
    elseif profile == "serious"
        return [(mode="continuous", readout=continuous),
                (mode="surrogate", readout="spike_count"),
                (mode="surrogate", readout="hybrid_zr"),
                (mode="event_time", readout="first_event_time"),
                (mode="event_time", readout="hybrid_time_vr")]
    end
    error("profile must be smoke, thursday, or serious")
end

function profile_values(profile)
    profile == "smoke" && return (seeds=1:1, epochs=1, hidden=24,
                                    batch=16, max_train=96, max_test=64,
                                    patience=1)
    profile == "thursday" && return (seeds=1:1, epochs=3, hidden=64,
                                      batch=32, max_train=1024, max_test=512,
                                      patience=3)
    profile == "serious" && return (seeds=1:5, epochs=40, hidden=256,
                                     batch=64, max_train=0, max_test=0,
                                     patience=8)
    error("profile must be smoke, thursday, or serious")
end

function experiment_grid(profile, cache_directory, results_root, device)
    values = profile_values(profile)
    jobs = NamedTuple[]
    for cache in caches_in(cache_directory), variant in architecture_variants(profile),
        cell in ("hyperlif", "adaptive", "next"), seed in values.seeds,
        learning in mode_readouts(profile, cell)
        arguments = [
            "--cache=$cache",
            "--architecture=$(variant.architecture)",
            "--delay-mode=$(variant.delay_mode)",
            "--cell=$cell",
            "--learning-mode=$(learning.mode)",
            "--readout=$(learning.readout)",
            "--seed=$seed",
            "--epochs=$(values.epochs)",
            "--hidden=$(values.hidden)",
            "--batch-size=$(values.batch)",
            "--max-train=$(values.max_train)",
            "--max-test=$(values.max_test)",
            "--patience=$(values.patience)",
            "--device=$device",
            "--results-root=$results_root",
            "--skip-existing",
        ]
        # One Julia process handles all three/five modes for a fixed seed and
        # neuron/architecture.  This amortizes the large one-time AD compile.
        bundle_key = (cache, variant.architecture, variant.delay_mode, cell, seed)
        push!(jobs, (arguments=arguments, bundle_key=bundle_key))
    end
    return jobs
end

function experiment_bundles(jobs)
    keys_in_order = unique(job.bundle_key for job in jobs)
    return [[job.arguments for job in jobs if job.bundle_key == key]
            for key in keys_in_order]
end

function shell_quote(argument)
    occursin(r"[\s'\"]", argument) || return argument
    return "'" * replace(argument, "'" => "'\"'\"'") * "'"
end

function grid_main(args=ARGS)
    options = grid_cli(args)
    jobs = experiment_grid(options["profile"], options["cache-dir"],
                           options["results-root"], options["device"])
    bundles = experiment_bundles(jobs)
    options["count"] == "true" && (println(length(jobs)); return)
    options["bundle-count"] == "true" && (println(length(bundles)); return)
    if !isempty(options["index"])
        index = parse(Int, options["index"]) + 1  # SLURM is zero based
        1 <= index <= length(jobs) || error("index is outside 0:$(length(jobs)-1)")
        println(join(shell_quote.(jobs[index].arguments), " "))
        return
    end
    if !isempty(options["bundle-index"])
        index = parse(Int, options["bundle-index"]) + 1
        1 <= index <= length(bundles) || error("bundle index is outside 0:$(length(bundles)-1)")
        for arguments in bundles[index]
            println(join(shell_quote.(arguments), " "))
        end
        return
    end
    for (index, job) in enumerate(jobs)
        println(index - 1, '\t', join(shell_quote.(job.arguments), " "))
    end
end

if abspath(PROGRAM_FILE) == abspath(@__FILE__)
    grid_main()
end

