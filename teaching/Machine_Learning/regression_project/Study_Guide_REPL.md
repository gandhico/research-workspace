# Project Regression: Study Guide with REPL Commands

Work through it in order. For each problem:

1. **Idea:** the math in two or three lines.
2. **Code:** which lines in `src/ProblemN.jl` do what. Open the file next to the REPL.
3. **REPL:** commands to paste one at a time into the Julia window. Each command lists what you should see.

---

## 0. Start Julia in the project

Open a terminal and run:

```
cd C:\Teaching\Machine_Learning\regression_project\Project2_Regression\Project_Regression
julia --project=.
```

Then, in the Julia REPL:

```julia
using Revise                 # reloads src files automatically when you edit them
using Project_Regression     # loads all six functions
using Plots, Random, Statistics, LinearAlgebra
```

The first `using` takes 20–60 s while it compiles. After that:

```julia
names(Project_Regression)    # should list noisyLinearMultiDim, noisySin, bivariate, ...
```

Two helpers you'll reuse:

```julia
loadData(f) = permutedims(reduce(hcat, [parse.(Float64, split(l)) for l in readlines(joinpath("data", f)) if !isempty(strip(l))]))
fitR(Y, Ŷ) = norm(Ŷ .- mean(Y)) / norm(Y .- mean(Y))
```

> **Typing Unicode in the REPL:** type the LaTeX name and press Tab, for example `\bfX` Tab → 𝐗,
> `\sigma` Tab `\^2` Tab → σ², `\lambda` Tab → λ, `\Phi` Tab → Φ, `Y\hat` Tab → Ŷ.
> Plain names (`X`, `Y`, `s2`) work just as well in the REPL.

---

## Problem 1: Noisy linear multi-dimensional data

**Idea**

$$X_{n,m} \sim \mathcal U(0,1), \qquad Y_n = a + b_1X_{n,1} + \dots + b_mX_{n,m} + \sqrt{\sigma^2}\,z_n, \quad z_n\sim\mathcal N(0,1)$$

**Code** (`src/Problem1.jl`)

| Line | What it does |
|---|---|
| `m = length(b)` | The dimension comes from how many coefficients you pass. |
| `𝐗 = rand(N, m)` | N×m uniform matrix; one row per sample. |
| `Ŷ = a .+ 𝐗*b .+ sqrt(σ²) .* randn(N)` | Matrix-vector product gives all N linear values at once, then noise is added. |

**Key point:** `σ²` is a *variance*. `randn` has std 1, so multiply by `sqrt(σ²)`, not by `σ²`.

**REPL**

```julia
Random.seed!(1)
X, Y = noisyLinearMultiDim(5, 5.0, [1.0, 2.0])
size(X)          # (5, 2)
Y                # 5 numbers between 5 and 8
```

Check that the function is correct without noise. The result should be `0.0`:

```julia
X, Y = noisyLinearMultiDim(5, 5.0, [1.0, 2.0]; σ²=0.0)
maximum(abs.(Y .- (5.0 .+ X*[1.0, 2.0])))
```

Check the noise variance. The result should be ≈ 0.1:

```julia
X, Y = noisyLinearMultiDim(100_000, 5.0, [2.0]; σ²=0.1)
var(Y .- (5.0 .+ 2.0 .* X[:,1]))
```

Part b plot (2-D):

```julia
Random.seed!(2026)
X, Y = noisyLinearMultiDim(100, 5.0, [2.0]; σ²=0.1)
scatter(X[:,1], Y, color=:blue, label="Noisy Data")
plot!(0:0.01:1, x -> 5 + 2x, color=:green, lw=2, label="Ground Truth")
```

Part c plots (3-D):

```julia
X, Y = noisyLinearMultiDim(300, 5.0, [1.0, 0.0]; σ²=0.05)
scatter(X[:,1], X[:,2], Y, color=:blue, ms=2, xlabel="X1", ylabel="X2", label="")

X, Y = noisyLinearMultiDim(300, 5.0, [1.0, 2.0]; σ²=0.05)
scatter(X[:,1], X[:,2], Y, color=:blue, ms=2, xlabel="X1", ylabel="X2", label="")
```

**Ask yourself:** why is the first cloud flat along X2? Because b₂ = 0.

---

## Problem 2: Noisy sinusoid

**Idea**

$$X_n\sim\mathcal U(0,1), \qquad Y_n = \sin(2\pi X_n) + \sqrt{\sigma^2}\,z_n$$

