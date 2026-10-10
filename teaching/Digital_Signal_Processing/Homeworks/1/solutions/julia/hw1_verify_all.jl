# hw1_verify_all.jl
#   Numerical check of every closed-form answer in Homework 1.
#   Mitra, "Digital Signal Processing: A Computer-Based Approach", 4th ed.,
#   Chapter 2, Problems 2.4-2.54.
#
#   Julia port of matlab/hw1_verify_all.m -- an independent second
#   implementation, so agreement between the two is real evidence.
#
#   Run:  julia hw1_verify_all.jl          (no packages required)
include("HW1Utils.jl")
using .HW1Utils
using Printf

const PASS = Ref(0); const FAIL = Ref(0)

function report(name, ok)
    if ok
        @printf("  PASS  %s\n", name); PASS[] += 1
    else
        @printf("  FAIL  %s\n", name); FAIL[] += 1
    end
end

function check(name, got, want; tol = 1e-12)
    g, w = collect(got), collect(want)
    ok = length(g) == length(w) && maximum(abs.(g .- w)) <= tol
    report(name, ok)
    if !ok
        @printf("        got  : %s\n", string(round.(g, digits = 4)))
        @printf("        want : %s\n", string(round.(w, digits = 4)))
    end
end

println("=== Homework 1 : numerical verification =====================\n")

# ---- Problem 2.3 sequences (used throughout) -------------------------
x = [ 3.0, -4, -2,  5,  0,  1, -3];  nx = -1
y = [-5.0, -1,  0,  3,  6, -2,  8];  ny = -3
w = [-1.0,  3, -4,  0,  1, -5,  6];  nw =  3

# -------------------------------------------------------------- 2.7
x1 = Float64[1,0,1,0,1,0,1,0,1,0,1,0,1,0,1]
x2 = Float64[1,1]
x3 = Float64[1,1,0,0,0,0,0,0,1,1]
x4_printed  = Float64[1,1,0,0,0,1,1]      # as printed  -> identity FAILS
x4_intended = Float64[1,0,1,0,1,0,1]      # intended    -> identity HOLDS
lhs = conv(x1, x2)
check("2.7   x1*x2 = sixteen ones",          lhs, ones(16))
check("2.7   x3*x4 (intended) equals x1*x2", conv(x3, x4_intended), lhs)
report("2.7   x3*x4 (as printed) DIFFERS  [book misprint]",
       conv(x3, x4_printed) != lhs)

# -------------------------------------------------------------- 2.8
check("2.8a  x1 (*) x1", conv([1.0,-1,1], [1.0,-1,1]), [1.0,-2,3,-2,1])
check("2.8b  x2 (*) x2", conv([1.0,-1,0,1,-1], [1.0,-1,0,1,-1]),
                          [1.0,-2,1,2,-4,2,1,-2,1])
check("2.8c  x3 (*) x3", conv([-1.0,2,0,-2,1], [-1.0,2,0,-2,1]),
                          [1.0,-4,4,4,-10,4,4,-4,1])

# -------------------------------------------------------------- 2.9
check("2.9a  u = x (*) y   [n = -4..8]", conv(x, y),
      [-15.0,17,14,-14,1,-41,49,5,-23,37,-20,14,-24])
check("2.9b  v = x (*) w   [n =  2..14]", conv(x, w),
      [-3.0,13,-22,5,26,-40,42,-22,-25,31,-8,21,-18])
check("2.9c  g = w (*) y   [n =  0..12]", conv(w, y),
      [5.0,-14,17,1,-2,32,-63,29,-41,-14,54,-52,48])
report("2.9   start indices (-4, 2, 0)",
       [nx+ny, nx+nw, nw+ny] == [-4, 2, 0])

# -------------------------------------------------------------- 2.13
xa = [2.0,-3,4,1];  nxa = -1
ha = [-3.0,5,-6,4]; nha = -2
ya = conv(xa, ha);  nya = nxa + nha
check("2.13  y[-1] = -39", [ya[-1-nya+1]], [-39.0])

# -------------------------------------------------------------- 2.14
# Peak of {n} (*) {n} predicted by
#   mstar = (5-2N+sqrt(8N^2-24N+25))/2 ,  nmax = ceil(mstar)+N-3
let ok = true
    for N in 5:60
        yy = conv(collect(0.0:N-1), collect(0.0:N-3))
        _, k = findmax(yy);  nmax_num = k - 1
        mstar = (5 - 2N + sqrt(8N^2 - 24N + 25)) / 2
        nmax_pred = Int(ceil(mstar)) + N - 3
        if nmax_num != nmax_pred && yy[nmax_pred+1] != maximum(yy)
            ok = false
            @printf("   mismatch at N = %d\n", N)
        end
    end
    report("2.14  closed-form location of the peak (N = 5..60)", ok)
