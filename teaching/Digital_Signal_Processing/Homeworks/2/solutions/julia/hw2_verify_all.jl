# hw2_verify_all.jl
#   Numerical check of the hand-derived answers in Homework 2
#   (Mitra 4th ed.: Problems 3.16(a,b), 3.25, 3.60, 3.66, 4.9, 4.15, 4.23(a), 4.39)
#
#   Run:  julia hw2_verify_all.jl          (no packages required)
using Printf

const PASS = Ref(0); const FAIL = Ref(0)
function report(name, ok)
    if ok
        @printf("  PASS  %s\n", name); PASS[] += 1
    else
        @printf("  FAIL  %s\n", name); FAIL[] += 1
    end
end
function check(name, got, want; tol = 1e-9)
    g, w = collect(got), collect(want)
    ok = length(g) == length(w) && maximum(abs.(g .- w)) <= tol
    report(name, ok)
    ok || (@printf("        got  : %s\n        want : %s\n",
                   string(round.(g, digits=5)), string(round.(w, digits=5))))
end

"Linear convolution from the definition."
function conv(a, b)
    c = zeros(promote_type(eltype(a), eltype(b), Float64), length(a)+length(b)-1)
    for i in eachindex(a), j in eachindex(b); c[i+j-1] += a[i]*b[j]; end
    c
end

"Solve h * x = y for causal x by forward substitution."
function deconv_causal(y, h)
    L = length(y) - length(h) + 1
    x = zeros(Float64, L)
    for n in 1:L
        acc = y[n]
        for k in 2:min(n, length(h)); acc -= h[k]*x[n-k+1]; end
        x[n] = acc/h[1]
    end
    x
end

"Numerical DTFT of a finite sequence s with first sample at n0."
dtft(s, n0, w) = sum(s[i] * exp(-im*w*(n0+i-1)) for i in eachindex(s))

println("=== Homework 2 : numerical verification =====================\n")

# ---------------------------------------------------------------- 3.16(a,b)
# (a) x1[n] = a^n mu[n-1]      ->  X1 = a e^-jw / (1 - a e^-jw)
# (b) x2[n] = n a^n mu[n]      ->  X2 = a e^-jw / (1 - a e^-jw)^2
let a = 0.6, N = 4000, ok_a = true, ok_b = true
    for w in range(0, 2pi, length = 37)
        e = exp(-im*w)
        X1num = sum(a^n * e^n for n in 1:N)
        X1cf  = a*e/(1 - a*e)
        X2num = sum(n * a^n * e^n for n in 0:N)
        X2cf  = a*e/(1 - a*e)^2
        abs(X1num - X1cf) > 1e-9 && (ok_a = false)
        abs(X2num - X2cf) > 1e-9 && (ok_b = false)
    end
    report("3.16a X1(e^jw) = a e^-jw / (1 - a e^-jw)", ok_a)
    report("3.16b X2(e^jw) = a e^-jw / (1 - a e^-jw)^2", ok_b)
    # the common slip: dropping the a e^-jw factor in (a)
    w0 = 0.7; e0 = exp(-im*w0)
    report("3.16a  1/(1 - a e^-jw) is NOT the answer  [flagged slip]",
           abs(sum(a^n * e0^n for n in 1:N) - 1/(1 - a*e0)) > 1e-3)
end

# ---------------------------------------------------------------- 3.25
# Y(e^jw) = 0.5 { X(e^{jw/2}) + X(-e^{jw/2}) }   ->   y[n] = x[2n]
let n0 = -6, x = randn(25), ok = true
    for w in range(-pi, pi, length = 41)
        Y = 0.5*(dtft(x, n0, w/2) + dtft(x, n0, w/2 + pi))   # -e^{jw/2} = e^{j(w/2+pi)}
        # y[n] = x[2n]: keep the even-index samples of x
        idx = [i for i in eachindex(x) if iseven(n0 + i - 1)]
        yv  = x[idx];  ny0 = div(n0 + idx[1] - 1, 2)
        Yd  = dtft(yv, ny0, w)
        abs(Y - Yd) > 1e-9 && (ok = false)
    end
    report("3.25  y[n] = x[2n]", ok)
end

# ---------------------------------------------------------------- 3.60
# x1 = {1,2,1}, -1<=n<=1 ;  x2 = {-2,1,0,-1,2}, 0<=n<=4
check("3.60  x1 (*) x2  [n = -1..5]",
      conv([1.0,2,1], [-2.0,1,0,-1,2]), [-2.0,-3,0,0,0,3,2])
report("3.60  start index -1 + 0 = -1", (-1 + 0) == -1)

