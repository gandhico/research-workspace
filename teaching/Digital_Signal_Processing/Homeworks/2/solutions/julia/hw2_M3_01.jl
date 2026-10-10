#=
hw2_M3_01.jl — MATLAB Exercise M3.1 (Mitra, 4th ed., Chapter 3), Julia version

    G(e^{jω}) = 1 / (1 - 2r cos(θ) e^{-jω} + r² e^{-j2ω}),   0 < r < 1

Same computation as Program 3_1: evaluate the rational function of Eq. (3.37)
on a dense grid of ω in [0, π] and plot real part, imaginary part, magnitude
and phase.  Only [0, π] is needed because the coefficients are real, so
G(e^{-jω}) = conj(G(e^{jω})).

    num = [1]
    den = [1, -2r*cos(θ), r^2]        (coefficients of e^{-jω}, ascending)
    poles at z = r*exp(±jθ) — inside the unit circle for r < 1, which is
    exactly the condition for the DTFT to converge.

Dependencies:  Plots.jl        ]add Plots
Run:           julia --project hw2_M3_01.jl
=#

using Printf

# Plots.jl is optional: without it the script still runs and writes the CSV
# data for every sweep.  Install with  ]add Plots  to get the figures.
const HAVE_PLOTS = try
    @eval using Plots
    true
catch
    println("  (Plots.jl not installed - figures skipped, CSV data still written)")
    false
end

"Evaluate Σ c[k] z^(k-1) — c holds coefficients of e^{-jω} in ascending order."
polyval(c, z) = sum(c[k] * z^(k - 1) for k in eachindex(c))

"""
    dtft(num, den, K) -> (ω, G)

Program 3_1 kernel: the DTFT of a rational function in e^{jω} at K equally
spaced points on 0 ≤ ω ≤ π.
"""
function dtft(num, den, K::Integer)
    ω = collect(range(0, π; length = K))
    G = [polyval(num, exp(-im * w)) / polyval(den, exp(-im * w)) for w in ω]
    return ω, G
end

"Phase unwrapping (Julia Base has none; DSP.unwrap would also do)."
function unwrap(φ::AbstractVector)
    out = copy(float(φ))
    for k in 2:length(out)
        d = out[k] - out[k-1]
        out[k] -= 2π * round(d / (2π))
    end
    return out
end

den(r, θ) = [1.0, -2r * cos(θ), r^2]

"""Write omega/pi, Re, Im, |G| and arg G for every case to a CSV file."""
function write_sweep(fname, cases, K)
    open(fname, "w") do io
        println(io, "case,omega_over_pi,real,imag,abs,phase")
        for (r, θ, lbl) in cases
            ω, G = dtft([1.0], den(r, θ), K)
            ph = unwrap(angle.(G))
            for i in eachindex(ω)
                row = @sprintf("%s,%.6f,%.8f,%.8f,%.8f,%.8f",
                               lbl, ω[i]/π, real(G[i]), imag(G[i]), abs(G[i]), ph[i])
                println(io, row)
            end
        end
    end
    println("  wrote ", fname)
end

"Program 3_1 plotting layout, overlaying several (r, θ) cases."
function p3_1(cases, K, ttl)
    panels = ("Real part", "Imaginary part", "Magnitude spectrum", "Phase spectrum")
    ylabs  = ("Amplitude", "Amplitude", "Magnitude", "Phase, radians")
    plt = plot(layout = (2, 2), size = (980, 620), plot_title = ttl)
    for (r, θ, lbl) in cases
        ω, G = dtft([1.0], den(r, θ), K)
        vals = (real.(G), imag.(G), abs.(G), unwrap(angle.(G)))
        for p in 1:4
            plot!(plt, ω ./ π, vals[p]; subplot = p, label = lbl, lw = 1.5,
                  title = panels[p], xlabel = "ω/π", ylabel = ylabs[p],
                  grid = true, legend = :best)
        end
    end
    return plt
end

const K = 512

# ---- Sweep 1: θ = π/4 fixed, r varied -----------------------------------
cases1 = [(r, π/4, "r = $(r)") for r in (0.5, 0.8, 0.95)]
write_sweep("hw2_M3_01_r_sweep.csv", cases1, K)
HAVE_PLOTS && savefig(p3_1(cases1, K, "M3.1  θ = π/4, r varied"),
                      "hw2_M3_01_r_sweep.png")

# ---- Sweep 2: r = 0.8 fixed, θ varied -----------------------------------
cases2 = [(0.8, π/6, "θ = π/6"), (0.8, π/3, "θ = π/3"), (0.8, 2π/3, "θ = 2π/3")]
write_sweep("hw2_M3_01_theta_sweep.csv", cases2, K)
HAVE_PLOTS && savefig(p3_1(cases2, K, "M3.1  r = 0.8, θ varied"),
                      "hw2_M3_01_theta_sweep.png")

# ---- Numerical observations ---------------------------------------------
# The peak of |G| sits essentially at ω = θ and grows like 1/(1-r).
println()
println("     r   theta/pi   peak|G|   w_peak/pi   1/[(1-r)|1-r e^{-j2θ}|]")
println("  ---------------------------------------------------------------")
for r in (0.5, 0.8, 0.95, 0.99), θ in (π/6, π/4, π/3)
    ω, G = dtft([1.0], den(r, θ), K)
    pk, i = findmax(abs.(G))
    pred  = 1 / ((1 - r) * abs(1 - r * exp(-im * 2θ)))
    @printf("%6.2f %9.4f %10.3f %11.4f %14.3f\n", r, θ/π, pk, ω[i]/π, pred)
end

# ---- Check against the direct DTFT sum of the impulse response ----------
# h[n] = r^n sin((n+1)θ)/sin(θ)  for the two-pole resonator.
let r = 0.8, θ = π/3, N = 400
    n = 0:N-1
    h = @. r^n * sin((n + 1) * θ) / sin(θ)
    ω, G = dtft([1.0], den(r, θ), 64)
    Gsum = [sum(h[k] * exp(-im * w * (k - 1)) for k in eachindex(h)) for w in ω]
    err  = maximum(abs.(G .- Gsum))
    @printf("\nrational form == direct DTFT sum of h[n] : %s  (max err %.2e)\n",
            err < 1e-8, err)
end
