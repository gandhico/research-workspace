# testHebbianLearning.jl — Deep Spatial Credit Assignment Comparison
#
# Benchmarks four methods for propagating the output error to hidden layers of
# a two-hidden-layer Adaptive HyperLIF SNN on the 3-bit XOR parity task:
#
#   :Exact        — exact backpropagation (W^T times error), the gold standard
#   :SignSymmetry — sign of W^T replaces W^T (no weight transport required)
#   :RFA          — Random Feedback Alignment (fixed random matrix B per layer)
#   :DFA          — Direct Feedback Alignment (broadcast to each hidden layer
#                   directly from the output error, bypassing intermediate layers)
#
# Current results (see embedded log at end of file) show all four methods fail
# to converge on this simple task.  See equations.md §IX for the diagnosis.

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))  # activate the Project.toml in the repo root

using LinearAlgebra
using Statistics
using Printf
using Random
using Plots

include("HyperSNN.jl")
using .HyperSNN

println("Starting Deep Spatial Credit Comparison (Library Powered: Clipping + Decay)...")

# ==============================================================================
# 1. Configuration
# ==============================================================================
# 3-bit parity: output is 1 iff an odd number of input bits are 1.
# All 8 binary inputs, presented as a complete batch each epoch.
const PARITY_X = Float32[0 0 0; 0 0 1; 0 1 0; 0 1 1; 1 0 0; 1 0 1; 1 1 0; 1 1 1]
const PARITY_Y_LOGIC = Float32[0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0]

# Target output value for "active" class (True); inactive class target is 0.
# This is a rate-code target: the output gate r_out should reach TARGET_ACTIVE.
const TARGET_ACTIVE = 0.5f0

# ── Physics constants (match Table III in the paper) ──────────────────────────
const DT        = 0.5f0    # Integration time step Δt [ms]
const TAU_SOMA  = 5.0f0    # Membrane time constant τ [ms]
const TAU_TRACE = 10.0f0   # Pre-synaptic trace time constant [ms]
const TAU_R     = 0.2f0    # Gate time constant τ_r [ms]
const V_THRESH  = 1.0f0    # Spike threshold (normalised)
const GAMMA     = 3.0f0    # Hysteresis factor γ
const ALPHA     = 50.0f0   # Forward sigmoid steepness α
const ALPHA_LEARN = 2.0f0  # Surrogate sigmoid steepness (wide, sub-threshold coverage)
const G_BASE    = 800.0f0  # Baseline reset conductance G_base
const BETA      = 100.0f0  # Adaptive scaling β (feedforward, prevents DB)
const G_A       = 0.1f0    # Dendritic–somatic coupling conductance

# NOTE (diagnosis): G_A / G_BASE = 0.1 / 800 ≈ 1.25e-4.  The error feedback
# injected via v_dend is negligible compared to the reset conductance during
# the reset phase.  See equations.md §9.2.

# ── Network topology ──────────────────────────────────────────────────────────
const N_IN    = 3    # Input neurons (3 parity bits)
const N_HID   = 64   # Hidden layer width (same for both layers)
const N_OUT   = 1    # Output neuron (binary parity decision)
const BATCH_SIZE  = 8   # Complete parity truth table
const TIME_STEPS  = 60  # Simulation duration per sample [steps] = 30 ms at DT=0.5

