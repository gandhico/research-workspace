module HyperLIFLearning

using LinearAlgebra
using Random
using Statistics
using Zygote

export HyperConfig, HyperState, init_parameters, initial_state
export neuron_step, forward, loss_and_accuracy, parameter_count
export classification_loss
export hard_upcrossing, surrogate_upcrossing, interpolated_event_time
export validate_config, feature_dimension

"""Numerical and learning contract for the three HyperLIF stages.

`cell` is `:hyperlif`, `:adaptive`, or `:next`.  `learning_mode` is
`:continuous`, `:surrogate`, or `:event_time`.  The forward event is always an
upward crossing.  Only its backward interpretation changes.

The `:next` cell adds three stable dendritic filters and a slow readiness-
adaptation state.  These are computational abstractions, not claims of
biophysical equivalence.
"""
Base.@kwdef struct HyperConfig
    cell::Symbol = :hyperlif
    learning_mode::Symbol = :continuous
    architecture::Symbol = :dense
    readout::Symbol = :mode_default
    delay_mode::Symbol = :causal
    dt::Float32 = 1f-3
    tau_v::Float32 = 0.02f0
    tau_r::Float32 = 0.002f0
    tau_a::Float32 = 0.20f0
    dendritic_taus::NTuple{3,Float32} = (0.004f0, 0.02f0, 0.10f0)
    alpha::Float32 = 100f0
    gamma::Float32 = 0.2f0
    kappa_a::Float32 = 0.15f0
    v_rest::Float32 = 0f0
    v_threshold::Float32 = 1f0
    v_reset::Float32 = 0f0
    reset_gain::Float32 = 100f0
    base_gain::Float32 = 20f0
    gain_scaling::Float32 = 80f0
    drive_smoothing::Float32 = 1f-4
    event_threshold::Float32 = 1f0
    surrogate_slope::Float32 = 10f0
    transversality_floor::Float32 = 1f-3
    input_scale::Float32 = 16f0
    recurrent_gain::Float32 = 0.2f0
    delay_kernel_size::Int = 7
end

function validate_config(c::HyperConfig)
    c.cell in (:hyperlif, :adaptive, :next) ||
        error("cell must be :hyperlif, :adaptive, or :next")
    c.learning_mode in (:continuous, :surrogate, :event_time) ||
        error("learning_mode must be :continuous, :surrogate, or :event_time")
    c.architecture in (:dense, :recurrent, :delay) ||
        error("architecture must be :dense, :recurrent, or :delay")
    c.delay_mode in (:causal, :centered) ||
        error("delay_mode must be :causal or :centered")
    c.delay_kernel_size > 0 && isodd(c.delay_kernel_size) ||
        error("delay_kernel_size must be a positive odd integer")
    all(>(0f0), (c.dt, c.tau_v, c.tau_r, c.tau_a, c.dendritic_taus...)) ||
        error("all time constants and dt must be positive")
    c.alpha > 0f0 && c.surrogate_slope > 0f0 && c.drive_smoothing > 0f0 ||
        error("alpha, surrogate_slope, and drive_smoothing must be positive")
    return c
end

"""Pure forward upward-crossing indicator; no reset is applied."""
hard_upcrossing(v_previous, v_next, threshold) =
    Float32.((v_previous .< threshold) .& (v_next .>= threshold))

"""Hard forward crossing with an explicitly declared fast-sigmoid backward.

The adjoint is intentionally a surrogate, not the derivative of the Boolean
forward map.  No gradient is assigned to `v_previous` or the threshold.
"""
surrogate_upcrossing(v_previous, v_next, threshold, slope) =
    hard_upcrossing(v_previous, v_next, threshold)

Zygote.@adjoint function surrogate_upcrossing(v_previous, v_next, threshold, slope)
    output = hard_upcrossing(v_previous, v_next, threshold)
    function pullback(delta)
        distance = v_next .- threshold
        local_gradient = slope ./ (1f0 .+ slope .* abs.(distance)).^2
        return (zero(v_previous), delta .* local_gradient, nothing, nothing)
    end
    return output, pullback
end

