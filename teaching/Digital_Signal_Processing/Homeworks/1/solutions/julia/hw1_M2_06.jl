# M2.6  Plot a continuous-time sinusoid and its sampled version; verify Figure 2.28
#
#   Example 2.15: g1(t) = cos(6 pi t), g2(t) = cos(14 pi t), g3(t) = cos(26 pi t)
#   (3, 7 and 13 Hz) sampled at 10 Hz (T = 0.1 s) all give the SAME sequence
#
#       g1[n] = cos(0.6 pi n) = g2[n] = g3[n]
#
#   because  cos(1.4 pi n) = cos((2pi - 0.6pi) n) = cos(0.6 pi n)
#            cos(2.6 pi n) = cos((2pi + 0.6pi) n) = cos(0.6 pi n)
#
#   Run:  julia hw1_M2_06.jl
using Printf

const T  = 0.1          # sampling period, s  -> 10 Hz sampling rate
const N  = 11           # samples over 0 <= t <= 1 s
n = 0:N-1
t = 0:0.001:1.0         # dense grid for the continuous-time curves

println("=====  M 2.6  Ambiguity in the discrete-time representation  =====\n")
@printf("  sampling period T = %.3f s   (rate %.1f Hz)\n\n", T, 1/T)

freqs = [3.0, 7.0, 13.0]
seqs  = [cos.(2pi * f .* n .* T) for f in freqs]

println("   n |    g1[n]      g2[n]      g3[n]")
println("  ---+--------------------------------")
for i in 1:N
    @printf("  %2d | %9.5f  %9.5f  %9.5f\n", i-1, seqs[1][i], seqs[2][i], seqs[3][i])
end

e12 = maximum(abs.(seqs[1] .- seqs[2]))
e13 = maximum(abs.(seqs[1] .- seqs[3]))
@printf("\n  max |g1[n] - g2[n]| = %.3e\n", e12)
@printf("  max |g1[n] - g3[n]| = %.3e   -->  %s\n\n",
        e13, max(e12, e13) < 1e-12 ? "IDENTICAL (PASS)" : "DIFFERENT (FAIL)")

# every f = 10k +/- 3 Hz folds onto the same sequence
println("  all frequencies f = 10k +/- 3 Hz give the same sequence at a 10 Hz rate:")
ref = seqs[1]
allok = true
for k in 0:4, s in (-1, 1)
    f = 10k + 3s
    f <= 0 && continue
    g = cos.(2pi * f .* n .* T)
    ok = maximum(abs.(g .- ref)) < 1e-12
    global allok &= ok
    @printf("     f = %4.0f Hz : %s\n", f, ok ? "same" : "DIFFERENT")
end
println(allok ? "\n  Figure 2.28 verified.\n" : "\n  MISMATCH\n")

open("hw1_M2_06_signals.csv", "w") do io
    println(io, "t,g1,g2,g3")
    for tt in t
        @printf(io, "%.4f,%.8f,%.8f,%.8f\n",
                tt, cos(6pi*tt), cos(14pi*tt), cos(26pi*tt))
    end
end
open("hw1_M2_06_samples.csv", "w") do io
    println(io, "n,t,sample")
    for i in 1:N
        @printf(io, "%d,%.4f,%.8f\n", i-1, (i-1)*T, seqs[1][i])
    end
end
println("  wrote hw1_M2_06_signals.csv and hw1_M2_06_samples.csv")