**Code** (`src/Problem2.jl`): two lines. `rand(N)` gives the inputs, and `sin.(2π .* 𝐗) .+ sqrt(σ²) .* randn(N)` gives the targets. The dot (`.`) means element-wise. The default σ² = 0.09 (std 0.3) is Bishop's noise level.

**REPL**

```julia
Random.seed!(3)
X, Y = noisySin(100_000)
var(Y .- sin.(2π .* X))        # ≈ 0.09

Random.seed!(2028)
X, Y = noisySin(50; σ²=0.05)
scatter(X, Y, color=:blue, label="Noisy Data")
plot!(0:0.005:1, x -> sin(2π*x), color=:green, lw=2, label="Ground Truth")
```

---

## Problem 3: Bivariate regression

**Idea**

The subject-space picture from the slides:

1. Centre the data: x = X − X̄ and y = Y − Ȳ.
2. Choose b so the error is perpendicular to x: x·(y − bx) = 0, which gives **b = (x·y)/‖x‖²**.
3. Recover the intercept: **a = Ȳ − bX̄**.

**Code** (`src/Problem3.jl`)

| Line | What it does |
|---|---|
| `X̄ = mean(𝐗)`, `Ȳ = mean(𝐘)` | Sample means. |
| `𝐱 = 𝐗 .- X̄`, `𝐲 = 𝐘 .- Ȳ` | Centring. |
| `b = sum(𝐱 .* 𝐲) / sum(𝐱 .* 𝐱)` | Dot product over squared length: the projection of y on x. |
| `a = Ȳ - b*X̄` | Back to uncentred data. |

**REPL:** follow the slide example by hand.

```julia
X = [1.0, 1, 3, 3, 4, 4, 5, 6, 6, 7]
Y = [4.0, 7, 9, 12, 11, 12, 17, 13, 18, 17]
mean(X), mean(Y)                 # (4.0, 12.0)
x = X .- mean(X); y = Y .- mean(Y)
x                                # matches the slide's x column: -3 -3 -1 -1 0 0 1 2 2 3
sum(x .* y), sum(x .* x)         # (56.0, 28.0) → b = 2
bivariate(X, Y)                  # (4.0, 2.0)
```

Check perpendicularity. The result should be 0:

```julia
a, b = bivariate(X, Y)
e = y .- b .* x
dot(x, e)
```

Part b, `linear1.txt` (column 1 = Y, column 2 = X, as the assignment states):

```julia
D = loadData("linear1.txt")
Y1 = D[:,1]; X1 = D[:,2]
a, b = bivariate(X1, Y1)         # (0.5637, -0.3422)
fitR(Y1, a .+ b .* X1)           # 0.6587
scatter(X1, Y1, color=:blue, label="data")
plot!(x -> a + b*x, extrema(X1)..., color=:green, lw=2, label="fit")
```

Part c, generated data:

```julia
Random.seed!(2029)
X, Y = noisyLinearMultiDim(100, 5.0, [2.0]; σ²=0.1)
a, b = bivariate(X[:,1], Y)      # ≈ (4.97, 2.08); the truth is (5, 2)
scatter(X[:,1], Y, color=:blue, label="data")
plot!(x -> a + b*x, 0, 1, color=:green, lw=2, label="fit")
```

---

## Problem 4: Multiple regression

**Idea**

After centring, the error must be perpendicular to both x₁ and x₂. That gives the **normal equations**:

$$\begin{aligned}
b_1(\mathbf{x}_1\cdot\mathbf{x}_1) + b_2(\mathbf{x}_1\cdot\mathbf{x}_2) &= \mathbf{x}_1\cdot\mathbf{y}\\
b_1(\mathbf{x}_2\cdot\mathbf{x}_1) + b_2(\mathbf{x}_2\cdot\mathbf{x}_2) &= \mathbf{x}_2\cdot\mathbf{y}
\end{aligned}$$

Solve with Cramer's rule, where D = s₁₁s₂₂ − s₁₂². Then a = Ȳ − b₁X̄₁ − b₂X̄₂.

**Code** (`src/Problem4.jl`)

| Line | What it does |
|---|---|
| `s₁₁ … s₂y` | The five dot products in the normal equations. |
| `D = s₁₁*s₂₂ - s₁₂^2` | Determinant. A value of 0 means X₁ and X₂ are collinear, so the function raises an error. |
| `b₁ = (s₁y*s₂₂ - s₂y*s₁₂)/D`, `b₂ = …` | Cramer's rule. |
| `a = Ȳ - b₁*X̄₁ - b₂*X̄₂` | Intercept. |

