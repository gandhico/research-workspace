# hw4_verify_all.jl
#   Numerical verification of every hand-derived result in HW #4
#   (Mitra 4th ed., Chapter 5: Problems 5.11, 5.13, 5.18, 5.20, 5.23, 5.58, 5.65)
#   Run:  julia hw4_verify_all.jl
include("DFTUtils.jl")
using .DFTUtils
using Printf, Random

Random.seed!(1)

const PASS = Ref(0); const FAIL = Ref(0)
function check(name, cond)
    if cond
        @printf("  PASS  %s\n", name); PASS[] += 1
    else
        @printf("  FAIL  %s\n", name); FAIL[] += 1
    end
end
tol = 1e-9

println("===========================================================")
println("  HW #4  --  verification of hand-derived results")
println("===========================================================\n")

# ---------------- Problem 5.11 :  F^4{x[n]} = N^2 x[n] ----------------
println("Problem 5.11   y[n] = F{F{F{F{x[n]}}}} = N^2 x[n]")
for N in (4, 5, 8, 12)
    x = randn(N) .+ im .* randn(N)
    y = dft(dft(dft(dft(x))))
    check("N=$N : F^4{x} = N^2 x", maximum(abs.(y .- N^2 .* x)) < tol * N^3)
    x2 = dft(dft(x))
    xr = [x[circidx(-k, N)] for k in 0:N-1]
    check("N=$N : F^2{x}[k] = N x[<-k>_N]", maximum(abs.(x2 .- N .* xr)) < tol * N^2)
end
println()

# ---------------- Problem 5.13 : DIF butterfly ------------------------
println("Problem 5.13   X[2l] = G[l],  X[2l+1] = H[l]")
for N in (6, 8, 12, 16)
    x = randn(N); M = N ÷ 2; WN = cis(-2π / N)
    g = [x[n+1] + x[n+M+1]                for n in 0:M-1]
    h = [(x[n+1] - x[n+M+1]) * WN^n       for n in 0:M-1]
    G, H, X = dft(g), dft(h), dft(x)
    check("N=$N : X[2l]   = G[l]",   maximum(abs.([X[2l+1] for l in 0:M-1] .- G)) < tol * N)
    check("N=$N : X[2l+1] = H[l]",   maximum(abs.([X[2l+2] for l in 0:M-1] .- H)) < tol * N)
end
println()

# ---------------- Problem 5.18 : X[k] = Y[kM] -------------------------
println("Problem 5.18   X[k] = Y[kM]  (zero-padding by factor M)")
for N in (5, 7, 8), M in (2, 3, 4)
    x  = randn(N)
    xe = vcat(x, zeros((M - 1) * N))
    Y, X = dft(xe), dft(x)
    check("N=$N, M=$M : X[k] = Y[kM]",
          maximum(abs.(X .- [Y[M*k+1] for k in 0:N-1])) < tol * N * M)
end
println()

# ---------------- Problem 5.20 : zero interpolation -------------------
println("Problem 5.20   Y[k] = X[<k>_N]  (L-fold zero interpolation)")
for N in (4, 5, 6), L in (2, 3, 4)
    x = randn(N)
    y = zeros(N * L); for m in 0:N-1; y[L*m+1] = x[m+1]; end   # Eq. (5.202)
    Y, X = dft(y), dft(x)
    check("N=$N, L=$L : Y[k] = X[<k>_N]",
          maximum(abs.(Y .- [X[mod(k, N)+1] for k in 0:N*L-1])) < tol * N * L)
end
# part (b): the specific sketch
X5 = ComplexF64[1, 1, 4, 3, 2]; L = 4
x5 = idft(X5); y = zeros(ComplexF64, 20); for m in 0:4; y[L*m+1] = x5[m+1]; end
Y20 = dft(y)
check("part (b) : Y[k] = four periods of {1,1,4,3,2}",
      maximum(abs.(Y20 .- repeat(X5, 4))) < tol * 20)
@printf("       Y[k] = [%s]\n\n", join([@sprintf("%.4g", real(v)) for v in Y20], " "))

