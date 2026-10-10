# Project Regression: Video Explanation Script

**Target length:** 7 to 9 minutes (the requirement is 5 to 10).

Lines in *italics* are screen directions. Don't read them aloud.

If Canvas lists specific questions for the video, answer those first; the sections below are
ordered so each one can stand alone.

---

## 1. Introduction (about 30 s)

*Open the project folder in VS Code and show the `src` folder with `Problem1.jl` to `Problem6.jl`.*

Hello. In this video I'll explain the logic behind the six functions in my regression project.
There are two data generators, then bivariate and multiple linear regression, and finally polynomial
least squares with and without regularization. None of the fitting functions use a regression
package. Every one is written from the equations in the lecture.

---

## 2. Data generators: Problems 1 and 2 (about 1 min 15 s)

*Open `Problem1.jl`.*

`noisyLinearMultiDim` takes the number of samples `N`, the intercept `a`, a coefficient vector `b`,
and the noise variance `σ²`.

*Point to `m = length(b)` and `𝐗 = rand(N, m)`.*

The dimension `m` comes from the length of `b`, so the same function produces 1-D, 2-D or any
higher-dimensional data. `rand(N, m)` fills an N-by-m matrix with uniform values between zero and one.
Each row is one sample.

*Point to the `Ŷ = ...` line.*

`𝐗*b` computes the linear combination for every row at once. I add `a` and then the noise. One
detail matters here: `σ²` is a variance, and `randn` gives a standard deviation of one, so I
multiply by the square root of `σ²`. If I multiplied by `σ²` directly, the noise would be far too small.

*Open `Problem2.jl`.*

`noisySin` uses the same idea in one dimension: uniform inputs, then `sin(2πX)` plus Gaussian noise
scaled by the square root of the variance. In the report I check this by generating a hundred
thousand samples. The measured noise variance is 0.0899 against the requested 0.09.

---

## 3. Bivariate regression: Problem 3 (about 1 min 15 s)

*Open `Problem3.jl`.*

For `bivariate` I followed the subject-space picture from the lecture.

*Point to the centring lines.*

First I centre both variables by subtracting their means. In centred form the prediction is just
`ŷ = b x`, a scalar multiple of the vector `x`.

*Point to `b = sum(𝐱 .* 𝐲) / sum(𝐱 .* 𝐱)`.*

The best `b` is the one that makes the error vector `y − b x` perpendicular to `x`. Setting that dot
product to zero gives `b` equals x dot y divided by the squared length of x. That's the projection
of y onto x. Then the intercept comes back from the means: `a = Ȳ − b X̄`.

*Switch to the report, Problem 3a.*

To check the function I used the ten-point example from the slides. It returns `a = 4` and `b = 2`,
which matches the hand calculation. On the generated data, with true values a equals 5 and b equals 2,
I get 4.97 and 2.08.

---

## 4. Multiple regression: Problem 4 (about 1 min 15 s)

*Open `Problem4.jl`.*

`multivariate` extends the same idea to two predictors. After centring, the error has to be
perpendicular to both `x₁` and `x₂`. That gives two equations in two unknowns, the normal equations.

*Point to the `s₁₁ ... s₂y` block.*

These five sums are the dot products that appear in the normal equations.

*Point to `D`, `b₁`, `b₂`.*

I solve the 2-by-2 system in closed form with Cramer's rule. `D` is the determinant. If it is zero,
the two predictors are collinear and the coefficients are not unique, so the function raises an
error instead of dividing by zero. Finally the intercept is again recovered from the means.

*Switch to the report, Problem 4a and 4b.*

I checked the function against the eleven-point slide example and against Julia's backslash
solution of the full system. They agree to every digit shown. For `linear2.txt`, the coefficient on
X₂ is almost zero, so in that data set Y depends almost entirely on X₁.

---

## 5. Polynomial least squares: Problem 5 (about 2 min)

*Open `Problem5.jl`.*

`polyfitLS` implements Algorithm 1. The polynomial is nonlinear in X but linear in the weights, so
it becomes an ordinary linear least-squares problem once I build the design matrix.

*Point to the `for m in 0:M` loop.*

Column `m+1` of `𝚽` is X raised to the power `m`. The first column is all ones for `w₀`.

*Point to `𝐰 = pinv(𝚽)*𝐘`.*

The weights are `(𝚽ᴴ𝚽)⁻¹𝚽ᴴY`, which is the pseudoinverse of `𝚽` times Y. I used `pinv`, which
computes the same quantity through the singular value decomposition. That choice matters for M = 9.
The 10-by-10 Vandermonde matrix is badly conditioned, and forming `𝚽ᴴ𝚽` squares the condition number.

*Switch to the report, the Problem 5b table.*

On `curvefitting.txt`, the M = 0, 1 and 3 weights match Bishop's Table 1.1 exactly. The M = 9 weights
agree to a fraction of a percent, as the assignment's footnote predicts.

*Scroll to the 2-by-2 figure.*

These plots show under-fitting for M = 0 and 1, and a good fit for M = 3. For M = 9 the curve passes
through every point but oscillates wildly between them. That's over-fitting.

*Scroll to the E_RMS plot.*

This is the root-mean-square error on the ten training points and on a separate 500-point test set
from `noisySin`. Training error keeps falling and reaches zero at M = 9. Test error is lowest from
M = 3 to about M = 8, then jumps to 1.32 at M = 9. That gap is how over-fitting looks in numbers.

*Scroll to the N = 15 and N = 100 figure.*

With M fixed at 9, more data fixes the problem. With 15 points the curve still chases the noise.
With 100 points it is almost exactly the sine wave.

---

## 6. Regularized least squares: Problem 6 (about 1 min 30 s)

*Open `Problem6.jl`.*

`polyfitRegLS` builds the same design matrix, but it minimizes the squared error plus λ over two times
the squared norm of the weights. The solution is `(λI + 𝚽ᴴ𝚽)⁻¹𝚽ᴴY`.

*Point to `𝐀 = λ*I + 𝚽'*𝚽` and `𝐰 = 𝐀 \ (𝚽'*𝐘)`.*

Instead of computing the inverse, I solve the linear system with backslash, which is faster and more
accurate. Adding λ to the diagonal also raises the smallest eigenvalues, so the system is better
conditioned. With λ = 0 it reduces to ordinary least squares, and the report checks that.

*Switch to the report, the Problem 6b table.*

One interesting result: the λ = 10 column reproduces Bishop's ln λ = 0 column exactly. Bishop's
penalty is effectively scaled by the number of points, N = 10, which explains why the assignment asks
for λ = 10. With λ = e⁻¹⁸ the weights drop from about a million to a few hundred, and the curve
becomes a smooth sine-like fit even though the model still has ten parameters. With λ = 10 the
penalty dominates and the fit is nearly flat, so it under-fits.

*Scroll to the last plot.*

Finally, test error as a function of ln λ has its minimum near ln λ = −17. The best test error, about
0.36, is the same as choosing M = 3 in Problem 5. So regularization controls model complexity just as
the model order does, without having to remove any terms.

---

## 7. Closing (about 15 s)

*Show the report title page.*

To summarize, all six functions are written directly from the lecture equations, each one is checked
against a known answer, and the results reproduce Bishop's tables and figures for over-fitting and
regularization. Thank you for watching.
