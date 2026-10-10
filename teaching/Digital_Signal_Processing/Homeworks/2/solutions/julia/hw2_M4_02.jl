#=
hw2_M4_02.jl — MATLAB Exercise M4.2 (Mitra, 4th ed., Chapter 4), Julia version

Implement the discrete-time system of Eq. (4.109), Problem 4.11,

        y[n] = 0.5 * ( y[n-1] + x[n]/y[n-1] ),

and show that for x[n] = α·μ[n] with y[-1] = 1 the output converges to √α.

Why it works: with x[n] = α for n ≥ 0 the recursion is Newton–Raphson on
f(y) = y² - α,

        y[n] = y[n-1] - f(y[n-1])/f'(y[n-1]) = 0.5*(y[n-1] + α/y[n-1]),

whose fixed point satisfies y² = α.  With e[n] = y[n] - √α,

        e[n] = e[n-1]² / (2·y[n-1]),

so the error squares each step (quadratic convergence) and stays positive
after the first step — the output approaches √α monotonically from above.

Dependencies:  Plots.jl        ]add Plots
Run:           julia --project hw2_M4_02.jl
=#

# Plots.jl is optional: without it the script still runs and writes the CSV.
# Install with  ]add Plots  to get the figure.
const HAVE_PLOTS = try
    @eval using Plots
    true
catch
    println("  (Plots.jl not installed - figure skipped, CSV data still written)")
    false
end
using Printf

"""
    sqrtsys(x; yinit = 1.0) -> y

Eq. (4.109):  y[n] = 0.5*( y[n-1] + x[n]/y[n-1] ),  y[-1] = yinit.
"""
function sqrtsys(x::AbstractVector; yinit::Real = 1.0)
    y  = similar(float(collect(x)))
    ym = float(yinit)                      # y[n-1]
    for n in eachindex(x)
        y[n] = 0.5 * (ym + x[n] / ym)
        ym   = y[n]
    end
    return y
end

const N      = 12                          # samples n = 0 … N-1
const ALPHAS = (0.25, 2.0, 9.0, 100.0, 1e4)

# ---- Table: y[n] and the error for each α -------------------------------
for a in ALPHAS
    y = sqrtsys(fill(a, N))                # x[n] = α·μ[n]
    @printf("\nalpha = %g   (sqrt(alpha) = %.12f)\n", a, sqrt(a))
    println("   n        y[n]            |y[n]-sqrt(alpha)|")
    for n in 0:N-1
        @printf("%4d  %18.12f  %18.3e\n", n, y[n+1], abs(y[n+1] - sqrt(a)))
    end
    @printf("   converged to sqrt(alpha) : %s\n",
            abs(y[end] - sqrt(a)) < 1e-12 * max(1, sqrt(a)))
end

# ---- Convergence data ----------------------------------------------------
open("hw2_M4_02_convergence.csv", "w") do io
    println(io, "alpha,n,y,normalized,abs_error")
    for a in ALPHAS
        y = sqrtsys(fill(a, N))
        for k in 1:N
            row = @sprintf("%g,%d,%.12f,%.12f,%.6e",
                           a, k-1, y[k], y[k]/sqrt(a), abs(y[k]-sqrt(a)))
            println(io, row)
        end
    end
end
println("  wrote hw2_M4_02_convergence.csv")

if HAVE_PLOTS
    # ---- Convergence plots ---------------------------------------------------
    p = plot(layout = (1, 2), size = (960, 420),
             plot_title = "M4.2  convergence of y[n] to √α")
    for a in ALPHAS
        y = sqrtsys(fill(a, N))
        lbl = "α = $(a)"
        scatter!(p, 0:N-1, y ./ sqrt(a); subplot = 1, label = lbl, ms = 4,
                 xlabel = "Time index n", ylabel = "y[n] / √α", ylims = (0, 4),
                 title = "Normalized output (early samples clipped)", grid = true)
        plot!(p, 0:N-1, abs.(y .- sqrt(a)) .+ eps(); subplot = 2, label = lbl,
              marker = :circle, lw = 1.5, yscale = :log10,
              xlabel = "Time index n", ylabel = "|y[n] - √α|",
              title = "Error (digits double each step)", grid = true)
    end
    hline!(p, [1.0]; subplot = 1, ls = :dash, c = :black, label = "")
    savefig(p, "hw2_M4_02_convergence.png")
end

# ---- Verify the quadratic error recursion e[n] = e[n-1]²/(2 y[n-1]) ------
let a = 2.0, yinit = 1.0
    y  = sqrtsys(fill(a, N); yinit = yinit)
    s  = sqrt(a)
    e  = y .- s
    ep = vcat(yinit - s, e[1:end-1])        # e[n-1], starting from y[-1]
    yp = vcat(yinit,     y[1:end-1])        # y[n-1]
    err = maximum(abs.(e .- ep .^ 2 ./ (2 .* yp)))
    @printf("\ne[n] == e[n-1]^2/(2 y[n-1]) : %s  (max err %.2e)\n", err < 1e-12, err)
end

# ---- Problem 4.11 follow-ups: nonlinear and time-varying ----------------
let
    x  = fill(4.0, N)
    y1 = sqrtsys(x)                         # → √4  = 2
    y2 = sqrtsys(2 .* x)                    # → √8 ≈ 2.828, not 2·2 = 4
    @printf("nonlinear  (2x -> 2y fails) : %s   [y=%.4f, y(2x)=%.4f, 2y=%.4f]\n",
            abs(y2[end] - 2 * y1[end]) > 1e-6, y1[end], y2[end], 2 * y1[end])

    n0 = 3                                  # delaying the input ≠ delaying the output
    xd = vcat(zeros(n0), fill(4.0, N - n0))
    yd = sqrtsys(xd)
    @printf("time-varying (delay not preserved) : %s\n",
            maximum(abs.(yd[n0+1:end] .- y1[1:end-n0])) > 1e-6)
end