# ---------------- Problem 5.23 : rational DTFT ------------------------
println("Problem 5.23   p[n], d[n] from P[k], D[k]")
P = ComplexF64[3.5, -0.5 - 9.5im, 2.5, -0.5 + 9.5im]
D = ComplexF64[17, 7.4 + 12im, 17.8, 7.4 - 12im]
pc, dc = idft(P), idft(D)
check("p[n] is real", maximum(abs.(imag.(pc))) < tol)
check("d[n] is real", maximum(abs.(imag.(dc))) < tol)
p, d = real.(pc), real.(dc)
@printf("       p[n] = [%s]\n", join([@sprintf("%g", v) for v in p], " "))
@printf("       d[n] = [%s]\n", join([@sprintf("%g", v) for v in d], " "))
check("p[n] = {1.25, 5, 1.75, -4.5}", maximum(abs.(p .- [1.25, 5, 1.75, -4.5])) < 1e-10)
check("d[n] = {12.4, -6.2, 5, 5.8}",  maximum(abs.(d .- [12.4, -6.2, 5, 5.8]))  < 1e-10)
w   = [2π * k / 4 for k in 0:3]
num = [sum(p[i+1] * cis(-wi * i) for i in 0:3) for wi in w]
den = [sum(d[i+1] * cis(-wi * i) for i in 0:3) for wi in w]
check("numerator   matches P[k] on w = 2pi k/4", maximum(abs.(num .- P)) < 1e-9)
check("denominator matches D[k] on w = 2pi k/4", maximum(abs.(den .- D)) < 1e-9)
println("       X(e^jw) = (1.25 + 5e^-jw + 1.75e^-j2w - 4.5e^-j3w)")
println("               / (12.4 - 6.2e^-jw + 5e^-j2w + 5.8e^-j3w)\n")

# ---------------- Problem 5.58 : circular cross-correlation -----------
println("Problem 5.58   DFT{r_xy[l]} = X[k] * conj(Y[k])")
for N in (4, 5, 8)
    local xs, ys, r, R, X, Y, ra
    xs, ys = randn(N), randn(N)
    r  = [sum(xs[n+1] * ys[circidx(n - l, N)] for n in 0:N-1) for l in 0:N-1]  # (5.203)
    R, X, Y = dft(r), dft(xs), dft(ys)
    check("N=$N : R_xy[k] = X[k] conj(Y[k])", maximum(abs.(R .- X .* conj.(Y))) < tol * N^2)
    check("N=$N : R_xy[k] = X[k] Y[<-k>_N]",
          maximum(abs.(R .- X .* [Y[circidx(-k, N)] for k in 0:N-1])) < tol * N^2)
    ra = [sum(xs[n+1] * xs[circidx(n - l, N)] for n in 0:N-1) for l in 0:N-1]
    check("N=$N : R_xx[k] = |X[k]|^2", maximum(abs.(dft(ra) .- abs2.(X))) < tol * N^2)
end
println()

# ---------------- Problem 5.65 : circular shift -----------------------
println("Problem 5.65   G[k] = W12^(5k) H[k]")
Hh = ComplexF64[4.0, 17.19 + 1.46im, -9.0 + 3.46im, -9.0 + 5.0im,
                1.0 + 24.25im, 6.8 - 5.46im, 6.0]
H  = vcat(Hh, conj.(reverse(Hh[2:6])))          # fill in by conjugate symmetry
check("H[k] has length 12", length(H) == 12)
hc = idft(H)
check("h[n] is real", maximum(abs.(imag.(hc))) < 1e-9)
h = real.(hc)
@printf("       h[n] = [%s]   (integers, as expected)\n",
        join([@sprintf("%.3f", v) for v in h], " "))
G = [cis(-2π * 5 * k / 12) * H[k+1] for k in 0:11]     # circular time-shift theorem
g = real.(idft(G))
check("g[n] = h[<n-17>_12] = h[<n-5>_12]",
      maximum(abs.(g .- [h[circidx(n - 5, 12)] for n in 0:11])) < 1e-9)
check("G[0] =  H[0] =  4  (real)", abs(G[1] - 4) < 1e-9)
check("G[6] = -H[6] = -6  (real)", abs(G[7] + 6) < 1e-9)
check("G[k] conjugate symmetric",
      maximum(abs.(G .- [conj(G[circidx(-k, 12)]) for k in 0:11])) < 1e-9)
println("\n       k |          G[k]\n      ---+---------------------")
for k in 0:11
    @printf("      %2d | %10.4f %+9.4fj\n", k, real(G[k+1]), imag(G[k+1]))
end

# ---------------- summary ----------------------------------------------
println("\n===========================================================")
@printf("  %d/%d checks PASSED", PASS[], PASS[] + FAIL[])
FAIL[] > 0 && @printf("   (%d FAILED)", FAIL[])
println("\n===========================================================")
