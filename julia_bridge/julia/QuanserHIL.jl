module QuanserHIL
# Generic Julia ccall bridge to the Quanser HIL C library, generalized from the
# validated Aero2HilCBridge (04_Aero2_SNNs/julia/). Family-A (host-HIL) robots +
# QLabs virtual cards. Family-B (onboard/streamed) robots are reached via
# PythonCall->PAL for now (see README).

using Libdl

const TCard = Ptr{Cvoid}
const TError = Cint
const TUInt32 = UInt32
const TInt32 = Int32
const TBoolean = Int8
const TDouble = Float64

const DEFAULT_SEARCH_DIRS = [
    raw"C:\Program Files\Common Files\Quanser\bin",
    raw"C:\Quanser\0_libraries\bin",
]

const LIBRARY_CACHE = Dict{String, Ptr{Cvoid}}()

struct Board
    key::Symbol
    card_type::Union{String, Nothing}   # nothing => not host-HIL (family B)
    physical_id::String
    virtual_id::Union{String, Nothing}  # QLabs virtual card identifier, if any
    family::Symbol                      # :host_hil | :streamed | :daq_mediated
    note::String
end

# Card types verified from Quanser's own PAL/HAL sources on this machine.
const BOARDS = Dict{Symbol, Board}(
    :qube3      => Board(:qube3, "qube_servo3_usb", "0", "0@tcpip://localhost:18923?nagle='off'", :host_hil, "port map: 18920 v2, 18921 v2+pend, 18922 v3, 18923 v3+pendulum"),
    :aero2      => Board(:aero2, "quanser_aero2_usb", "0", "0@tcpip://localhost:18950", :host_hil, "virtual read/zero validated in 04 repo"),
    :hover3dof   => Board(:hover3dof, "q8_usb", "0", nothing, :daq_mediated, "AO0..3=front/back/left/right; ENC0..2=pitch/roll/yaw on the verified lab rig"),
    :qarm       => Board(:qarm, "qarm_usb", "0", nothing, :host_hil, "twin via qvl, not virtual HIL"),
    :qarm_mini  => Board(:qarm_mini, "qarm_mini", "0", nothing, :host_hil, ""),
    :qbot2e     => Board(:qbot2e, "qbot2e", "0", nothing, :host_hil, "legacy QBot"),
    :qbot3      => Board(:qbot3, "qbot3", "0", nothing, :host_hil, "legacy QBot"),
    :qcar       => Board(:qcar, "qcar", "0", nothing, :host_hil, "card opens ON the car; host uses streams/PAL"),
    :qcar2      => Board(:qcar2, "qcar2", "0", nothing, :host_hil, "card opens ON the car; host uses streams/PAL"),
    :qdrone2    => Board(:qdrone2, nothing, "tcpip://<ip>:18491", nothing, :streamed, "onboard HIL; host connects by stream (PAL)"),
    :qbot_platform => Board(:qbot_platform, nothing, "driver tcpip port (18889 aux)", nothing, :streamed, "onboard; LiDAR/video via local ports"),
    :actuators_trainer => Board(:actuators_trainer, "mech_actuators_trainer_usb", "0", nothing, :host_hil, ""),
    :sensors_trainer   => Board(:sensors_trainer, "mech_sensors_trainer_usb", "0", nothing, :host_hil, ""),
    :gyro3dof   => Board(:gyro3dof, nothing, "via Q8-class DAQ", nothing, :daq_mediated, "QUARC-era: open the DAQ card type, device = channel map"),
    :haptic_hd  => Board(:haptic_hd, nothing, "via Q8-class DAQ", nothing, :daq_mediated, "QUARC-era: open the DAQ card type, device = channel map"),
)

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

require_hil_library(lib=find_hil_library()) = lib === nothing ?
    error("hil.dll not found; set QUANSER_HIL_LIBRARY or install QUARC") : String(lib)

library_handle(lib::AbstractString) = get!(() -> Libdl.dlopen(lib), LIBRARY_CACHE, String(lib))
hil_symbol(lib::AbstractString, name::Symbol) = Libdl.dlsym(library_handle(lib), name)
check_error(result::Integer, op::AbstractString) =
    (result < 0 && error("$(op) failed with HIL error $(result)"); result)

