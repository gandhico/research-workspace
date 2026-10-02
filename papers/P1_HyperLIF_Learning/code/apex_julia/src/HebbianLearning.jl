module HebbianLearning

using DifferentialEquations
using LinearAlgebra

export LTDParams, ltd_dynamics
export accumulate_drive!, apply_batch_weights!, clip_by_norm!

# ==============================================================================
# 1. Legacy Online Plasticity (Scalar ODE Engine)
# ==============================================================================
#
# ltd_dynamics implements a Hebbian / BCM-like rule embedded directly in the
# ODE so that DifferentialEquations.jl integrates weights and neuron states
# simultaneously.  This is retained for backward compatibility with 16-neuron
# sandbox scripts but is NOT the engine used in testHebbianLearning.jl.
#
# The weight update has three components (per synapse W[i,j], i=post, j=pre):
#   1. Decay:    -decay_rate · W[i,j]  (L2 weight regularization)
#   2. LTP:   η · (r[j] - θ_LTD) · (w_max - W[i,j])   when v[i] > 0.5
#             (BCM-style: pre-synaptic gate above threshold → strengthen weight,
#             but multiplicatively bounded by the headroom to w_max)
#   3. LTD:   η · (r[j] - θ_LTD) · W[i,j]              when v[i] > 0.5
#             (gate below threshold → weaken weight multiplicatively)
#
# The voltage threshold 0.5 for plasticity activation is a heuristic: it
# requires the post-synaptic neuron to be near threshold before weight changes
# are applied.  This approximates a Hebbian "pre AND post" conjunction.

struct LTDParams{T}
    tau::T; v_rest::T; v_thresh::T; v_reset::T
    alpha::T; base_gain::T; beta::T
    tau_r_rise::T   # Gate rise time constant (fast, for spike onset)
    tau_r_fall::T   # Gate fall time constant (slower, for refractory effect)
    gamma::T        # Hysteresis factor γ
    N::Int          # Number of neurons in the pool
    I_base::Vector{T} # Per-neuron baseline input currents
    plasticity_on::Bool
    eta::T          # Learning rate
    w_max::T        # Maximum absolute weight (multiplicative bound)
    ltd_threshold::T  # BCM sliding threshold θ_LTD for pre-synaptic gate r
    decay_rate::T   # Synaptic weight decay rate
    coupling::T     # Scaling of recurrent synaptic currents
    g_inhibit::T    # Lateral inhibition conductance (0 = no inhibition)
    layer_mask::Vector{Int}  # Layer assignment per neuron (for lateral inhibition)
    learning_mask::Matrix{T} # Binary mask: 1 = trainable synapse, 0 = fixed
end

function adaptive_sigmoid(v, v_thresh, alpha)
    arg = clamp(alpha * (v - v_thresh), -60.0, 60.0)
    return 1.0 / (1.0 + exp(-arg))
end

# ODE for a fully recurrent pool of N Adaptive HyperLIF neurons with online
# BCM-like plasticity.
#
# State vector layout (total dimension 2N + N²):
#   u[1:N]        — membrane potentials v_i
#   u[N+1:2N]     — gate variables r_i
#   u[2N+1:end]   — flattened weight matrix W[i,j] (post×pre, row-major)
function ltd_dynamics(du, u, p, t)
    N = p.N
    vs = @view u[1:N]
    rs = @view u[N+1:2N]
    Ws = reshape(@view(u[2N+1:end]), N, N)    # W[post, pre]

    dvs = @view du[1:N]
    drs = @view du[N+1:2N]
    dWs = reshape(@view(du[2N+1:end]), N, N)

    for i in 1:N
        # ── Recurrent synaptic input ──
        # I_syn[i] = Σ_{j≠i} W[i,j] · r[j] · coupling
        # Using gate variable r as the pre-synaptic "spike rate" proxy.
        I_syn = 0.0
        for j in 1:N
            if i != j
                I_syn += Ws[i, j] * rs[j] * p.coupling
            end
        end

        # ── Lateral inhibition (optional) ──
        # Computes the total gate activity in the same layer and subtracts
        # the neuron's own contribution, implementing WTA-like competition.
        I_inhibit = 0.0
        if p.g_inhibit > 0
            my_layer = p.layer_mask[i]
            layer_activity = 0.0
            for k in 1:N
                if p.layer_mask[k] == my_layer
                    layer_activity += rs[k]
                end
            end
            I_inhibit = (layer_activity - rs[i]) * p.g_inhibit
        end

        I_total = p.I_base[i] + I_syn - I_inhibit
        v = vs[i]; r = rs[i]

        # ── Gate dynamics (Adaptive HyperLIF, eq. 3 with asymmetric τ_r) ──
        eff_thresh = p.v_thresh - (p.gamma * r)
        target_r   = adaptive_sigmoid(v, eff_thresh, p.alpha)
        # Asymmetric gate: faster rise (spike initiation) than fall (refractoriness)
        eff_tau = (target_r > r) ? p.tau_r_rise : p.tau_r_fall
        drs[i] = (target_r - r) / eff_tau

        # ── Voltage dynamics (eq. 2 with adaptive conductance) ──
        drift        = (-(v - p.v_rest) + I_total) / p.tau
        dynamic_gain = p.base_gain + (p.beta * abs(I_total))
        conductance  = dynamic_gain * (r^2)
        dvs[i]       = drift - conductance * (v - p.v_reset)

        # ── BCM-like synaptic plasticity ──
        for j in 1:N
            if i == j || !p.plasticity_on || p.learning_mask[i, j] == 0.0
                dWs[i, j] = 0.0; continue
            end

            # Weight decay: pulls W toward 0 at rate decay_rate (L2 regularization).
            decay = -p.decay_rate * Ws[i, j]

            learning = 0.0
            if v > 0.5  # Post-synaptic voltage must be near threshold for plasticity
                # drive = r[j] - θ_LTD:
                #   drive > 0 → LTP (pre-synaptic gate above threshold)
                #   drive < 0 → LTD (pre-synaptic gate below threshold)
                drive = rs[j] - p.ltd_threshold
                if drive > 0
                    # LTP: multiplicative bound limits growth as W approaches w_max.
                    learning = p.eta * drive * (p.w_max - Ws[i, j])
                else
                    # LTD: multiplicative bound limits depression as W approaches 0.
                    learning = p.eta * drive * Ws[i, j]
                end
            end
            dWs[i, j] = learning + decay
        end
    end
