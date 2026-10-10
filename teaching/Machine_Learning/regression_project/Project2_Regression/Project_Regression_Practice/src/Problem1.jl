module Problem1

    export noisyLinearMultiDim

    function noisyLinearMultiDim(N::Int, a::Float64,b::Vector{Float64},σ²=0.001)

        m = length(b)

        X = randn(N, m)
        ϵ = sqrt(σ²) * randn(N)
        Ŷ = a .+ X * b .+ ϵ

        return X::Matrix{Float64}, Ŷ::Vector{Float64}
    end

end