# DSP HW #4 — Solutions (Mitra 4th ed., Chapter 5)

Assigned: **5.11, 5.13, 5.18, 5.20, 5.23, 5.58, 5.65, M5.2, M5.6, M5.10**
(M5.10 refers to **Example 5.14**, per the instructor's correction.)

Hand derivations are in the chat transcript / write-up. This folder holds the
code that independently reproduces every number.

## Layout

```
matlab/
  circconv_dft.m     M5.2  — circular convolution via the DFT
  circonv.m                 direct time-domain circular convolution (cross-check)
  dft2real.m         M5.6  — two real DFTs from one complex DFT (Sec. 5.9.1)
  m5_2.m             M5.2  driver
  m5_6.m             M5.6  driver
  m5_10.m            M5.10 — Fourier-domain filtering (Example 5.14)
  hw4_verify_all.m          checks every hand result: 5.11, 5.13, 5.18, 5.20,
                            5.23, 5.58, 5.65
julia/
  DFTUtils.jl               dft / idft / circconv_dft / circonv / dft2real
                            (dependency-free: DFT evaluated from the definition)
  m5_2.jl, m5_6.jl, m5_10.jl, hw4_verify_all.jl    same four programs
```

## Running

MATLAB (from `matlab/`):

```matlab
hw4_verify_all    % 56/56 checks
m5_2
m5_6
m5_10
```

Julia (from `julia/`) — no packages required:

```
julia hw4_verify_all.jl
julia m5_2.jl
julia m5_6.jl
julia m5_10.jl
```

`m5_10.jl` writes `m5_10_signals.csv`; it also writes `m5_10_figure.png` if
Plots.jl happens to be installed. The MATLAB version plots directly and
exports `m5_10_figure.png`.

## Status

`hw4_verify_all` reports **56/56 PASS** in both MATLAB R2025a and Julia 1.12,
and the two implementations agree with each other to ~1e-13.

## Key results

| Problem | Result |
|---|---|
| 5.11 | `y[n] = N² x[n]`  (and `F²{x}[k] = N·x[⟨−k⟩_N]`) |
| 5.13 | `X[2ℓ] = G[ℓ]`, `X[2ℓ+1] = H[ℓ]` — first DIF-FFT stage |
| 5.18 | `X[k] = Y[kM]` — zero-padding only interpolates the spectrum |
| 5.20 | `Y[k] = X[⟨k⟩_N]`; for the sketch, 4 periods of `{1,1,4,3,2}` |
| 5.23 | `p[n] = {1.25, 5, 1.75, −4.5}`, `d[n] = {12.4, −6.2, 5, 5.8}` |
| 5.58 | `R_xy[k] = X[k]·Y*[k] = X[k]·Y[⟨−k⟩_N]` |
| 5.65 | `G[k] = W₁₂^{5k} H[k]` (17 mod 12 = 5) |
| M5.2 | (a) `{−18,−14,19,1,5,22}` (b) `{−15+j18, −15−j23, 4+j7, 29−j3, 5+j13}` (c) `{−23,−69,35,105,73}` |
| M5.6 | one complex DFT replaces two real DFTs; matches `fft` to ~1e-15 |
| M5.10 | band-limited noise: 404× error reduction; white noise: only 1.5× |

## Note on the printed problem statement

Problem 5.65 prints `H[4]` as `1.0 + 24.25` — the `j` is missing. It must be
`1.0 + j24.25`: with that reading the IDFT of the completed `H[k]` is the
integer sequence `h[n] = {2, −4, 7, 3, −6, 1, −3, −6, 2, 0, 3, 5}`, which is
clearly what the problem was built from.
