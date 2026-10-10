# Project Unsupervised Learning — Video Explanation Speech

**Estimated length:** 7–9 minutes

The italicized sentences are screen directions and should not be read aloud.

## Introduction

*Share the screen and open the `src` folder.*

Hello. In this video, I will answer the three questions about my implementations for Problems 2 through 5. I will explain what the `circGauss` function does and returns, how the `compDistInd` function works and what its outputs mean, and then the similarities and differences between `myKmeansBatch` and `myKmeansOnline`.

## Question 1 — Problem 2

> Explain your `circGauss` function and what is being returned.

*Open `Problem2.jl` and point to the `circGauss` function.*

My `circGauss` function generates random observations from a circular multivariate Gaussian distribution.

The function receives three inputs. `N` is the number of observations to generate. `μ` is the mean vector, and its length determines the number of dimensions. `σ²` is the variance used in every dimension.

*Point to the input-validation lines.*

First, the function checks that `N` is not negative. It also checks that the variance is finite and nonnegative. A variance of zero is valid; it means every generated observation will be equal to the mean vector.

*Point to `D = length(μ)` and the allocation of `X`.*

Next, `D` is set equal to the length of the mean vector. The function then allocates `X`, which will contain `N` observations. Each observation is stored as a vector of `Float64` values.

*Point to the `for` loop and the expression that generates each observation.*

Inside the loop, `randn(D)` generates a vector of `D` independent standard-normal values. Each value initially has mean zero and variance one. The vector is multiplied by `sqrt(σ²)`, which is the standard deviation, and then the mean vector `μ` is added coordinate by coordinate.

The formula implemented by this line is

\[
x_n = \mu + \sqrt{\sigma^2}z_n,
\]

where \(z_n\) is a standard Gaussian random vector. Because the same variance is applied in every direction and the coordinates are independent, the distribution is circular in two dimensions, or spherical in higher dimensions.

*Point to the return statement.*

The function returns `X`. Its type is `Vector{Vector{Float64}}`. The outer vector has `N` entries, and each inner vector has `D` coordinates. In other words, the returned value is the complete generated dataset: `N` random, `D`-dimensional observations centered around `μ` with variance `σ²` in every direction.

## Question 2 — Problem 3

> Explain how your `compDistInd` function works and what the output is.

*Open `Problem3.jl` and point to the `compDistInd` function signature.*

My `compDistInd` function compares every observation with every cluster center. It calculates all pairwise Euclidean distances and also identifies the nearest center for each observation.

The function receives `x`, which contains the observations, and `centers`, which contains the candidate cluster centers.

*Point to the validation block.*

The function first verifies that there is at least one center, that the vectors have at least one dimension, and that all observations and centers have the same dimensionality. It also verifies that all coordinates are finite. These checks prevent invalid distance calculations.

*Point to `num_data`, `num_centers`, `distances`, and `indicators`.*

The function calculates the number of observations, `N`, and the number of centers, `K`. It then creates two `N`-by-`K` matrices. `distances` stores numerical Euclidean distances. `indicators` is a Boolean matrix initially filled with `false`.

*Point to the nested loops.*

The outer loop processes one observation at a time. For each observation, the function starts by treating center 1 as the current closest center and sets the best squared distance to infinity.

The next loop checks every center. The innermost loop goes through every coordinate, subtracts the center coordinate from the observation coordinate, squares that difference, and adds it to a running total. The code uses `muladd` to compute the squared difference plus the current total efficiently.

After all coordinates have been processed, the square root of the total is stored in the distance matrix. Therefore, `distances[n, k]` is the Euclidean distance between observation `n` and center `k`.

The function compares squared distances when selecting the closest center. Taking a square root is unnecessary for that comparison because the square-root function preserves the ordering of nonnegative values.

If the current center has a strictly smaller squared distance, its index becomes the new closest-center index. Because the comparison is strictly less than, a tie does not replace an earlier center. Therefore, if two centers are equally close, the center with the lower index is selected.

*Point to `indicators[n, closest_center] = true`.*

After all centers have been checked, the entry corresponding to the selected center is changed to `true`. All other entries in that row remain `false`. Consequently, each row of the indicator matrix contains exactly one `true` value.

*Point to the return statement.*

The function returns two outputs: `distances` and `indicators`. `distances` is an `N`-by-`K` matrix containing every observation-to-center Euclidean distance. `indicators` is an `N`-by-`K` one-hot Boolean matrix showing the nearest center assigned to each observation.

## Question 3 — Problems 4 and 5

> What are the similarities and differences between the `myKmeansBatch` and `myKmeansOnline` functions?

*Place `Problem4.jl` and `Problem5.jl` side by side if possible.*

The two functions have the same overall goal: they divide the observations into clusters by repeatedly finding the nearest center and updating the center locations.

Both functions accept a dataset and a set of initial centers. Both copy the initial centers so that the original input is not changed. They validate the dimensions and numerical values, use squared Euclidean distance to find the nearest center, and use a strict comparison, so distance ties favor the lower-indexed center. They also both stop when the maximum center movement is within a specified tolerance or when the maximum number of iterations is reached.

The most important difference is how and when they update the centers.

*Point to the assignment and mean-update sections in `myKmeansBatch`.*

In `myKmeansBatch`, all observations are first assigned using the same fixed set of old centers. After every observation has been assigned, the function calculates a new center for each cluster by taking the exact mean of all observations assigned to that cluster. Therefore, every center is updated once per iteration, after the complete dataset has been processed.

The batch function also explicitly handles empty clusters. If a center receives no observations, it is replaced with a distinct observation that is far from the current centers. After convergence, the function assigns the data one final time using the final centers and creates the Boolean indicator matrix.

The batch function returns three values: the final centers, the final one-hot indicator matrix, and the number of iterations performed.

*Point to the shuffled order and immediate update in `myKmeansOnline`.*

In `myKmeansOnline`, the observations are shuffled at the beginning of each epoch. The function processes them one at a time. As soon as the nearest center for an observation is found, that center is updated immediately using

\[
c \leftarrow c + \eta(x-c).
\]

Here, `η`, or `eta`, is the learning rate. This equation moves the center a fraction `eta` of the distance toward the current observation. A smaller `eta` produces gradual movement, while an `eta` of one moves the center directly to the current observation.

Because each update happens immediately, later observations in the same epoch see centers that have already changed. This makes the online result dependent on the order of the observations, which is why the code shuffles their order. In contrast, the batch assignments within one iteration are all based on the same unchanged centers.

The online function does not calculate an exact cluster mean, does not build a final indicator matrix, and does not use the batch function's empty-cluster replacement. A center that is never selected during an epoch simply remains unchanged. The online function returns two values: the final centers and the number of completed epochs.

In summary, the similarities are that both methods use initial centers, nearest-center assignments, squared Euclidean distance, a convergence tolerance, and a maximum iteration limit. The key difference is that batch K-means updates each center using all assigned observations at once, whereas online K-means updates a center immediately after each individual observation. Batch K-means returns centers, assignments, and an iteration count; online K-means returns centers and an epoch count and introduces the additional learning-rate parameter `eta`.

## Closing

That concludes my explanation of `circGauss`, the outputs of `compDistInd`, and the similarities and differences between my batch and online K-means implementations.
