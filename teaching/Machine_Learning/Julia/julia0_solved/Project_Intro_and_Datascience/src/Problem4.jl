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
        length(fencePost) == 4 || throw(ArgumentError("Exactly four fence posts are required."))

        center = reduce(+, fencePost) ./ length(fencePost)
        ordered_posts = sort(fencePost; by = p -> atan(p[2] - center[2], p[1] - center[1]))

        cross2d(a, b, p) = (b[1] - a[1]) * (p[2] - a[2]) -
                           (b[2] - a[2]) * (p[1] - a[1])
        function inside(point)
            sides = [cross2d(ordered_posts[i], ordered_posts[mod1(i + 1, 4)], point) for i in 1:4]
            return all(sides .>= -eps(Float64)) || all(sides .<= eps(Float64))
        end

        lostCow = [cow for cow in cowLocation if !inside(cow)]
        return lostCow::Vector{Vector{Float64}}
    end
end # module Problem4
