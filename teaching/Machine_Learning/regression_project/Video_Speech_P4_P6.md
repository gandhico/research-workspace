# Project Regression: Video Speech (Problems 4, 5 and 6)

**Main script:** about 4 min 40 s at a calm pace (~650 words).
**Optional extension:** about 40 s more, to clear the 5-minute minimum.

Lines in *italics* are screen directions. Don't read them aloud. Line numbers refer to the
files in `src/`.

---

## Opening (≈ 15 s)

*Share the screen with VS Code open on the `src` folder.*

Hello. In this video I'll answer two questions. First, how my `multivariate` function in
Problem 4 works and what it returns. Second, how `polyfitLS` and `polyfitRegLS` from Problems 5
and 6 work, and what their similarities and differences are.

---

## Question 1: `multivariate` (≈ 1 min 45 s)

*Open `Problem4.jl` and highlight the signature on line 11.*

The `multivariate` function performs multiple linear regression with two predictors. It receives
three vectors, `X₁`, `X₂` and `Y`, and finds the plane Y-hat equals a plus b₁ X₁ plus b₂ X₂ that
best fits the data in the least-squares sense.

*Highlight lines 13 to 15.*

First, it checks that the three vectors have the same length, because each position is one
observation.

*Highlight lines 17 to 24.*

Next, it computes the mean of each variable and subtracts it to get centred variables. Centring
removes the intercept from the problem, so I only need to solve for the two slopes first.

*Highlight lines 27 to 31.*

The best prediction is the one where the error vector is orthogonal to both centred predictors.
Writing that condition out gives the two normal equations shown in the comment on lines 8 and 9.
These five sums are exactly the dot products that appear in those equations.

*Highlight lines 33 to 36.*

`D` is the determinant of the two-by-two system. If `D` is zero, the two predictors are
collinear: one is a multiple of the other, and the slopes are not unique. In that case the function
stops with an error instead of dividing by zero.

*Highlight lines 38 to 40.*

Then it solves the system in closed form with Cramer's rule to get `b₁` and `b₂`. Finally, it
recovers the intercept from the means: `a` equals Y-bar minus b₁ times X₁-bar minus b₂ times X₂-bar.

*Highlight line 42.*

The function returns three numbers as a tuple: the intercept `a` and the two slopes `b₁` and
`b₂`. In my report I verified it against the example from the lecture slides. On the generated
data, with true values 5, 2 and 1, it recovered approximately 4.96, 2.21 and 0.91.

---

## Question 2: `polyfitLS` vs. `polyfitRegLS` (≈ 2 min 30 s)

*Open `Problem5.jl` and `Problem6.jl` side by side.*

Now Problems 5 and 6. I'll start with what the two functions share, then explain the
difference and how it changes the approach.

**Similarities**

*Highlight lines 9 to 17 in both files.*

Both functions fit a polynomial of order M to the data. A polynomial is nonlinear in X but linear
in its weights, so both functions turn the problem into linear least squares. They have identical
first steps. They check that M is not larger than the number of points. They allocate the design
matrix Phi with N rows and M plus one columns. Then this loop fills column m plus one with X to the
power m, so the first column is all ones for the constant term. Both return the weight vector `w`,
from w₀ up to w_M.

**How `polyfitLS` works**

*Highlight line 21 in `Problem5.jl`.*

`polyfitLS` minimizes only the squared error. The solution is Phi-transpose-Phi inverse, times
Phi-transpose, times Y, which is the pseudoinverse of Phi times Y. I compute it with `pinv`, which
uses the singular value decomposition. I chose that because for M equals 9 the matrix Phi is badly
conditioned, and forming Phi-transpose-Phi explicitly squares the condition number and amplifies
round-off error.

**How `polyfitRegLS` works, and the key difference**

*Highlight the signature on line 9 of `Problem6.jl`, then lines 20 and 21.*

`polyfitRegLS` takes one extra input, lambda. It minimizes the squared error plus lambda over
two times the squared length of `w`. That penalty discourages large weights. The solution changes
in just one place: lambda times the identity matrix is added to Phi-transpose-Phi. Line 20 builds
that matrix. On line 21, instead of computing an inverse, I solve the linear system with Julia's
backslash operator, which is faster and more accurate.

**How the difference affects the approach**

*Switch to the report: the Problem 5 figure for M = 9, then the Problem 6 figure.*

The difference changes how I control overfitting. With `polyfitLS`, the only control is the
model order M. With ten points and M equals 9, the curve passes through every point but
oscillates wildly, and the weights reach about a million. With `polyfitRegLS`, I keep M equals 9
and tune lambda instead. At lambda equals e to the minus 18, the weights drop to a few hundred and
the curve follows the sine wave smoothly. At lambda equals 10, the penalty dominates and the
curve is almost flat, which is underfitting. So lambda takes over the role that M played in
Problem 5.

There is also a numerical benefit. Adding lambda to the diagonal makes the system well
conditioned, so I can solve it directly instead of needing the pseudoinverse. And setting lambda
equal to zero recovers ordinary least squares, which I used as a consistency check.

---

## Closing (≈ 10 s)

To summarize: `multivariate` returns the intercept and two slopes from the normal equations.
`polyfitLS` and `polyfitRegLS` share the same design matrix, but the regularization term lets me
control model complexity with lambda instead of the polynomial order. Thank you.

---

## Optional extension (≈ 40 s): insert before the Closing

*Show the Problem 6 table in the report.*

One result I found interesting: my lambda equals 10 column reproduces Bishop's Table 1.2
column for ln lambda equals zero exactly. That's because Bishop's penalty is effectively scaled
by the number of data points, which is 10 here. That explains why the assignment asks for
lambda equals 10.

*Show the last plot, error versus ln λ.*

This plot shows the test error as a function of ln lambda. It is lowest near ln lambda equals
minus 17, at about 0.36. That is the same best error I got by choosing M equals 3 in Problem 5. So
regularization reaches the same generalization without removing any terms from the model.
