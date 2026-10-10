module Problem3

using LinearAlgebra

export compDistInd

"""
    compDistInd(x, centers)

Compute the Euclidean distance from every data point to every center and
return `(d, r)`. Row `n` of `r` contains exactly one `true` value: the
index of the closest center to `x[n]`. Ties are resolved in favor of the
lowest-index center, matching Julia's `argmin` convention.
"""
function compDistInd(
    x::Vector{Vector{Float64}},
    centers::Vector{Vector{Float64}},
)
    isempty(centers) && throw(ArgumentError("at least one center is required"))

    dimension = length(first(centers))
    dimension > 0 || throw(ArgumentError("points must have at least one dimension"))
    all(length(point) == dimension for point in x) ||
        throw(DimensionMismatch("all data points must have the same dimension as the centers"))
    all(length(center) == dimension for center in centers) ||
        throw(DimensionMismatch("all centers must have the same dimension"))
    all(all(isfinite, point) for point in x) ||
        throw(ArgumentError("data points must contain only finite values"))
    all(all(isfinite, center) for center in centers) ||
        throw(ArgumentError("centers must contain only finite values"))

    number_of_points = length(x)
    number_of_centers = length(centers)
    distances = Matrix{Float64}(undef, number_of_points, number_of_centers)
    indicators = falses(number_of_points, number_of_centers)

    @inbounds for n in 1:number_of_points
        closest_center = 1
        closest_squared_distance = Inf

        for k in 1:number_of_centers
            squared_distance = 0.0
            for coordinate in 1:dimension
                difference = x[n][coordinate] - centers[k][coordinate]
                squared_distance = muladd(difference, difference, squared_distance)
            end

            distances[n, k] = sqrt(squared_distance)
            if squared_distance < closest_squared_distance
                closest_squared_distance = squared_distance
                closest_center = k
            end
        end

        indicators[n, closest_center] = true
    end

    return distances, indicators
end

end