end

# -------------------------------------------------------------- 2.15
check("2.15a x[n]", deconv_causal([2.0,5,-5,0,12,10,3], [2.0,-3,1,3]), [1.0,4,3,1])
check("2.15b x[n]", deconv_causal([0.0,-15,-7,9,-4,2], [5.0,-1,1]),    [0.0,-3,-2,2])
check("2.15c x[n]", deconv_causal([6.0,8,-12,-11,14,-22,-12,3,-18],
                                  [-3.0,2,2,0,3]),                     [-2.0,-4,0,1,-6])

# -------------------------------------------------------------- 2.16 / 2.17
xs = [2.0,-5,6,-3,4,-4,0,-7,8];  n0 = -5;  N9 = 9
xt(n) = xs[mod(n - n0, N9) + 1]                     # 9-periodic extension
check("2.16a y[-3] after LEFT circular shift by 12",  [xt(-3+12)], [-4.0])
check("2.16b z[2]  after RIGHT circular shift by 15", [xt(2-15)],  [-5.0])

gs = [-3.0,0,4,9,2,0,-2,5];  g0 = -4;  N8 = 8
gt(n) = gs[mod(n - g0, N8) + 1]
check("2.17a h[n] = right circular shift of g by 5",
      [gt(n-5) for n in -4:3], [9.0,2,0,-2,5,-3,0,4])
check("2.17b w[n] = left  circular shift of g by 4",
      [gt(n+4) for n in -4:3], [2.0,0,-2,5,-3,0,4,9])

# -------------------------------------------------------------- 2.19
# Energy of sin(2*pi*k*n/N) over one period: N/2 unless 2k/N is an integer.
let ok = true
    for N in 3:20, k in 0:2N
        E  = sum(sin.(2*pi*k*(0:N-1)/N).^2)
        Ep = mod(2k, N) != 0 ? N/2 : 0.0
        abs(E - Ep) > 1e-10 && (ok = false)
    end
    report("2.19  E = N/2  (0 when 2k/N is an integer)", ok)
end

# -------------------------------------------------------------- 2.20
ev, od, nn = evenodd(x, nx)
report("2.20  x_ev even, x_od odd, parts sum to x",
       ev ≈ reverse(ev) && od ≈ -reverse(od) &&
       ev .+ od ≈ embed(x, nx, first(nn), last(nn)))
check("2.20  x_ev[n], n = -5..5", ev,
      [-1.5,0.5,0,2.5,0.5,-4,0.5,2.5,0,0.5,-1.5])
check("2.20  x_od[n], n = -5..5", od,
      [ 1.5,-0.5,0,-2.5,2.5,0,-2.5,2.5,0,0.5,-1.5])
ev2, od2, _ = evenodd(y, ny)
check("2.20  y_ev[n], n = -3..3", ev2, [1.5,-1.5,3,3,3,-1.5,1.5])
check("2.20  y_od[n], n = -3..3", od2, [-6.5,0.5,-3,0,3,-0.5,6.5])

# -------------------------------------------------------------- 2.21
xc  = ComplexF64[-1+3im, 2-7im, 4-5im, 3+5im, -2-1im]      # -2 <= n <= 2
rev = conj.(reverse(xc))
check("2.21a x_cs", (xc .+ rev) ./ 2,
      ComplexF64[-1.5+2im, 2.5-6im, 4+0im, 2.5+6im, -1.5-2im])
check("2.21a x_ca", (xc .- rev) ./ 2,
      ComplexF64[0.5+1im, -0.5-1im, 0-5im, 0.5-1im, -0.5+1im])
nsym = -20:20
x2c = exp.(im*2*pi*nsym/5) .+ exp.(im*pi*nsym/3)
report("2.21b x2 is conjugate symmetric (x_ca = 0)",
       maximum(abs.(x2c .- conj.(reverse(x2c)))) < 1e-10)
x3c = im .* cos.(2*pi*nsym/7) .- sin.(2*pi*nsym/4)
report("2.21c x3 is conjugate antisymmetric (x_cs = 0)",
       maximum(abs.(x3c .+ conj.(reverse(x3c)))) < 1e-10)

# -------------------------------------------------------------- 2.37
check("2.37a  x~[n], N = 6", perext(x, nx, 6), [-4.0,-2,5,0,1,0])
check("2.37a  y~[n], N = 6", perext(y, ny, 6), [ 3.0, 6,-2,3,-1,0])
check("2.37a  w~[n], N = 6", perext(w, nw, 6), [ 0.0, 1,-5,5, 3,-4])
check("2.37b  x~[n], N = 8", perext(x, nx, 8), [-4.0,-2,5,0,1,-3,0,3])
check("2.37b  y~[n], N = 8", perext(y, ny, 8), [ 3.0, 6,-2,8,0,-5,-1,0])
check("2.37b  w~[n], N = 8", perext(w, nw, 8), [-5.0, 6, 0,-1,3,-4,0,1])

