# M5.2  Circular convolution via the DFT-based approach
#        Mitra 4th ed., Chapter 5.   Run:  julia m5_2.jl
include("DFTUtils.jl")
using .DFTUtils
using Printf

fmt(z::Real)    = @sprintf("%g", z)
fmt(z::Complex) = abs(imag(z)) < 1e-12 ? @sprintf("%g", real(z)) :
                                         @sprintf("%g%+gj", real(z), imag(z))
seqstr(v) = "{ " * join(fmt.(v), ", ") * " }"

println("=========  M 5.2  Circular convolution via the DFT  =========\n")

n5 = 0:4
cases = [
    ("(a)", [3.0, 2, -2, 1, 0, 1],
            [-5.0, -1, 3, -2, 4, 4]),
    ("(b)", ComplexF64[3-2im, 4-1im, -2+3im, 0+1im, 0],
            ComplexF64[1-3im, -2-1im, 2+2im, 3, -2+4im]),
    ("(c)", cos.(π .* n5 ./ 2),
            3.0 .^ n5),
]

for (tag, g, h) in cases
    N  = length(g)
    yd = circconv_dft(g, h)     # DFT based
    yt = circonv(g, h)          # direct, time domain
    err = maximum(abs.(yd .- yt))
    @printf("%s  N = %d\n", tag, N)
    println("    g[n] = ", seqstr(g))
    println("    h[n] = ", seqstr(h))
    println("    y[n] = ", seqstr(round.(yd, digits = 10)), "   (DFT based)")
    @printf("    max |y_dft - y_circonv| = %.3e   -->  %s\n\n",
            err, err < 1e-10 ? "PASS" : "FAIL")
end