# ==============================================================================
# 2. Training Function
# ==============================================================================
function train_parity(method::Symbol; epochs=2500)
    Random.seed!(42)

    # ── Weight initialisation (He / Kaiming for ReLU-like activations) ───────
    # W ∼ N(0, 2/fan_in) — chosen to keep pre-activation variance ≈ 1 at init.
    W1     = randn(Float32, N_HID, N_IN)  .* Float32(sqrt(2.0 / N_IN))
    B1     = randn(Float32, N_HID)        .* 0.1f0 .+ 0.85f0  # bias near threshold

    W2     = randn(Float32, N_HID, N_HID) .* Float32(sqrt(2.0 / N_HID))
    B2     = randn(Float32, N_HID)        .* 0.1f0 .+ 0.85f0

    W_out  = randn(Float32, N_OUT, N_HID) .* Float32(sqrt(2.0 / N_HID))
    B_out  = Float32[0.85f0]

    # ── Spatial credit routing matrices ───────────────────────────────────────
    # B_route_2 / B_DFA_1: fixed random feedback weights used in :RFA and :DFA.
    # B_RFA_1: full random matrix for RFA (same shape as W2 transpose).
    B_route_2 = randn(Float32, N_HID) .* 1.5f0       # DFA broadcast to layer 2
    B_DFA_1   = randn(Float32, N_HID) .* 1.5f0       # DFA broadcast to layer 1
    B_RFA_1   = randn(Float32, N_HID, N_HID) .*
                Float32(sqrt(2.0 / N_HID))             # RFA random matrix for layer 1

    # ── Gradient accumulators (pre-allocated, reset each epoch) ───────────────
    Drive_W1   = zeros(Float32, N_HID, N_IN)
    bias_drive_1 = zeros(Float32, N_HID)       # scratch for accumulate_drive!
    Drive_W2   = zeros(Float32, N_HID, N_HID)
    bias_drive_2 = zeros(Float32, N_HID)
    Drive_Wout = zeros(Float32, N_OUT, N_HID)
    bias_drive_out = zeros(Float32, N_OUT)

    loss_hist = Float32[]
    println("\n--- TRAINING START: $(method) ---")

    for epoch in 1:epochs
        epoch_loss = 0.0f0

        # Zero gradient accumulators at the start of each epoch.
        Drive_W1   .= 0.0f0
        Drive_W2   .= 0.0f0
        Drive_Wout .= 0.0f0

        for idx in 1:BATCH_SIZE
            # ── Input encoding ─────────────────────────────────────────────
            # Bipolar mapping: {0,1} → {-1, +1}.  Gives zero mean, unit variance
            # under balanced random inputs, preventing bias in initial activations.
            input_stim   = (PARITY_X[idx, :] .* 2.0f0) .- 1.0f0
            target_logic = PARITY_Y_LOGIC[idx] > 0.5f0 ? TARGET_ACTIVE : 0.0f0

            # ── State initialisation (fresh per sample) ────────────────────
            # Soma voltages v, gate variables r, and dendritic voltages v_dend.
            v_hid1_soma = zeros(Float32, N_HID)
            r_hid1      = zeros(Float32, N_HID)
            v_hid1_dend = zeros(Float32, N_HID)  # error signal buffer for layer 1

            v_hid2_soma = zeros(Float32, N_HID)
            r_hid2      = zeros(Float32, N_HID)
            v_hid2_dend = zeros(Float32, N_HID)  # error signal buffer for layer 2

            v_out_soma  = Float32[0.0f0]
            r_out_soma  = Float32[0.0f0]

            # Eligibility traces: low-pass filtered pre-synaptic activity.
            # x(t+1) = x(t) + (DT/TAU_TRACE)*(-x(t) + a(t)) — first-order IIR.
            trace_in   = zeros(Float32, N_IN)
            trace_hid1 = zeros(Float32, N_HID)
            trace_hid2 = zeros(Float32, N_HID)
            trace_out  = Float32[0.0f0]

            error_accum = 0.0f0  # accumulated |error| * dt over the time window

            for t in 1:TIME_STEPS
                # ── Pre-synaptic trace update (Code-8) ──────────────────────
                # Input trace: x_in(t) ← x_in(t) + (Δt/τ_trace)*(-x_in + stimulus)
                @. trace_in += (DT / TAU_TRACE) * (-trace_in + input_stim)

                # ── Forward pass: Layer 1 ────────────────────────────────────
                # Synaptic current: I_h1 = W1 · input + B1
                I_h1 = (W1 * input_stim) .+ B1

                # Dendritic feedback: adds error signal as a small correction to
                # the somatic input current.
                # NOTE (diagnosis §9.1): this contaminates the forward pass with
                # the backward signal.  Removing G_A here is a key fix to try.
                I_h1_total = I_h1 .+ G_A .* (v_hid1_dend .- v_hid1_soma)

                # Adaptive HyperLIF step (Algorithm 1): returns updated v, r, and
                # the surrogate derivative ds_dv for the backward pass (Code-4).
                v_hid1_soma, r_hid1, ds_dv_hid1 =
                    adaptive_hyper_step(v_hid1_soma, r_hid1, I_h1_total, dt=DT)

                # Layer-1 eligibility trace: low-pass of the gate variable r_hid1.
                @. trace_hid1 += (DT / TAU_TRACE) * (-trace_hid1 + r_hid1)

                # ── Forward pass: Layer 2 ────────────────────────────────────
                I_h2       = (W2 * r_hid1) .+ B2
                I_h2_total = I_h2 .+ G_A .* (v_hid2_dend .- v_hid2_soma)
                v_hid2_soma, r_hid2, ds_dv_hid2 =
                    adaptive_hyper_step(v_hid2_soma, r_hid2, I_h2_total, dt=DT)
                @. trace_hid2 += (DT / TAU_TRACE) * (-trace_hid2 + r_hid2)

                # ── Forward pass: Output layer ───────────────────────────────
                I_o = Float32[dot(W_out, r_hid2) + B_out[1]]
                v_out_soma, r_out_soma, ds_dv_out =
                    adaptive_hyper_step(v_out_soma, r_out_soma, I_o, dt=DT)
                @. trace_out += (DT / TAU_TRACE) * (-trace_out + r_out_soma)

                # ── Error signal ─────────────────────────────────────────────
                # Instantaneous error: target gate value minus current output trace.
                # NOTE (diagnosis §9.3): error_accum accumulates |e|·Δt over time;
                # epoch_loss += error_accum² is the square of the integral, NOT MSE.
                inst_error         = target_logic - trace_out[1]
                amplified_error    = inst_error * 10.0f0        # scaling heuristic
                output_error_current = amplified_error * ds_dv_out[1]  # δ_out ← error·σ'(v_out)

                error_accum += abs(inst_error) * DT

                # ── Spatial credit routing (Code-10) ─────────────────────────
                # Compute the learning signal for layer 2 (L^{h2} in the e-prop notation).
                if method == :Exact
                    # Exact backprop: L^{h2} = W_out^T · δ_out
                    inst_I_dend2 = W_out[1, :] .* output_error_current
                elseif method == :SignSymmetry
                    # Sign Symmetry: replace W_out with sign(W_out)
                    inst_I_dend2 = sign.(W_out[1, :]) .* output_error_current
                else
                    # DFA / RFA: fixed random feedback weights
                    inst_I_dend2 = B_route_2 .* output_error_current
                end

                # Layer-2 surrogate error: L^{h2} × σ'(v_hid2)
                inst_error_current_2 = inst_I_dend2 .* ds_dv_hid2

                # Compute the learning signal for layer 1 (L^{h1}).
                if method == :Exact
                    inst_I_dend1 = transpose(W2) * inst_error_current_2
                elseif method == :SignSymmetry
                    inst_I_dend1 = transpose(sign.(W2)) * inst_error_current_2
                elseif method == :RFA
                    inst_I_dend1 = B_RFA_1 * inst_error_current_2  # random feedback
                elseif method == :DFA
                    inst_I_dend1 = B_DFA_1 .* output_error_current # direct from output
                end

                # ── Dendritic voltage update ──────────────────────────────────
                # Low-pass filter the learning signal through the dendritic compartment.
                # v_dend(t+1) = v_dend(t) + (Δt/τ)·(-v_dend + L^{h})
                # Time constant = TAU_SOMA = 5 ms → 10 steps to decay.
                @. v_hid2_dend += (-v_hid2_dend + inst_I_dend2) * (DT/TAU_SOMA)
                @. v_hid1_dend += (-v_hid1_dend + inst_I_dend1) * (DT/TAU_SOMA)

                # ── Gradient accumulation (Code-9, e-prop outer product) ──────
                # ΔW_out += (amplified_error · σ'(v_out)) × trace_hid2^T
                accumulate_drive!(Drive_Wout, bias_drive_out, trace_hid2,
                                  ds_dv_out, Float32[amplified_error])
                # ΔW2    += (v_hid2_dend · σ'(v_hid2)) × trace_hid1^T
                accumulate_drive!(Drive_W2, bias_drive_2, trace_hid1,
                                  ds_dv_hid2, v_hid2_dend)
                # ΔW1    += (v_hid1_dend · σ'(v_hid1)) × trace_in^T
                accumulate_drive!(Drive_W1, bias_drive_1, trace_in,
                                  ds_dv_hid1, v_hid1_dend)
            end

            # Accumulate loss: square of the time-integrated absolute error.
            # NOTE (diagnosis §9.3): This is (∫|e|dt)², not ∫e²dt.  Change to
            # `epoch_loss += error_accum` (remove the squaring) for proper MSE.
            epoch_loss += (error_accum)^2
        end

        # ── Time/batch normalisation ──────────────────────────────────────────
        time_norm   = 1.0f0 / Float32(TIME_STEPS * BATCH_SIZE)
        Drive_Wout .*= time_norm
        Drive_W2   .*= time_norm
        Drive_W1   .*= time_norm

        # ── Global gradient clipping ──────────────────────────────────────────
        MAX_NORM = 2.0f0
        clip_by_norm!(Drive_Wout, MAX_NORM)
        clip_by_norm!(Drive_W2,   MAX_NORM)
        clip_by_norm!(Drive_W1,   MAX_NORM)

        # ── Learning rate schedule: linear decay from lr → 0 ─────────────────
        # NOTE (diagnosis §9.4): decay_factor → 0 at epoch=epochs; the network
        # cannot converge after the rate reaches zero.  Replace with cosine annealing:
        #   decay_factor = 0.5 * (1 + cos(π * epoch / epochs))
        decay_factor = Float32(1.0 - (epoch / epochs))
        ETA_BATCH    = 0.2f0 * DT * decay_factor

        # ── Weight update (multiplicative bounds, no L2 decay) ────────────────
        # NOTE (diagnosis §9.5): lambda=0 → no weight decay → weights can grow
        # without bound, eventually triggering the DB latch.  Set lambda=0.01f0.
        apply_batch_weights!(W_out, Drive_Wout, eta_w=ETA_BATCH, dt=DT)
        apply_batch_weights!(W2,    Drive_W2,   eta_w=ETA_BATCH, dt=DT)
        apply_batch_weights!(W1,    Drive_W1,   eta_w=ETA_BATCH, dt=DT)

        push!(loss_hist, epoch_loss / 8.0f0)

        if epoch % 500 == 0 || epoch == 1
            @printf("Epoch %4d | Err: %6.2f\n", epoch, epoch_loss / 8.0f0)
        end
    end

    return loss_hist