# -------------------------------------------------------------- 2.38
n3 = 0:3
check("2.38a  A = sqrt(2), w = pi/2,  phi = pi/4",
      sqrt(2) .* sin.(pi/2 .* n3 .+ pi/4), [1.0,1,-1,-1])
check("2.38b  A = 0.5,     w = pi,    phi = pi/2",
      0.5 .* sin.(pi .* n3 .+ pi/2),       [0.5,-0.5,0.5,-0.5])
check("2.38c  A = 1,       w = 0.8pi, phi = 0",
      sin.(0.8*pi .* (0:4)), [0.0,0.5878,-0.9511,0.9511,-0.5878], tol = 1e-4)
check("2.38d  A = 2,       w = pi/2,  phi = pi/2",
      2 .* sin.(pi/2 .* n3 .+ pi/2),       [2.0,0,-2,0])

# -------------------------------------------------------------- 2.39 / 2.40 / 2.41 / 2.42
check("2.39  fundamental periods",
      [fper(0.25*pi), lcmv([fper(0.6*pi)]),
       lcmv([fper(pi/8), fper(pi/5)]),
       lcmv([fper(0.15*pi), fper(0.12*pi)]),
       lcmv([fper(0.1*pi), fper(0.8*pi), fper(1.3*pi)])],
      [8, 10, 80, 200, 20])
check("2.40  fundamental periods",
      [fper(pi*a) for a in (0.3, 0.48, 0.45, 0.525, 0.75, 0.75)],
      [20, 25, 40, 80, 8, 8])
check("2.41  period of sin(0.06*pi*n) and two others",
      [fper(0.06*pi), fper(0.14*pi), fper(0.26*pi)], [100, 100, 100])
check("2.42  fundamental periods",
      [fper(pi/3), fper(2*pi/5), fper(2*pi/7), fper(5*pi/7),
       lcmv([fper(2*pi/5), fper(3*pi/5)]), lcmv([fper(5*pi/3), fper(3*pi/5)])],
      [6, 5, 7, 14, 10, 30])
Pnum(s, N) = sum(s.(0:N-1) .^ 2) / N
check("2.42  average powers",
      [Pnum(n -> 5*cos(pi*n/3), 6),   Pnum(n -> 2*cos(2*pi*n/5), 5),
       Pnum(n -> 2*cos(2*pi*n/7), 7), Pnum(n -> 3*cos(5*pi*n/7), 14),
       Pnum(n -> 4*cos(2*pi*n/5) + 3*cos(3*pi*n/5), 10),
       Pnum(n -> 4*cos(5*pi*n/3) + 3*cos(3*pi*n/5), 30)],
      [12.5, 2, 2, 4.5, 12.5, 12.5], tol = 1e-10)

# -------------------------------------------------------------- 2.43 / 2.44
check("2.43b x[n] step coefficients", stepcoef(x), [3.0,-7,2,7,-5,1,-4,3])
check("2.43b y[n] step coefficients", stepcoef(y), [-5.0,4,1,3,3,-8,10,-8])
check("2.43b w[n] step coefficients", stepcoef(w), [-1.0,4,-7,4,1,-6,11,-6])
check("2.44  step coefficients",      stepcoef([2.1,-3.3,-1.7,5.2]),
      [2.1,-5.4,1.6,6.9,-5.2], tol = 1e-12)

# -------------------------------------------------------------- 2.46
al = 0.7;  nn2 = 0:25;  L = length(nn2)
c1 = conv(al .^ nn2,        ones(L))
c2 = conv(nn2 .* al .^ nn2, ones(L))
check("2.46a closed form", c1[1:L], (1 .- al .^ (nn2 .+ 1)) ./ (1 - al), tol = 1e-10)
check("2.46b closed form", c2[1:L],
      al .* (1 .- (nn2 .+ 1) .* al .^ nn2 .+ nn2 .* al .^ (nn2 .+ 1)) ./ (1-al)^2,
      tol = 1e-10)

