module Problem1

    export histo

    # bold X /= ordinary x
    function histo(𝐱::Vector, B::Integer)

        # \bfx (bold x)
        # x \_m \_i \_n
        xₘᵢₙ  = minimum(𝐱)
        xₘₐₓ = maximum(𝐱)

        bₙ = range(xₘᵢₙ,xₘₐₓ,length=B)

        hᵢ = zeros(B)

        for m in 1:length(𝐱)
            eₙ = zeros(B)
            for n in 1:B 
                eₙ[n]=abs(bₙ[n]- 𝐱[m])
            end
            i = argmin(eₙ)
            hᵢ[i] += 1
        end 

        return bₙ::StepRangeLen,hᵢ::Vector{Float64}
    end

end