module ViabilityHyperLIF

using HyperLIFLearning
using LinearAlgebra
using Random
using Statistics

export ViabilityBox, normalized_slacks, viability_health, viability_region
export RegimeSpec, default_regimes, shd_calibrated_regimes
export shd_shared_gain_regimes, mean_regime, matched_homogeneous_regime
export regime_weights, build_population_configs
export init_heterogeneous_parameters, heterogeneous_forward
export heterogeneous_classification_loss, population_activity
export HomeostaticState, update_homeostasis, apply_threshold_offsets
export plasticity_gate, rate_band_penalty
export CBFConstraints, SafetyResult, cbf_constraints, project_halfspaces, shield_action

"""Axis-aligned operating envelope for robot or neural state.

The implementation starts with boxes because their lower/upper barrier
functions are explicit and auditable. More general learned or analytic
barriers belong behind the same interface in later phases.
"""
struct ViabilityBox
    lower::Vector{Float32}
    upper::Vector{Float32}
    names::Vector{Symbol}
end

function ViabilityBox(lower::AbstractVector, upper::AbstractVector;
                      names=Symbol.("x" .* string.(eachindex(lower))))
    length(lower) == length(upper) || error("lower and upper must have equal length")
    length(names) == length(lower) || error("one name is required per state dimension")
    lo, hi = Float32.(lower), Float32.(upper)
    all(isfinite, lo) && all(isfinite, hi) || error("viability bounds must be finite")
    all(lo .< hi) || error("every lower bound must be strictly below its upper bound")
    return ViabilityBox(lo, hi, Symbol.(names))
end

"""Dimensionless lower and upper slacks.

Each component is zero on its corresponding boundary, positive inside, and
negative outside. Scaling by the interval width prevents units with a large
numeric range from dominating the aggregate margin.
"""
function normalized_slacks(x::AbstractVector, box::ViabilityBox)
    length(x) == length(box.lower) || error("state dimension does not match viability box")
    span = box.upper .- box.lower
    return vcat((Float32.(x) .- box.lower) ./ span,
                (box.upper .- Float32.(x)) ./ span)
end

"""Scalar health margin: 1 at the box center, 0 at a boundary, negative outside."""
viability_health(x::AbstractVector, box::ViabilityBox) =
    min(1f0, 2f0 * minimum(normalized_slacks(x, box)))

"""Nested operating region induced by the exact viability margin."""
function viability_region(health::Real; nominal=0.50f0, protective=0.20f0)
    0f0 < protective < nominal < 1f0 || error("require 0 < protective < nominal < 1")
    h = Float32(health)
    h > nominal && return :nominal
    h > protective && return :adaptive
    h > 0f0 && return :protective
    return :emergency
end

"""A deliberately distinct HyperLIF operating regime.

Rate bands are measured as upcrossings per neuron per sampled time step. The
tuning values are hypotheses to calibrate against the dataset input scale;
their names do not assert that a desired firing regime has already occurred.
"""
Base.@kwdef struct RegimeSpec
    name::Symbol
    health_center::Float32
    health_width::Float32
    target_rate_min::Float32
    target_rate_max::Float32
    tau_v::Float32
    tau_r::Float32
    alpha::Float32
    gamma::Float32
    v_threshold::Float32
    reset_gain::Float32
    input_scale::Float32
end

function default_regimes()
    return (
        RegimeSpec(name=:subthreshold, health_center=0.95f0, health_width=0.30f0,
                   target_rate_min=0f0, target_rate_max=0.005f0,
                   tau_v=0.030f0, tau_r=0.005f0, alpha=100f0, gamma=0.20f0,
                   v_threshold=1.25f0,
                   reset_gain=140f0, input_scale=8f0),
        RegimeSpec(name=:sparse, health_center=0.75f0, health_width=0.28f0,
                   target_rate_min=0.002f0, target_rate_max=0.03f0,
                   tau_v=0.024f0, tau_r=0.003f0, alpha=100f0, gamma=0.20f0,
                   v_threshold=1.05f0,
                   reset_gain=110f0, input_scale=12f0),
        RegimeSpec(name=:regular, health_center=0.45f0, health_width=0.25f0,
                   target_rate_min=0.01f0, target_rate_max=0.10f0,
                   tau_v=0.018f0, tau_r=0.002f0, alpha=100f0, gamma=0.20f0,
                   v_threshold=0.90f0,
                   reset_gain=85f0, input_scale=16f0),
        RegimeSpec(name=:burst, health_center=0.10f0, health_width=0.20f0,
                   target_rate_min=0.04f0, target_rate_max=0.30f0,
                   tau_v=0.012f0, tau_r=0.0005f0, alpha=60f0, gamma=0.10f0,
                   v_threshold=1.05f0, reset_gain=400f0, input_scale=20f0),
    )
