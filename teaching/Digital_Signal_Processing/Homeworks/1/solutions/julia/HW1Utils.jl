"""
    HW1Utils

Time-domain sequence utilities for Mitra, *Digital Signal Processing:
A Computer-Based Approach*, 4th ed., Chapter 2.

Dependency-free: everything is built from base Julia, so these run on a bare
install.  Julia port of the helper set in `matlab/hw1_verify_all.m`.

All sequences are 1-based Julia vectors paired with the time index `n0` of
their first sample, so `s[i]` in code is `s[n0 + i - 1]` in the book.
"""
module HW1Utils

export conv, deconv_causal, embed, evenodd, perext, fper, lcmv,
       stepcoef, xcorrseq, peakis, plateauis, circshift_seq

"""
    conv(a, b) -> c

Linear convolution, `c[n] = Σ_k a[k] b[n-k]`, from the definition.
Length `length(a) + length(b) - 1` (Problem 2.5).
"""
function conv(a::AbstractVector, b::AbstractVector)
    La, Lb = length(a), length(b)
    T = promote_type(eltype(a), eltype(b), Float64)
    c = zeros(T, La + Lb - 1)
    for i in 1:La, j in 1:Lb
        c[i+j-1] += a[i] * b[j]
    end
    return c
end

"""
    deconv_causal(y, h) -> x

Solve `h ⊛ x = y` for a causal `x` by forward substitution (Problem 2.15):

    x[0] = y[0]/h[0]
    x[n] = ( y[n] - Σ_{k=1..n} h[k] x[n-k] ) / h[0]
"""
function deconv_causal(y::AbstractVector, h::AbstractVector)
    L = length(y) - length(h) + 1
    x = zeros(promote_type(eltype(y), eltype(h), Float64), L)
    for n in 1:L
        acc = y[n]
        for k in 2:min(n, length(h))
            acc -= h[k] * x[n-k+1]
        end
        x[n] = acc / h[1]
    end
    return x
end

"""
    embed(s, n0, lo, hi) -> v

Place the sequence `s` (first sample at index `n0`) into a zero vector
spanning `lo:hi`.
"""
function embed(s::AbstractVector, n0::Integer, lo::Integer, hi::Integer)
    v = zeros(promote_type(eltype(s), Float64), hi - lo + 1)
    v[n0-lo+1 : n0-lo+length(s)] .= s
    return v
end

"""
    evenodd(s, n0) -> (ev, od, nn)

Even and odd parts, `s_ev[n] = ½(s[n]+s[-n])`, `s_od[n] = ½(s[n]-s[-n])`,
returned on the symmetric index range `nn` (Problem 2.20).
"""
function evenodd(s::AbstractVector, n0::Integer)
    L  = max(abs(n0), abs(n0 + length(s) - 1))
    nn = -L:L
    f  = embed(s, n0, -L, L)
    return (f .+ reverse(f)) ./ 2, (f .- reverse(f)) ./ 2, nn
end

"""
    perext(s, n0, N) -> p

One period (`n = 0 … N-1`) of the `N`-periodic extension
`s̃[n] = Σ_k s[n+kN]` (Problem 2.37):  fold each sample to `n mod N` and add.
"""
function perext(s::AbstractVector, n0::Integer, N::Integer)
    p = zeros(promote_type(eltype(s), Float64), N)
    for i in 1:length(s)
        p[mod(n0 + i - 1, N) + 1] += s[i]
    end
    return p
end

"""
    fper(w) -> N

Fundamental period of `exp(j w n)`: the smallest `N > 0` with `wN = 2πr`,
i.e. the denominator of `w/2π` in lowest terms.  Returns 1 for `w = 0`.
"""
function fper(w::Real)
    r = rationalize(w / (2π), tol = 1e-12)
    return numerator(r) == 0 ? 1 : denominator(r)
end

"LCM of a collection of periods (Eq. 2.32)."
lcmv(v) = foldl(lcm, v)

"""
    stepcoef(s) -> c

Coefficients of the delayed unit steps representing `s`: the first
differences, `c[k] = s[k] - s[k-1]` (Problem 2.43b).
"""
stepcoef(s::AbstractVector) = diff(vcat(0, collect(s), 0))

"""
    xcorrseq(a, b) -> (r, lag)

Linear cross-correlation `r_ab[ℓ] = Σ_n a[n] b[n-ℓ]`, computed as
`a ⊛ b[-n]` (Problem 2.52).  `lag` gives the corresponding ℓ values when
both sequences start at `n = 0`.
"""
function xcorrseq(a::AbstractVector, b::AbstractVector)
    r   = conv(a, reverse(b))
    lag = -(length(b) - 1) : (length(a) - 1)
    return r, lag
end

"True if the maximum of `c` (first sample at `n0`) equals `val` at index `loc`."
function peakis(c::AbstractVector, n0::Integer, val, loc)
    m, k = findmax(c)
    return abs(m - val) < 1e-9 && (k - 1 + n0) == loc
end

"True if `c` holds the constant `val` over `lo:hi` and `val` is its extreme."
function plateauis(c::AbstractVector, n0::Integer, val, lo, hi)
    idx = (lo:hi) .- n0 .+ 1
    return all(abs.(c[idx] .- val) .< 1e-9) &&
           abs(maximum(abs.(c)) - abs(val)) < 1e-9
end

"Circular shift of one period: `y[n] = x[⟨n-ℓ⟩_N]`."
circshift_seq(x::AbstractVector, l::Integer) =
    [x[mod(n - l, length(x)) + 1] for n in 0:length(x)-1]

end # module
