module Hover3DOFHIL

include(joinpath(@__DIR__, "..", "..", "julia_bridge", "julia", "QuanserHIL.jl"))
using .QuanserHIL

export HoverSample, RateFilter, probe, open_hardware, read_sample!, step!
export motor_to_dac, write_motor_voltages!, safe_zero!, close

const AO_CHANNELS = UInt32[0, 1, 2, 3]       # front, back, left, right
const ENCODER_CHANNELS = UInt32[0, 1, 2]     # pitch, roll, yaw
const K_ENCODER = 2pi / (8 * 1024)
const K_ENCODER_YAW = -K_ENCODER
const AMPLIFIER_GAIN = 3.0
const MAX_MOTOR_VOLTAGE = 24.0
const MAX_DAC_VOLTAGE = 10.0

struct HoverSample
    yaw::Float64
    pitch::Float64
    roll::Float64
    yaw_rate::Float64
    pitch_rate::Float64
    roll_rate::Float64
end

mutable struct RateFilter
    x1::Vector{Float64}
    x2::Vector{Float64}
    cutoff::Float64
    damping::Float64
end

RateFilter(n::Integer=3; cutoff::Real=2pi*20, damping::Real=0.8) =
    RateFilter(zeros(n), zeros(n), Float64(cutoff), Float64(damping))

"""Vendor band-limited differentiator, discretized as in the validated Python runner."""
function step!(filter::RateFilter, angles::AbstractVector, dt::Real)
    length(angles) == length(filter.x1) || throw(DimensionMismatch("angle dimension"))
    w = filter.cutoff
    x1_dot = copy(filter.x2)
    x2_dot = -w^2 .* filter.x1 .- 2filter.damping*w .* filter.x2 .+ angles
    filter.x1 .+= dt .* x1_dot
    filter.x2 .+= dt .* x2_dot
    w^2 .* filter.x2
end

probe() = QuanserHIL.probe(:hover3dof)

"""Open the physical Q8 only when called explicitly by a hardware runner."""
open_hardware(identifier::AbstractString="0") = QuanserHIL.open_card("q8_usb", identifier)

function read_sample!(card, filter::RateFilter, dt::Real; home=zeros(3))
    raw = QuanserHIL.read_immediate(card; encoders=ENCODER_CHANNELS)
    pitch = raw.encoders[1] * K_ENCODER - home[2]
    roll = raw.encoders[2] * K_ENCODER - home[3]
    yaw = raw.encoders[3] * K_ENCODER_YAW - home[1]
    rates = step!(filter, [yaw, pitch, roll], dt)
    HoverSample(yaw, pitch, roll, rates[1], rates[2], rates[3])
end

"""Convert motor-equivalent voltage to the Q8 DAC command with both limits enforced."""
function motor_to_dac(volts::AbstractVector;
                      amplifier_gain::Real=AMPLIFIER_GAIN,
                      max_motor_voltage::Real=MAX_MOTOR_VOLTAGE,
                      max_dac_voltage::Real=MAX_DAC_VOLTAGE)
    length(volts) == 4 || throw(DimensionMismatch("expected four motor voltages"))
    amplifier_gain > 0 || error("amplifier_gain must be positive")
    clamp.(Float64.(volts), 0.0, Float64(max_motor_voltage)) ./ amplifier_gain |>
        x -> clamp.(x, 0.0, Float64(max_dac_voltage))
end

function write_motor_voltages!(card, volts::AbstractVector; armed::Bool=false)
    dac = armed ? motor_to_dac(volts) : zeros(4)
    QuanserHIL.write_analog(card, AO_CHANNELS, Float64.(dac))
    dac
end

safe_zero!(card) = QuanserHIL.write_analog(card, AO_CHANNELS, zeros(4))
close(card) = QuanserHIL.close(card)

end
