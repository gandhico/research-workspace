module HyperLIFArchitectures

using LinearAlgebra
using Random
using Statistics

export HyperLIFParams, HyperLIFState, Architecture, init_architecture
export hyperlif_step, forward, readout_features, batchnorm_features

"""Parameters of the stable discrete HyperLIF map.

`adaptive=false` gives HyperLIF with fixed reset conductance. With
`adaptive=true`, the conductance gain is affine in `abs(current)`.
"""
Base.@kwdef struct HyperLIFParams{T<:AbstractFloat}
    dt::T = T(1e-3)
    tau::T = T(0.02)
    tau_r::T = T(0.002)
    alpha::T = T(100)
    gamma::T = T(0.2)
    v_rest::T = zero(T)
    v_threshold::T = one(T)
    v_reset::T = zero(T)
    reset_gain::T = T(100)
    base_gain::T = T(20)
    gain_scaling::T = T(80)
    min_voltage::T = zero(T)
    event_threshold::T = one(T)
    event_mode::Symbol = :occupancy
    delta_reset::T = zero(T)
    adaptive::Bool = false
end

mutable struct HyperLIFState{T<:AbstractFloat}
    v::Matrix{T}
    r::Matrix{T}
end

function HyperLIFState(hidden::Integer, batch::Integer, p::HyperLIFParams{T}) where T
    HyperLIFState(fill(p.v_rest, hidden, batch), zeros(T, hidden, batch))
end

"""One exact frozen-current step of the validated PyTorch dynamics.

The gate is integrated analytically over `dt` after freezing its logistic
target at the beginning of the interval. The voltage is then integrated
analytically after freezing `r_next` and the input current. This split map is
the numerical model used by the PyTorch implementation; it is not an exact
flow of the fully coupled continuous ODE.
"""
function hyperlif_step(state::HyperLIFState{T}, current::AbstractMatrix{T},
                       p::HyperLIFParams{T}) where T
    size(state.v) == size(current) || throw(DimensionMismatch("state/current shape mismatch"))
    p.event_mode in (:occupancy, :upcrossing) ||
        error("event_mode must be :occupancy or :upcrossing")
    v_previous = copy(state.v)
    effective_threshold = p.v_threshold .- p.gamma .* state.r
    argument = clamp.(p.alpha .* (state.v .- effective_threshold), T(-700), T(700))
    target = one(T) ./ (one(T) .+ exp.(-argument))
    gate_decay = exp(-p.dt / p.tau_r)
    r_next = clamp.(target .+ (state.r .- target) .* gate_decay, zero(T), one(T))

    gain = p.adaptive ? p.base_gain .+ p.gain_scaling .* abs.(current) :
                        fill(p.reset_gain, size(current))
    conductance = gain .* r_next.^2
    reset_anchor = p.v_reset .- p.delta_reset .* r_next
    lambda = inv(p.tau) .+ conductance
    drive = p.v_rest / p.tau .+ current ./ p.tau .+ conductance .* reset_anchor
    decay = exp.(-lambda .* p.dt)
    v_next = state.v .* decay .+ (drive ./ lambda) .* (one(T) .- decay)
    v_next = max.(v_next, p.min_voltage)
    # `:occupancy` reproduces the published snnTorch/APEX-v2 architecture
    # harness: one binary mark for every sample held above threshold. It is
    # not a physical spike count. `:upcrossing` emits one event only when the
    # sampled trajectory crosses the event surface from below; this matches
    # the standalone/Nengo event semantics (up to within-step interpolation).
    spikes = if p.event_mode == :occupancy
        T.(v_next .>= p.event_threshold)
    else
        T.((v_previous .< p.event_threshold) .& (v_next .>= p.event_threshold))
    end

    state.v .= v_next
    state.r .= r_next
    return (spikes=spikes, voltage=v_next, gate=r_next,
            conductance=tanh.(conductance ./ T(20)))
end

"""Dense, recurrent, or centered-delay HyperLIF classifier trunk.

Arrays use Julia's efficient layout `features x batch x time`. The `delay`
architecture intentionally reproduces PyTorch `Conv1d(..., padding=k//2)`:
it is centered and therefore noncausal. Use `delay_mode=:causal` for online
control; that mode uses only the present and past samples and is not expected
to match the published offline PyTorch delay benchmark.
"""
mutable struct Architecture{T<:AbstractFloat}
    kind::Symbol
    readout::Symbol
    params::HyperLIFParams{T}
    W_in::Matrix{T}
    b_in::Vector{T}
    W_rec::Union{Nothing,Matrix{T}}
    delay_kernel::Union{Nothing,Matrix{T}}
    W_head::Matrix{T}
    b_head::Vector{T}
    delay_mode::Symbol
end

