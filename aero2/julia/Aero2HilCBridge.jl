module Aero2HilCBridge

using Libdl

const TCard = Ptr{Cvoid}
const TError = Cint
const TUInt32 = UInt32
const TInt32 = Int32
const TBoolean = Int8
const TDouble = Float64

const PITCH_COUNTS_PER_REV = 2880.0
const YAW_COUNTS_PER_REV = 4096.0
const MOTOR_COUNTS_PER_REV = 2048.0

const DEFAULT_SEARCH_DIRS = [
    raw"C:\Program Files\Common Files\Quanser\bin",
    raw"C:\Quanser\0_libraries\bin",
]

const READ_ANALOG_CHANNELS = TUInt32[0, 1]
const READ_ENCODER_CHANNELS = TUInt32[0, 1, 2, 3]
const READ_OTHER_CHANNELS = TUInt32[3000, 3001, 3002, 4000, 4001, 4002, 14000, 14001, 14002, 14003]
const WRITE_ANALOG_CHANNELS = TUInt32[0, 1]
const WRITE_DIGITAL_CHANNELS = TUInt32[0, 1]
const WRITE_LED_CHANNELS = TUInt32[11000, 11001, 11002]

const LIBRARY_CACHE = Dict{String, Ptr{Cvoid}}()

struct HilCard
    lib::String
    handle::TCard
end

function find_hil_library()
    env_path = get(ENV, "QUANSER_HIL_LIBRARY", "")
    if !isempty(env_path) && isfile(env_path)
        return env_path
    end
    found = Libdl.find_library(["hil"], DEFAULT_SEARCH_DIRS)
    return isempty(found) ? nothing : found
end

function require_hil_library(lib=find_hil_library())
    lib === nothing && error("Quanser hil.dll was not found. Set QUANSER_HIL_LIBRARY or add it to PATH.")
    return String(lib)
end

function library_handle(lib::AbstractString)
    return get!(LIBRARY_CACHE, String(lib)) do
        Libdl.dlopen(lib)
    end
end

function hil_symbol(lib::AbstractString, name::Symbol)
    return Libdl.dlsym(library_handle(lib), name)
end

function check_error(result::Integer, operation::AbstractString)
    result < 0 && error("$(operation) failed with Quanser HIL error code $(result)")
    return result
end

function open_card(card_type::AbstractString="quanser_aero2_usb", card_identifier::AbstractString="0"; lib=find_hil_library())
    library = require_hil_library(lib)
    card_ref = Ref{TCard}(C_NULL)
    result = ccall(hil_symbol(library, :hil_open), TError, (Cstring, Cstring, Ref{TCard}), card_type, card_identifier, card_ref)
    check_error(result, "hil_open")
    return HilCard(library, card_ref[])
end

function default_card_identifier(target::AbstractString="hardware", id::AbstractString="0")
    if target == "hardware"
        return String(id)
    elseif target == "virtual"
        return "$(id)@tcpip://localhost:18950"
    end
    error("target must be \"hardware\" or \"virtual\"")
end

function close(card::HilCard)
    result = ccall(hil_symbol(card.lib, :hil_close), TError, (TCard,), card.handle)
    check_error(result, "hil_close")
    return nothing
end

function write_analog(card::HilCard, channels::Vector{TUInt32}, values::Vector{TDouble})
    length(channels) == length(values) || error("channels and values must have the same length")
    result = ccall(
        hil_symbol(card.lib, :hil_write_analog),
        TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TDouble}),
        card.handle,
        channels,
        TUInt32(length(channels)),
        values,
    )
    check_error(result, "hil_write_analog")
    return nothing
end

function write_digital(card::HilCard, lines::Vector{TUInt32}, values::Vector{TBoolean})
    length(lines) == length(values) || error("lines and values must have the same length")
    result = ccall(
        hil_symbol(card.lib, :hil_write_digital),
        TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TBoolean}),
        card.handle,
        lines,
        TUInt32(length(lines)),
        values,
    )
    check_error(result, "hil_write_digital")
    return nothing
end

