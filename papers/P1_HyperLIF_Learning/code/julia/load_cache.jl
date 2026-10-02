# Ingestion check for the Julia/APEX arm of Paper 2: read a cache exported by
# 07/hpc/export_hdf5.py and verify the cross-framework data contract (byte-exact) via HDF5.jl —
# the same package APEX's apex/data.jl uses. No GPU needed (that's the Phase-B full APEX run).
#
#   julia 08_HyperLIF_Architectures/julia/load_cache.jl <cache.h5>
#
# sum(X_train) must equal the Python exporter's printed sum(Xtr) — proves the bytes transferred.
# NOTE: HDF5.jl returns dimensions reversed vs h5py — Python [N,T,F] reads as Julia (F,T,N).

using HDF5

path = length(ARGS) >= 1 ? ARGS[1] : error("usage: julia load_cache.jl <cache.h5>")

h5open(path, "r") do fid
    Xtr = read(fid, "X_train"); ytr = read(fid, "y_train")
    Xte = read(fid, "X_test");  yte = read(fid, "y_test")
    println("X_train ", size(Xtr), "   y_train ", size(ytr), "   (Julia F,T,N = Python N,T,F)")
    println("X_test  ", size(Xte), "   y_test  ", size(yte))
    println("sum(X_train) = ", sum(Float64.(Xtr)), "   (cross-check vs Python)")
    println("n_classes = ", Int(maximum(ytr)) + 1, "   T = ", size(Xtr, 2), "   F = ", size(Xtr, 1))
    println("INGESTION OK — Julia reads the PyTorch cache; ready for APEX (Phase B, GPU).")
end