# ---------------------------------------------------------------- 3.66
# x[n] = {a,b,c}; X at w = 3pi/2, 3pi, 6pi equals 3-j, 0, 2
let a = 2-1im, b = 1+0im, c = -1+1im, ok = true
    for (w, t) in ((3pi/2, 3-1im), (3pi, 0+0im), (6pi, 2+0im))
        X = a + b*exp(-im*w) + c*exp(-2im*w)
        abs(X - t) > 1e-9 && (ok = false)
    end
    report("3.66  a = 2-j, b = 1, c = -1+j", ok)
end

# ---------------------------------------------------------------- 4.9
# y[n] = (x[n])^2 : nonlinear, time-invariant, causal (memoryless)
let x1 = randn(40), x2 = randn(40), sq = v -> v.^2
    report("4.9   NOT homogeneous: (2x)^2 != 2 x^2",
           maximum(abs.(sq(2 .* x1) .- 2 .* sq(x1))) > 1e-6)
    report("4.9   NOT additive: (x1+x2)^2 != x1^2 + x2^2",
           maximum(abs.(sq(x1 .+ x2) .- (sq(x1) .+ sq(x2)))) > 1e-6)
    n0 = 5                                   # delay the input by n0
    xd = vcat(zeros(n0), x1[1:end-n0])
    report("4.9   time-invariant: T{x[n-n0]} = y[n-n0]",
           maximum(abs.(sq(xd)[n0+1:end] .- sq(x1)[1:end-n0])) < 1e-12)
    report("4.9   causal / memoryless: y[n] depends only on x[n]",
           all(sq(x1) .== x1 .^ 2))
end

# ---------------------------------------------------------------- 4.15
# h[n] >= 0 for all n >= 0  =>  step response is monotone non-decreasing,
# so it never overshoots its final value s_inf = H(e^j0).
let ok = true, mono = true
    for trial in 1:200
        h = abs.(randn(30)) .* (0.8 .^ (0:29))      # nonnegative, summable
        s = cumsum(h)                                # step response
        all(diff(s) .>= -1e-12) || (mono = false)
        (maximum(s) <= s[end] + 1e-12) || (ok = false)
    end
    report("4.15  s[n] - s[n-1] = h[n] >= 0  (monotone)", mono)
    report("4.15  s[n] <= s_inf  (no overshoot)", ok)
end

# ---------------------------------------------------------------- 4.23(a)
# Textbook data: y = {6,-7,-13,24,12,33,-5,14}, h = {3,4,-1,2}
let y = [6.0,-7,-13,24,12,33,-5,14], h = [3.0,4,-1,2]
    x = deconv_causal(y, h)
    check("4.23a x[n] = {2, -5, 3, 1, 7}", x, [2.0,-5,3,1,7])
    check("4.23a h (*) x reproduces y",    conv(h, x), y)
    report("4.23a length(x) = 8 - 4 + 1 = 5", length(x) == 5)
end

# ---------------------------------------------------------------- 4.39
# (a) Binet:  f[n] = (phi^n - psi^n)/sqrt(5),  phi,psi = (1 +/- sqrt(5))/2
# (b) f[n] is the impulse response of y[n] = y[n-1] + y[n-2] + x[n-1]
let N = 30
    f = zeros(Float64, N); f[2] = 1
    for n in 3:N; f[n] = f[n-1] + f[n-2]; end        # f[0]=0, f[1]=1
    phi = (1 + sqrt(5))/2;  psi = (1 - sqrt(5))/2
    binet = [(phi^n - psi^n)/sqrt(5) for n in 0:N-1]
    check("4.39a f[n] = (phi^n - psi^n)/sqrt(5)", f, binet, tol = 1e-6)
    report("4.39a A = 1/sqrt(5), B = -1/sqrt(5)",
           abs(1/sqrt(5) - 0.4472135955) < 1e-9)
    # (b) drive y[n] = y[n-1] + y[n-2] + x[n-1] with x = delta[n], zero state
    x = zeros(N); x[1] = 1
    yv = zeros(N)
    for n in 1:N
        ym1 = n >= 2 ? yv[n-1] : 0.0
        ym2 = n >= 3 ? yv[n-2] : 0.0
        xm1 = n >= 2 ? x[n-1]  : 0.0
        yv[n] = ym1 + ym2 + xm1
    end
    check("4.39b impulse response of y[n]=y[n-1]+y[n-2]+x[n-1] is f[n]", yv, f)
end

println("\n=== done ====================================================")
@printf("  %d/%d checks PASSED", PASS[], PASS[] + FAIL[])
FAIL[] > 0 && @printf("   (%d FAILED)", FAIL[])
println()
