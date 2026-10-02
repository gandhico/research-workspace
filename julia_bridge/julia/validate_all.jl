# V0/V1 sweep over the board registry; optional V2 twin connect.
#   julia validate_all.jl                       -> V0 + V1 (never opens anything)
#   julia validate_all.jl --connect qube3       -> + V2 attempt on that robot's QLabs virtual card
# Hardware is NEVER opened by this script.

include(joinpath(@__DIR__, "QuanserHIL.jl"))
using .QuanserHIL

function main(args)
    lib = QuanserHIL.find_hil_library()
    println("V0  hil.dll: ", lib === nothing ? "NOT FOUND" : lib)
    println()
    println(rpad("robot", 16), rpad("family", 14), rpad("card_type", 26), "virtual id / note")
    println("-"^96)
    order = [:qube3, :aero2, :hover3dof, :qarm, :qarm_mini, :qbot_platform, :qbot2e, :qbot3,
             :qcar, :qcar2, :qdrone2, :gyro3dof, :haptic_hd, :actuators_trainer, :sensors_trainer]
    for key in order
        p = QuanserHIL.probe(key)
        vid = p.virtual === nothing ? (isempty(p.note) ? "-" : p.note) : p.virtual
        println(rpad(String(p.key), 16), rpad(String(p.family), 14),
                rpad(p.card_type === nothing ? "(not host-HIL)" : p.card_type, 26), vid)
    end
    println()
    println("V1  registry resolves for all ", length(QuanserHIL.BOARDS), " boards; no device opened.")

    i = findfirst(==("--connect"), args)
    if i !== nothing && i < length(args)
        key = Symbol(args[i + 1])
        b = QuanserHIL.BOARDS[key]
        println("\nV2  attempting VIRTUAL connect: ", key, " -> ", b.virtual_id)
        try
            card = QuanserHIL.open_board(key; target=:virtual)
            println("    hil_open OK (QLabs virtual card is live)")
            if key === :aero2
                s = QuanserHIL.read_immediate(card; encoders=UInt32[2, 3])
                println("    encoder read OK: ", s.encoders)
                QuanserHIL.write_analog(card, UInt32[0, 1], [0.0, 0.0])  # safe zero
            elseif key === :qube3
                s = QuanserHIL.read_immediate(card; encoders=UInt32[0, 1])
                println("    encoder read OK: ", s.encoders)
                QuanserHIL.write_analog(card, UInt32[0], [0.0])          # safe zero
            end
            QuanserHIL.close(card)
            println("    safe zero + close OK -> V2 PASS for ", key)
        catch err
            println("    V2 not reachable: ", sprint(showerror, err)[1:min(end, 160)])
            println("    (expected when the QLabs scene for this robot is not running)")
        end
    end
end

main(ARGS)