end

function _replace_fields(regime::RegimeSpec, overrides::NamedTuple)
    names = fieldnames(RegimeSpec)
    source = NamedTuple{names}(Tuple(getfield(regime, name) for name in names))
    return RegimeSpec(; merge(source, overrides)...)
end

_replace_input_scale(regime::RegimeSpec, scale) =
    _replace_fields(regime, (input_scale=Float32(scale),))

"""Training-only SHD calibration frozen from `calibrate_dataset_activity.jl`.

Only input gain differs from `default_regimes`; labels and test examples were
not used. Recalibrate rather than transferring these gains to another cache.
"""
function shd_calibrated_regimes()
    scales = (2f0, 4f0, 32f0, 32f0)
    return Tuple(_replace_input_scale(regime, scale)
                 for (regime, scale) in zip(default_regimes(), scales))
end

"""SHD shared-gain regime profile grounded in the measured reachable envelope.

`shd_calibrated_regimes` selects a separate input gain per regime. On the only
local cache that lever fails: at gain 32 the `regular` and `burst` populations
sit above threshold for roughly half of all neuron-time steps while their
crossing count stays pinned near one per 20-step sequence, and both of those
gains were the maximum of the search grid rather than an interior optimum.
Sweeping the gain to 512 moves the crossing rate by less than a factor of two
(`results/reachable_rate_envelope.csv`).

A single shared gain inside the unsaturated window instead lets the intrinsic
parameters set the regime, which is what the heterogeneity hypothesis claims,
and removes the input-SNR confound between populations. At gain 1.4 the four
regimes measure 0.0024 / 0.0057 / 0.0116 / 0.0221 upcrossings per neuron-step
in the intended order with burst occupancy 0.037
(`results/shared_gain_sweep.csv`).
"""
function shd_shared_gain_regimes(scale=1.4f0)
    bands = ((0f0, 0.0035f0), (0.0035f0, 0.0085f0),
             (0.0085f0, 0.0165f0), (0.0165f0, 0.0400f0))
    return Tuple(_replace_fields(regime,
                                 (input_scale=Float32(scale),
                                  target_rate_min=band[1],
                                  target_rate_max=band[2]))
                 for (regime, band) in zip(default_regimes(), bands))
end

"""Parameter-mean regime used to build matched homogeneous controls.

Averaging is over the numeric fields only. The result is the null against which
a heterogeneity claim must be tested: one population whose intrinsic parameters
are the mean of the bank, at the same input gain.
"""
function mean_regime(regimes; name=:homogeneous_mean)
    numeric = (:health_center, :health_width, :target_rate_min, :target_rate_max,
               :tau_v, :tau_r, :alpha, :gamma, :v_threshold, :reset_gain,
               :input_scale)
    averaged = NamedTuple{numeric}(Tuple(
        Float32(sum(getfield(regime, field) for regime in regimes) / length(regimes))
        for field in numeric))
    return RegimeSpec(; merge((name=name,), averaged)...)
end

"""Single mean-parameter regime carrying the whole hidden budget of the bank."""
matched_homogeneous_regime(regimes) = (mean_regime(regimes),)

function _softmax(values::AbstractVector)
    centered = values .- maximum(values)
    positive = exp.(centered)
    return positive ./ sum(positive)
end

"""State-dependent arbitration prior over heterogeneous populations."""
function regime_weights(health::Real, regimes=default_regimes(); temperature=0.20f0)
    temperature > 0 || error("temperature must be positive")
    h = Float32(health)
    logits = Float32[-0.5f0 * ((h - r.health_center) / r.health_width)^2
                     for r in regimes]
    return _softmax(logits ./ Float32(temperature))
end

function _config_namedtuple(config::HyperConfig)
    names = fieldnames(HyperConfig)
    return NamedTuple{names}(Tuple(getfield(config, name) for name in names))
end

"""Create one configuration per regime without changing the HyperLIF equations."""
function build_population_configs(base::HyperConfig, regimes=default_regimes())
    original = _config_namedtuple(base)
    return Tuple(begin
        overrides = (tau_v=regime.tau_v, tau_r=regime.tau_r,
                     alpha=regime.alpha, gamma=regime.gamma,
                     v_threshold=regime.v_threshold,
                     event_threshold=regime.v_threshold,
                     reset_gain=regime.reset_gain,
                     input_scale=regime.input_scale)
        validate_config(HyperConfig(; merge(original, overrides)...))
    end for regime in regimes)
end