function open_card(card_type::AbstractString, card_identifier::AbstractString; lib=find_hil_library())
    library = require_hil_library(lib)
    ref = Ref{TCard}(C_NULL)
    check_error(ccall(hil_symbol(library, :hil_open), TError,
        (Cstring, Cstring, Ref{TCard}), card_type, card_identifier, ref), "hil_open")
    return HilCard(library, ref[])
end

open_board(key::Symbol; target::Symbol=:virtual) = begin
    b = BOARDS[key]
    b.card_type === nothing && error("$(key) is not a host-HIL board ($(b.family)); use the PAL/stream path")
    id = target === :virtual ? (b.virtual_id === nothing ?
            error("$(key) has no virtual HIL card; use qvl twin") : b.virtual_id) :
         target === :hardware ? b.physical_id : error("target must be :virtual or :hardware")
    open_card(b.card_type, id)
end

function close(card::HilCard)
    check_error(ccall(hil_symbol(card.lib, :hil_close), TError, (TCard,), card.handle), "hil_close")
    return nothing
end

function write_analog(card::HilCard, channels::Vector{TUInt32}, values::Vector{TDouble})
    length(channels) == length(values) || error("length mismatch")
    check_error(ccall(hil_symbol(card.lib, :hil_write_analog), TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TDouble}),
        card.handle, channels, TUInt32(length(channels)), values), "hil_write_analog")
    return nothing
end

function write_digital(card::HilCard, lines::Vector{TUInt32}, values::Vector{TBoolean})
    length(lines) == length(values) || error("length mismatch")
    check_error(ccall(hil_symbol(card.lib, :hil_write_digital), TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TBoolean}),
        card.handle, lines, TUInt32(length(lines)), values), "hil_write_digital")
    return nothing
end

function write_other(card::HilCard, channels::Vector{TUInt32}, values::Vector{TDouble})
    length(channels) == length(values) || error("length mismatch")
    check_error(ccall(hil_symbol(card.lib, :hil_write_other), TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TDouble}),
        card.handle, channels, TUInt32(length(channels)), values), "hil_write_other")
    return nothing
end

"""Generic immediate read: any subset of analog/encoder/other channels."""
function read_immediate(card::HilCard;
        analog::Vector{TUInt32}=TUInt32[], encoders::Vector{TUInt32}=TUInt32[],
        other::Vector{TUInt32}=TUInt32[])
    abuf = zeros(TDouble, length(analog))
    ebuf = zeros(TInt32, length(encoders))
    obuf = zeros(TDouble, length(other))
    check_error(ccall(hil_symbol(card.lib, :hil_read), TError,
        (TCard, Ptr{TUInt32}, TUInt32, Ptr{TUInt32}, TUInt32, Ptr{TUInt32}, TUInt32,
         Ptr{TUInt32}, TUInt32, Ptr{TDouble}, Ptr{TInt32}, Ptr{TBoolean}, Ptr{TDouble}),
        card.handle,
        isempty(analog) ? Ptr{TUInt32}(C_NULL) : analog, TUInt32(length(analog)),
        isempty(encoders) ? Ptr{TUInt32}(C_NULL) : encoders, TUInt32(length(encoders)),
        Ptr{TUInt32}(C_NULL), TUInt32(0),
        isempty(other) ? Ptr{TUInt32}(C_NULL) : other, TUInt32(length(other)),
        isempty(analog) ? Ptr{TDouble}(C_NULL) : abuf,
        isempty(encoders) ? Ptr{TInt32}(C_NULL) : ebuf,
        Ptr{TBoolean}(C_NULL),
        isempty(other) ? Ptr{TDouble}(C_NULL) : obuf), "hil_read")
    return (analog=abuf, encoders=ebuf, other=obuf)
end

"""V0/V1 probe: library + registry resolution; never opens anything."""
function probe(key::Symbol)
    b = BOARDS[key]
    lib = find_hil_library()
    return (key=key, family=b.family, card_type=b.card_type,
            physical=b.physical_id, virtual=b.virtual_id,
            hil_found=lib !== nothing, note=b.note)
end

export BOARDS, Board, HilCard, find_hil_library, open_card, open_board, close,
       read_immediate, write_analog, write_digital, write_other, probe, check_error

end
