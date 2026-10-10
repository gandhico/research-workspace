# M2.7  The family of continuous-time sinusoids of Eq. (2.65) gives identical
#       sampled signals.
#
#       x_{a,k}(t) = A cos( +/-(Omega_o t + phi) + k Omega_T t ),  k = 0, +/-1, ...
#
#   Sampling at t = nT with Omega_T = 2*pi/T:
#
#       x_{a,k}(nT) = A cos( (Omega_o + k Omega_T) nT + phi )
#                   = A cos( Omega_o nT + phi + 2*pi*k*n )
#                   = A cos( w_o n + phi )                     Eq. (2.66)
#
#   since k*n is an integer; the minus sign is absorbed because cos is even.
#
#   Run:  julia hw1_M2_07.jl
using Printf

const A     = 1.3
const phi   = 0.7
const T     = 0.05                 # sampling period, s
const Om_o  = 2pi * 3.0            # 3 Hz
const Om_T  = 2pi / T              # 20 Hz sampling rate
const N     = 21

n = 0:N-1
w_o = Om_o * T                     # normalized angular frequency, Eq. (2.64)

println("=====  M 2.7  Eq. (2.65): a family of sinusoids, one sequence  =====\n")
@printf("  A = %.1f   phi = %.1f rad   T = %.3f s\n", A, phi, T)
@printf("  Omega_o/2pi = %.1f Hz   Omega_T/2pi = %.1f Hz   w_o = %.4f pi rad/sample\n\n",
        Om_o/2pi, Om_T/2pi, w_o/pi)

ref = A .* cos.(w_o .* n .+ phi)   # the target sequence x[n]

println("    k   sign      alias freq (Hz)     max |x_{a,k}(nT) - x[n]|")
println("  ------------------------------------------------------------")
allok = true
for k in (-1, 0, 1, 2), s in (1, -1)
    # x_{a,k}(t) = A cos( s*(Om_o t + phi) + k*Om_T*t )
    xk = [A * cos(s * (Om_o * (m*T) + phi) + k * Om_T * (m*T)) for m in n]
    err = maximum(abs.(xk .- ref))
    ok  = err < 1e-12;  global allok &= ok
    @printf("  %3d    %+d      %10.1f            %.3e   %s\n",
            k, s, (s*Om_o + k*Om_T)/2pi, err, ok ? "PASS" : "FAIL")
end

println(allok ?
    "\n  All members of the family sample to the SAME sequence -- Eq. (2.66).\n" :
    "\n  MISMATCH\n")

println("  The parent waveforms are genuinely different functions of t:")
tt = 0:0.0005:0.2
for k in (0, 1, 2)
    c0 = [A * cos(Om_o * s + phi) for s in tt]
    ck = [A * cos(Om_o * s + phi + k * Om_T * s) for s in tt]
    @printf("     k = %d : max |x_{a,k}(t) - x_{a,0}(t)| over 0<=t<=0.2 s = %.4f\n",
            k, maximum(abs.(ck .- c0)))
end
println("\n  -- different in continuous time, identical at t = nT.  That is aliasing.")