**REPL:** slide example, then compare with a matrix solution.

```julia
X1 = [2.0, 2, 4, 4, 5, 5, 5, 6, 7, 7, 8]
X2 = [3.0, 5, 4, 7, 5, 8, 9, 8, 7, 10, 11]
Y  = [15.0, 16, 15, 10, 13, 9, 8, 7, 8, 5, 4]
multivariate(X1, X2, Y)          # (21.4423, -0.8077, -1.0577)
[ones(11) X1 X2] \ Y             # same numbers; this is only an independent check
```

Look inside the normal equations:

```julia
x1 = X1 .- mean(X1); x2 = X2 .- mean(X2); y = Y .- mean(Y)
S = [dot(x1,x1) dot(x1,x2); dot(x2,x1) dot(x2,x2)]
S \ [dot(x1,y), dot(x2,y)]       # = (b1, b2)
```

See the collinear error. This line *should* fail with "collinear":

```julia
multivariate(X1, 2 .* X1, Y)
```

Part b, `linear2.txt` (columns Y, X1, X2):

```julia
D = loadData("linear2.txt")
Y2, A, B = D[:,1], D[:,2], D[:,3]
a, b1, b2 = multivariate(A, B, Y2)          # (5.52, 1.51, 0.0025): X2 barely matters
fitR(Y2, a .+ b1 .* A .+ b2 .* B)           # 0.978
surface(range(extrema(A)..., 20), range(extrema(B)..., 20), (u,v) -> a + b1*u + b2*v, alpha=0.4, colorbar=false)
scatter!(A, B, Y2, color=:blue, label="")
```

Part c, generated data:

```julia
Random.seed!(2030)
X, Y = noisyLinearMultiDim(100, 5.0, [2.0, 1.0]; σ²=0.1)
multivariate(X[:,1], X[:,2], Y)             # ≈ (4.96, 2.21, 0.91); the truth is (5, 2, 1)
```

---

## Problem 5: Polynomial least squares

**Idea**

The model Ŷ = w₀ + w₁X + … + w_M X^M is linear in **w**. Build Φ with Φ[n, m+1] = Xₙ^m, then

$$\mathbf w^\star = (\Phi^H\Phi)^{-1}\Phi^H\mathbf Y = \Phi^\dagger\mathbf Y, \qquad E_{RMS} = \sqrt{2E/N} = \sqrt{\text{mean squared residual}}$$

**Code** (`src/Problem5.jl`)

| Line | What it does |
|---|---|
| `𝚽 = zeros(N, M+1)` | Template line: allocate the design matrix. |
| `for m in 0:M; 𝚽[:,m+1] = 𝐗.^m; end` | Column m+1 holds Xᵐ. The first column is all ones. |
| `𝐰 = pinv(𝚽)*𝐘` | Pseudoinverse through the SVD. It equals (ΦᴴΦ)⁻¹ΦᴴY mathematically but is safer numerically for M = 9. |

**REPL:** build Φ yourself first.

```julia
D = loadData("curvefitting.txt"); X = D[:,1]; Y = D[:,2]
Φ = [x^m for x in X, m in 0:3]   # 10×4 Vandermonde matrix
Φ[1:3, :]                         # first rows: 1, x, x², x³
(Φ'Φ) \ (Φ'Y)                     # textbook formula
polyfitLS(X, Y, 3)                # same: [0.31, 7.99, -25.43, 17.37] (Table 1.1)
```

Why `pinv`: compare condition numbers.

```julia
Φ9 = [x^m for x in X, m in 0:9]
cond(Φ9), cond(Φ9'Φ9)             # ~1e7 vs ~1e14: forming ΦᴴΦ squares it
```

Part b, Table 1.1:

```julia
for M in (0, 1, 3, 9); println(M, " => ", round.(polyfitLS(X, Y, M), digits=2)); end
```

Part b, Figure 1.4. Change `M` and re-run the block:

```julia
M = 9
w = polyfitLS(X, Y, M)
plot(x -> sin(2π*x), 0, 1, color=:green, lw=2, label="sin")
plot!(x -> Polynomial(w)(x), 0, 1, color=:red, lw=2, label="M=$M", ylims=(-1.5,1.5))
scatter!(X, Y, mc=:white, msc=:blue, label="data")
```

Part c, training vs test E_RMS (Figure 1.5):

