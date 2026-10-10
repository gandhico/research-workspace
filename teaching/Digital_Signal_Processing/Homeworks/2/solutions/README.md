# DSP II — Homework 2  (Mitra 4th ed., Chapters 3 and 4)

Assigned: **3.16(a,b), 3.25, 3.60, 3.66(a,b), M3.1, 4.9, 4.15, 4.23a, 4.39, M4.2**

Submitted to Canvas on 2026-09-19 as `Hm2_DSPII.pdf` (handwritten) and
`Hm2_DSPII_2.pdf` (handwritten + MATLAB listings), both in `../`.

## Layout

```
matlab/
  hw2_M3_01.m        M3.1 — DTFT of 1/(1 - 2r cos(th) e^-jw + r^2 e^-j2w),
                            own function taking r and theta as inputs
  hw2_M4_02.m        M4.2 — y[n] = 0.5(y[n-1] + x[n]/y[n-1]) converges to sqrt(alpha)
  hw2_verify_all.m         checks the hand results: 3.16, 3.25, 3.60, 3.66,
                           4.9, 4.15, 4.23a, 4.39
julia/
  hw2_M3_01.jl, hw2_M4_02.jl, hw2_verify_all.jl      same three programs
```

## Running

```matlab
hw2_verify_all      % from matlab/
hw2_M3_01
hw2_M4_02
```

```
julia hw2_verify_all.jl      # from julia/ — no packages required
julia hw2_M3_01.jl
julia hw2_M4_02.jl
```

## Status of the submitted work

`hw2_verify_all` is **19/19 PASS** against the corrected answers below.
Comparing those against what was actually submitted:

| Problem | Submitted | Verdict |
|---|---|---|
| 3.16(a) | `X1 = a e^-jw/(1 - a e^-jw)` (final line) | **correct** — but an earlier line in the same solution states `X1 = 1/(1 - a e^-jw)`, which is wrong; the factor `a e^-jw` was dropped and then recovered. Strike the bad line. |
| 3.16(b) | `X2 = a e^-jw/(1 - a e^-jw)^2` | correct |
| 3.25 | `y[n] = x[2n]` | correct |
| 3.60 | `y[n] = {-2,-3,0,0,0,3,2}`, `-1 <= n <= 5` | correct |
| 3.66 | `a = 2-j, b = 1, c = -1+j` | correct (samples are complex; the problem never says `x[n]` is real) |
| **4.9** | **not submitted** | **missing — see below** |
| 4.15 | monotone step response, `s[n] <= s_inf` | correct |
| **4.23(a)** | `y` read as `{6,-2,-13,24,12,33,-5,19}` | **wrong data.** The textbook has `y[1] = -7` and `y[7] = 14`. With the submitted numbers the deconvolution gives non-integer `x` and does not reconvolve to `y`. Correct answer: `x[n] = {2, -5, 3, 1, 7}`. |
| **4.39** | stops at `B = -A` | **incomplete.** Part (a) needs `A = 1/sqrt(5)` from `f[1] = 1`, giving Binet's formula. Part (b) was not attempted. |
| M3.1, M4.2 | MATLAB listings in `Hm2_DSPII_2.pdf` | correct; Julia twins were written but not submitted |

Also: the instructions said **"Problems must be submitted in order."** The PDF
runs 4.39 → 4.15/4.23 → 3.60/3.66 → 3.25 → 3.16, i.e. reversed.

## The corrected answers

**4.9** — `y[n] = (x[n])^2`, the squaring operator:
- **Nonlinear.** Homogeneity fails: `(a x[n])^2 = a^2 x^2[n] != a y[n]`.
  Additivity fails: `(x1+x2)^2 = x1^2 + x2^2 + 2 x1 x2`, and the cross term
  does not vanish.
- **Time-invariant.** `T{x[n-n0]} = (x[n-n0])^2 = y[n-n0]`; the rule has no
  explicit dependence on `n`.
- **Causal** (indeed memoryless): `y[n0]` is determined by `x[n0]` alone.
  It is also BIBO stable: `|x[n]| <= B` implies `|y[n]| <= B^2`.

**4.23(a)** — `y = {6,-7,-13,24,12,33,-5,14}`, `h = {3,4,-1,2}`, so `x` has
length `8 - 4 + 1 = 5`. Forward substitution `x[n] = (y[n] - sum_{k>=1} h[k]x[n-k])/h[0]`:

```
x[0] = 6/3                                        = 2
x[1] = (-7 - 4(2))/3                              = -5
x[2] = (-13 - 4(-5) - (-1)(2))/3                  =  3
x[3] = (24 - 4(3) - (-1)(-5) - 2(2))/3            =  1
x[4] = (12 - 4(1) - (-1)(3) - 2(-5))/3            =  7
```
Trailing checks: `y[5] = 4(7)-1(1)+2(3) = 33`, `y[6] = -1(7)+2(1) = -5`,
`y[7] = 2(7) = 14`. All three hold, so `x[n] = {2, -5, 3, 1, 7}`.

**4.39** — characteristic equation `lambda^2 - lambda - 1 = 0`, roots
`phi = (1+sqrt 5)/2`, `psi = (1-sqrt 5)/2`, so `f[n] = A phi^n + B psi^n`.
`f[0] = 0` gives `B = -A`; `f[1] = 1` gives `A(phi - psi) = A sqrt 5 = 1`, so

```
        A = 1/sqrt(5),  B = -1/sqrt(5)

        f[n] = ( phi^n - psi^n ) / sqrt(5)              (Binet)
```
(b) For `y[n] = y[n-1] + y[n-2] + x[n-1]` with `x[n] = delta[n]` and zero
initial conditions, `y[0] = 0`, `y[1] = x[0] = 1`, and `y[n] = y[n-1]+y[n-2]`
for `n >= 2` — the Fibonacci recursion with the right initial pair, so
`h[n] = f[n]`. Verified numerically to `n = 29`.
