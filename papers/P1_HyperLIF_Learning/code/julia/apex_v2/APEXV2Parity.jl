module APEXV2Parity

using CUDA
using LinearAlgebra
using Random
using Statistics

export ARCHITECTURES, NEURONS, READOUT_MULT, READOUTS
export FeatureAccumulator, ParityConfig, ParityModel
export forward_summary!, init_model, reset_states!

const READOUT_MULT = Dict(
    "spike_count" => 1,
    "membrane" => 1,
    "gate" => 1,
    "hybrid_gr" => 2,
    "hybrid_vr" => 2,
    "hybrid_vr_conductance" => 3,
)

const READOUTS = collect(keys(READOUT_MULT))
const ARCHITECTURES = ["dense", "recurrent", "delay"]
const NEURONS = ["lif", "hyperlif", "adaptive"]

Base.@kwdef struct ParityConfig
    dt::Float32 = 0.001f0
    input_scale::Float32 = 16.0f0
    lif_beta::Float32 = 0.95f0
    tau::Float32 = 0.02f0
    tau_r::Float32 = 0.002f0
    alpha::Float32 = 100.0f0
    gamma::Float32 = 0.2f0
    v_rest::Float32 = 0.0f0
    v_thresh::Float32 = 1.0f0
    v_reset::Float32 = 0.0f0
    reset_gain::Float32 = 100.0f0
    base_gain::Float32 = 20.0f0
    gain_scaling::Float32 = 80.0f0
    min_voltage::Float32 = 0.0f0
    event_threshold::Float32 = 1.0f0
    delta_reset::Float32 = 0.0f0
    recurrent_gain::Float32 = 0.2f0
    delay_kernel_size::Int = 7
end

mutable struct FeatureAccumulator
    vbar::CuArray{Float32,2}
    rbar::CuArray{Float32,2}
    gbar::CuArray{Float32,2}
    spk_sum::CuArray{Float32,2}
    time_steps::Int
end

function FeatureAccumulator(hidden_dim::Int, batch_size::Int)
    return FeatureAccumulator(
        CUDA.zeros(Float32, hidden_dim, batch_size),
        CUDA.zeros(Float32, hidden_dim, batch_size),
        CUDA.zeros(Float32, hidden_dim, batch_size),
        CUDA.zeros(Float32, hidden_dim, batch_size),
        0,
    )
end

function reset!(acc::FeatureAccumulator)
    fill!(acc.vbar, 0.0f0)
    fill!(acc.rbar, 0.0f0)
    fill!(acc.gbar, 0.0f0)
    fill!(acc.spk_sum, 0.0f0)
    acc.time_steps = 0
    return nothing
end

function accumulate!(acc::FeatureAccumulator, v, r, g, spk)
    acc.vbar .+= v
    acc.rbar .+= r
    acc.gbar .+= g
    acc.spk_sum .+= spk
    acc.time_steps += 1
    return nothing
end

function finalized(acc::FeatureAccumulator)
    scale = acc.time_steps == 0 ? 1.0f0 : 1.0f0 / Float32(acc.time_steps)
    return (
        vbar = acc.vbar .* scale,
        rbar = acc.rbar .* scale,
        gbar = acc.gbar .* scale,
        spk_sum = copy(acc.spk_sum),
    )
end

mutable struct ParityModel
    architecture::String
    neuron::String
    readout::String
    W_in::CuArray{Float32,2}
    B_in::CuArray{Float32,1}
    W_rec::Union{Nothing,CuArray{Float32,2}}
    delay_kernel::Union{Nothing,CuArray{Float32,2}}
    W_head::CuArray{Float32,2}
    B_head::CuArray{Float32,1}
    v::CuArray{Float32,2}
    r::CuArray{Float32,2}
    mem::CuArray{Float32,2}
    prev_spk::CuArray{Float32,2}
    current::CuArray{Float32,2}
    rec_buf::CuArray{Float32,2}
    zeros_state::CuArray{Float32,2}
    acc::FeatureAccumulator
end

function _orthogonal_weight(n::Int, gain::Float32)
    q = Matrix(qr(randn(Float32, n, n)).Q)
    return gain .* q
end

