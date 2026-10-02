module HyperLIFadapt

using DifferentialEquations

export AdaptiveHyperLIFParams
export adaptive_hyper_lif_dynamics
export adaptive_hyper_step

# ==============================================================================
# Adaptive HyperLIF — Mitigating Depolarization Block in a Design Envelope
# ==============================================================================
#
# Background (paper §IV):
#   The baseline HyperLIF latches into a silent depolarization block (DB) when
#   the sustained input current exceeds the static discharge capacity:
#       I_in > G_base · (v_thresh - v_reset)               (eq. 6)
#   In this regime v̇ > 0 even when r=1, so the gate never closes and
#   repetitive spiking ceases.
#
#   The Adaptive HyperLIF increases discharge capacity via a *feedforward conductance law*
#   (eq. 7) whose discharge capacity scales proportionally with |I_in|:
#       G(r, I_in) = (G_base + β|I_in|) · r²
#   Whether the β|I_in| term counterbalances a drive depends on the complete
#   parameter inequality and operating envelope; the scaling alone is not a
#   global guarantee of repetitive spiking.
#
# This file provides two implementations:
#   1. adaptive_hyper_lif_dynamics — continuous ODE (for phase-plane analysis,
#      stiff solver Rodas5, matches paper §IV exactly)
#   2. adaptive_hyper_step — discrete exponential-Euler step (for GPU/batch
#      training, matches Algorithm 1 in the paper, differentiable via Zygote)

# ==============================================================================
# 1. Continuous ODE (Legacy / Analysis)
# ==============================================================================

struct AdaptiveHyperLIFParams{T}
    tau::T          # Membrane time constant τ        [ms]
    v_rest::T       # Resting potential               [normalized]
    v_thresh::T     # Spike threshold                 [normalized]
    v_reset::T      # Post-spike reset target         [normalized]
    alpha::T        # Sigmoid steepness α
    base_gain::T    # Baseline reset conductance G_base
    gain_scaling::T # Adaptive gain β (feedforward |I_in| scaling)
    I_in::T         # Net input drive
    tau_r::T        # Gate time constant τ_r          [ms]
    gamma::T        # Hysteresis factor γ
end

function adaptive_sigmoid(v, v_thresh, alpha)
    arg = clamp(alpha * (v - v_thresh), -700.0, 700.0)
    return 1.0 / (1.0 + exp(-arg))
end

# ODE right-hand side for Adaptive HyperLIF (paper eqs. 2–3 with eq. 7):
#   Slow:  τ v̇ = -(v - v_rest) + I_in - G(r,I_in)·(v - v_reset)
#   Fast:  τ_r ṙ = σ(v; θ_eff, α) - r
#   G(r, I_in) = (G_base + β|I_in|) · r²                         (eq. 7)
#
# The dynamic_gain mirrors Algorithm 1 steps 7–8 in the paper:
#   G_dynamic = G_base + β|I_in|   (feedforward scaling)
#   g_reset   = G_dynamic · r²     (soft-start gating)
function adaptive_hyper_lif_dynamics(du, u, p, t)
    v = u[1]; r = u[2]

    # Gate dynamics — identical to baseline HyperLIF (eq. 3)
    effective_thresh = p.v_thresh - (p.gamma * r)
    target_r = adaptive_sigmoid(v, effective_thresh, p.alpha)
    dr = (target_r - r) / p.tau_r

    # Adaptive conductance law (eq. 7)
    # dynamic_gain grows with |I_in|, preventing DB for any finite drive.
    dynamic_gain = p.base_gain + (p.gain_scaling * abs(p.I_in))
    conductance = dynamic_gain * (r^2)

    # Voltage dynamics (eq. 2 with adaptive G)
    drift = (-(v - p.v_rest) + p.I_in) / p.tau
    du[1] = drift - conductance * (v - p.v_reset)
    du[2] = dr
end

# ==============================================================================
# 2. Discrete Exponential-Euler Step (Training / GPU)
# ==============================================================================
#
# Implements Algorithm 1 from the paper using frozen-target exponential steps.
# Each scalar frozen-coefficient subproblem is solved analytically; this does
# not establish A-stability or unconditional stability of the coupled split map.
#
# Three quantities are returned per forward step:
#   v_new   — updated membrane potential
#   r_new   — updated gate variable
#   ds_dv   — surrogate derivative dσ_learn/dv, used in place of the true
#             (nearly discontinuous) forward sigmoid derivative during the
#             backward pass.  Computed with a *wide* sigmoid (alpha_learn ≪ alpha)
#             so the gradient is non-zero well into the sub-threshold region,
#             preventing dead-neuron initialization (paper §VI-A, Fig. 7).
#
# Note on the surrogate mismatch (deliberate design):
#   Forward:  alpha = 50  → nearly step-like gate, sharp spike onset
#   Backward: alpha_learn = 2  → wide smooth gradient
#   This is the standard SuperSpike / surrogate-gradient convention [Zenke &
#   Ganguli 2018; Neftci et al. 2019].  The price is that ds_dv does NOT equal
#   the derivative of the forward sigmoid; the gradients are "exact for the
#   stated differentiable dynamics" only when alpha_learn = alpha.

