module Problem3

    using Statistics
    export bivariate

    # Bivariate regression Ŷ = a + b𝐗 (subject-space formulation)
    #   centre the data:  x = 𝐗 - X̄,  y = 𝐘 - Ȳ
    #   project y on x:   b = (x⋅y)/‖x‖²
    #   recover offset:   a = Ȳ - bX̄
    function bivariate(𝐗::Vector{Float64}, 𝐘::Vector{Float64})

        if length(𝐗) != length(𝐘)
            error("𝐗 and 𝐘 must have the same length")
        end

        X̄ = mean(𝐗)
        Ȳ = mean(𝐘)

        # centred variables
        𝐱 = 𝐗 .- X̄
        𝐲 = 𝐘 .- Ȳ

        b = sum(𝐱 .* 𝐲) / sum(𝐱 .* 𝐱)
        a = Ȳ - b*X̄

        return a::Float64, b::Float64
    end 

end