# -------------------------------------------------------------- 2.47
p1 = [-2.0,0,2];             q1 = -1
p2 = [-1.0,0,3];             q2 =  0
r1 = [1.0,0,0,-1.5,0,-1];    s1 = -3
r2 = [-1.0,0,2,0,3];         s2 = -1
check("2.47a y1 = x1 (*) h1  [n = -4..3]", conv(p1,r1), [-2.0,0,2,3,0,-1,0,-2])
check("2.47b y2 = x2 (*) h2  [n = -1..5]", conv(p2,r2), [ 1.0,0,-5,0,3,0,9])
check("2.47c y3 = x1 (*) h2  [n = -2..4]", conv(p1,r2), [ 2.0,0,-6,0,-2,0,6])
check("2.47d y4 = x2 (*) h1  [n = -3..4]", conv(p2,r1), [-1.0,0,3,1.5,0,-3.5,0,-3])
report("2.47  start indices (-4, -1, -2, -3)",
       [q1+s1, q2+s2, q1+s2, q2+s1] == [-4,-1,-2,-3])

# -------------------------------------------------------------- 2.48
let ok = true
    for N in 6:14, M in 2:N-1
        xr = ones(N);      nxr = 0      # mu[n] - mu[n-N]
        hr = ones(M);      nhr = 0      # mu[n] - mu[n-M]
        gr = -ones(N-M);   ngr = M      # mu[n-N] - mu[n-M]
        wr = ones(N+M);    nwr = -M     # mu[n+M] - mu[n-N]
        ok &= peakis(conv(xr,xr), nxr+nxr, N,   N-1)
        ok &= peakis(conv(hr,hr), nhr+nhr, M,   M-1)
        ok &= peakis(conv(gr,gr), ngr+ngr, N-M, M+N-1)
        ok &= peakis(conv(wr,wr), nwr+nwr, N+M, N-M-1)
        ok &= plateauis(conv(xr,hr), nxr+nhr,  M,      M-1,   N-1)
        ok &= plateauis(conv(xr,gr), nxr+ngr, -(N-M),  N-1,   N+M-1)
        ok &= plateauis(conv(xr,wr), nxr+nwr,  N,      N-M-1, N-1)
    end
    report("2.48  peak values and locations (all N,M with 6<=N<=14)", ok)
end

# -------------------------------------------------------------- 2.51
check("2.51  period of cos(30 * pi/6 * n) is 2", [fper(30*pi/6)], [2])

# -------------------------------------------------------------- 2.52
check("2.52a r_xx  [l = -6..6]", xcorrseq(x,x)[1],
      [-9.0,15,2,-2,-21,-17,64,-17,-21,-2,2,15,-9])
check("2.52a r_yy  [l = -6..6]", xcorrseq(y,y)[1],
      [-40.0,2,-28,3,39,-5,139,-5,39,3,-28,2,-40])
check("2.52a r_ww  [l = -6..6]", xcorrseq(w,w)[1],
      [-6.0,23,-40,23,6,-50,88,-50,6,23,-40,23,-6])
check("2.52b r_xy  [l = -4..8]", xcorrseq(x,y)[1],
      [24.0,-38,10,29,-34,29,-22,34,-10,-34,-1,-2,15])
check("2.52b r_xw  [l = -10..2]", xcorrseq(x,w)[1],
      [18.0,-39,11,36,-39,36,-30,-6,14,-9,15,-10,3])

# -------------------------------------------------------------- 2.53
ae = 0.8;  ne = 0:400;  xe = ae .^ ne
re, lag = xcorrseq(xe, xe)
check("2.53a r[l] = a^|l| / (1-a^2)", re[abs.(lag) .<= 10],
      ae .^ abs.(-10:10) ./ (1 - ae^2), tol = 1e-6)
Nb = 9;  rb, _ = xcorrseq(ones(Nb), ones(Nb))
check("2.53b r[l] = N - |l|", rb, Nb .- abs.(-(Nb-1):(Nb-1)))

# -------------------------------------------------------------- 2.54
Mp = 4;  Np = 2*Mp;  xp1 = cos.(pi .* (0:Np-1) ./ Mp)
rp1 = [sum(xp1 .* circshift_seq(xp1, l)) / Np for l in 0:Np-1]
check("2.54a r~[l] = 0.5*cos(pi*l/M)", rp1,
      0.5 .* cos.(pi .* (0:Np-1) ./ Mp), tol = 1e-12)
xp2 = Float64.(mod.(0:5, 6))
rp2 = [sum(xp2 .* circshift_seq(xp2, l)) / 6 for l in 0:5]
check("2.54b r~[l] = [55 40 31 28 31 40]/6", rp2, [55.0,40,31,28,31,40] ./ 6, tol = 1e-12)
xp3 = Float64[(-1)^n for n in 0:1]
rp3 = [sum(xp3 .* circshift_seq(xp3, l)) / 2 for l in 0:1]
check("2.54c r~[l] = (-1)^l", rp3, [1.0,-1])

println("\n=== done ====================================================")
@printf("  %d/%d checks PASSED", PASS[], PASS[] + FAIL[])
FAIL[] > 0 && @printf("   (%d FAILED)", FAIL[])
println()
