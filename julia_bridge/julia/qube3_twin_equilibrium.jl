# Qube Servo 3 PENDULUM twin — energy swing-up + LQR balance (Julia / Bridge 2).
#
# Parity twin of the Python reference:
#   07_ServoPendulum_SNNs/runners/twin_swingup_balance.py
# Same conventions, same gains, same capture logic, same metrics, same CSV schema,
# so the two implementations can be compared directly.
#
# Conventions (VERIFIED by 07/runners/twin_diagnostic.py, 2026-07-23):
#   * virtual card 0@tcpip://localhost:18923  (Qube3 + pendulum)
#   * encoder zero == RESTING (hanging)  =>  alpha_upright = wrap(raw - pi)
#   * theta uses the raw sign (no negation)
#   * rad = 2*pi*counts/2048 for both encoders and both tachometers
#
# LEDs (channels 11000/11001/11002, visible in QLabs):
#   RED = idle/shutdown, BLUE = swing-up, GREEN = balancing
#
#   julia qube3_twin_equilibrium.jl [duration_s] [hz] [mu] [V_sw] [gainset] [bal_sign]
#     gainset: "twin" -> [-1.000, 26.72, -0.8269, 2.214]
#              "code" -> [-1.2247, 24.9044, -0.6877, 3.1321]

include(joinpath(@__DIR__, "QuanserHIL.jl"))
using .QuanserHIL
using Printf, Dates

# ---- args ----
const DUR      = length(ARGS) >= 1 ? parse(Float64, ARGS[1]) : 20.0
const HZ       = length(ARGS) >= 2 ? parse(Float64, ARGS[2]) : 500.0
const MU       = length(ARGS) >= 3 ? parse(Float64, ARGS[3]) : 100.0
const V_SW     = length(ARGS) >= 4 ? parse(Float64, ARGS[4]) : 10.0
const GAINSET  = length(ARGS) >= 5 ? ARGS[5] : "twin"
const BAL_SIGN = length(ARGS) >= 6 ? parse(Float64, ARGS[6]) : 1.0
const KC = 1.0
const DT = 1.0 / HZ

# ---- QUBE-Servo 3 rotary pendulum parameters (qube3_rotpen_param.m) ----
const Rm = 7.5;   const kt = 0.0422
const mr = 0.095; const r  = 0.085
const mp = 0.024; const Lp = 0.129; const l = Lp/2
const g  = 9.81
const Jp_cm   = mp*Lp^2/12
const Er      = 2*mp*g*l
const tau_max = kt*10.0/Rm
const a_max   = tau_max/(mr*r)
const ACC2V   = mr*r*Rm/kt

const K = GAINSET == "code" ? [-1.2247, 24.9044, -0.6877, 3.1321] :
                              [-1.000, 26.72, -0.8269, 2.214]
const V_BAL         = 5.0
const CAPTURE_RAD   = deg2rad(20.0)
const CAPTURE_RATE  = 6.0
const CAPTURE_THETA = deg2rad(110.0)
const HOLD_RAD      = deg2rad(35.0)
const CPR = 2048.0

const LED_IDLE    = [1.0, 0.0, 0.0]
const LED_SWINGUP = [0.0, 0.0, 1.0]
const LED_BALANCE = [0.0, 1.0, 0.0]
const LED_CH = UInt32[11000, 11001, 11002]

ang(c) = 2pi * Float64(c) / CPR
wrap(x) = mod(x + pi, 2pi) - pi

