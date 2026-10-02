using Printf

include("Aero2HilCBridge.jl")
using .Aero2HilCBridge

function usage()
    return """
    usage: julia julia/aero2_hil_sensor_check.jl [options]

    Options:
      --connect                  Open the HIL board. Without this flag, the script only reports configuration.
      --target virtual|hardware  Board target used to derive the default identifier. Default: virtual.
      --id VALUE                 Board id before transport suffix. Default: 0.
      --card-identifier VALUE    Explicit HIL card identifier. Overrides --target/--id.
      --card-type VALUE          HIL card type. Default: quanser_aero2_usb.
      --duration SECONDS         Sensor read duration after --connect. Default: 1.0.
      --hz HZ                    Sensor read frequency after --connect. Default: 20.0.
      --library PATH             Explicit Quanser HIL library path.
      --help                     Show this message.

    This is sensor-only. It never sends active motor commands; on any open it
    writes zero voltage and red LED, then zeros/red/closes in a finally block.
    """
end

function next_value(args, i, name)
    i == length(args) && error("missing value after $(name)")
    return args[i + 1], i + 2
end

function parse_args(args)
    connect = false
    target = "virtual"
    id = "0"
    card_identifier = nothing
    card_type = "quanser_aero2_usb"
    duration = 1.0
    hz = 20.0
    library = nothing

    i = 1
    while i <= length(args)
        arg = args[i]
        if arg == "--help" || arg == "-h"
            println(usage())
            return nothing
        elseif arg == "--connect"
            connect = true
            i += 1
        elseif arg == "--target"
            value, i = next_value(args, i, arg)
            target = value
        elseif arg == "--id"
            value, i = next_value(args, i, arg)
            id = value
        elseif arg == "--card-identifier"
            value, i = next_value(args, i, arg)
            card_identifier = value
        elseif arg == "--card-type"
            value, i = next_value(args, i, arg)
            card_type = value
        elseif arg == "--duration"
            value, i = next_value(args, i, arg)
            duration = parse(Float64, value)
        elseif arg == "--hz"
            value, i = next_value(args, i, arg)
            hz = parse(Float64, value)
        elseif arg == "--library"
            value, i = next_value(args, i, arg)
            library = value
        else
            error("unknown argument: $(arg)")
        end
    end

    target in ("virtual", "hardware") || error("--target must be virtual or hardware")
    duration > 0.0 || error("--duration must be positive")
    hz > 0.0 || error("--hz must be positive")

    identifier = card_identifier === nothing ? default_card_identifier(target, id) : card_identifier
    return (
        connect=connect,
        target=target,
        id=id,
        card_identifier=identifier,
        card_type=card_type,
        duration=duration,
        hz=hz,
        library=library,
    )
end

function print_config(cfg, lib)
    println("[Aero2 Julia HIL sensor check]")
    println("  hil_library=$(lib === nothing ? "missing" : lib)")
    println("  connect=$(cfg.connect)")
    println("  target=$(cfg.target)")
    println("  card_type=$(cfg.card_type)")
    println("  card_identifier=$(cfg.card_identifier)")
    println("  duration=$(cfg.duration)")
    println("  hz=$(cfg.hz)")
end

function run_sensor_loop(cfg, lib)
    lib === nothing && error("Quanser HIL library was not found; set --library or QUANSER_HIL_LIBRARY.")
    card = open_card(cfg.card_type, cfg.card_identifier; lib=lib)
    try
        safe_zero_aero2(card)
        samples = max(1, ceil(Int, cfg.duration * cfg.hz))
        dt = 1.0 / cfg.hz
        t0 = time()
        println("sample,t_s,theta,psi,pitch_rate,yaw_rate,gyro_y,gyro_z,motor0_current,motor1_current,encoder2,encoder3")
        for k in 0:(samples - 1)
            raw = read_aero2_immediate(card)
            sample = aero2_sensor_sample(raw)
            @printf(
                "%d,%.6f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%.9f,%d,%d\n",
                k,
                time() - t0,
                sample.theta,
                sample.psi,
                sample.pitch_rate,
                sample.yaw_rate,
                sample.gyro_y,
                sample.gyro_z,
                sample.motor0_current,
                sample.motor1_current,
                sample.encoder2,
                sample.encoder3,
            )
            delay = t0 + (k + 1) * dt - time()
            delay > 0.0 && sleep(delay)
        end
        println("  status=connected_sensor_only")
    finally
        try
            safe_zero_aero2(card)
        catch exc
            @warn "safe_zero_aero2 failed during shutdown" exception=(exc, catch_backtrace())
        end
        Aero2HilCBridge.close(card)
    end
end

function main(args=ARGS)
    cfg = parse_args(args)
    cfg === nothing && return
    lib = cfg.library === nothing ? find_hil_library() : cfg.library
    print_config(cfg, lib)
    if !cfg.connect
        println("  status=not_connected")
        println("  note=pass --connect to open the Aero2 board")
        return
    end
    run_sensor_loop(cfg, lib)
end

if abspath(PROGRAM_FILE) == @__FILE__
    main(ARGS)
end