"""Initialize independent population trunks and a learned logit-level mixer."""
function init_heterogeneous_parameters(rng::AbstractRNG, n_input::Int,
                                       hidden_per_population::Int, n_classes::Int,
                                       configs)
    hidden_per_population > 0 || error("hidden_per_population must be positive")
    populations = Tuple(init_parameters(rng, n_input, hidden_per_population,
                                        n_classes, config) for config in configs)
    return (populations=populations, mix_logits=zeros(Float32, length(configs)))
end

"""Mix independently decoded population evidence.

`prior_weights` can be uniform for image/audio complementarity experiments or
can come from `regime_weights(viability_health(...))` in closed-loop control.
The learned mixer is multiplied by the prior, so plant state can override a
classifier preference without erasing trainable specialization.
"""
function heterogeneous_forward(parameters, input, configs;
                               prior_weights=fill(1f0 / length(configs), length(configs)))
    length(parameters.populations) == length(configs) ||
        error("one parameter block is required per population config")
    length(prior_weights) == length(configs) || error("prior weight count mismatch")
    learned = _softmax(parameters.mix_logits)
    combined = learned .* Float32.(prior_weights)
    weights = combined ./ sum(combined)
    outputs = Tuple(forward(parameters.populations[index], input, configs[index])
                    for index in eachindex(configs))
    logits = zero(outputs[1][1])
    for index in eachindex(outputs)
        logits = logits .+ weights[index] .* outputs[index][1]
    end
    return logits, (weights=weights,
                    population_logits=Tuple(output[1] for output in outputs),
                    populations=Tuple(output[2] for output in outputs))
end

function heterogeneous_classification_loss(parameters, input, targets, configs;
                                           prior_weights=fill(1f0 / length(configs),
                                                              length(configs)))
    logits, _ = heterogeneous_forward(parameters, input, configs;
                                      prior_weights=prior_weights)
    shifted = logits .- maximum(logits; dims=1)
    log_probabilities = shifted .- log.(sum(exp.(shifted); dims=1))
    return -sum(targets .* log_probabilities) / Float32(size(input, 2))
end

"""Convert existing HyperLIF diagnostics to event and occupancy fractions."""
function population_activity(aux, hidden::Int, time_steps::Int)
    denominator = Float32(hidden * time_steps)
    return (event_rate=Float32(aux.crossings_per_sample) / denominator,
            occupancy_rate=Float32(aux.occupancy_per_sample) / denominator,
            gate_mean=Float32(aux.gate_mean),
            no_event_fraction=Float32(aux.no_event_fraction))
end

struct HomeostaticState
    ema_rates::Vector{Float32}
    threshold_offsets::Vector{Float32}
end

HomeostaticState(populations::Int) =
    HomeostaticState(zeros(Float32, populations), zeros(Float32, populations))

"""Slow intrinsic homeostasis that preserves population-specific rate bands.

If a population is too active, its threshold offset increases; if it is too
quiet, the offset decreases. Updates are multiplied by a plant-level
plasticity gate, coupling neural adaptation to robot viability while keeping
the two notions mathematically distinct.
"""
function update_homeostasis(state::HomeostaticState, observed_rates, regimes;
                            ema_fraction=0.10f0, learning_rate=0.05f0,
                            gate=1f0, offset_limit=0.40f0)
    length(observed_rates) == length(regimes) == length(state.ema_rates) ||
        error("homeostatic vector lengths must match")
    0f0 <= ema_fraction <= 1f0 || error("ema_fraction must lie in [0,1]")
    0f0 <= gate <= 1f0 || error("gate must lie in [0,1]")
    ema = (1f0 - ema_fraction) .* state.ema_rates .+
          ema_fraction .* Float32.(observed_rates)
    targets = Float32[(r.target_rate_min + r.target_rate_max) / 2f0 for r in regimes]
    offsets = clamp.(state.threshold_offsets .+
                     Float32(learning_rate * gate) .* (ema .- targets),
                     -Float32(offset_limit), Float32(offset_limit))
    return HomeostaticState(ema, offsets)
end

function apply_threshold_offsets(configs, state::HomeostaticState)
    length(configs) == length(state.threshold_offsets) || error("offset count mismatch")
    return Tuple(begin
        source = _config_namedtuple(configs[index])
        threshold = max(0.05f0, configs[index].v_threshold + state.threshold_offsets[index])
        validate_config(HyperConfig(; merge(source, (v_threshold=threshold,
                                                      event_threshold=threshold))...))
    end for index in eachindex(configs))
end

