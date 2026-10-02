# Reproducible GPU loader smoke for the P1 Julia/APEX bridge.
#
# Optional environment variables:
# - APEX_ROOT: path to the old APEXEngine project.
# - P1_SHD_CACHE: path to the exported P1 SHD HDF5 cache.
#
# Usage:
#   julia .\julia\apex_loader_smoke.jl [batch_size]

using Pkg

const DEFAULT_APEX_ROOT = raw"C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF\03_Adaptive_HyperLIF_Apex_Engine\SNN_NSA_2"
const DEFAULT_CACHE = raw"C:\00_Research_\Neural_Networks_and_Learning\07_AdHyperLIF_Triage\hpc\upload_data\shd_wide_T20.h5"

apex_root = get(ENV, "APEX_ROOT", DEFAULT_APEX_ROOT)
cache_path = get(ENV, "P1_SHD_CACHE", DEFAULT_CACHE)
batch_size = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 64

Pkg.activate(apex_root)
include(joinpath(apex_root, "src", "APEXEngine.jl"))
using .APEXEngine

include(joinpath(@__DIR__, "apex_load_cache_h5_adapter.jl"))

train_loader, test_loader = load_cache_h5(cache_path, batch_size)
first_x, first_y = first(train_loader)

println("APEX_ROOT=", apex_root)
println("CACHE=", cache_path)
println("BATCH_SIZE=", batch_size)
println("TRAIN_BATCHES=", length(train_loader), " TEST_BATCHES=", length(test_loader))
println("FIRST_BATCH_X=", size(first_x), " FIRST_BATCH_Y=", size(first_y))
println("FIRST_BATCH_LABEL_MIN=", minimum(Array(first_y)), " FIRST_BATCH_LABEL_MAX=", maximum(Array(first_y)))
println("APEX_LOADER_SMOKE_OK")
