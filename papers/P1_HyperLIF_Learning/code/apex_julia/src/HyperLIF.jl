module HyperLIF

using DifferentialEquations

export HyperLIFParams, StandardLIFParams
export hyper_lif_dynamics, standard_lif_dynamics
export sigmoid_switch, get_standard_callback

# ==============================================================================
# 1. Baseline Hyperreal LIF (HyperLIF) — Continuous ODE Formulation
# ==============================================================================
#
# Background (paper §III):
#   The standard LIF reset  v(t⁺) ← v_reset  when  v(t) ≥ v_thresh
#   is a discontinuous jump that breaks the chain rule, preventing
#   reverse-mode automatic differentiation through spike events.
#
#   HyperLIF replaces this jump with a *continuous micro-time discharge*
#   derived via Nonstandard Analysis (NSA).  A dimensionless gate variable
#   r(t) ∈ [0,1] acts as a continuous proxy for the discrete reset state,
#   evolving on a fast time scale τ_r ≪ τ.  The resulting two-time-scale
#   ODE (eqs. 2–3 in the paper) is smooth for finite sigmoid slope. Gradients
#   through detected event times still require separate transversality and
#   fixed-event-topology assumptions.
#
# State vector: u = [v, r]
#   v — membrane potential (normalized; v_reset=0, v_thresh=1 by convention)
#   r — continuous reset gate  (r≈0: integrating phase; r≈1: reset phase)

struct HyperLIFParams{T}
    tau::T        # Membrane (slow) time constant τ  [ms]
    v_rest::T     # Resting potential v_rest          [normalized]
    v_thresh::T   # Spike threshold v_thresh          [normalized]
    v_reset::T    # Post-spike reset target v_reset   [normalized]

    # --- NSA / Gate parameters ---
    alpha::T      # Sigmoid steepness α — controls how sharply the gate
                  # opens at threshold. Paper uses α=50, giving LIF-like
                  # voltage upstroke (soft-start via r² suppresses leakage
                  # below threshold; see §III-B).
    reset_gain::T # Baseline reset conductance G_base  (dimensionless).
                  # Sets available discharge capacity.  If the sustained
                  # input current exceeds G_base*(v_thresh - v_reset), the
                  # neuron enters the depolarization block (DB) latch
                  # (inequality §III-C, eq. 6).  Paper: G_base = 800.

    I_in::T       # Net input drive I_in (signed, excitatory minus inhibitory,
                  # in normalized units matching the leak term)
    tau_r::T      # Gate (fast) time constant τ_r  [ms].  Must satisfy
                  # τ_r ≪ τ for the stiff two-time-scale separation.
                  # Paper: τ_r = 0.2 ms, τ = 10 ms.
    gamma::T      # Hysteresis factor γ.  The effective threshold
                  # θ_eff = v_thresh - γ·r drops as r→1, locking the
                  # gate open until v fully returns to v_reset.
                  # Paper: γ = 3.0.
end

# --- Sigmoid gate detector (paper eq. 4) ---
# σ(v; θ_eff, α) = [1 + exp(-α(v - θ_eff))]⁻¹
# Returns r_target ∈ (0,1).  The clamp prevents IEEE-754 overflow at
# large α and large |v − θ_eff| without altering the mathematical limit.
function sigmoid_switch(v, v_thresh, alpha)
    arg = alpha * (v - v_thresh)
    arg_clamped = clamp(arg, -700.0, 700.0)
    return 1.0 / (1.0 + exp(-arg_clamped))
end

# --- HyperLIF ODE right-hand side (paper eqs. 2–3) ---
#
#   Slow scale (membrane):
#     τ v̇ = -(v - v_rest) + I_in - G(r)·(v - v_reset)          (eq. 2)
#   Fast scale (gate):
#     τ_r ṙ = σ(v; θ_eff, α) - r                                (eq. 3)
#
#   Conductance law (baseline, eq. 5):
#     G(r) = G_base · r²
#
#   The quadratic term r² is *essential* (paper §III-B):
#     - Linear G ∝ r → non-zero derivative at r→0 → premature leakage
#       → soft spike onset, destroyed temporal precision.
#     - Quadratic G ∝ r² → ∂G/∂r = 0 at r→0 → sharp LIF-like upstroke
#       until the gate is fully committed.
#
#   State layout: u[1]=v, u[2]=r  (du is the derivative vector)
function hyper_lif_dynamics(du, u, p, t)
    v = u[1]
    r = u[2]

    # --- Gate dynamics (fast time scale, eq. 3) ---
    # Hysteresis: threshold drops as r rises, preventing premature closure.
    effective_thresh = p.v_thresh - (p.gamma * r)         # θ_eff = v_thresh - γr
    target_r = sigmoid_switch(v, effective_thresh, p.alpha) # r_target = σ(v; θ_eff, α)
    dr = (target_r - r) / p.tau_r                          # τ_r ṙ = r_target - r

    # --- Voltage dynamics (slow time scale, eq. 2) ---
    drift = (-(v - p.v_rest) + p.I_in) / p.tau            # leak + input drive

    # G(r) = G_base · r²   (baseline conductance law, eq. 5)
    # When r≈0: conductance≈0, no reset force — neuron integrates freely.
    # When r≈1: conductance≈G_base, maximum discharge current applied.
    conductance = p.reset_gain * (r^2)
    reset_force = -conductance * (v - p.v_reset)           # -G(r)·(v - v_reset)/τ (absorbed in drift scale)

    du[1] = drift + reset_force
    du[2] = dr
end

# ==============================================================================
# 2. Standard LIF — Reference Baseline
# ==============================================================================
# Canonical LIF with a ContinuousCallback for the hard-threshold reset.
# The callback introduces the non-differentiable jump that HyperLIF eliminates.
# Retaining this alongside HyperLIF enables direct phase-plane comparison.

struct StandardLIFParams{T}
    tau::T; v_rest::T; v_thresh::T; v_reset::T; I_in::T
end

# ODE: τ v̇ = -(v - v_rest) + I_in
function standard_lif_dynamics(dv, v, p, t)
    dv[1] = (-(v[1] - p.v_rest) + p.I_in) / p.tau
end

# ContinuousCallback triggers at  v - v_thresh = 0  (zero-crossing)
# and immediately sets v ← v_reset.  This is the discontinuous jump
# that breaks the chain rule.
function get_standard_callback(v_thresh, v_reset)
    condition(v, t, integrator) = v[1] - v_thresh
    affect!(integrator) = integrator.u[1] = v_reset
    return ContinuousCallback(condition, affect!)
end

end # module HyperLIF
