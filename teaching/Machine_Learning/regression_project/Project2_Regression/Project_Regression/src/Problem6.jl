module Problem6    
    
    using LinearAlgebra
    export polyfitRegLS

    # Regularized least squares polynomial regression (Algorithm 2)
    #   𝚽[n,m+1] = 𝐗[n]^m,  m = 0,…,M
    #   𝐰 = (λ𝐈 + 𝚽ᴴ𝚽)⁻¹𝚽ᴴ𝐘
    function polyfitRegLS(𝐗::Vector{Float64}, 𝐘::Vector{Float64}, M::Integer, λ::Float64)
        N = length(𝐗)
        if N<M; error("M must be less than the length of 𝐗"); end
        𝚽 = zeros(N,M+1)

        # build the design (Vandermonde) matrix column by column
        for m in 0:M
            𝚽[:,m+1] = 𝐗.^m
        end

        # solve (λ𝐈 + 𝚽ᴴ𝚽)𝐰 = 𝚽ᴴ𝐘 directly instead of forming the inverse
        𝐀 = λ*I + 𝚽'*𝚽
        𝐰 = 𝐀 \ (𝚽'*𝐘)

        return 𝐰::Vector{Float64}
    end

end
