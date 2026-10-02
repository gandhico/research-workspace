#!/usr/bin/env julia

using CUDA
using HDF5
using HyperLIFLearning
using Random
using Zygote

cache_directory = get(ENV, "HLL_CACHE", length(ARGS) >= 1 ? ARGS[1] : "")
isempty(cache_directory) && error("set HLL_CACHE or pass the cache directory")
isdir(cache_directory) || error("cache directory does not exist: $cache_directory")
caches = sort(filter(path -> endswith(lowercase(path), ".h5"),
                     readdir(cache_directory; join=true)))
isempty(caches) && error("no HDF5 caches found in $cache_directory")

println("Julia $(VERSION)")
cuda_available = try CUDA.functional() catch; false end
println("CUDA functional: $cuda_available")
for path in caches
    h5open(path, "r") do file
        keys_required = ("X_train", "y_train", "X_test", "y_test")
        all(haskey(file, key) for key in keys_required) ||
            error("$(basename(path)) lacks a required split")
        train_shape = size(file["X_train"])
        test_shape = size(file["X_test"])
        n_train = length(file["y_train"])
        n_test = length(file["y_test"])
        (n_train in train_shape && n_test in test_shape) ||
            error("$(basename(path)) has no sample dimension matching its labels")
        println("cache=$(basename(path)) train=$train_shape/$n_train test=$test_shape/$n_test")
    end
end

# Small mechanism-level derivative test independent of any dataset.
rng = MersenneTwister(7)
for mode in (:continuous, :surrogate, :event_time)
    config = HyperConfig(cell=:next, learning_mode=mode,
                         architecture=:recurrent,
                         readout=mode == :continuous ? :hybrid_next :
                                 mode == :surrogate ? :hybrid_zr : :hybrid_time_vr)
    parameters = init_parameters(rng, 3, 4, 2, config)
    input = randn(rng, Float32, 3, 2, 5)
    targets = Float32[1 0; 0 1]
    loss = classification_loss(parameters, input, targets, config)
    gradients = Zygote.gradient(
        candidate -> classification_loss(candidate, input, targets, config), parameters)[1]
    isfinite(loss) || error("$mode loss is not finite")
    all(isfinite, gradients.W_in) || error("$mode input gradient is not finite")
    println("mode=$mode loss=$loss gradient_norm=$(sqrt(sum(abs2, gradients.W_in)))")
    if cuda_available
        gpu_parameters = NamedTuple{keys(parameters)}(map(CUDA.cu, values(parameters)))
        gpu_input, gpu_targets = CUDA.cu(input), CUDA.cu(targets)
        gpu_loss = classification_loss(gpu_parameters, gpu_input, gpu_targets, config)
        gpu_gradients = Zygote.gradient(candidate ->
            classification_loss(candidate, gpu_input, gpu_targets, config), gpu_parameters)[1]
        CUDA.synchronize()
        isfinite(Float64(gpu_loss)) || error("$mode CUDA loss is not finite")
        all(isfinite, Array(gpu_gradients.W_in)) || error("$mode CUDA gradient is not finite")
        println("mode=$mode CUDA loss=$gpu_loss")
    end
end
println("PREFLIGHT PASS")
