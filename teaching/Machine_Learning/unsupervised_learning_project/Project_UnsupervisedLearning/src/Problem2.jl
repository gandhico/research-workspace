module Problem2

    using Random: randn
    export circGauss

    function circGauss(N::Integer,μ::Vector{Float64},σ²::Float64)
        N >= 0 || throw(ArgumentError("N must be nonnegative"))
        isfinite(σ²) && σ² >= 0 || throw(ArgumentError("σ² must be finite and nonnegative"))

        D = length(μ)

        X = Vector{Vector{Float64}}(undef, N)
        
        for n in 1:N
            X[n] = μ .+ sqrt(σ²) * randn(D)
        end

        return X::Vector{Vector{Float64}}
    end

end
