# Coaxial Trirotor (Y6) — Nengo Neuromorphic Control: Paper Development

Working folder for a **two-paper** effort on Nengo/NEF neuromorphic UAV control
(benchmark axis: **neuromorphic vs. classical performance**). See [`docs/paper_plan.md`](docs/paper_plan.md).

- **Paper 1 (priority, → ComRob, IEEE 2-col, 6 pp, English):** NEF controller validated on
  Victor's **quadrotor**, then **evolved to a coaxial trirotor** (importing the coaxial
  allocation from the Y6).
- **Paper 2 (secondary, venue TBD):** a full-SNN coaxial **Y6** controller built from the
  `00_SOTA` literature, independent of Victor's lineage.

> All reference material lives *outside* this folder and is **read-only**:
> `baseline_victor\`, `01_Code\`, `github_anel\`, `github_gandhi\`, `00_SOTA\`.
> Everything new goes **here**.

## Status

| Phase | What | State |
|---|---|---|
| 0 | Inventory of reference folders | ✅ done |
| 1 | Review of Victor's baseline → [`docs/victor_review.md`](docs/victor_review.md) | ✅ done |
| 1b | Two-paper strategy + plan → [`docs/paper_plan.md`](docs/paper_plan.md) | ✅ done — **awaiting go-ahead for Phase 2** |
| 2 | 1-DOF altitude → [`experiments/exp01_altitude_1dof`](experiments/exp01_altitude_1dof) | ✅ done (benchmark + Nengo GUI + block diagrams) |
| 3 | Attitude/position subsystems → [`experiments/exp02_attitude_subsystems`](experiments/exp02_attitude_subsystems) | ✅ done (roll/pitch/yaw + x/y cascades) |
| 4 | Full quadrotor baseline → [`experiments/exp03_quadrotor_full`](experiments/exp03_quadrotor_full) | ✅ done (classical vs NEF rate/spiking, 50 s 3-D) |
| 5 | Coaxial trirotor → [`experiments/exp04_coaxial_trirotor`](experiments/exp04_coaxial_trirotor) | ✅ done (Y6 model + 6×4 allocation + neural allocator; sub-cm after Phase 5a) |
| 6 | Paper 1 assembly → [`paper/main.tex`](paper/main.tex) | ✅ draft compiled (IEEEtran, 4 dense pp, 5 figs, 3 tables) |

Phases 2–5 ran for real (classical vs NEF spiking/rate). Consolidated results:
[`docs/results_summary.md`](docs/results_summary.md). Full spiking quad matches classical to
~1.5 mm RMSE (Phase 4); the coaxial Y6 trirotor flies under a **neural allocator** to within a
few cm (Phase 5). Math diff quad→trirotor: [`docs/trirotor_vs_quad.md`](docs/trirotor_vs_quad.md).

## Toolchain (verified 2026-06-17)

- Python 3.11 in `..\.venv` — **nengo 4.1.0**, numpy 2.4.6, scipy 1.17.1, matplotlib 3.10.9, pandas 3.0.3, nengo_gui 0.6.0
- LaTeX: MiKTeX (pdflatex / xelatex / latexmk) — paper build OK
- Missing (non-blocking): `python-control` (scipy covers step metrics); no MATLAB (Simulink `.slx` not runnable here)

## Layout

```
docs/        victor_review.md, paper_plan.md, + (later) mathematical_model, controller_design, nengo_design, implementation_path
paper/       main.tex, sections/, figures/, diagrams/ (TikZ), references.bib
src/         models, controllers_classical, controllers_nengo, allocation, simulation, gui, utils
experiments/ exp01_altitude_1dof … exp05_benchmark  (runnable, emit CSV+plots+metrics)
results/     csv/, plots/, summaries/
```

## Conventions (decided in Phase 1)

- **Coaxial Trirotor = Y6 = "Coaxial Hexarotor"**: 3 arms × coaxial top+bottom rotor pairs = 6 motors, 4 virtual commands `(T, τ_x, τ_y, τ_z)`.
- Frame: **z-up** (matches all existing code). State `[x,y,z,u,v,w,φ,θ,ψ,p,q,r]`.
- Every experiment must emit real CSV + plots + a metrics row. No illustrative-only numbers.
