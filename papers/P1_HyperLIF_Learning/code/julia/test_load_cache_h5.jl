# Validates the CPU read+permute logic of APEX's load_cache_h5 (no GPU/CUDA — the APEXDataLoader
# wrapper allocates CuArrays and runs only on the cluster). Confirms an exported cache lands in the
# strict APEX topology [F, N, T].
#
#   julia 08_HyperLIF_Architectures/julia/test_load_cache_h5.jl <cache.h5>

using HDF5

path = length(ARGS) >= 1 ? ARGS[1] : error("usage: julia test_load_cache_h5.jl <cache.h5>")

h5open(path, "r") do fid
    x_train = permutedims(Float32.(read(fid, "X_train")), (1, 3, 2))   # (F,T,N) -> (F,N,T)
    x_test  = permutedims(Float32.(read(fid, "X_test")),  (1, 3, 2))
    y_train = Int.(read(fid, "y_train"))
    F, N, T = size(x_train)
    println("X_train [F,N,T] = ", size(x_train), "   X_test = ", size(x_test))
    println("y_train ", size(y_train), "   classes = ", Int(maximum(y_train)) + 1)
    println("sum(X_train) = ", sum(Float64.(x_train)), "   (invariant under permute)")
    @assert size(x_train, 2) == length(y_train) "batch dim (N) must be axis 2 for APEXDataLoader"
    @assert F > 0 && N > 0 && T > 0
    println("APEX topology OK: [F=$F, N=$N, T=$T] — ready for APEXDataLoader (GPU, cluster).")
end
