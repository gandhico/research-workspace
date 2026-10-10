module Problem5    
    
    using LinearAlgebra:pinv
    export polyfitLS

    # Least squares polynomial regression (Algorithm 1)
    #   𝚽[n,m+1] = 𝐗[n]^m,  m = 0,…,M
    #   𝐰 = (𝚽ᴴ𝚽)⁻¹𝚽ᴴ𝐘 = 𝚽†𝐘
    function polyfitLS(𝐗::Vector{Float64}, 𝐘::Vector{Float64}, M::Integer)
        N = length(𝐗)
        if N<M; error("M must be less than the length of 𝐗"); end
        𝚽 = zeros(N,M+1)

        # build the design (Vandermonde) matrix column by column
        for m in 0:M
            𝚽[:,m+1] = 𝐗.^m
        end

        # 𝚽† = (𝚽ᴴ𝚽)⁻¹𝚽ᴴ; pinv computes it through the SVD, which is
        # numerically safer than inverting 𝚽ᴴ𝚽 when M is large
        𝐰 = pinv(𝚽)*𝐘

        return 𝐰::Vector{Float64}
    end

end
