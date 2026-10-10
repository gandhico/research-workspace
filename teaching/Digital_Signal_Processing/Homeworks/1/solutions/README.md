# DSP II — Homework 1 solutions

Mitra, *Digital Signal Processing: A Computer-Based Approach*, 4th ed., Chapter 2.
Covers **Problems 2.4 – 2.54** and **MATLAB Exercises M2.1 – M2.10** (the full
problem set on the scanned pages 82–88).

> **Canvas actually assigned only nine of these**, to be submitted in order:
> **2.8, 2.10, 2.17, 2.21, 2.30, 2.36, M2.4, M2.6, M2.7.**
> Everything else here is extra work, kept for reference.

## Files

| File | What it is |
|---|---|
| `hw1_solutions.pdf` | **The deliverable** — 36 pages, every problem worked by hand with full derivations |
| `hw1_solutions.tex` | Master LaTeX file (`\input`s the eight section files) |
| `sec1_conv.tex` … `sec8_errata.tex` | Section sources |
| `matlab/` | MATLAB code (see below) |
| `julia/` | Julia twins of the same code (see below) |

Rebuild the PDF with:

```bash
pdflatex hw1_solutions.tex
```

## MATLAB

| Script | Purpose |
|---|---|
| `hw1_verify_all.m` | Checks **every** numerical answer in the PDF — 67 assertions, all PASS |
| `hw1_M2_01.m` … `hw1_M2_10.m` | The ten assigned MATLAB exercises |
| `hw1_p207.m`, `hw1_p214.m` | Standalone checks for Problems 2.7 and 2.14 |

Run from the `matlab/` folder:

```bash
matlab -batch hw1_verify_all
```

No toolboxes required — only `conv`, `rand`, `rat`, `lcm` and base plotting.
Tested on R2025a.

## Julia

| Script | Purpose |
|---|---|
| `hw1_verify_all.jl` | Same 67 assertions as the MATLAB version - **67/67 PASS** |
| `HW1Utils.jl` | conv / deconv / evenodd / perext / fper / xcorrseq helpers |
| `hw1_M2_04.jl` | M2.4 sinusoid generator, Figure 2.22 family, Problem 2.40 periods |
| `hw1_M2_06.jl` | M2.6 sampling ambiguity, Figure 2.28 |
| `hw1_M2_07.jl` | M2.7 the Eq. (2.65) family of sinusoids |

Dependency-free - the DFT/convolution routines are written out from their
definitions, so these run on a bare Julia install:

```
julia hw1_verify_all.jl
```

The MATLAB and Julia versions are independent implementations, so their
agreement is real evidence rather than a repeated calculation.

## Book misprints found

Five statements on the scanned pages are internally inconsistent; each is flagged in
red in the PDF and solved both as printed and as intended. Appendix A of the PDF
collects them:

- **2.7** — `x4` as printed makes the required identity false; intended `{1,0,1,0,1,0,1}`
- **2.8(b)** — range `0 ≤ n ≤ 5` stated but only five samples listed
- **2.40** — parts (e) and (f) print the same frequency `0.75π`
- **2.48(iii)** — `g[n] = μ[n−N] − μ[n−N] ≡ 0`; intended `μ[n−N] − μ[n−M]`
- **2.48(c,d)** — `y3` and `y4` are both `g ⊛ g`; `y4` should be `w ⊛ w`

The scanned printing also numbers problems and examples slightly differently from the
electronic 4th-edition chapter file. Where the two disagree numerically, the **scanned**
statement was taken as authoritative.
