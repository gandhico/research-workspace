# V3 — pure-Julia swing-up + balance on the QLabs QUBE-Servo 3 twin.
# Swing-up matches Quanser's own courseware (sp6_pendulum_control/2_swingup_control):
#   energy law commands a PIVOT ACCELERATION, saturated at a_max, then -> voltage.
# Balance: LQR regulator v = -K x with Quanser's digital-twin gain.
#   julia qube3_twin_swingup_balance.jl [duration_s] [hz] [mu] [V_sw]
#
# Bridge 2: Julia owns timing + I/O via ccall -> hil.dll. Amplifier enabled at start,
# safe zero + amplifier off + close on exit.

include(joinpath(@__DIR__, "QuanserHIL.jl"))
using .QuanserHIL

# --- QUBE-Servo 3 rotary-pendulum parameters (Quanser qube3_rotpen_param.m) ---
const Rm = 7.5; const kt = 0.0422
const mr = 0.095; const r = 0.085
const mp = 0.024; const Lp = 0.129; const l = Lp/2
const g  = 9.81
const Jp_cm = mp*Lp^2/12          # about CM — used for swing-up energy (Quanser)

# --- swing-up constants (Quanser setup_swingup.m) ---
const Er = 2*mp*g*l               # reference energy (top), J
const tau_max = kt*10/Rm          # torque at 10 V
const a_max = tau_max/(mr*r)      # max pivot acceleration, m/s^2  (<-> 10 V)
const ACC2V = mr*r*Rm/kt          # pivot accel -> motor voltage

# --- balance: Quanser digital-twin LQR gain ---
const K = [-1.000, 26.72, -0.8269, 2.214]
const V_BAL = 5.0
const CAPTURE_RAD = deg2rad(20.0)
const CAPTURE_RATE = 6.0          # rad/s — hand off on a reasonably slow arrival
const CAPTURE_THETA = deg2rad(110.0) # arm just needs to be off the ±135° limit

const CPR = 2048.0
angle(c) = 2pi * Float64(c) / CPR
wrap(x) = mod(x + pi, 2pi) - pi

