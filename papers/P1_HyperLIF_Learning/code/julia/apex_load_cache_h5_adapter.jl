# Generic HDF5 cache adapter for the Julia/APEX arm of P1.
#
# Context:
# - 07_AdHyperLIF_Triage/hpc/export_hdf5.py writes Python tensors as [N,T,F].
# - HDF5.jl reads that layout as [F,T,N].
# - APEXDataLoader expects strict [F,N,T] host tensors and 0-based class labels.
#
# Usage from the APEXEngine project after including the local engine:
#
#   include("src/APEXEngine.jl")
#   using .APEXEngine
#   include(raw"C:\00_Research_\Neural_Networks_and_Learning\08_HyperLIF_Architectures\julia\apex_load_cache_h5_adapter.jl")
#   train_loader, test_loader = load_cache_h5(raw"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5", 64)

using HDF5

function inspect_cache_h5(filepath::AbstractString)
    h5open(filepath, "r") do fid
        x_train = read(fid, "X_train")
        x_test = read(fid, "X_test")
        y_train = Int.(read(fid, "y_train"))
        y_test = Int.(read(fid, "y_test"))

        x_train_apex = permutedims(Float32.(x_train), (1, 3, 2))
        x_test_apex = permutedims(Float32.(x_test), (1, 3, 2))
        n_classes = max(maximum(y_train), maximum(y_test)) + 1

        println("X_train raw(HDF5.jl) = ", size(x_train), " -> APEX [F,N,T] = ", size(x_train_apex))
        println("X_test  raw(HDF5.jl) = ", size(x_test), " -> APEX [F,N,T] = ", size(x_test_apex))
        println("y_train = ", size(y_train), " y_test = ", size(y_test), " classes = ", n_classes)
        println("labels: train min/max = ", minimum(y_train), "/", maximum(y_train),
                " test min/max = ", minimum(y_test), "/", maximum(y_test),
                " (APEX expects 0-based labels and adds +1 internally)")
        println("sum(X_train) = ", sum(Float64.(x_train_apex)), " (invariant under permute)")
    end
end

function load_cache_h5(filepath::AbstractString, batch_size::Integer;
                       shuffle_train::Bool=true, shuffle_test::Bool=false)
    local x_train, y_train, x_test, y_test

    h5open(filepath, "r") do fid
        x_train = permutedims(Float32.(read(fid, "X_train")), (1, 3, 2))
        x_test = permutedims(Float32.(read(fid, "X_test")), (1, 3, 2))
        y_train = Int.(read(fid, "y_train"))
        y_test = Int.(read(fid, "y_test"))
    end

    @assert ndims(x_train) == 3 "APEX cache must be [F,N,T]"
    @assert size(x_train, 2) == length(y_train) "training labels must match APEX batch axis"
    @assert size(x_test, 2) == length(y_test) "test labels must match APEX batch axis"
    @assert minimum(y_train) >= 0 && minimum(y_test) >= 0 "APEX classification labels must be 0-based"

    train_loader = APEXDataLoader(x_train, y_train, Int(batch_size); shuffle=shuffle_train)
    test_loader = APEXDataLoader(x_test, y_test, Int(batch_size); shuffle=shuffle_test)
    return train_loader, test_loader
end

if abspath(PROGRAM_FILE) == @__FILE__
    path = length(ARGS) >= 1 ? ARGS[1] : error("usage: julia apex_load_cache_h5_adapter.jl <cache.h5>")
    inspect_cache_h5(path)
    println("ADAPTER INSPECTION OK. Include this file from an APEXEngine session to construct APEXDataLoader objects.")
end
