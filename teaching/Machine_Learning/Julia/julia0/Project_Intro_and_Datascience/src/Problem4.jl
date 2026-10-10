# =====================================================================
# Problem4.jl
#
# Same structure as Problem1.jl: one problem, one submodule, pulled into the
# package by include("Problem4.jl") in Project_Intro_and_Datascience.jl.
# =====================================================================

module Problem4

    # Step one of two. Project_Intro_and_Datascience.jl must export lostCows
    # as well before you can call it from the REPL or from doc/.
    export lostCows

    function lostCows(fencePost::Vector{Vector{Float64}}, cowLocation::Vector{Vector{Float64}})

        return lostCow::Vector{Vector{Float64}}
    end
end # module Problem4
