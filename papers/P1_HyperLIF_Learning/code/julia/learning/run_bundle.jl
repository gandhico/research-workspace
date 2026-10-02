#!/usr/bin/env julia

include(joinpath(@__DIR__, "grid.jl"))
include(joinpath(@__DIR__, "train_hpc.jl"))

function bundle_main(args=ARGS)
    options = grid_cli(args)
    isempty(options["bundle-index"]) && error("run_bundle.jl requires --bundle-index")
    jobs = experiment_grid(options["profile"], options["cache-dir"],
                           options["results-root"], options["device"])
    bundles = experiment_bundles(jobs)
    index = parse(Int, options["bundle-index"]) + 1
    1 <= index <= length(bundles) || error("bundle index outside 0:$(length(bundles)-1)")

    failures = 0
    for arguments in bundles[index]
        try
            main(arguments)
        catch exception
            failures += 1
            showerror(stderr, exception, catch_backtrace())
            println(stderr)
        end
    end
    failures == 0 || error("$failures experiment(s) failed in bundle $(index - 1)")
end

bundle_main()