"""Linearly interpolated within-step event time and transversal speed.

This formula is differentiable only while the event topology is fixed and
`v_next-v_previous != 0`.  The caller must use the crossing mask and report the
speed diagnostic; grazing events are ill-conditioned by construction.
"""
function interpolated_event_time(v_previous, v_next, threshold, step_start, dt)
    delta_v = v_next .- v_previous
    magnitude = max.(abs.(delta_v), eps(Float32))
    safe_delta = ifelse.(delta_v .>= 0f0, magnitude, .-magnitude)
    fraction = clamp.((threshold .- v_previous) ./ safe_delta, 0f0, 1f0)
    return step_start .+ dt .* fraction, abs.(delta_v) ./ dt
end

struct HyperState{A,D,S}
    v::A
    r::A
    a::A
    dendrites::D
    previous_event::A
    seen_event::S
    first_event_time::A
    minimum_event_speed::A
end

function initial_state(template, hidden::Int, batch::Int, horizon::Float32)
    z = zero(template[1:hidden, 1:batch])
    dendrites = (zero(z), zero(z), zero(z))
    seen = z .> Inf32
    return HyperState(z, z, z, dendrites, z, seen,
                      z .+ horizon, z .+ Inf32)
end

function _dendritic_update(state::HyperState, current, c::HyperConfig, mix)
    if c.cell != :next
        return state.dendrites, current
    end
    updated = ntuple(3) do branch
        decay = exp(-c.dt / c.dendritic_taus[branch])
        state.dendrites[branch] .* decay .+ current .* (1f0 - decay)
    end
    # Learned logits become a convex combination.  This preserves the meaning
    # of the branches as a mixture of stable low-pass filters and prevents an
    # unconstrained signed sum from masquerading as biological dendrites.
    centered_mix = mix .- maximum(mix; dims=2)
    positive_mix = exp.(centered_mix)
    weights = positive_mix ./ sum(positive_mix; dims=2)
    drive = zero(current)
    for branch in 1:3
        drive = drive .+ reshape(view(weights, :, branch), :, 1) .* updated[branch]
    end
    return updated, drive
end

function neuron_step(state::HyperState, current, c::HyperConfig, dendritic_mix;
                     step_start::Float32=0f0)
    validate_config(c)
    dendrites, drive = _dendritic_update(state, current, c, dendritic_mix)

    effective_threshold = c.v_threshold .+ c.kappa_a .* state.a .- c.gamma .* state.r
    argument = clamp.(c.alpha .* (state.v .- effective_threshold), -80f0, 80f0)
    target = 1f0 ./ (1f0 .+ exp.(-argument))
    gate_decay = exp(-c.dt / c.tau_r)
    r_next = clamp.(target .+ (state.r .- target) .* gate_decay, 0f0, 1f0)

    smooth_magnitude = sqrt.(drive.^2 .+ c.drive_smoothing^2) .- c.drive_smoothing
    scale = c.cell in (:adaptive, :next) ?
        c.base_gain .+ c.gain_scaling .* smooth_magnitude :
        c.reset_gain .+ zero(drive)
    conductance = scale .* r_next.^2
    lambda = inv(c.tau_v) .+ conductance
    forcing = c.v_rest / c.tau_v .+ drive ./ c.tau_v .+ conductance .* c.v_reset
    decay = exp.(-lambda .* c.dt)
    v_next = state.v .* decay .+ (forcing ./ lambda) .* (1f0 .- decay)

    event = c.learning_mode == :surrogate ?
        surrogate_upcrossing(state.v, v_next, c.event_threshold, c.surrogate_slope) :
        hard_upcrossing(state.v, v_next, c.event_threshold)
    occupancy = Float32.(v_next .>= c.event_threshold)

    candidate_time, speed = interpolated_event_time(
        state.v, v_next, c.event_threshold, step_start, c.dt)
    crossing_mask = (state.v .< c.event_threshold) .& (v_next .>= c.event_threshold)
    first_mask = (.!state.seen_event) .& crossing_mask
    first_time = ifelse.(first_mask, candidate_time, state.first_event_time)
    minimum_speed = ifelse.(crossing_mask,
                            min.(state.minimum_event_speed, speed),
                            state.minimum_event_speed)
    seen = state.seen_event .| crossing_mask

    # The next-cell slow state is a readiness adaptation driven by the smooth
    # gate.  Event-driven SFA is a separate ablation because it changes the
    # differentiability contract.
    a_decay = exp(-c.dt / c.tau_a)
    a_drive = c.cell == :next ? r_next : zero(r_next)
    a_next = state.a .* a_decay .+ a_drive .* (1f0 - a_decay)

    next_state = HyperState(v_next, r_next, a_next, dendrites, event,
                            seen, first_time, minimum_speed)
    return next_state, (
        event=event,
        occupancy=occupancy,
        voltage=v_next,
        gate=r_next,
        adaptation=a_next,
        dendritic_mean=(dendrites[1] .+ dendrites[2] .+ dendrites[3]) ./ 3f0,
        conductance=tanh.(conductance ./ 20f0),
    )
