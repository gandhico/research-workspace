module Problem4
    
    using Statistics
    export multivariate

    # Multiple regression Ŷ = a + b₁𝐗₁ + b₂𝐗₂
    # Solves the normal equations of the centred problem
    #   b₁(x₁⋅x₁) + b₂(x₁⋅x₂) = x₁⋅y
    #   b₁(x₂⋅x₁) + b₂(x₂⋅x₂) = x₂⋅y
    # in closed form, then a = Ȳ - b₁X̄₁ - b₂X̄₂
    function multivariate(𝐗₁::Vector{Float64}, 𝐗₂::Vector{Float64}, 𝐘::Vector{Float64})
        
        if !(length(𝐗₁) == length(𝐗₂) == length(𝐘))
            error("𝐗₁, 𝐗₂ and 𝐘 must have the same length")
        end

        X̄₁ = mean(𝐗₁)
        X̄₂ = mean(𝐗₂)
        Ȳ  = mean(𝐘)

        # centred variables
        𝐱₁ = 𝐗₁ .- X̄₁
        𝐱₂ = 𝐗₂ .- X̄₂
        𝐲  = 𝐘  .- Ȳ

        # dot products appearing in the normal equations
        s₁₁ = sum(𝐱₁ .* 𝐱₁)
        s₂₂ = sum(𝐱₂ .* 𝐱₂)
        s₁₂ = sum(𝐱₁ .* 𝐱₂)
        s₁y = sum(𝐱₁ .* 𝐲)
        s₂y = sum(𝐱₂ .* 𝐲)

        D = s₁₁*s₂₂ - s₁₂^2
        if D == 0
            error("𝐗₁ and 𝐗₂ are collinear; the normal equations are singular")
        end

        b₁ = (s₁y*s₂₂ - s₂y*s₁₂) / D
        b₂ = (s₂y*s₁₁ - s₁y*s₁₂) / D
        a  = Ȳ - b₁*X̄₁ - b₂*X̄₂

        return a::Float64, b₁::Float64, b₂::Float64
    end 

end