end

# ==============================================================================
# 3. Run Experiments
# ==============================================================================
EPOCHS = 2500

loss_exact = train_parity(:Exact,        epochs=EPOCHS)
loss_dfa   = train_parity(:DFA,          epochs=EPOCHS)
loss_rfa   = train_parity(:RFA,          epochs=EPOCHS)
loss_ss    = train_parity(:SignSymmetry, epochs=EPOCHS)

# ==============================================================================
# 4. Plotting
# ==============================================================================
p = plot(loss_exact, label="Exact Backprop", lw=2, c=:blue,   alpha=0.3,
         title="Deep Spatial Credit (Library Powered)",
         xlabel="Epoch", ylabel="Mean Squared Error", legend=:topright)
plot!(p, loss_rfa, label="RFA",           lw=2, c=:orange, alpha=0.3)
plot!(p, loss_dfa, label="DFA",           lw=2, c=:green,  alpha=0.3)
plot!(p, loss_ss,  label="Sign Symmetry", lw=2, c=:purple, alpha=0.3)

smooth_window = 30
smooth(x) = [mean(x[max(1, i-smooth_window):i]) for i in 1:length(x)]

p_smooth = plot(smooth(loss_exact), label="Exact",        lw=3, c=:blue)
plot!(p_smooth, smooth(loss_rfa),   label="RFA",          lw=3, c=:orange)
plot!(p_smooth, smooth(loss_dfa),   label="DFA",          lw=3, c=:green)
plot!(p_smooth, smooth(loss_ss),    label="Sign Symmetry",lw=3, c=:purple,
      title="Stabilized Deep Spatial Credit (Smoothed)", xlabel="Epoch", ylabel="MSE")