"""Smoothly freeze learning close to or outside the viability boundary."""
function plasticity_gate(health::Real; freeze_health=0.15f0, temperature=0.03f0)
    temperature > 0 || error("temperature must be positive")
    argument = clamp((Float32(health) - freeze_health) / temperature, -80f0, 80f0)
    return inv(1f0 + exp(-argument))
end

function rate_band_penalty(observed_rates, regimes)
    length(observed_rates) == length(regimes) || error("rate/regime count mismatch")
    total = 0f0
    for (rate, regime) in zip(observed_rates, regimes)
        below = max(0f0, regime.target_rate_min - Float32(rate))
        above = max(0f0, Float32(rate) - regime.target_rate_max)
        total += below^2 + above^2
    end
    return total / Float32(length(regimes))
end

struct CBFConstraints
    A::Matrix{Float32}
    b::Vector{Float32}
end

struct SafetyResult
    action::Vector{Float32}
    max_violation::Float32
    certified::Bool
    iterations::Int
end

"""Linear CBF inequalities for a control-affine model xdot=f+G*u.

For h_lower=x-l and h_upper=u-x, the exponential CBF condition
hdot+kappa*h >= 0 becomes A*u <= b. Action bounds are appended to the same
halfspace system. This is a local model-based condition, not a learned global
viability-kernel certificate.
"""
function cbf_constraints(x, drift, control_matrix, box::ViabilityBox;
                         kappa=5f0, action_lower=nothing, action_upper=nothing)
    n = length(box.lower)
    length(x) == n == length(drift) || error("state/drift dimension mismatch")
    size(control_matrix, 1) == n || error("control matrix row count mismatch")
    m = size(control_matrix, 2)
    lo_u = action_lower === nothing ? fill(-Inf32, m) : Float32.(action_lower)
    hi_u = action_upper === nothing ? fill(Inf32, m) : Float32.(action_upper)
    length(lo_u) == m == length(hi_u) || error("action-bound dimension mismatch")
    all(lo_u .<= hi_u) || error("action lower bound exceeds upper bound")

    xf, ff, gf = Float32.(x), Float32.(drift), Float32.(control_matrix)
    A = vcat(-gf, gf)
    b = vcat(ff .+ Float32(kappa) .* (xf .- box.lower),
             -ff .+ Float32(kappa) .* (box.upper .- xf))
    finite_lower = findall(isfinite, lo_u)
    finite_upper = findall(isfinite, hi_u)
    if !isempty(finite_lower)
        rows = zeros(Float32, length(finite_lower), m)
        for (row, column) in enumerate(finite_lower)
            rows[row, column] = -1f0
        end
        A = vcat(A, rows)
        b = vcat(b, -lo_u[finite_lower])
    end
    if !isempty(finite_upper)
        rows = zeros(Float32, length(finite_upper), m)
        for (row, column) in enumerate(finite_upper)
            rows[row, column] = 1f0
        end
        A = vcat(A, rows)
        b = vcat(b, hi_u[finite_upper])
    end
    return CBFConstraints(A, b)
end

"""Cyclic Euclidean projection onto linear halfspaces.

The returned action is marked certified only when every inequality is within
`tolerance`. Infeasible constraints or non-convergence are therefore surfaced
rather than silently described as safe. A production robot should replace
this reference projection with a monitored QP solver and backup controller.
"""
function project_halfspaces(action, constraints::CBFConstraints;
                            max_sweeps=200, tolerance=1f-5)
    u = Float32.(collect(action))
    size(constraints.A, 2) == length(u) || error("action dimension mismatch")
    iterations = 0
    for sweep in 1:max_sweeps
        iterations = sweep
        changed = false
        for row in axes(constraints.A, 1)
            normal = view(constraints.A, row, :)
            violation = dot(normal, u) - constraints.b[row]
            if violation > tolerance
                norm_squared = dot(normal, normal)
                norm_squared > eps(Float32) || continue
                u .-= (violation / norm_squared) .* normal
                changed = true
            end
        end
        !changed && break
    end
    violations = constraints.A * u .- constraints.b
    maximum_violation = isempty(violations) ? 0f0 : max(0f0, maximum(violations))
    return SafetyResult(u, maximum_violation,
                        maximum_violation <= tolerance, iterations)
end

function shield_action(action, x, drift, control_matrix, box::ViabilityBox; kwargs...)
    constraint_keys = (:kappa, :action_lower, :action_upper)
    projection_keys = (:max_sweeps, :tolerance)
    constraint_args = (; (key => value for (key, value) in kwargs if key in constraint_keys)...)
    projection_args = (; (key => value for (key, value) in kwargs if key in projection_keys)...)
    constraints = cbf_constraints(x, drift, control_matrix, box; constraint_args...)
    return project_halfspaces(action, constraints; projection_args...)
end

end
