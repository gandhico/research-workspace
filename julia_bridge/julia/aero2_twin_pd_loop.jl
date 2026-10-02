# V3 — pure-Julia closed loop on the QLabs Aero2 twin (Bridge 2, "Julia drives").
# Pitch-only square-wave tracking with the implemented Aero2 PD gains; yaw held 0
# (current QLabs scene is pitch-only, validated in 04). Safe zero + red LED + close.
#   julia aero2_twin_pd_loop.jl [duration_s] [hz]

include(joinpath(@__DIR__, "QuanserHIL.jl"))
using .QuanserHIL

# Implemented Aero2 PD gains (04_Aero2_SNNs/aero2/config/gains.py; code truth)
const KP_PITCH = 116.24203523333735
const KD_PITCH = 99.698951398313469
const V_LIMIT = 24.0
const A_THETA = deg2rad(20.0)      # Ref-3 square wave
const F_THETA = 0.05               # Hz
const PITCH_CPR = 2880.0

# validated direct-HIL channel map (04): pitch enc ch2, yaw enc ch3,
# pitch-rate other 14002, yaw-rate other 14003 (counts/s); LEDs 11000-11002
const ENC = UInt32[2, 3]
const RATE = UInt32[14002, 14003]
const LED = UInt32[11000, 11001, 11002]

pitch_angle(c) = 2pi * Float64(c) / PITCH_CPR
square_ref(t) = (F_THETA * t) % 1.0 < 0.5 ? -A_THETA : A_THETA

function main(args)
    duration = length(args) >= 1 ? parse(Float64, args[1]) : 8.0
    hz = length(args) >= 2 ? parse(Float64, args[2]) : 200.0
    dt_nom = 1.0 / hz

    println("V3: Julia PD loop on QLabs Aero2 twin — $(duration)s @ $(hz) Hz target")
    card = QuanserHIL.open_board(:aero2; target=:virtual)
    println("hil_open OK: ", QuanserHIL.BOARDS[:aero2].virtual_id)
    QuanserHIL.write_other(card, LED, [0.0, 1.0, 0.0])   # green = active

    n_target = round(Int, duration * hz)
    errs = Float64[]; dts = Float64[]
    t0 = time(); t_prev = t0; next_t = t0 + dt_nom
    try
        for k in 1:n_target
            s = QuanserHIL.read_immediate(card; encoders=ENC, other=RATE)
            t = time()
            dt_meas = t - t_prev; t_prev = t
            theta = pitch_angle(s.encoders[1])
            theta_dot = pitch_angle(s.other[1])          # hardware-timed tach, counts/s -> rad/s
            theta_r = square_ref(t - t0)
            u_p = clamp(KP_PITCH * (theta_r - theta) - KD_PITCH * theta_dot, -V_LIMIT, V_LIMIT)
            QuanserHIL.write_analog(card, UInt32[0, 1], [u_p, 0.0])
            push!(errs, theta_r - theta); push!(dts, dt_meas)
            # hybrid pacing: coarse sleep + spin to the deadline
            rem = next_t - time()
            rem > 0.002 && sleep(rem - 0.002)
            while time() < next_t; end
            next_t += dt_nom
        end
    finally
        QuanserHIL.write_analog(card, UInt32[0, 1], [0.0, 0.0])   # safe zero
        QuanserHIL.write_other(card, LED, [1.0, 0.0, 0.0])        # red = idle
        QuanserHIL.close(card)
    end
    n = length(errs)
    settled = errs[max(1, n - round(Int, 0.75n)) : end]
    rms = sqrt(sum(abs2, settled) / length(settled))
    realized = 1.0 / (sum(dts[2:end]) / (length(dts) - 1))
    println("samples: ", n)
    println("realized rate: ", round(realized, digits=1), " Hz")
    println("pitch RMS (last 75%): ", round(rms, digits=4), " rad")
    println("safe zero + red LED + close done")
end

main(ARGS)