function init_model(n_input::Int, hidden_dim::Int, n_classes::Int, batch_size::Int;
                    architecture::AbstractString="dense", neuron::AbstractString="hyperlif",
                    readout::AbstractString="hybrid_vr", seed::Int=1,
                    config::ParityConfig=ParityConfig())
    architecture = lowercase(String(architecture))
    architecture = architecture == "rsnn" ? "recurrent" : architecture
    neuron = lowercase(String(neuron))
    readout = lowercase(String(readout))

    architecture in ARCHITECTURES || error("Unknown architecture: $(architecture)")
    neuron in NEURONS || error("Unknown neuron for APEX-v2 forward parity: $(neuron)")
    haskey(READOUT_MULT, readout) || error("Unknown readout: $(readout)")
    if neuron == "lif" && readout in ("gate", "hybrid_gr", "hybrid_vr_conductance")
        # Keep these legal for structural-blindness checks; gate/conductance features will be zero.
    end

    Random.seed!(seed)
    CUDA.seed!(seed)

    w_scale = config.input_scale / sqrt(Float32(max(n_input, 1)))
    W_in = CuArray(randn(Float32, hidden_dim, n_input) .* w_scale)
    B_in = CUDA.zeros(Float32, hidden_dim)

    W_rec = architecture == "recurrent" ? CuArray(_orthogonal_weight(hidden_dim, config.recurrent_gain)) : nothing

    delay_kernel = nothing
    if architecture == "delay"
        kernel = zeros(Float32, hidden_dim, config.delay_kernel_size)
        center = cld(config.delay_kernel_size, 2)
        kernel[:, center] .= 1.0f0
        delay_kernel = CuArray(kernel)
    end

    feature_dim = hidden_dim * READOUT_MULT[readout]
    W_head = CuArray(randn(Float32, n_classes, feature_dim) .* sqrt(2.0f0 / Float32(max(feature_dim, 1))))
    B_head = CUDA.zeros(Float32, n_classes)

    z = CUDA.zeros(Float32, hidden_dim, batch_size)
    return ParityModel(
        architecture, neuron, readout,
        W_in, B_in, W_rec, delay_kernel, W_head, B_head,
        copy(z), copy(z), copy(z), copy(z), copy(z), copy(z), copy(z),
        FeatureAccumulator(hidden_dim, batch_size),
    )
end

function reset_states!(model::ParityModel, config::ParityConfig)
    fill!(model.v, config.v_rest)
    fill!(model.r, 0.0f0)
    fill!(model.mem, 0.0f0)
    fill!(model.prev_spk, 0.0f0)
    fill!(model.current, 0.0f0)
    fill!(model.rec_buf, 0.0f0)
    fill!(model.zeros_state, 0.0f0)
    reset!(model.acc)
    return nothing
end

function _input_current!(model::ParityModel, x_t)
    mul!(model.current, model.W_in, x_t)
    model.current .+= reshape(model.B_in, :, 1)
    return model.current
end

function _lif_step!(model::ParityModel, current, config::ParityConfig)
    @. model.mem = config.lif_beta * model.mem + current
    spk = ifelse.(model.mem .> config.event_threshold, 1.0f0, 0.0f0)
    @. model.mem = model.mem - spk * config.event_threshold
    return (spk=spk, v=model.mem, r=model.zeros_state, g=model.zeros_state)
end

function _hyperlif_step!(model::ParityModel, current, config::ParityConfig; adaptive::Bool=false)
    gate_decay = Float32(exp(-config.dt / config.tau_r))
    @. model.r = clamp(
        (1.0f0 / (1.0f0 + exp(-clamp(config.alpha * (model.v - (config.v_thresh - config.gamma * model.r)), -80.0f0, 80.0f0)))) +
        (model.r - (1.0f0 / (1.0f0 + exp(-clamp(config.alpha * (model.v - (config.v_thresh - config.gamma * model.r)), -80.0f0, 80.0f0))))) * gate_decay,
        0.0f0,
        1.0f0,
    )

    g = adaptive ?
        (config.base_gain .+ config.gain_scaling .* abs.(current)) .* (model.r .^ 2) :
        config.reset_gain .* (model.r .^ 2)
    v_reset_eff = config.v_reset .- config.delta_reset .* model.r
    lam = (1.0f0 / config.tau) .+ g
    drive = (config.v_rest / config.tau) .+ (current ./ config.tau) .+ (g .* v_reset_eff)
    decay = exp.(-lam .* config.dt)
    @. model.v = model.v * decay + (drive / lam) * (1.0f0 - decay)
    @. model.v = max(model.v, config.min_voltage)
    spk = ifelse.(model.v .> config.event_threshold, 1.0f0, 0.0f0)
    gbar_signal = tanh.(g ./ 20.0f0)
    return (spk=spk, v=model.v, r=model.r, g=gbar_signal)
