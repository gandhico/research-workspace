# DILISIC — local setup

Python replication scaffold for

> *Limbic System-Inspired Performance-Guaranteed Control for Nonlinear
> Multi-Agent Systems With Uncertainties* — `docs/paper.pdf`

Extracted on 2026-09-05 from the D: backup at
`NMSU_backups\Backup\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control`.
Only the DILISIC subproject came across; the parent repository's MuJoCo,
Nengo, QCar and Julia trees are not needed and are not here.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Verified working with Python 3.13.11, NumPy 2.5.2, SciPy 1.18.1,
Matplotlib 3.11.1.

The controller and the experiment need **only NumPy**. SciPy is optional
(`riccati.py` falls back to a NumPy Hamiltonian solver without it), and
Matplotlib is needed only to draw plots, not to compute summaries. Install
`pip install -e .` alone if you just want to run the dynamics.

## Check it works

```
python -m pytest tests -q
```

Eleven tests, about five seconds.

```
python verify.py
```

Re-runs the full 80-second, seven-agent experiment and compares all eleven
summary metrics against `reference/dilisic_80s_smoothed`, the best run
recorded in the replication report. Takes about 40 seconds. Use
`--quick` for a 5-second smoke run with no reference comparison.

The 2026-09-08 audit fixed the reference/plant input contract and a one-step
duration error. `verify.py` now checks the regenerated, contract-corrected
reference under `reference/dilisic_80s_contract_fixed_20260908`; the older
reference is preserved for provenance.

## Running the experiment

```
python -m dilisic.experiments.flexible_arm_mas --duration 80 --dt 0.001 --output runs/my_run
python -m dilisic.experiments.plot_flexible_arm_mas runs/my_run/trajectory.csv --output runs/my_run/plots
```

The plotting step writes `positions.png`, `velocities.png`, `controls.png`,
`agent0_lisic_estimates.png` and `summary.json`. Add `--summary-only` style
use by calling `summarize()` directly if Matplotlib is unavailable.

## What is and is not replicated

`docs/dilisic_replication_report.md` is the authoritative account. In short:

**Replicated** — the fourth-order flexible single-link arm plant with the
paper's parameters, the seven-agent initial spread, the `t = 70`–`75 s`
disturbance, the `p = 45` RBF basis, projection-bounded adaptive weights,
and the robust Riccati term.

**Not replicated** — the outer multi-agent controller. The paper uses the
Appendix flocking law `u_i = u_α + u_β + u_γ` with sigma-norms, bump
functions and β-agent obstacle terms. What is implemented is
`controllers/flocking.py`, a simplified 1-D double-integrator formation
controller, and its own docstring says so. **This is the main gap between
this code and the paper.**

**Engineering scaffolding, not paper equations** — `h_hat` initialised near
the known inverse gain, RBF input clipping, reduced adaptation rates, a
first-order filter on `u_DI` before finite differencing, and smoothed
obstacle activation. These make the reproduction numerically stable; they
are additions, not reproductions.

## Layout

```
src/dilisic/
  controllers/   dilisic.py, lisic.py, riccati.py, flocking.py
  plants/        flexible_arm.py
  experiments/   flexible_arm_mas.py, plot_flexible_arm_mas.py
tests/           three test modules, six tests
docs/            paper.pdf, dilisic_replication_report.md
reference/       dilisic_80s_smoothed — the run verify.py checks against
runs/            experiment output (not in version control)
```

## Next steps, from the report

1. Implement the exact Appendix flocking equations (39)–(43).
2. Overlay obstacle and reference events on the position plot.
3. Add a centre-of-mass versus reference tracking-error plot.
4. Keep `dt = 0.001` until the exact outer controller is stable, then move
   to the paper-scale `dt = 1e-4` (80 s becomes 800,000 steps).
5. Only after numerical validation, add MuJoCo and Quanser adapters.

This code is simulation-only. It does not start MuJoCo, does not touch
Quanser hardware, and writes nothing outside `runs/`.
