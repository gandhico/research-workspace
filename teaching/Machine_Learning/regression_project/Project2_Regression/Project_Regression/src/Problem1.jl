module Problem1

    export noisyLinearMultiDim

    # Draws N samples of an m-dimensional noisy linear data set
    #   𝐗[n,j] ~ U(0,1)
    #   Ŷ[n]   = a + b₁𝐗[n,1] + ... + bₘ𝐗[n,m] + 𝒩(0,σ²)
    # σ² is the noise variance, so the noise is scaled by √σ²
    function noisyLinearMultiDim(N::Integer, a::Float64 , b::Vector{Float64}; σ²=0.001)

        m = length(b)

        # inputs drawn uniformly on [0,1), one row per sample
        𝐗 = rand(N, m)

        # clean linear part: a + 𝐗b, then add Gaussian noise
        Ŷ = a .+ 𝐗*b .+ sqrt(σ²) .* randn(N)

        return 𝐗::Matrix{Float64},Ŷ::Vector{Float64}
    end
    
end
