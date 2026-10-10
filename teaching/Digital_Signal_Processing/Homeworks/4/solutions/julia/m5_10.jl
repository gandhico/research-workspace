# M5.10  Fourier-domain filtering  (Example 5.14, Mitra 4th ed.)
#
#   x[n] = 0.1 n exp(-0.03 n),  0 <= n <= 255,  corrupted by high-frequency
#   random noise.  Take the 256-point DFT, zero every sample in the band
#   50 <= k <= 206, and inverse transform.  The real part is kept: the zeroed
#   band is conjugate-symmetric about k = 128 (206 = 256 - 50), so the
#   imaginary part of the IDFT is zero up to round-off.
#
#   Two noise models are run:
#     (A) noise confined to the stopband 50 <= k <= 206  -- the premise of
#         Example 5.14; the filter removes it essentially completely, and the
#         residual error is only the signal's own energy in that band;
#     (B) white noise, which spreads over the whole band -- the filter can
#         only remove the 61% of its energy that falls inside the stopband.
#
#   Run:  julia m5_10.jl
include("DFTUtils.jl")
using .DFTUtils
using Printf, Random, LinearAlgebra

Random.seed!(0)

const N  = 256
const k1 = 50            # first zeroed DFT index
const k2 = 206           # last  zeroed DFT index
n = 0:N-1

"Real white noise band-limited to k1 <= k <= k2, scaled to RMS `rms`."
function bandlimited_noise(N, k1, k2, rms)
    W = dft(randn(N))
    W[1:k1] .= 0                     # zero k = 0 .. k1-1
    W[k2+2:N] .= 0                   # zero k = k2+1 .. N-1
    d = real.(idft(W))               # real, since the kept band is conj-symmetric
    return d .* (rms / sqrt(sum(abs2, d) / N))
end

# (1) original signal ---------------------------------------------------
x = 0.1 .* n .* exp.(-0.03 .* n)

# (2) the Fourier-domain filter -----------------------------------------
"Zero the DFT band k1..k2 and inverse transform; returns (filtered, S, Y, imagResidue)."
function fourier_filter(s, k1, k2)
    S = dft(s)
    Y = copy(S)
    Y[k1+1:k2+1] .= 0
    yc = idft(Y)
    return real.(yc), S, Y, maximum(abs.(imag.(yc)))
end

println("=====  M 5.10 : Fourier-domain filtering (Example 5.14)  =====\n")
@printf("  DFT length N                     : %d\n", N)
@printf("  zeroed DFT band                  : %d <= k <= %d  (%d of %d samples)\n",
        k1, k2, k2 - k1 + 1, N)
@printf("  retained band                    : k = 0..%d and %d..%d\n", k1 - 1, k2 + 1, N - 1)
@printf("  equivalent passband              : |w| <= %.4f pi  (%.1f%% of the band)\n",
        2k1 / N, 100 * 2k1 / N)
@printf("  conjugate-symmetric zeroing?     : %s  (k2 = N - k1 = %d)\n\n",
        k2 == N - k1 ? "yes" : "NO", N - k1)

results = Dict{String,Any}()
for (tag, d) in [("A  high-frequency (band-limited) noise", bandlimited_noise(N, k1, k2, 0.9)),
                 ("B  white noise",                        0.9 .* randn(N))]
    s = x .+ d
    y, S, Y, imres = fourier_filter(s, k1, k2)
    eBefore = norm(s .- x) / norm(x)
    eAfter  = norm(y .- x) / norm(x)
    println("  --- case ", tag, " ---")
    @printf("     max |imag(IDFT)| (round-off)  : %.3e\n", imres)
    @printf("     relative error BEFORE filter  : %.4f\n", eBefore)
    @printf("     relative error AFTER  filter  : %.4f\n", eAfter)
    @printf("     noise reduction factor        : %.1fx\n", eBefore / eAfter)
    @printf("     tail ripple, n >= 200         : max |y[n]-x[n]| = %.4f\n\n",
            maximum(abs.(y[201:end] .- x[201:end])))
    results[tag] = (s = s, y = y, S = S, Y = Y)
end

println("  The residual ripple at the tail of the filtered response is NOT noise:")
println("  the ideal (brick-wall) filter has an infinitely long impulse response,")
println("  so sampling its Fourier transform onto 256 DFT points aliases it in time")
println("  (Section 5.3.4).  This is the ripple visible in Figure 5.10(c).\n")

# (3) output -------------------------------------------------------------
rA = results["A  high-frequency (band-limited) noise"]
rB = results["B  white noise"]
open("m5_10_signals.csv", "w") do io
    println(io, "n,original,noisyA,filteredA,noisyB,filteredB,absDFT_before_A,absDFT_after_A")
    for i in 1:N
        @printf(io, "%d,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f\n", i - 1,
                x[i], rA.s[i], rA.y[i], rB.s[i], rB.y[i], abs(rA.S[i]), abs(rA.Y[i]))
    end
end
println("  wrote m5_10_signals.csv")

# Optional plots, if Plots.jl is installed (reproduces Figure 5.10)
try
    @eval using Plots
    p1 = plot(n, x, lw = 1.2, legend = false, xlabel = "n", ylabel = "Amplitude",
              title = "(a) Original signal")
    p2 = plot(n, rA.s, lw = 0.8, legend = false, xlabel = "n", ylabel = "Amplitude",
              title = "(b) Noise-corrupted signal")
    p3 = plot(n, rA.y, lw = 1.2, legend = false, xlabel = "n", ylabel = "Amplitude",
              title = "(c) After Fourier-domain filtering")
    p4 = plot(n, [abs.(rA.S) abs.(rA.Y)], lw = 0.8, xlabel = "k", ylabel = "|DFT|",
              title = "(d) DFT magnitude", label = ["|S[k]|" "|Y[k]|"])
    vline!(p4, [k1, k2], ls = :dash, label = "")
    savefig(plot(p1, p2, p3, p4, layout = (2, 2), size = (900, 700)), "m5_10_figure.png")
    println("  wrote m5_10_figure.png")
catch
    println("  (Plots.jl not installed - skipped the figure; the CSV has all the data)")
end