"""
    adaptive_hyper_step(v, r, I; kwargs...)

Batched discrete-time Adaptive HyperLIF step (Algorithm 1 in the paper).

Accepts `AbstractArray` so the same code runs on CPU `Array` or GPU `CuArray`
without modification (CUDA.jl dispatches the broadcasts and exp calls to cuBLAS
/ custom kernels automatically).

Returns `(v_new, r_new, ds_dv)`.
  - `v_new`, `r_new`: state at t+Δt
  - `ds_dv`: surrogate dσ_learn/dv, for use as the spiking nonlinearity
    derivative in the backward pass (NOT the derivative of the forward gate).
"""
function adaptive_hyper_step(v::AbstractArray{T},
                             r::AbstractArray{T},
                             I::AbstractArray{T};
                             v_thresh::T  = 1.0f0,   # spike threshold (normalized)
                             gamma::T     = 3.0f0,   # hysteresis factor γ
                             alpha::T     = 50.0f0,  # forward sigmoid steepness α
                             alpha_learn::T = 2.0f0, # surrogate sigmoid steepness (wide)
                             dt::T        = 0.5f0,   # time step Δt [ms]
                             tau_r::T     = 0.2f0,   # gate time constant τ_r [ms]
                             g_base::T    = 800.0f0, # baseline reset conductance G_base
                             beta::T      = 100.0f0, # adaptive scaling β
                             tau_soma::T  = 5.0f0    # membrane time constant τ [ms]
                             ) where T <: AbstractFloat

    # ── Step 1: Gate update (fast time scale, Algorithm 1 lines 2–5) ───────────
    # θ_eff = v_thresh - γ·r  (hysteresis: falling threshold locks gate open)
    eff_thresh = v_thresh .- (gamma .* r)

    # r_target = σ(v; θ_eff, α)  — forward (stiff) sigmoid, eq. 4
    # Sign convention: clamp the *negated* argument for numerical stability.
    arg_phys = clamp.(-alpha .* (v .- eff_thresh), -60.0f0, 60.0f0)
    r_target = 1.0f0 ./ (1.0f0 .+ exp.(arg_phys))

    # Exponential Euler for the stiff gate ODE: τ_r ṙ = r_target - r
    #   r(t+Δt) = r(t)·e^{-Δt/τ_r} + r_target·(1 - e^{-Δt/τ_r})
    # This is the exact scalar solution assuming r_target is constant over
    # [t, t+Δt]. Clamping preserves the declared numerical state interval; it
    # is not by itself evidence of biophysical validity.
    decay_r = exp(-dt / tau_r)
    r_new = (r .* decay_r) .+ (r_target .* (1.0f0 - decay_r))
    r_new = clamp.(r_new, 0.0f0, 1.0f0)

    # ── Step 2: Surrogate derivative (for backward pass only) ───────────────────
    # Uses alpha_learn ≪ alpha to ensure non-zero gradient sub-threshold.
    # s_learn = σ(v; v_thresh, alpha_learn)  — wide surrogate sigmoid
    # ds_dv   = alpha_learn · s_learn · (1 - s_learn)  — logistic derivative
    arg_learn = clamp.(-alpha_learn .* (v .- v_thresh), -20.0f0, 20.0f0)
    s_learn = 1.0f0 ./ (1.0f0 .+ exp.(arg_learn))
    ds_dv = alpha_learn .* s_learn .* (1.0f0 .- s_learn)

    # ── Step 3: Adaptive conductance (Algorithm 1 lines 7–8) ────────────────────
    # G_dynamic = G_base + β|I_in|  (feedforward scaling, eq. 7 numerator)
    # g_reset   = G_dynamic · r²     (soft-start quadratic gating)
    G_dyn  = g_base .+ (beta .* abs.(I))
    G_eff  = G_dyn .* (r_new.^2)

    # ── Step 4: Voltage update (slow time scale, Algorithm 1 lines 10–12) ───────
    # The continuous equation is:  τ v̇ = -(v - v_rest) + I - g_reset·(v - v_reset)
    # Collecting v terms: τ v̇ = -(1 + g_reset)·v + v_rest + I + g_reset·v_reset
    # Dividing by τ and grouping into (τ/τ_eff)·v̇ = v_inf - v  gives:
    #
    #   τ_eff = τ / (1 + G_eff)        (effective time constant)
    #   v_inf = (v_rest + I + G_eff·v_reset) / (1 + G_eff)
    #
    # With v_rest = 0 and v_reset = 0 (normalized):
    #   τ_eff = tau_soma / (1 + G_eff)
    #   v_inf = I / (1 + G_eff)         (asymptotic voltage under combined drive)
    #
    # Exponential Euler:  v(t+Δt) = v(t)·e^{-Δt/τ_eff} + v_inf·(1 - e^{-Δt/τ_eff})
    tau_eff = tau_soma ./ (1.0f0 .+ G_eff)
    v_inf   = I ./ (1.0f0 .+ G_eff)

    decay_v = exp.(-dt ./ tau_eff)
    v_new   = (v .* decay_v) .+ (v_inf .* (1.0f0 .- decay_v))

    return v_new, r_new, ds_dv
end

end # module HyperLIFadapt
