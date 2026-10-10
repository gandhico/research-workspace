module Problem5

using LinearAlgebra
using Random

export myKmeansOnline

@inline function squared_distance(a::Vector{Float64}, b::Vector{Float64})
    value = 0.0
    @inbounds for coordinate in eachindex(a)
        difference = a[coordinate] - b[coordinate]
        value = muladd(difference, difference, value)
    end
    return value
end

"""
    myKmeansOnline(x, initial_centers, eta; maxIter=100, tol=1e-5, verbose=true)

Run online K-means. The sample order is shuffled at the beginning of every
epoch, and convergence is declared when the maximum Euclidean movement of
any centroid during an epoch is no greater than `tol`.
"""
function myKmeansOnline(
    x::Vector{Vector{Float64}},
    initial_centers::Vector{Vector{Float64}},
    eta::Real;
    maxIter::Integer=100,
    tol::Real=1e-5,
    verbose::Bool=true,
)
    isempty(x) && throw(ArgumentError("at least one data point is required"))
    isempty(initial_centers) && throw(ArgumentError("at least one center is required"))
    maxIter > 0 || throw(ArgumentError("maxIter must be positive"))
    isfinite(eta) && 0 < eta <= 1 || throw(ArgumentError("eta must be in (0, 1]"))
    isfinite(tol) && tol >= 0 || throw(ArgumentError("tol must be finite and nonnegative"))

    dimension = length(first(x))
    dimension > 0 || throw(ArgumentError("points must have at least one dimension"))
    all(length(point) == dimension for point in x) ||
        throw(DimensionMismatch("all data points must have the same dimension"))
    all(length(center) == dimension for center in initial_centers) ||
        throw(DimensionMismatch("all centers must have the same dimension as the data"))
    all(all(isfinite, point) for point in x) ||
        throw(ArgumentError("data points must contain only finite values"))
    all(all(isfinite, center) for center in initial_centers) ||
        throw(ArgumentError("centers must contain only finite values"))

    centers = [copy(center) for center in initial_centers]
    order = collect(eachindex(x))
    epoch = 0

    for current_epoch in 1:maxIter
        epoch = current_epoch
        old_centers = [copy(center) for center in centers]
        shuffle!(order)

        @inbounds for n in order
            closest_center = 1
            closest_distance = squared_distance(x[n], centers[1])
            for k in 2:length(centers)
                candidate_distance = squared_distance(x[n], centers[k])
                if candidate_distance < closest_distance
                    closest_distance = candidate_distance
                    closest_center = k
                end
            end

            for coordinate in 1:dimension
                centers[closest_center][coordinate] +=
                    eta * (x[n][coordinate] - centers[closest_center][coordinate])
            end
        end

        maximum_shift = maximum(norm(centers[k] - old_centers[k]) for k in eachindex(centers))
        verbose && println("Epoch $epoch: maximum centroid shift = $maximum_shift")
        maximum_shift <= tol && break
    end

    verbose && println("Final centers: ", centers)
    return centers, epoch
end

end
