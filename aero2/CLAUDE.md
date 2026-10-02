# CLAUDE.md — working notes for this repo

Read this first. This is the migration/refactor of the Quanser Aero2 system-ID
and control project into a math-traceable tree, scaffolded for a future Adaptive
HyperLIF (neuromorphic) phase. The governing brief is `docs/00_source_brief.md`.

## Golden rules
1. **One source of truth for every constant** — `aero2/config/` (`params`,
   `gains`, `sensors`, `timing`, `references`). No magic numbers in controllers/models.
2. **Code = truth.** When code and paper disagree, the *implemented code* wins;
   record the resolution in `docs/math_code_map.md`.
3. **Backend-agnostic controllers.** Mode (offline / virtual-twin / hardware) is
   a config field, never an `if` inside a controller.
4. **Preserve honest results.** Do NOT silently improve free-run numbers or yaw.
5. **Half-rotor & HyperLIF are explicitly not-yet-produced.** Mark `NotValidated`
   / experimental; never fabricate hardware or SNN results.

## Do-not-drop list (each changed real results — brief §17)
- `cos(theta)` clip `|cθ| ≥ 0.25` (`config.params.MIN_COS_THETA`) — yaw authority at large pitch.
- **Actual measured Δt** in every derivative filter / discrete update (`Backend.dt_actual()`).
- Discard `t < 3 s` and demean in PRBS/trim identification (`config.timing.TRIM_DISCARD_S`).
- Pure-differential yaw drive `u_L = −v_ψ, u_R = +v_ψ`.

## Canonical migration sources (under `C:\02_Research\01_Robotics_Quanser\01_Aero2`)
| What | From | Notes |
|---|---|---|
| Science (ID, modelling, M1–M6) | `aero2_clean/M1..M8/` | module-organized; matches the traceability table |
| Control + Table IV benchmark | `aero2_minimal_control/src/` | consolidated PD/LQR/LQG/MPC/BS/SMC/NMPC + `hardware_runner.py` |
| Architecture reference | `aero2lab_project/` | backends/models/controllers/missions — closest to this tree |
| Docs / LaTeX / traceability | `aero2_paper_results/` | `14_latex_sections/full_integrated_paper_draft.tex` (Ref 3), `source_draft/conference_101719_updated.tex` (Ref 2) |
| Raw hardware CSVs | each module's `data/` + `aero2_minimal_control/data/raw/` | migrate to `data/raw_logs/` in Phase 2 |

Reference papers (place PDFs in `docs/papers/`):
- **Ref 1** Module 1 / *Computer-Controlled Systems* (sampling, IMU bias/noise, ZOH, excitation, state est).
- **Ref 2** *Mid-Project* (trim search, pitch doublet, yaw chirp, coupled ARX, validation).
- **Ref 3** *Final* (full models, ARX/DARX, validation/uncertainty, PD/LQR/LQG/MPC/BS/SMC/NMPC, hardware benchmark).

## Headline results to preserve (Ref 3 Table IV — hardware)
PD baseline best overall (pitch RMS 0.1544, yaw RMS 0.4215). SMC best nonlinear
tail pitch (0.0110). NMPC fast/realtime ~303 Hz, pitch-sat 0.79/0.84 — benchmarkable,
not competitive. Yaw unresolved for every model-based controller. Mean loop ≈ 380 Hz
(commanded 500). Full table is in `docs/09_benchmarking.md` (Phase 9/11).

## Identification targets (Ref 3 Table II / Ref 2 Table I)
DARX: Pitch SISO (θ, Ts 0.005571, na1/nb3, 98.23%); Yaw-rate SISO (ω_z,c, Ts 0.005581,
na2/nb2/nk2, 91.43%); Coupled pitch (θ, Ts 0.011272, na1/nb1, 99.26%); Coupled yaw-rate
(ω_z,c, Ts 0.005610, na3/nb4/nk2, 87.89%). Validation one-step/free-run: pitch 97.31/very-poor,
yaw 87.02/16.93, coupled-pitch 99.14/very-poor, coupled-yaw 90.99/poor.

