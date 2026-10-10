module Problem4

using LinearAlgebra

export myKmeansBatch

@inline function squared_distance(a::Vector{Float64}, b::Vector{Float64})
    value = 0.0
    @inbounds for coordinate in eachindex(a)
        difference = a[coordinate] - b[coordinate]
        value = muladd(difference, difference, value)
    end
    return value
end

function validate_inputs(
    x::Vector{Vector{Float64}},
    centers::Vector{Vector{Float64}},
    maxIter::Integer,
    tol::Real,
)
    isempty(x) && throw(ArgumentError("at least one data point is required"))
    isempty(centers) && throw(ArgumentError("at least one center is required"))
    maxIter > 0 || throw(ArgumentError("maxIter must be positive"))
    isfinite(tol) && tol >= 0 || throw(ArgumentError("tol must be finite and nonnegative"))

    dimension = length(first(x))
    dimension > 0 || throw(ArgumentError("points must have at least one dimension"))
    all(length(point) == dimension for point in x) ||
        throw(DimensionMismatch("all data points must have the same dimension"))
    all(length(center) == dimension for center in centers) ||
        throw(DimensionMismatch("all centers must have the same dimension as the data"))
    all(all(isfinite, point) for point in x) ||
        throw(ArgumentError("data points must contain only finite values"))
    all(all(isfinite, center) for center in centers) ||
        throw(ArgumentError("centers must contain only finite values"))

    return dimension
end

function assign_points!(
    assignments::Vector{Int},
    x::Vector{Vector{Float64}},
    centers::Vector{Vector{Float64}},
)
    @inbounds for n in eachindex(x)
        closest_center = 1
        closest_distance = squared_distance(x[n], centers[1])
        for k in 2:length(centers)
            candidate_distance = squared_distance(x[n], centers[k])
            if candidate_distance < closest_distance
                closest_distance = candidate_distance
                closest_center = k
            end
        end
        assignments[n] = closest_center
    end
    return assignments
end

function farthest_distinct_point(
    x::Vector{Vector{Float64}},
    centers::Vector{Vector{Float64}},
    used_points::BitVector,
)
    best_index = 0
    best_distance = -Inf

    @inbounds for n in eachindex(x)
        used_points[n] && continue
        any(center == x[n] for center in centers) && continue

        nearest_distance = minimum(squared_distance(x[n], center) for center in centers)
        if nearest_distance > best_distance
            best_distance = nearest_distance
            best_index = n
        end
    end

    return best_index
end

"""
    myKmeansBatch(x, initial_centers; maxIter=100, tol=1e-8, verbose=true)

Run batch K-means without using a clustering package. Empty clusters are
reinitialized to the currently worst-represented distinct data point. The
returned indicator matrix corresponds to the returned final centers.
"""
function myKmeansBatch(
    x::Vector{Vector{Float64}},
    initial_centers::Vector{Vector{Float64}};
    maxIter::Integer=100,
    tol::Real=1e-8,
    verbose::Bool=true,
)
    dimension = validate_inputs(x, initial_centers, maxIter, tol)
    centers = [copy(center) for center in initial_centers]

    number_of_points = length(x)
    number_of_centers = length(centers)
    assignments = zeros(Int, number_of_points)
    iteration = 0

    for current_iteration in 1:maxIter
        iteration = current_iteration
        old_centers = [copy(center) for center in centers]
        assign_points!(assignments, x, old_centers)

        sums = [zeros(Float64, dimension) for _ in 1:number_of_centers]
        counts = zeros(Int, number_of_centers)
        @inbounds for n in eachindex(x)
            cluster = assignments[n]
            counts[cluster] += 1
            for coordinate in 1:dimension
                sums[cluster][coordinate] += x[n][coordinate]
            end
        end

        for k in 1:number_of_centers
            if counts[k] > 0
                inverse_count = 1.0 / counts[k]
                @inbounds for coordinate in 1:dimension
                    centers[k][coordinate] = sums[k][coordinate] * inverse_count
                end
            end
        end

        # Move an empty cluster to a distinct point that is currently poorly
        # represented. This avoids division by zero and preserves K centers.
        used_points = falses(number_of_points)
        for k in 1:number_of_centers
            counts[k] > 0 && continue
            point_index = farthest_distinct_point(x, centers, used_points)
            if point_index != 0
                centers[k] = copy(x[point_index])
                used_points[point_index] = true
            end
        end

        maximum_shift = maximum(norm(centers[k] - old_centers[k]) for k in 1:number_of_centers)
        verbose && println("Iteration $iteration: maximum centroid shift = $maximum_shift")
        maximum_shift <= tol && break
    end

    assign_points!(assignments, x, centers)
    indicators = falses(number_of_points, number_of_centers)
    @inbounds for n in eachindex(assignments)
        indicators[n, assignments[n]] = true
    end

    verbose && println("Final centers: ", centers)
    return centers, indicators, iteration
end

end
