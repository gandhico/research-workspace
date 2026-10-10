"""
    DFTUtils

Self-contained DFT utilities for Mitra, *Digital Signal Processing*, 4th ed.,
Chapter 5.  No external packages: the DFT is evaluated directly from its
definition so the code runs on a bare Julia install.

Conventions follow the book exactly:

    W_N = exp(-j2π/N)
    X[k] = Σ_{n=0}^{N-1} x[n] W_N^{nk}          (5.11)  forward DFT
    x[n] = (1/N) Σ_{k=0}^{N-1} X[k] W_N^{-nk}   (5.12)  inverse DFT

All sequences are 1-based Julia vectors whose first element is the n = 0
sample, so `x[n+1]` in code is `x[n]` in the book.
"""
module DFTUtils

export dft, idft, circconv_dft, circonv, dft2real, cshift, circidx

"""
    dft(x) -> X

N-point DFT of `x`, evaluated from the definition (5.11).
"""
function dft(x::AbstractVector)
    N = length(x)
    W = cis(-2π / N)                       # cis(θ) = exp(jθ)
    X = zeros(ComplexF64, N)
    for k in 0:N-1, n in 0:N-1
        X[k+1] += x[n+1] * W^(n * k)
    end
    return X
end

"""
    idft(X) -> x

N-point inverse DFT of `X`, evaluated from the definition (5.12).
"""
function idft(X::AbstractVector)
    N = length(X)
    W = cis(-2π / N)
    x = zeros(ComplexF64, N)
    for n in 0:N-1, k in 0:N-1
        x[n+1] += X[k+1] * W^(-n * k)
    end
    return x ./ N
end

"""
    circidx(n, N) -> i

1-based Julia index of the sample `x[<n>_N]`, i.e. `mod(n, N) + 1`.
"""
circidx(n::Integer, N::Integer) = mod(n, N) + 1

"""
    cshift(x, n0) -> y

Circular shift `y[n] = x[<n - n0>_N]` (right shift for `n0 > 0`).
"""
cshift(x::AbstractVector, n0::Integer) =
    [x[circidx(n - n0, length(x))] for n in 0:length(x)-1]

"""
    circconv_dft(g, h) -> y

N-point circular convolution `g[n] ⊛ h[n]` computed with the DFT-based
approach of Table 5.3:  `y = IDFT{ DFT(g) .* DFT(h) }`.

Solution to Problem **M5.2**.  Real inputs give a real result (the round-off
imaginary part is discarded).
"""
function circconv_dft(g::AbstractVector, h::AbstractVector)
    length(g) == length(h) ||
        throw(DimensionMismatch("sequences must have equal length " *
                                "(g: $(length(g)), h: $(length(h)))"))
    y = idft(dft(g) .* dft(h))
    return (eltype(g) <: Real && eltype(h) <: Real) ? real.(y) : y
end

"""
    circonv(x, h) -> y

N-point circular convolution evaluated directly in the time domain,

    y[n] = Σ_{m=0}^{N-1} x[m] h[<n-m>_N],

used as the independent check on [`circconv_dft`](@ref).
"""
function circonv(x::AbstractVector, h::AbstractVector)
    N = length(x)
    N == length(h) ||
        throw(DimensionMismatch("sequences must have equal length " *
                                "(x: $N, h: $(length(h)))"))
    T = promote_type(eltype(x), eltype(h))
    y = zeros(T, N)
    for n in 0:N-1, m in 0:N-1
        y[n+1] += x[m+1] * h[circidx(n - m, N)]
    end
    return y
end

"""
    dft2real(g, h) -> (G, H, X)

N-point DFTs of **two real** length-N sequences from a **single** N-point DFT,
by the method of Section 5.9.1:

    x[n] = g[n] + j h[n]                                    (5.116)
    G[k] = ( X[k] + conj(X[<-k>_N]) ) / 2                   (5.117)
    H[k] = ( X[k] - conj(X[<-k>_N]) ) / (2j)                (5.118)

Solution to Problem **M5.6**.  Also returns the packed DFT `X[k]`.
"""
function dft2real(g::AbstractVector{<:Real}, h::AbstractVector{<:Real})
    N = length(g)
    N == length(h) ||
        throw(DimensionMismatch("sequences must have equal length " *
                                "(g: $N, h: $(length(h)))"))
    x = complex.(float.(g), float.(h))          # (5.116)
    X = dft(x)                                   #  ONE N-point DFT
    Xr = [conj(X[circidx(-k, N)]) for k in 0:N-1]   # conj(X[<-k>_N])
    G = (X .+ Xr) ./ 2                           # (5.117)
    H = (X .- Xr) ./ (2im)                       # (5.118)
    return G, H, X
end

end # module