```julia
Erms(w, X, Y) = sqrt(mean((Y .- Polynomial(w).(X)).^2))
Random.seed!(2031); Xt, Yt = noisySin(500)
Etr = [Erms(polyfitLS(X, Y, M), X, Y) for M in 0:9]
Ete = [Erms(polyfitLS(X, Y, M), Xt, Yt) for M in 0:9]
[0:9 round.(Etr, digits=2) round.(Ete, digits=2)]   # train → 0 at M=9; test jumps to 1.32
plot(0:9, Etr, m=:o, label="Training"); plot!(0:9, Ete, m=:o, label="Test", xlabel="M")
```

Part d, more data tames M = 9 (Figure 1.6). Change N between 15 and 100:

```julia
Random.seed!(2032)
N = 15
Xn, Yn = noisySin(N); w = polyfitLS(Xn, Yn, 9)
plot(x -> sin(2π*x), 0, 1, color=:green, lw=2, label="")
plot!(x -> Polynomial(w)(x), 0, 1, color=:red, lw=2, label="N=$N", ylims=(-1.6,1.6))
scatter!(Xn, Yn, mc=:white, msc=:blue, label="")
```

**Takeaway:** a low training error ≠ a good model. Over-fitting shows up as huge weights and a high test error. More data or a lower M fixes it.

---

## Problem 6: Regularized least squares

**Idea**

Add a penalty on the size of the weights:

$$\tilde E(\mathbf w) = \tfrac12\|\mathbf Y-\Phi\mathbf w\|^2 + \tfrac{\lambda}{2}\|\mathbf w\|^2 \;\Rightarrow\; \mathbf w^\star = (\lambda\mathbf I + \Phi^H\Phi)^{-1}\Phi^H\mathbf Y$$

**Code** (`src/Problem6.jl`)

| Line | What it does |
|---|---|
| `for m in 0:M …` | Same design matrix as Problem 5. |
| `𝐀 = λ*I + 𝚽'*𝚽` | `I` is the identity from LinearAlgebra and sizes itself automatically. |
| `𝐰 = 𝐀 \ (𝚽'*𝐘)` | Solves the system instead of inverting; faster and more accurate. |

**REPL**

λ = 0 gives back ordinary least squares. The result should be ~1e-14:

```julia
maximum(abs.(polyfitRegLS(X, Y, 3, 0.0) .- polyfitLS(X, Y, 3)))
```

Part b, the table. Watch how the weights shrink:

```julia
for λ in (0.0, exp(-18), 1.0, 10.0)
    w = polyfitRegLS(X, Y, 9, λ)
    println(rpad("λ=$(round(λ, sigdigits=3))", 14), round.(w, digits=2), "   ‖w‖=", round(norm(w), digits=2))
end
```

The λ = 10 row is Bishop's ln λ = 0 column exactly (0.13, −0.05, −0.06, …), because Bishop's λ is effectively scaled by N = 10.

Regularization improves conditioning:

```julia
cond(Φ9'Φ9), cond(exp(-18)*I + Φ9'Φ9)       # huge vs much smaller
```

Part b, Figure 1.7. Try λ = exp(-18), then 10.0:

```julia
λ = exp(-18)
w = polyfitRegLS(X, Y, 9, λ)
plot(x -> sin(2π*x), 0, 1, color=:green, lw=2, label="")
plot!(x -> Polynomial(w)(x), 0, 1, color=:red, lw=2, label="λ=$λ", ylims=(-1.5,1.5))
scatter!(X, Y, mc=:white, msc=:blue, label="")
```

Extra (Figure 1.8), error vs ln λ:

```julia
lnλ = -40:1:5
Etr = [Erms(polyfitRegLS(X, Y, 9, exp(l)), X, Y)   for l in lnλ]
Ete = [Erms(polyfitRegLS(X, Y, 9, exp(l)), Xt, Yt) for l in lnλ]
lnλ[argmin(Ete)], minimum(Ete)              # ≈ (-17, 0.36)
plot(lnλ, Etr, label="Training"); plot!(lnλ, Ete, label="Test", ylims=(0,1), xlabel="ln λ")
```

**Takeaway:** λ plays the same role as M. Too small over-fits, too large under-fits (flat line), and a value in the middle is best. The best test error (≈ 0.36) is the same as picking M = 3 in Problem 5.

---

## Finish: rebuild the report

```julia
include("report/makeReport.jl")     # regenerates report/ProjectReport.html (~20 s)
```

Then open the HTML in a browser and print it to `ProjectReport.pdf`.
