module HyperSNN

# Top-level umbrella module for the Adaptive HyperLIF project.
# Aggregates three component modules and the Utils sub-module:
#
#   HyperLIF        — continuous ODE formulation (HyperLIF, standard LIF)
#   HyperLIFadapt   — adaptive variant + discrete GPU step (adaptive_hyper_step)
#   HebbianLearning — online BCM plasticity + batched e-prop gradient engine
#   Utils           — AdamW optimizer, data loaders, encoders
#
# Dependency graph (no circular imports):
#   HyperSNN
#   ├── HyperLIF.jl          (DifferentialEquations)
#   ├── HyperLIFadapt.jl     (DifferentialEquations)
#   ├── HebbianLearning.jl   (DifferentialEquations, LinearAlgebra)
#   └── Utils (inline)        (CUDA, Downloads, GZip, HDF5, LinearAlgebra, Random)

using DifferentialEquations
using LinearAlgebra
using Statistics
using Random

# ==============================================================================
# 1. Sub-Module Inclusion
# ==============================================================================
include("HyperLIF.jl");     using .HyperLIF
include("HyperLIFadapt.jl"); using .HyperLIFadapt
include("HebbianLearning.jl"); using .HebbianLearning

# Public API — re-export everything the training scripts need.
export HyperLIFParams, StandardLIFParams, hyper_lif_dynamics, standard_lif_dynamics,
       get_standard_callback, sigmoid_switch
export AdaptiveHyperLIFParams, adaptive_hyper_lif_dynamics
export run_hyper_simulation
export adaptive_hyper_step
export accumulate_drive!, apply_batch_weights!, clip_by_norm!