## Phased plan & status
1. ✅ **Scaffold + config + 4 interfaces + CLAUDE.md + param tests.**
2. 🟦 Migrate: **36 recorded CSVs → `data/raw_logs/`** (M1–M3 + hardware; see MANIFEST); code ports incrementally per phase; `math_code_map.md` filling.
3. ✅ **Models:** `helicopter_2dof` (+ `linear_2dof`), `pitch_only`, `yaw_only`, `half_rotor` (NotValidated) behind `Model`; registry `models.make_model`; 34 tests pass.  ← done
4. ✅ **IO / state estimation:** encoders, IMU bias/noise (reproduced *exactly* from M1 log), ZOH, gyro-vs-encoder pitch-rate estimator (gyro 58.6× smoother); `runners/run_state_estimation.py`. 48 tests pass.  ← done
5. ✅ **Identification:** ARX/DARX reproduces Table II to 2 d.p. (pitch 98.23, yaw 91.43, coupled 99.26/88.07) + one-step/free-run split; excitation/validation/ss-realize; `run_identification.py`.  ← done
6. ⬜ Backends: offline (done) → virtual-twin → hardware, all behind `Backend`.
7. ✅ **Control:** full suite — PD, LQR, LQG, MPC, backstepping, SMC, NMPC (+ yawboost) on measured Δt; offline ranking matches Table IV (PD best pitch 0.182, linear under-drive at 0 sat); `run_benchmark.py`. `aero2` gyro estimator wired into `run_control --estimator`.  ← done
8. 🟦 Applications: **reference_tracking done** (square-wave); regulation-under-disturbance next. Runners `run_control/run_identification/run_benchmark/run_state_estimation` live.
9. ⬜ Docs pass: every `docs/*.md`, math-code map, references, insights.
10. ✅ **Neuromorphic BUILT** (`aero2/control/neuromorphic/`, `identification/neuromorphic_identifier.py`, `config/hyperlif.py`): HyperLIF neuron core + `HyperLIFResidualController` (registered `hyperlif`) + `NeuromorphicIdentifier` + **Python e-prop trainer `eprop.py`** (`EpropSNN`; replicates Julia gate-eligibility; ψ gate_exact/gate_temp/surrogate, credit exact/ss/dfa; **FD-validated**: gate Jacobian 2e-10, readout exact, hidden≈BPTT cos 0.97, learns). Gates now *trainable*, not fixed. Honest: fixed-weight residual/reservoir don't beat classical *yet* — needs trained gates + harder regimes (noise/hardware/**yaw**). **79 tests pass.** Survey `docs/10`; Julia↔Quanser bridge `docs/11`.

## Future phase — Adaptive HyperLIF (scaffold now, implement later)
Cross-repo sources to READ before integrating (do not assume contents):
`C:\00_Research_\Neural_Networks_and_Learning\01_Adaptive_HyperLIF`,
`...\04_Adaptive_HyperLIF_Nengo`,
`C:\00_Research_\Neuromorphic_Embodied_AI\01_HyperLIF_Gate_Residual`.
Plan: `NeuromorphicIdentifier` (same fit/validate API as `arx.py`) and
`HyperLIFController` (the `Controller` interface) + a gate/residual augmentation
on a model-based baseline (e.g. PD + neuromorphic residual). Keep partitioned and
labeled experimental; the classical pipeline must stay runnable on its own.

## Conventions
- State `x = [θ, θ̇, ψ, ψ̇]`, input `u = [u_p, u_y]`, output `y = [θ, ψ]`.
- Encoders: `θ = 2π·n_θ/2880`, `ψ = 2π·n_ψ/4096`.
- Command clip `±24 V` (HIL). Trim `U0 ≈ 1.4 V`.
- Tests: `pytest`. Constants asserted against paper values in `tests/test_config_*`.
