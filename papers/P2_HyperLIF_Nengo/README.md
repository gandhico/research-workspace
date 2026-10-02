# Adaptive HyperLIF / HyperLIF — Nengo Reference Implementation and Paper

This project is a complete, self-contained research package for the **HyperLIF**
and **Adaptive HyperLIF** continuous-reset spiking neurons, implemented as a
clean Python reference and as Nengo custom `NeuronType` classes, validated
numerically, and written up as a journal-style manuscript.

It is the **companion implementation/validation study** to the Adaptive HyperLIF
*theory* manuscript (continuous-reset neurons derived via nonstandard analysis;
depolarization block; flux-balance stabilization). This project does **not**
re-derive the theory: it gives a faithful, equation-for-equation realization,
analyzes its numerics, validates the Nengo port to floating-point exactness, and
interprets the continuous gate as a decodable readiness signal for downstream
neural-engineering use (gate-state residual decoding for quaternion attitude
control, framed as future work).

It builds directly on the clean baseline at
`04_Adaptive_HyperLIF_Nengo` — the `src/` package here is a verbatim copy of the
baseline neuron/simulation code (so the equations are identical), extended with
an `analysis/` module and publication plotting.

## Headline results (all reproducible)

| Result | Value | Source |
|---|---|---|
| Depolarization-block onset (analytical) | `J_DB = (v_thresh−γ)(1+τ·G_b) = 2.4` | `03_db_analysis.csv` |
| Latched voltage at `J=4` (predicted vs simulated) | `1.3333` vs `1.3333` (exact) | `03_db_analysis.csv` |
| Adaptive asymptotic open-gate voltage vs gate knee | `0.625 < 0.8` ⇒ no high-voltage latch | `03_db_analysis.csv` |
| Adaptive stabilization condition | `β=80 > 1/(τ(v_thresh−γ))=62.5` | `03_db_analysis.csv` |
| Firing band / peak rate (HyperLIF vs Adaptive) | `[1.5,2.2]`, 73 Hz vs `[1.6,3.5]`, 151 Hz | `03_current_sweep.csv` |
| **Python vs Nengo parity** | voltage/gate RMSE `= 0`, max\|Δ\| `= 0`, event mismatch `= 0` | `07_parity_metrics.csv` |
| Decoding test RMSE (voltage / events / gate) | `0.258 / 0.321 / 0.287` | `05_decoding_metrics.csv` |
| Numerical schemes | both 1st-order vs RK4; explicit unstable for `λΔt>2`, exponential bounded | `06_*` |

The compiled manuscript is **`paper/main.pdf`** (20 pages).

## Project layout

```text
src/                 Reference implementation (equations == code)
  neurons/           lif, hyperlif, adaptive_hyperlif, nengo_hyperlif
  simulation/        current_protocols, ode_integrators, metrics
  analysis/          depolarization_block (fixed points, DB onset, beta condition)
  visualization/     publication plotting style
experiments/         01..07 data generators -> results/csv, results/logs
figures/             make_figures.py  (CSV -> results/figures + paper/figures)
tables/              make_tables.py   (CSV/params -> paper/tables/*.tex)
paper/               main.tex, references.bib, figures/, tables/, main.pdf
results/             csv/, logs/, figures/  (generated)
scripts/             setup_env, run_experiments, make_figures, make_tables,
                     build_paper, build_all  (PowerShell)
docs/                additional notes
README.md RUNNERS.md REPRODUCIBILITY.md MATH_CODE_MAP.md
FIGURE_TABLE_MAP.md RESULTS_AUDIT.md PAPER_NOTES.md
requirements.txt pyproject.toml
```

## Quickstart (Windows / PowerShell)

```powershell
# 1. Python environment (creates .venv and installs numpy, matplotlib, nengo)
scripts\setup_env.ps1

# 2. Regenerate everything and compile the PDF
scripts\build_all.ps1
```

Or step by step:

```powershell
scripts\run_experiments.ps1   # -> results/csv/*.csv, results/logs/*.txt
scripts\make_figures.ps1      # -> results/figures + paper/figures (PNG + PDF)
scripts\make_tables.ps1       # -> paper/tables/*.tex
scripts\build_paper.ps1       # -> paper/main.pdf
```

You can also run the Python entry points directly without the venv:

```powershell
python experiments\run_all.py
python figures\make_figures.py
python tables\make_tables.py
```

## Requirements

- **Python 3.10+** (verified on 3.11.0) with `numpy`, `matplotlib`, `nengo 4.x`
  (see `requirements.txt`).
- **A LaTeX toolchain** to compile the paper. MiKTeX is recommended on Windows:
  `winget install MiKTeX.MiKTeX`. `scripts\build_paper.ps1` auto-locates
  `pdflatex` on `PATH` or in a user-scope MiKTeX install and runs
  `pdflatex → bibtex → pdflatex → pdflatex`. TeX Live / Tectonic also work.

## Documentation map

- `RUNNERS.md` — what each runner script does, in order.
- `REPRODUCIBILITY.md` — environment, determinism, exact commands, TeX notes.
- `MATH_CODE_MAP.md` — every manuscript equation ↔ exact code location.
- `FIGURE_TABLE_MAP.md` — every figure/table ↔ generating script + source data.
- `RESULTS_AUDIT.md` — validated vs exploratory; paper-ready vs future work.
- `PAPER_NOTES.md` — narrative arc and scientific-honesty decisions.