end

function _readout_symbol(c::HyperConfig)
    c.readout != :mode_default && return c.readout
    c.learning_mode == :continuous && return c.cell == :next ? :hybrid_next : :hybrid_vr
    c.learning_mode == :surrogate && return :spike_count
    return :first_event_time
end

function feature_dimension(c::HyperConfig, hidden::Int)
    r = _readout_symbol(c)
    factors = Dict(
        :membrane => 1, :gate => 1, :conductance => 1,
        :spike_count => 1, :first_event_time => 1,
        :hybrid_vr => 2, :hybrid_zr => 2, :hybrid_time_vr => 3,
        :hybrid_next => 5,
    )
    haskey(factors, r) || error("unsupported readout $(r)")
    return hidden * factors[r]
end

function init_parameters(rng::AbstractRNG, n_input::Int, hidden::Int,
                         n_classes::Int, c::HyperConfig)
    validate_config(c)
    w_in = randn(rng, Float32, hidden, n_input) .* (c.input_scale / sqrt(Float32(n_input)))
    b_in = zeros(Float32, hidden)
    # Raw recurrence parameters are bounded in the forward pass; see
    # `_bounded_recurrent_matrix` below.
    w_rec = randn(rng, Float32, hidden, hidden)
    kernel = zeros(Float32, hidden, c.delay_kernel_size)
    kernel[:, cld(c.delay_kernel_size, 2)] .= 1f0
    mix = zeros(Float32, hidden, 3)  # softmax -> equal one-third weights
    n_features = feature_dimension(c, hidden)
    w_head = randn(rng, Float32, n_classes, n_features) .* sqrt(2f0 / n_features)
    b_head = zeros(Float32, n_classes)
    return (W_in=w_in, b_in=b_in, W_rec=w_rec,
            delay_kernel=kernel, dendritic_mix=mix,
            W_head=w_head, b_head=b_head)
end

function _bounded_recurrent_matrix(raw, c::HyperConfig)
    hidden = size(raw, 1)
    # ||tanh(raw)||₂ ≤ ||tanh(raw)||F ≤ hidden.  Thus division by hidden
    # gives the explicit bound ||W_eff||₂ ≤ recurrent_gain.  This bounds the
    # recurrent linear operator only; it is not a global stability proof for
    # the complete nonlinear cell.
    return (c.recurrent_gain / Float32(hidden)) .* tanh.(raw)
end

function _base_currents(p, input)
    time_steps = size(input, 3)
    return [p.W_in * view(input, :, :, t) .+ reshape(p.b_in, :, 1)
            for t in 1:time_steps]
end

function _delay_currents(p, base, c::HyperConfig)
    c.architecture != :delay && return base
    time_steps = length(base)
    center = cld(c.delay_kernel_size, 2)
    return [begin
        total = zero(base[t])
        for tap in 1:c.delay_kernel_size
            source = c.delay_mode == :causal ? t - (tap - 1) : t + tap - center
            if 1 <= source <= time_steps
                total = total .+ reshape(view(p.delay_kernel, :, tap), :, 1) .* base[source]
            end
        end
        total
    end for t in 1:time_steps]
end

function _assemble_features(c::HyperConfig, state::HyperState, sums, horizon)
    readout = _readout_symbol(c)
    time_feature = ifelse.(state.seen_event,
                           1f0 .- state.first_event_time ./ horizon,
                           zero(state.first_event_time))
    readout == :membrane && return sums.voltage
    readout == :gate && return sums.gate
    readout == :conductance && return sums.conductance
    readout == :spike_count && return sums.events
    readout == :first_event_time && return time_feature
    readout == :hybrid_vr && return vcat(sums.voltage, sums.gate)
    readout == :hybrid_zr && return vcat(sums.events, sums.gate)
    readout == :hybrid_time_vr && return vcat(time_feature, sums.voltage, sums.gate)
    readout == :hybrid_next && return vcat(
        sums.voltage, sums.gate, sums.conductance, sums.adaptation, sums.dendritic)
    error("unsupported readout $(readout)")