function write_other(card::HilCard, channels::Vector{TUInt32}, values::Vector{TDouble})
    length(channels) == length(values) || error("channels and values must have the same length")
    result = ccall(
        hil_symbol(card.lib, :hil_write_other),
        TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TDouble}),
        card.handle,
        channels,
        TUInt32(length(channels)),
        values,
    )
    check_error(result, "hil_write_other")
    return nothing
end

function read_aero2_immediate(card::HilCard)
    analog = zeros(TDouble, length(READ_ANALOG_CHANNELS))
    encoders = zeros(TInt32, length(READ_ENCODER_CHANNELS))
    other = zeros(TDouble, length(READ_OTHER_CHANNELS))
    result = ccall(
        hil_symbol(card.lib, :hil_read),
        TError,
        (
            TCard,
            Ptr{TUInt32}, TUInt32,
            Ptr{TUInt32}, TUInt32,
            Ptr{TUInt32}, TUInt32,
            Ptr{TUInt32}, TUInt32,
            Ptr{TDouble},
            Ptr{TInt32},
            Ptr{TBoolean},
            Ptr{TDouble},
        ),
        card.handle,
        READ_ANALOG_CHANNELS, TUInt32(length(READ_ANALOG_CHANNELS)),
        READ_ENCODER_CHANNELS, TUInt32(length(READ_ENCODER_CHANNELS)),
        Ptr{TUInt32}(C_NULL), TUInt32(0),
        READ_OTHER_CHANNELS, TUInt32(length(READ_OTHER_CHANNELS)),
        analog,
        encoders,
        Ptr{TBoolean}(C_NULL),
        other,
    )
    check_error(result, "hil_read")
    return (analog=analog, encoders=encoders, other=other)
end

pitch_angle(counts::Real) = 2.0 * pi * Float64(counts) / PITCH_COUNTS_PER_REV
yaw_angle(counts::Real) = 2.0 * pi * Float64(counts) / YAW_COUNTS_PER_REV
motor_speed(counts_per_second::Real) = 2.0 * pi * Float64(counts_per_second) / MOTOR_COUNTS_PER_REV

function aero2_sensor_sample(raw)
    analog = raw.analog
    encoders = raw.encoders
    other = raw.other
    return (
        theta=pitch_angle(encoders[3]),
        psi=yaw_angle(encoders[4]),
        gyro_x=Float64(other[1]),
        gyro_y=Float64(other[2]),
        gyro_z=Float64(other[3]),
        accel_x=Float64(other[4]),
        accel_y=Float64(other[5]),
        accel_z=Float64(other[6]),
        motor0_speed=motor_speed(other[7]),
        motor1_speed=motor_speed(other[8]),
        pitch_rate=pitch_angle(other[9]),
        yaw_rate=yaw_angle(other[10]),
        motor0_current=Float64(analog[1]),
        motor1_current=Float64(analog[2]),
        encoder0=Int32(encoders[1]),
        encoder1=Int32(encoders[2]),
        encoder2=Int32(encoders[3]),
        encoder3=Int32(encoders[4]),
    )
end

function write_aero2_voltage(card::HilCard, motor0::Real, motor1::Real; limit::Real=15.0)
    lim = abs(TDouble(limit))
    write_analog(card, WRITE_ANALOG_CHANNELS, TDouble[clamp(TDouble(motor0), -lim, lim), clamp(TDouble(motor1), -lim, lim)])
end

function write_aero2_led(card::HilCard, red::Real, green::Real, blue::Real)
    write_other(card, WRITE_LED_CHANNELS, TDouble[red, green, blue])
end

function safe_zero_aero2(card::HilCard)
    write_aero2_voltage(card, 0.0, 0.0)
    write_aero2_led(card, 1.0, 0.0, 0.0)
end

export HilCard, find_hil_library, require_hil_library, check_error, open_card, close,
    read_aero2_immediate, write_aero2_voltage, write_aero2_led, safe_zero_aero2,
    hil_symbol, default_card_identifier, pitch_angle, yaw_angle, motor_speed,
    aero2_sensor_sample

end