function main()
    println("="^70)
    println("QUBE3 PENDULUM TWIN — energy swing-up + LQR balance  (Julia / Bridge 2)")
    println("="^70)
    @printf("gains[%s] K = %s   bal_sign = %+d   V_bal = %.1f V\n", GAINSET, string(K), Int(BAL_SIGN), V_BAL)
    @printf("mu = %.1f   V_sw = %.1f V   a_max = %.2f m/s^2   Er = %.4f J   ACC2V = %.3f\n",
            MU, V_SW, a_max, Er, ACC2V)

    card = QuanserHIL.open_board(:qube3; target=:virtual)
    println("connection OK: ", QuanserHIL.BOARDS[:qube3].virtual_id)
    QuanserHIL.write_digital(card, UInt32[0], Int8[1])     # amplifier ENABLE
    QuanserHIL.write_other(card, LED_CH, copy(LED_IDLE))   # LED red
    println("amplifier enabled (digital ch0 = 1); LED = RED (idle)")

    n = round(Int, DUR*HZ)
    ts = Float64[]; dts = Float64[]; modes = Int[]; volts = Float64[]
    thetas = Float64[]; alphas = Float64[]; thds = Float64[]; ads = Float64[]
    mcounts = Float64[]; pcounts = Float64[]
    mode_prev = -1; catch_k = -1; streak = 0; best_streak = 0

    t0 = time(); t_prev = t0; next_t = t0 + DT
    try
        for k in 1:n
            s = QuanserHIL.read_immediate(card; encoders=UInt32[0,1], other=UInt32[14000,14001])
            t = time(); push!(dts, t - t_prev); t_prev = t; push!(ts, t - t0)

            theta     = ang(s.encoders[1])
            alpha     = wrap(ang(s.encoders[2]) - pi)     # 0 == UPRIGHT
            theta_dot = ang(s.other[1])
            alpha_dot = ang(s.other[2])

            latched = (mode_prev == 1)
            capture = (abs(alpha) <= CAPTURE_RAD && abs(alpha_dot) <= CAPTURE_RATE &&
                       abs(theta) <= CAPTURE_THETA)
            local v::Float64
            if capture || (latched && abs(alpha) <= HOLD_RAD)
                mode = 1
                catch_k < 0 && (catch_k = k)
                streak += 1; best_streak = max(best_streak, streak)
                v = clamp(BAL_SIGN*(K[1]*theta + K[2]*alpha + K[3]*theta_dot + K[4]*alpha_dot),
                          -V_BAL, V_BAL)
            else
                mode = 0; streak = 0
                E = 0.5*Jp_cm*alpha_dot^2 + mp*g*l*(1 + cos(alpha))
                u_pump = MU*(E - Er)*sign(alpha_dot*cos(alpha))
                u = clamp(u_pump - KC*theta, -a_max, a_max)
                v = clamp(ACC2V*u, -V_SW, V_SW)
            end

            QuanserHIL.write_analog(card, UInt32[0], [v])
            if mode != mode_prev
                QuanserHIL.write_other(card, LED_CH, mode == 1 ? copy(LED_BALANCE) : copy(LED_SWINGUP))
                mode_prev = mode
            end

            push!(modes, mode); push!(volts, v)
            push!(thetas, theta); push!(alphas, alpha)
            push!(thds, theta_dot); push!(ads, alpha_dot)
            push!(mcounts, Float64(s.encoders[1])); push!(pcounts, Float64(s.encoders[2]))

            rem = next_t - time()
            rem > 0.002 && sleep(rem - 0.002)
            while time() < next_t; end
            next_t += DT
        end
    finally
        QuanserHIL.write_analog(card, UInt32[0], [0.0])
        QuanserHIL.write_other(card, LED_CH, copy(LED_IDLE))
        QuanserHIL.write_digital(card, UInt32[0], Int8[0])
        QuanserHIL.close(card)
        println("shutdown: 0 V, LED RED, amplifier disabled, card closed.")
    end

    realized = 1.0/(sum(dts[2:end])/(length(dts)-1))
    tail = round(Int, min(2.0, DUR/4)*HZ)
    a_tail = alphas[end-tail+1:end]
    bal_frac = count(==(1), modes[end-tail+1:end])/tail
    rms = sqrt(sum(abs2, a_tail)/length(a_tail))

    @printf("\nsamples %d   realized %.1f Hz\n", length(alphas), realized)
    println(catch_k > 0 ? @sprintf("first capture : %.2f s", catch_k/HZ) : "first capture : NEVER")
    @printf("longest hold  : %.2f s (%d samples)\n", best_streak/HZ, best_streak)
    @printf("closest to top: %.2f deg\n", rad2deg(minimum(abs.(alphas))))
    @printf("final %.1fs -> balance fraction %.3f, alpha RMS %.4f rad (%.2f deg), |alpha|max %.2f deg\n",
            min(2.0, DUR/4), bal_frac, rms, rad2deg(rms), rad2deg(maximum(abs.(a_tail))))

    outdir = joinpath(@__DIR__, "..", "results")
    mkpath(outdir)
    stamp = Dates.format(now(), "yyyymmdd_HHMMSS")
    tag = "julia_$(GAINSET)_sign$(Int(BAL_SIGN))_$(stamp)"
    open(joinpath(outdir, "twin_swingup_$(tag).csv"), "w") do io
        println(io, "t,dt,mode,voltage,theta,alpha,theta_dot,alpha_dot,alpha_deg,theta_deg,motor_counts,pend_counts")
        for i in eachindex(alphas)
            @printf(io, "%.6f,%.6f,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.4f,%.4f,%.0f,%.0f\n",
                    ts[i], dts[i], modes[i], volts[i], thetas[i], alphas[i], thds[i], ads[i],
                    rad2deg(alphas[i]), rad2deg(thetas[i]), mcounts[i], pcounts[i])
        end
    end
    open(joinpath(outdir, "twin_swingup_$(tag).json"), "w") do io
        @printf(io, "{\n  \"impl\": \"julia_bridge2\",\n  \"gains\": \"%s\",\n  \"K\": %s,\n", GAINSET, string(K))
        @printf(io, "  \"bal_sign\": %.1f,\n  \"duration_s\": %.1f,\n  \"hz\": %.1f,\n  \"realized_hz\": %.3f,\n", BAL_SIGN, DUR, HZ, realized)
        @printf(io, "  \"mu\": %.1f,\n  \"v_sw\": %.1f,\n  \"v_bal\": %.1f,\n", MU, V_SW, V_BAL)
        @printf(io, "  \"first_capture_s\": %s,\n", catch_k > 0 ? @sprintf("%.4f", catch_k/HZ) : "null")
        @printf(io, "  \"longest_hold_s\": %.4f,\n  \"balance_fraction_tail\": %.4f,\n", best_streak/HZ, bal_frac)
        @printf(io, "  \"alpha_rms_tail_rad\": %.6f,\n  \"alpha_max_tail_deg\": %.4f,\n", rms, rad2deg(maximum(abs.(a_tail))))
        @printf(io, "  \"closest_to_top_deg\": %.4f\n}\n", rad2deg(minimum(abs.(alphas))))
    end
    println("saved: ", joinpath(outdir, "twin_swingup_$(tag).csv"))
end

main()
