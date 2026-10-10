module Problem2

    export noisySin

    # Draws N samples of the 1-D noisy sinusoid
    #   𝐗[n] ~ U(0,1)
    #   𝐘[n] = sin(2π𝐗[n]) + 𝒩(0,σ²)
    function noisySin(N::Integer;σ²=0.09)

        𝐗 = rand(N)
        𝐘 = sin.(2π .* 𝐗) .+ sqrt(σ²) .* randn(N)

        return 𝐗::Vector{Float64},𝐘::Vector{Float64}
    end

end