savefig(p,        "Parity_Deep_Library.png")
savefig(p_smooth, "Parity_Deep_Library_Smoothed.png")
println("\nSaved Parity_Deep_Library.png and Parity_Deep_Library_Smoothed.png")

#=
Known results (all four methods fail to converge — see equations.md §IX for diagnosis):

Starting Deep Spatial Credit Comparison (Library Powered: Clipping + Decay)...

--- TRAINING START: Exact ---
Epoch    1 | Err: 120.74
Epoch  500 | Err:  59.78
Epoch 1000 | Err:  41.06
Epoch 1500 | Err:  59.08
Epoch 2000 | Err:  57.70
Epoch 2500 | Err:  44.83

--- TRAINING START: DFA ---
Epoch    1 | Err: 118.78
Epoch  500 | Err:  60.08
Epoch 1000 | Err:  58.37
Epoch 1500 | Err:  93.30
Epoch 2000 | Err:  60.95
Epoch 2500 | Err:  66.96

--- TRAINING START: RFA ---
Epoch    1 | Err: 133.34
Epoch  500 | Err:  91.16
Epoch 1000 | Err:  59.71
Epoch 1500 | Err:  62.15
Epoch 2000 | Err:  59.06
Epoch 2500 | Err:  74.45

--- TRAINING START: SignSymmetry ---
Epoch    1 | Err:  71.29
Epoch  500 | Err:  42.70
Epoch 1000 | Err:  50.51
Epoch 1500 | Err:  49.68
Epoch 2000 | Err:  49.43
Epoch 2500 | Err:  44.24

Saved Parity_Deep_Library.png and Parity_Deep_Library_Smoothed.png
=#
