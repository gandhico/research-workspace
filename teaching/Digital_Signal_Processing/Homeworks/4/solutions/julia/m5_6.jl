# M5.6  DFTs of two real sequences of equal length using a single DFT
#        Method of Section 5.9.1, Mitra 4th ed.   Run:  julia m5_6.jl
include("DFTUtils.jl")
using .DFTUtils
using Printf

println("=====  M 5.6  Two real DFTs from one complex DFT (Sec. 5.9.1)  =====\n")

cases = [
    ("(a)", [-3.0, 2, 4, -6, 1, 2], [ 2.0, -1, 3, -4, 5, 6]),
    ("(b)", [ 5.0, -4, -2, 6, 1, 3], [ 4.0, -5, 5,  1, -2, 3]),
]

for (tag, x, h) in cases
    N = length(x)
    X, H, Xc = dft2real(x, h)       # one complex DFT -> two real DFTs
    Xref, Href = dft(x), dft(h)     # reference: two separate DFTs

    @printf("%s  N = %d\n", tag, N)
    println("    x[n] = {", join(string.(Int.(x)), ", "), "}")
    println("    h[n] = {", join(string.(Int.(h)), ", "), "}")
    @printf("    packed x[n] + j*h[n]  ->  single %d-point DFT\n\n", N)
    println("     k |        Xc[k] (packed)      |          X[k] (DFT of x)     |          H[k] (DFT of h)")
    println("    ---+----------------------------+------------------------------+-----------------------------")
    for k in 0:N-1
        @printf("    %2d | %10.4f %+10.4fj | %10.4f %+10.4fj  | %10.4f %+10.4fj\n", k,
                real(Xc[k+1]), imag(Xc[k+1]),
                real(X[k+1]),  imag(X[k+1]),
                real(H[k+1]),  imag(H[k+1]))
    end
    eX = maximum(abs.(X .- Xref)); eH = maximum(abs.(H .- Href))
    @printf("\n    max error vs. dft(x): %.3e     vs. dft(h): %.3e   -->  %s\n\n\n",
            eX, eH, max(eX, eH) < 1e-10 ? "PASS" : "FAIL")
end
