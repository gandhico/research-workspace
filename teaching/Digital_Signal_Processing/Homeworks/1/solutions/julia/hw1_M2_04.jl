# M2.4  Sinusoidal-sequence generator
#   (a) x[n] = A sin(w0 n + phi), user-supplied L, A, w0 (0<w0<pi), phi;
#       used to reproduce the family of Figure 2.22.
#   (b) The angular frequencies of Problem 2.40: the period measured from the
#       sequence is compared with the theory N = 2*pi*r/w0.
#
#   Run:  julia hw1_M2_04.jl          (no packages required)
include("HW1Utils.jl")
using .HW1Utils
using Printf

"x[n] = A sin(w0 n + phi), n = 0 … L-1."
gensin(L, A, w0, phi) = (A .* sin.(w0 .* (0:L-1) .+ phi), 0:L-1)

"Smallest N > 0 with x[n+N] == x[n] for all tested n (NaN if none <= 1500)."
function measure_period(f)
    n = 0:3000;  x = f.(n)
    for N in 1:1500
        maximum(abs.(x[1:end-N] .- x[1+N:end])) < 1e-9 && return N
    end
    return -1
end

println("=====  M 2.4  Sinusoidal sequence generator  =====\n")

# ---- (a) the family of Figure 2.22: x[n] = 1.5 cos(w0 n) = 1.5 sin(w0 n + pi/2)
w0list = pi .* [0, 0.1, 0.2, 0.8, 0.9, 1.0, 1.1, 1.2]
labels = ["0", "0.1pi", "0.2pi", "0.8pi", "0.9pi", "pi", "1.1pi", "1.2pi"]
println("(a) Figure 2.22 family, x[n] = 1.5 cos(w0 n):")
println("      w0        N")
for (w0, lab) in zip(w0list, labels)
    @printf("    %-8s %4d\n", lab, fper(w0))
end

# folding: w0 and 2*pi - w0 are indistinguishable
a1, _ = gensin(41, 1.5, 1.2*pi, pi/2);  a2, _ = gensin(41, 1.5, 0.8*pi, pi/2)
b1, _ = gensin(41, 1.5, 1.1*pi, pi/2);  b2, _ = gensin(41, 1.5, 0.9*pi, pi/2)
@printf("\n    1.2pi and 0.8pi give identical samples : %s\n",
        maximum(abs.(a1 .- a2)) < 1e-12 ? "PASS" : "FAIL")
@printf("    1.1pi and 0.9pi give identical samples : %s\n\n",
        maximum(abs.(b1 .- b2)) < 1e-12 ? "PASS" : "FAIL")

# ---- (b) the angular frequencies of Problem 2.40
println("(b) Problem 2.40 -- fundamental periods")
println("       w0/pi    N (theory)   N (measured)")
allok = true
for a in (0.3, 0.48, 0.45, 0.525, 0.75, 0.75)
    w0  = pi * a
    Nth = fper(w0)
    Nnum = measure_period(m -> sin(w0 * m))
    ok = Nth == Nnum;  global allok &= ok
    @printf("     %6.3f   %8d     %8d   %s\n", a, Nth, Nnum, ok ? "PASS" : "FAIL")
end
println(allok ? "\n    all periods verified\n" : "\n    MISMATCH\n")

# ---- data for plotting (Plots.jl is not required to run this file)
open("hw1_M2_04_fig222.csv", "w") do io
    println(io, "n," * join(["w0_" * l for l in labels], ","))
    cols = [gensin(41, 1.5, w0, pi/2)[1] for w0 in w0list]
    for i in 1:41
        println(io, string(i-1) * "," * join([@sprintf("%.8f", c[i]) for c in cols], ","))
    end
end
println("  wrote hw1_M2_04_fig222.csv")