function init_architecture(n_input::Integer, hidden::Integer, n_classes::Integer;
                           kind::Symbol=:dense, readout::Symbol=:hybrid_vr,
                           params::HyperLIFParams{T}=HyperLIFParams{Float32}(),
                           seed::Integer=1, input_scale::Real=16,
                           recurrent_gain::Real=0.2, kernel_size::Integer=7,
                           delay_mode::Symbol=:centered) where T
    kind in (:dense, :recurrent, :delay) || error("kind must be :dense, :recurrent, or :delay")
    readout in (:spike_count, :membrane, :gate, :hybrid_gr, :hybrid_vr,
                :hybrid_vr_conductance) || error("unknown readout")
    isodd(kernel_size) || error("kernel_size must be odd")
    delay_mode in (:centered, :causal) || error("delay_mode must be :centered or :causal")
    rng = MersenneTwister(seed)
    W_in = randn(rng, T, hidden, n_input) .* T(input_scale / sqrt(max(n_input, 1)))
    b_in = zeros(T, hidden)
    W_rec = nothing
    if kind == :recurrent
        q = Matrix(qr(randn(rng, T, hidden, hidden)).Q)
        W_rec = T(recurrent_gain) .* q
    end
    kernel = nothing
    if kind == :delay
        kernel = zeros(T, hidden, kernel_size)
        kernel[:, cld(kernel_size, 2)] .= one(T)
    end
    multiplier = readout in (:hybrid_gr, :hybrid_vr) ? 2 :
                 readout == :hybrid_vr_conductance ? 3 : 1
    feature_dim = hidden * multiplier
    W_head = randn(rng, T, n_classes, feature_dim) .* sqrt(T(2 / max(feature_dim, 1)))
    Architecture(kind, readout, params, W_in, b_in, W_rec, kernel, W_head,
                 zeros(T, n_classes), delay_mode)
end

function readout_features(readout::Symbol, vbar, rbar, gbar, spike_sum)
    readout == :spike_count && return spike_sum
    readout == :membrane && return vbar
    readout == :gate && return rbar
    readout == :hybrid_gr && return vcat(rbar, gbar)
    readout == :hybrid_vr && return vcat(vbar, rbar)
    readout == :hybrid_vr_conductance && return vcat(vbar, rbar, gbar)
    error("unknown readout")
end

function batchnorm_features(features::AbstractMatrix{T}; epsilon::T=T(1e-5)) where T
    mu = mean(features; dims=2)
    centered = features .- mu
    sigma = sqrt.(mean(centered.^2; dims=2) .+ epsilon)
    centered ./ sigma
end

function _current_sequence(model::Architecture{T}, x::AbstractArray{T,3}) where T
    n_input, batch, time = size(x)
    size(model.W_in, 2) == n_input || throw(DimensionMismatch("input feature mismatch"))
    hidden = size(model.W_in, 1)
    currents = Array{T}(undef, hidden, batch, time)
    for t in 1:time
        currents[:, :, t] .= model.W_in * @view(x[:, :, t]) .+ model.b_in
    end
    model.kind != :delay && return currents

    mixed = zeros(T, hidden, batch, time)
    kernel = something(model.delay_kernel)
    center = cld(size(kernel, 2), 2)
    for t in 1:time, k in axes(kernel, 2)
        source = model.delay_mode == :centered ? t + k - center : t - (k - 1)
        1 <= source <= time || continue
        mixed[:, :, t] .+= @view(currents[:, :, source]) .* @view(kernel[:, k])
    end
    mixed
end

"""Run a complete forward pass and return logits, features, and diagnostics."""
function forward(model::Architecture{T}, x::AbstractArray{T,3}) where T
    hidden, batch, time = size(model.W_in, 1), size(x, 2), size(x, 3)
    time > 0 || error("time dimension must be nonzero")
    currents = _current_sequence(model, x)
    state = HyperLIFState(hidden, batch, model.params)
    vbar = zeros(T, hidden, batch)
    rbar = zeros(T, hidden, batch)
    gbar = zeros(T, hidden, batch)
    spike_sum = zeros(T, hidden, batch)
    previous_spikes = zeros(T, hidden, batch)

    for t in 1:time
        current = copy(@view currents[:, :, t])
        if model.kind == :recurrent
            current .+= something(model.W_rec) * previous_spikes
        end
        step = hyperlif_step(state, current, model.params)
        vbar .+= step.voltage
        rbar .+= step.gate
        gbar .+= step.conductance
        spike_sum .+= step.spikes
        previous_spikes .= step.spikes
    end
    vbar ./= T(time)
    rbar ./= T(time)
    gbar ./= T(time)
    features = readout_features(model.readout, vbar, rbar, gbar, spike_sum)
    normalized = batchnorm_features(features)
    logits = model.W_head * normalized .+ model.b_head
    return (logits=logits, features=features, finite=all(isfinite, logits) && all(isfinite, features),
            events_per_sample=mean(sum(spike_sum; dims=1)), gate_mean=mean(rbar),
            voltage_mean=mean(vbar), conductance_mean=mean(gbar))
end

end