function main(args)
    duration = length(args) >= 1 ? parse(Float64, args[1]) : 20.0
    hz = length(args) >= 2 ? parse(Float64, args[2]) : 500.0
    mu = length(args) >= 3 ? parse(Float64, args[3]) : 100.0    # swing-up energy gain
    V_SW = length(args) >= 4 ? parse(Float64, args[4]) : 10.0   # swing-up voltage cap
    kc = length(args) >= 5 ? parse(Float64, args[5]) : 1.0      # arm-centering accel gain
    bal_sign = length(args) >= 6 ? parse(Float64, args[6]) : 1.0  # balance sign (+1 = this twin's convention)
    kd = 0.0   # NO derivative on arm speed: it amplifies limit-slam tach noise
    dt_nom = 1.0 / hz

    println("V3: Julia swing-up (Quanser energy law) + balance on QLabs Qube3 twin")
    println("  mu=$(mu), a_max=$(round(a_max,digits=2)) m/s^2, Er=$(round(Er,digits=4)) J, ACC2V=$(round(ACC2V,digits=3))")
    card = QuanserHIL.open_board(:qube3; target=:virtual)
    println("hil_open OK: ", QuanserHIL.BOARDS[:qube3].virtual_id)
    QuanserHIL.write_digital(card, UInt32[0], Int8[1])   # amplifier ENABLE
    println("amplifier enabled (digital ch0 = 1)")

    n_target = round(Int, duration * hz)
    dts = Float64[]; alphas = Float64[]; thetas = Float64[]; adots = Float64[]; modes = Int[]
    catch_k = -1; catch_state = (0.0, 0.0, 0.0)
    streak = 0; best_streak = 0
    bal_theta = Float64[]; bal_thd = Float64[]
    t0 = time(); t_prev = t0; next_t = t0 + dt_nom
    try
        for k in 1:n_target
            s = QuanserHIL.read_immediate(card; encoders=UInt32[0, 1], other=UInt32[14000, 14001])
            t = time(); push!(dts, t - t_prev); t_prev = t
            theta = angle(s.encoders[1])
            alpha = wrap(angle(s.encoders[2]) - pi)          # 0 = upright
            theta_dot = angle(s.other[1])
            alpha_dot = angle(s.other[2])

            # hand off only when near the top, slow, AND the arm has room to maneuver
            in_balance = !isempty(modes) && modes[end] == 1   # stay latched once balancing
            if (abs(alpha) <= CAPTURE_RAD && abs(alpha_dot) <= CAPTURE_RATE && abs(theta) <= CAPTURE_THETA) ||
               (in_balance && abs(alpha) <= deg2rad(35))
                if catch_k < 0
                    catch_k = k
                    catch_state = (rad2deg(alpha), alpha_dot, rad2deg(theta))
                end
                streak += 1; best_streak = max(best_streak, streak)
                push!(bal_theta, theta); push!(bal_thd, theta_dot)
                # LQR regulator; bal_sign resolves this twin's encoder/voltage convention
                v = clamp(bal_sign*(K[1]*theta + K[2]*alpha + K[3]*theta_dot + K[4]*alpha_dot), -V_BAL, V_BAL)
                push!(modes, 1)
            else
                streak = 0
                # Quanser energy swing-up: acceleration command -> voltage
                E = 0.5*Jp_cm*alpha_dot^2 + mp*g*l*(1 + cos(alpha))
                u_pump = mu*(E - Er)*sign(alpha_dot*cos(alpha))   # pivot accel, m/s^2
                u_center = -(kc*theta + kd*theta_dot)             # keep arm off ±135° limit
                u = clamp(u_pump + u_center, -a_max, a_max)
                v = clamp(ACC2V*u, -V_SW, V_SW)
                push!(modes, 0)
            end
            QuanserHIL.write_analog(card, UInt32[0], [v])
            push!(alphas, alpha); push!(thetas, theta); push!(adots, alpha_dot)
            rem = next_t - time()
            rem > 0.002 && sleep(rem - 0.002)
            while time() < next_t; end
            next_t += dt_nom
        end
    finally
        QuanserHIL.write_analog(card, UInt32[0], [0.0])
        QuanserHIL.write_digital(card, UInt32[0], Int8[0])   # amplifier disable
        QuanserHIL.close(card)
    end
    n = length(alphas)
    realized = 1.0 / (sum(dts[2:end]) / (length(dts) - 1))
    tail = round(Int, min(2.0, duration / 4) * hz)
    a_tail = alphas[end-tail+1:end]
    bal_frac = count(m -> m == 1, modes[end-tail+1:end]) / tail
    println("samples: ", n, "   realized rate: ", round(realized, digits=1), " Hz")
    println("first capture: ", catch_k > 0 ? string(round(catch_k / hz, digits=2), " s") : "never")
    if catch_k > 0
        println("  state at catch: alpha=", round(catch_state[1], digits=1), " deg, ",
                "alpha_dot=", round(catch_state[2], digits=2), " rad/s, theta=",
                round(catch_state[3], digits=1), " deg")
        println("  longest balance hold: ", round(best_streak / hz, digits=2), " s (", best_streak, " samples)")
    end
    if !isempty(bal_theta)
        println("  arm during balance: theta range [", round(rad2deg(minimum(bal_theta)),digits=1),
                ", ", round(rad2deg(maximum(bal_theta)),digits=1), "] deg, peak |theta_dot| = ",
                round(maximum(abs.(bal_thd)),digits=1), " rad/s")
    end
    println("  peak |alpha_dot| over run: ", round(maximum(abs.(adots)), digits=2), " rad/s")
    println("final-", round(min(2.0, duration/4),digits=1), "s: balance-mode fraction = ", round(bal_frac, digits=3),
            ",  alpha RMS = ", round(sqrt(sum(abs2, a_tail)/length(a_tail)), digits=4), " rad",
            ",  |alpha| max = ", round(maximum(abs.(a_tail)), digits=4), " rad")
    println("theta range over run: [", round(minimum(thetas), digits=3), ", ",
            round(maximum(thetas), digits=3), "] rad")
    imin = argmin(abs.(alphas))
    println("closest approach to upright: |alpha|min = ",
            round(rad2deg(abs(alphas[imin])), digits=1), " deg  ",
            "(at t=", round(imin/hz, digits=2), "s: alpha_dot=", round(adots[imin], digits=2),
            " rad/s, theta=", round(rad2deg(thetas[imin]), digits=1), " deg)")
    # how many times it passed within 15 deg of the top, and the slowest such pass
    near = findall(a -> abs(a) <= deg2rad(15), alphas)
    if !isempty(near)
        slowest = minimum(abs.(adots[near]))
        println("passes within 15deg of top: ", length(near), " samples; ",
                "slowest arrival |alpha_dot| = ", round(slowest, digits=2), " rad/s")
    end
    println("safe zero + amplifier off + close done")
end

main(ARGS)