# ==============================================================================
# 2. Utilities Sub-Module
# ==============================================================================
"""
    Utils

Internal sub-module providing:
  - AdamW optimizer (GPU-compatible via AbstractArray dispatch)
  - Fourier random-feature encoder (for positional / rate coding)
  - MNIST data loader (downloads and parses IDX files via GZip)
  - DVS128 Gesture data loader (reads pre-processed HDF5)
  - Saccade generator for synthetic N-MNIST (multi-threaded CPU)
  - DVS helper: downsample (spatial pooling) and one_hot_11 (11-class)
"""
module Utils
    using LinearAlgebra
    using Random
    using CUDA       # GPU arrays; remove and replace CuArray → Array for CPU-only runs
    using Downloads  # stdlib: HTTP download for MNIST
    using GZip       # parse .gz compressed IDX files

    export AdamW, update!, sigmoid_surrogate, fourier_encode
    export load_mnist_full, make_gpu_batch
    export one_hot_11, downsample

    # ── AdamW Optimizer ──────────────────────────────────────────────────────
    # Adam with decoupled weight decay (AdamW, Loshchilov & Hutter 2019).
    # Maintains first and second moment estimates (m, v) of the gradient.
    # The `wd` (weight decay) term is applied *after* the adaptive step,
    # decoupling regularisation from the adaptive learning rate — this is
    # the key difference from L2-regularised Adam.
    mutable struct AdamW{T}
        m::T         # First moment (EMA of gradient)
        v::T         # Second moment (EMA of gradient²)
        beta1::Float32   # Decay rate for m  (default 0.9)
        beta2::Float32   # Decay rate for v  (default 0.999)
        eps::Float32     # Numerical stabiliser (default 1e-8)
        lr::Float32      # Learning rate η
        wd::Float32      # Weight decay λ (decoupled from lr)
        t::Int           # Step counter for bias correction
    end

    function AdamW(params::AbstractArray; lr=0.001f0, wd=0.01f0)
        m = zero(params); v = zero(params)
        return AdamW(m, v, 0.9f0, 0.999f0, 1.0f-8, lr, wd, 0)
    end

    # One gradient descent step using AdamW.
    # Gradient clipping (norm ≤ 1.0) is applied before the moment update to
    # prevent early instability from large gradients in the stiff reset landscape.
    function update!(opt::AdamW, params, grads)
        opt.t += 1

        # Bias-correction denominators: 1 - β^t (avoids zero-initialisation bias)
        beta1_t = 1.0f0 - opt.beta1^opt.t
        beta2_t = 1.0f0 - opt.beta2^opt.t

        # Global gradient norm clipping to 1.0
        g_norm = norm(grads)
        if g_norm > 1.0f0
            grads .*= (1.0f0 / g_norm)
        end

        # Moment updates (EMA)
        @. opt.m = opt.beta1 * opt.m + (1.0f0 - opt.beta1) * grads
        @. opt.v = opt.beta2 * opt.v + (1.0f0 - opt.beta2) * (grads^2)

        # Bias-corrected Adam step + decoupled weight decay
        step = (opt.m / beta1_t) ./ (sqrt.(opt.v / beta2_t) .+ opt.eps)
        @. params -= opt.lr * (step + opt.wd * params)
    end

    # ── Physics Helpers ───────────────────────────────────────────────────────
    # Fixed threshold for the sigmoid surrogate used outside adaptive_hyper_step
    const V_THRESH_SURR = 1.0f0

    # Sigmoid surrogate with fixed steepness 3.0 (simple alternative to alpha_learn=2).
    # Returns a smooth approximation to the Heaviside spike indicator.
    sigmoid_surrogate(v) = 1.0f0 / (1.0f0 + exp(-3.0f0 * (v - V_THRESH_SURR)))

    # ── Fourier Encoder ───────────────────────────────────────────────────────
    # Projects an input vector x ∈ ℝ^d through a random Fourier feature matrix B
    # (shape: [k, d]) to produce a 2k-dimensional positional / rate encoding:
    #   φ(x) = [cos(2π·Bx); sin(2π·Bx)]
    # This lifts scalar or low-dimensional inputs into a high-dimensional space
    # where linear readouts can implement complex nonlinear functions — useful for
    # encoding time, rate codes, or spatial position into SNN inputs.
    function fourier_encode(x::AbstractVector, B_matrix::AbstractMatrix)
        proj = (2.0f0 * Float32(pi)) .* (B_matrix * x)
        return vcat(cos.(proj), sin.(proj))
    end

    # ── MNIST Data Loader ─────────────────────────────────────────────────────
    # Downloads the 4 IDX-format MNIST files (gzip compressed) if not present,
    # then parses them into Float32 arrays.
    # Returns (X_train [784, 60000], y_train [60000], X_test [784, 10000], y_test [10000]).
    # Pixel values are normalised to [0, 1].
    function load_mnist_full()
        data_dir = joinpath(@__DIR__, "..", "data")
        mkpath(data_dir)

        base_url = "https://ossci-datasets.s3.amazonaws.com/mnist/"
        files = ["train-images-idx3-ubyte.gz", "train-labels-idx1-ubyte.gz",
                 "t10k-images-idx3-ubyte.gz",  "t10k-labels-idx1-ubyte.gz"]

        paths = [joinpath(data_dir, f) for f in files]
        for (f, p) in zip(files, paths)
            if !isfile(p)
                println("Downloading $f...")
                try Downloads.download(base_url * f, p)
                catch; Downloads.download("https://storage.googleapis.com/cvdf-datasets/mnist/" * f, p) end
            end
        end

        # IDX3 image files: 16-byte header (magic, n_images, rows, cols) then raw bytes.
        # IDX1 label files:  8-byte header (magic, n_items) then raw bytes.
        parse_img(f) = (io=GZip.open(f); read(io, Int32); read(io, Int32);
                        read(io, Int32); read(io, Int32);
                        d=read(io); close(io); Float32.(reshape(d, (784, :))) ./ 255.0f0)
        parse_lbl(f) = (io=GZip.open(f); read(io, Int32); read(io, Int32);
                        d=read(io); close(io); Int.(d))

        return parse_img(paths[1]), parse_lbl(paths[2]),
               parse_img(paths[3]), parse_lbl(paths[4])
    end

    # ── DVS Helpers ───────────────────────────────────────────────────────────

    # Spatial average-pooling for DVS event frames.
    # Reduces 128×128 DVS128 resolution by summing `factor`×`factor` pixel blocks.
    # factor=4: 128×128 → 32×32 (16384 → 1024 channels, matching the paper's 2048
    #           when counting both polarities).
    function downsample(img::AbstractMatrix, factor::Int)
        h, w = size(img)
        new_h, new_w = div(h, factor), div(w, factor)
        out = zeros(Float32, new_h, new_w)
        for r in 1:new_h, c in 1:new_w
            r_start, r_end = (r-1)*factor + 1, r*factor
            c_start, c_end = (c-1)*factor + 1, c*factor
            out[r, c] = sum(view(img, r_start:r_end, c_start:c_end))
        end
        return out
    end

    # One-hot encoder for the 11-class DVS128 Gesture dataset.
    # Labels are expected as 0-indexed integers (0–10); output is Float32[11].
    # The target is set to 10.0 (not 1.0) to produce a strong voltage drive
    # toward the target output neuron (matches v_thresh=1 scale with headroom).
    function one_hot_11(label::Int)
        y = zeros(Float32, 11)
        idx = clamp(label + 1, 1, 11)
        y[idx] = 10.0f0
        return y
    end

    using HDF5  # HDF5 file reading for DVS128 dataset

    # Loads a pre-processed DVS128 Gesture HDF5 file.
    # Expected HDF5 structure:
    #   "X_train": raw event tensor (shape depends on pre-processing script)
    #   "y_train": integer class labels [Batch]
    #   "X_test", "y_test": same for the test split.
    #
    # Returns CuArrays (Float32) for direct GPU training.
    # The spatial dimensions are flattened to [2048, Time, Batch] (32×32×2 polarities).
    function load_dvs_real(filepath::String)
        if !isfile(filepath)
            error("Dataset not found at $filepath. Please download the pre-processed H5 file.")
        end
        fid = h5open(filepath, "r")
        println("Loading DVS128 Training Data...")
        x_train_raw = read(fid, "X_train")
        y_train     = read(fid, "y_train")
        println("Loading DVS128 Test Data...")
        x_test_raw  = read(fid, "X_test")
        y_test      = read(fid, "y_test")
        close(fid)

        # Flatten (32,32,2,Time,Batch) → (2048,Time,Batch)
        flat_train = reshape(x_train_raw, (2048, size(x_train_raw)[end-1], :))
        flat_test  = reshape(x_test_raw,  (2048, size(x_test_raw)[end-1], :))

        return CuArray(Float32.(flat_train)), CuArray(Int.(y_train)),
               CuArray(Float32.(flat_test)),  CuArray(Int.(y_test))
    end

    # ── Saccade Generator (Synthetic N-MNIST) ────────────────────────────────
    # Simulates the DVS saccade process used to create the N-MNIST dataset:
    # a static MNIST image is shifted over time with sinusoidal eye-movement
    # trajectories, and the temporal differences between frames are encoded as
    # positive (ON) and negative (OFF) event channels — mimicking a DVS event camera.
    #
    # Output tensor: [1568, TIME_STEPS, batch_size]
    #   1568 = 784 (ON) + 784 (OFF) channels; each channel is a flattened 28×28 image.
    # Targets: [10, batch_size] one-hot with value 10.0 for the correct digit class.
    const TIME_STEPS = 15

    function make_gpu_batch(indices, X, Y)
        batch_size  = length(indices)
        cpu_tensor  = zeros(Float32, 1568, TIME_STEPS, batch_size)
        cpu_targets = zeros(Float32, 10, batch_size)

        # Sinusoidal saccade trajectory: mimics micro-saccadic eye movements.
        # shifts_x[t] ∈ [-2.5, 2.5] pixels,  shifts_y[t] ∈ [-1.5, 1.5] pixels.
        shifts_x = [sin(t/3) * 2.5 for t in 1:TIME_STEPS]
        shifts_y = [cos(t/3) * 1.5 for t in 1:TIME_STEPS]

        Threads.@threads for b in 1:batch_size
            img_idx = indices[b]
            cpu_targets[Y[img_idx]+1, b] = 10.0f0

            img = reshape(view(X, :, img_idx), 28, 28)
            prev_frame = img

            for t in 1:TIME_STEPS
                sx, sy = shifts_x[t], shifts_y[t]
                current_frame = zeros(Float32, 28, 28)

                # Nearest-neighbour pixel shift (clamp-to-border boundary condition)
                for r in 1:28, c in 1:28
                    src_r = clamp(round(Int, r - sy), 1, 28)
                    src_c = clamp(round(Int, c - sx), 1, 28)
                    current_frame[r, c] = prev_frame[src_r, src_c]
                end

                # Temporal difference encoding:
                #   diff > +0.1  → ON  event (channel 1:784)
                #   diff < -0.1  → OFF event (channel 785:1568)
                # Threshold 0.1 suppresses sensor noise (matches DVS event threshold).
                diff = current_frame - prev_frame
                for i in 1:784
                    d = diff[i]
                    if     d >  0.1; cpu_tensor[i,     t, b] = 1.0f0
                    elseif d < -0.1; cpu_tensor[i+784, t, b] = 1.0f0
                    end
                end
                prev_frame = current_frame
            end
        end

        return CuArray(cpu_tensor), CuArray(cpu_targets)
    end

end # module Utils

using .Utils

end # module HyperSNN