end

# ==============================================================================
# 2. Batched e-prop-like Gradient Engine (HPC / GPU)
# ==============================================================================
#
# These three functions implement the three-stage gradient pipeline used in
# testHebbianLearning.jl:
#
#   Stage A — accumulate_drive!:  compute the outer-product gradient matrix
#             ΔW ← ΔW + (L_post ⊙ σ'(v_post)) · x_pre^T
#             This is the e-prop three-factor rule:
#               eligibility trace   e_{ij}(t) = σ'(v_j(t)) · x_i(t)
#               weight gradient    ∂L/∂W_{ij} ≈ Σ_t L_j(t) · e_{ij}(t)
#             where L_j is the learning signal, x_i is the pre-synaptic trace,
#             and σ'(v_j) = ds_dv is the surrogate derivative.
#
#   Stage B — clip_by_norm!:  global gradient norm clipping (paper §VI,
#             "gradient elements clamped to [−5,5]" — here applied to the
#             entire gradient matrix rather than element-wise).
#
#   Stage C — apply_batch_weights!:  multiplicatively bounded weight update
#             with optional L2 decay, enforcing W ∈ [−w_max, w_max].

"""
    accumulate_drive!(Drive_matrix, bias_drive, trace_pre, ds_dv_post, learning_signal)

Accumulates the e-prop outer-product gradient for one time step:

    bias_drive[j, b] = learning_signal[j, b] * ds_dv_post[j, b]   (element-wise)
    Drive_matrix     += bias_drive  ×  trace_pre^T                  (matrix multiply)

Dimensions (all Float32):
    Drive_matrix:   [N_post, N_pre]   — accumulated gradient, updated in-place
    bias_drive:     [N_post, Batch]   — temporary scratch (pre-allocated, reused)
    trace_pre:      [N_pre,  Batch]   — low-pass filtered pre-synaptic activity
    ds_dv_post:     [N_post, Batch]   — surrogate derivative (from adaptive_hyper_step)
    learning_signal:[N_post, Batch]   — error signal projected to post-synaptic layer

The `mul!` call maps to cuBLAS DGEMM on GPU, giving efficient O(N²·B) throughput.
"""
function accumulate_drive!(Drive_matrix::AbstractMatrix{T},
                           bias_drive::AbstractArray{T},
                           trace_pre::AbstractArray{T},
                           ds_dv_post::AbstractArray{T},
                           learning_signal::AbstractArray{T}) where T <: AbstractFloat

    # Hadamard product: pointwise learning signal × surrogate derivative
    @. bias_drive = learning_signal * ds_dv_post

    # Outer product collapse over the Batch dimension:
    #   Drive_matrix += bias_drive × trace_pre^T
    #   [N_post, N_pre] += [N_post, Batch] × [Batch, N_pre]
    mul!(Drive_matrix, bias_drive, transpose(trace_pre), 1.0f0, 1.0f0)
end

"""
    clip_by_norm!(Drive_matrix, max_norm)

Global gradient clipping: if ‖Drive_matrix‖_F > max_norm, rescale by max_norm / ‖·‖.
This preserves the *direction* (geometry) of the gradient vector while bounding
its magnitude, preventing gradient explosions from the stiff reset dynamics.
"""
function clip_by_norm!(Drive_matrix::AbstractMatrix{T}, max_norm::T) where T <: AbstractFloat
    current_norm = norm(Drive_matrix)
    if current_norm > max_norm
        Drive_matrix .*= (max_norm / current_norm)
    end
end

"""
    apply_batch_weights!(W, Drive_matrix; eta_w, lambda, w_max, dt)

Multiplicatively bounded weight update (one gradient descent step):

    W[i,j] += eta_w * Drive[i,j] * ifelse(Drive > 0, w_max - W, W + w_max)
            - lambda * W * dt

The multiplicative factor ensures:
  - LTP (Drive > 0): update shrinks to zero as W → +w_max  (no unbounded growth)
  - LTD (Drive < 0): update shrinks to zero as W → −w_max  (no sign flip)
Followed by hard clamp to W ∈ [−w_max, w_max] as a safety net.

The `lambda * W * dt` term is an L2 / weight-decay regularizer that independently
pulls all weights toward zero with rate λ.  Setting lambda=0 disables it.
"""
function apply_batch_weights!(W::AbstractMatrix{T},
                              Drive_matrix::AbstractMatrix{T};
                              eta_w::T  = 0.01f0,
                              lambda::T = 0.0f0,
                              w_max::T  = 3.0f0,
                              dt::T     = 0.5f0) where T <: AbstractFloat

    @. W += (eta_w * Drive_matrix * ifelse(Drive_matrix > 0.0f0, w_max - W, W + w_max)) -
            (lambda * W * dt)
    @. W = clamp(W, -w_max, w_max)
end

end # module HebbianLearning