end

"""Internal forward pass; diagnostics can be omitted from the AD graph."""
function _forward(p, input, c::HyperConfig, collect_diagnostics::Bool)
    validate_config(c)
    hidden, batch = size(p.W_in, 1), size(input, 2)
    time_steps = size(input, 3)
    horizon = Float32(time_steps) * c.dt
    base = _delay_currents(p, _base_currents(p, input), c)
    state = initial_state(base[1], hidden, batch, horizon + c.dt)
    z = zero(base[1])
    sums = (voltage=z, gate=z, conductance=z, events=z,
            occupancy=z, adaptation=z, dendritic=z)

    for t in 1:time_steps
        recurrent_signal = c.learning_mode == :surrogate ? state.previous_event : state.r
        recurrence = c.architecture == :recurrent ?
            _bounded_recurrent_matrix(p.W_rec, c) * recurrent_signal : zero(base[t])
        current = base[t] .+ recurrence
        state, output = neuron_step(state, current, c, p.dendritic_mix;
                                    step_start=Float32(t - 1) * c.dt)
        sums = (
            voltage=sums.voltage .+ output.voltage,
            gate=sums.gate .+ output.gate,
            conductance=sums.conductance .+ output.conductance,
            events=sums.events .+ output.event,
            occupancy=sums.occupancy .+ output.occupancy,
            adaptation=sums.adaptation .+ output.adaptation,
            dendritic=sums.dendritic .+ output.dendritic_mean,
        )
    end
    inv_steps = inv(Float32(time_steps))
    means = merge(sums, (
        voltage=sums.voltage .* inv_steps,
        gate=sums.gate .* inv_steps,
        conductance=sums.conductance .* inv_steps,
        adaptation=sums.adaptation .* inv_steps,
        dendritic=sums.dendritic .* inv_steps,
    ))
    features = _assemble_features(c, state, means, horizon)
    # Per-sample feature normalization avoids dependence on the other members
    # of a minibatch (and therefore avoids train/evaluation batch leakage).
    mu = mean(features; dims=1)
    sigma = sqrt.(mean((features .- mu).^2; dims=1) .+ 1f-5)
    normalized = (features .- mu) ./ sigma
    logits = p.W_head * normalized .+ reshape(p.b_head, :, 1)
    collect_diagnostics || return logits, nothing
    # Non-crossing neurons retain +Inf.  That is preferable to replacing them
    # by zero, which would falsely diagnose every sparse batch as grazing.
    minimum_crossing_speed = minimum(state.minimum_event_speed)
    event_neurons = Float32.(state.seen_event)
    grazing_neurons = Float32.(state.seen_event .&
        (state.minimum_event_speed .< c.transversality_floor))
    grazing_given_event = sum(grazing_neurons) / max(sum(event_neurons), 1f0)
    aux = (
        crossings_per_sample=mean(sum(sums.events; dims=1)),
        occupancy_per_sample=mean(sum(sums.occupancy; dims=1)),
        gate_mean=mean(means.gate),
        voltage_mean=mean(means.voltage),
        no_event_fraction=mean(Float32.(.!state.seen_event)),
        minimum_event_speed=minimum_crossing_speed,
        grazing_fraction=grazing_given_event,
        readout=_readout_symbol(c),
    )
    return logits, aux
end

"""Forward classifier. Input layout is features × batch × time."""
forward(p, input, c::HyperConfig) = _forward(p, input, c, true)

function classification_loss(p, input, targets, c::HyperConfig)
    logits, _ = _forward(p, input, c, false)
    shifted = logits .- maximum(logits; dims=1)
    log_probabilities = shifted .- log.(sum(exp.(shifted); dims=1))
    return -sum(targets .* log_probabilities) / Float32(size(input, 2))
end

function loss_and_accuracy(p, input, targets, labels, c::HyperConfig)
    logits, aux = forward(p, input, c)
    shifted = logits .- maximum(logits; dims=1)
    log_probabilities = shifted .- log.(sum(exp.(shifted); dims=1))
    loss = -sum(targets .* log_probabilities) / Float32(size(input, 2))
    cpu_logits = Array(logits)
    predictions = [argmax(view(cpu_logits, :, b)) for b in 1:size(cpu_logits, 2)]
    accuracy = mean(predictions .== labels)
    return loss, Float32(accuracy), aux
end

parameter_count(p) = sum(length, values(p))

end