end

function _step_neuron!(model::ParityModel, current, config::ParityConfig)
    if model.neuron == "lif"
        return _lif_step!(model, current, config)
    elseif model.neuron == "adaptive"
        return _hyperlif_step!(model, current, config; adaptive=true)
    else
        return _hyperlif_step!(model, current, config; adaptive=false)
    end
end

function _assemble(readout::AbstractString, trace)
    readout == "spike_count" && return trace.spk_sum
    readout == "membrane" && return trace.vbar
    readout == "gate" && return trace.rbar
    readout == "hybrid_gr" && return vcat(trace.rbar, trace.gbar)
    readout == "hybrid_vr" && return vcat(trace.vbar, trace.rbar)
    readout == "hybrid_vr_conductance" && return vcat(trace.vbar, trace.rbar, trace.gbar)
    error("Unknown readout: $(readout)")
end

function _batchnorm_features(features)
    mu = mean(features; dims=2)
    centered = features .- mu
    sigma = sqrt.(mean(centered .^ 2; dims=2) .+ 1.0f-5)
    return centered ./ sigma
end

function _forward_time_loop!(model::ParityModel, x_fbt, config::ParityConfig)
    time_steps = size(x_fbt, 3)
    for t in 1:time_steps
        x_t = view(x_fbt, :, :, t)
        current = _input_current!(model, x_t)
        if model.architecture == "recurrent"
            mul!(model.rec_buf, model.W_rec, model.prev_spk)
            current .+= model.rec_buf
        end
        state = _step_neuron!(model, current, config)
        accumulate!(model.acc, state.v, state.r, state.g, state.spk)
        if model.architecture == "recurrent"
            copyto!(model.prev_spk, state.spk)
        end
    end
    return nothing
end

function _forward_delay_loop!(model::ParityModel, x_fbt, config::ParityConfig)
    hidden_dim = size(model.W_in, 1)
    batch_size = size(x_fbt, 2)
    time_steps = size(x_fbt, 3)
    kernel_size = size(model.delay_kernel, 2)
    center = cld(kernel_size, 2)
    current_seq = CUDA.zeros(Float32, hidden_dim, batch_size, time_steps)

    for t in 1:time_steps
        x_t = view(x_fbt, :, :, t)
        current_t = view(current_seq, :, :, t)
        mul!(current_t, model.W_in, x_t)
        current_t .+= reshape(model.B_in, :, 1)
    end

    for t in 1:time_steps
        fill!(model.current, 0.0f0)
        for k in 1:kernel_size
            src_t = t + k - center
            if 1 <= src_t <= time_steps
                current_src = view(current_seq, :, :, src_t)
                kernel_col = view(model.delay_kernel, :, k)
                model.current .+= current_src .* reshape(kernel_col, :, 1)
            end
        end
        state = _step_neuron!(model, model.current, config)
        accumulate!(model.acc, state.v, state.r, state.g, state.spk)
    end
    return nothing
end

function forward_summary!(model::ParityModel, x_fbt, config::ParityConfig=ParityConfig())
    reset_states!(model, config)
    if model.architecture == "delay"
        _forward_delay_loop!(model, x_fbt, config)
    else
        _forward_time_loop!(model, x_fbt, config)
    end

    trace = finalized(model.acc)
    features = _assemble(model.readout, trace)
    norm_features = _batchnorm_features(features)
    logits = model.W_head * norm_features
    logits .+= reshape(model.B_head, :, 1)

    logits_cpu = Array(logits)
    features_cpu = Array(features)
    return (
        logits = logits,
        features = features,
        feature_dim = size(features, 1),
        logit_rows = size(logits, 1),
        logit_cols = size(logits, 2),
        finite = all(isfinite, logits_cpu) && all(isfinite, features_cpu),
        events_per_sample = Float64(mean(Array(sum(trace.spk_sum; dims=1)))),
        gate_mean = Float64(mean(Array(trace.rbar))),
        voltage_mean = Float64(mean(Array(trace.vbar))),
        conductance_mean = Float64(mean(Array(trace.gbar))),
    )
end

end
