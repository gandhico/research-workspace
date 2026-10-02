# 00 — Overview

## What this is
A math-traceable refactor of the Quanser Aero2 system-ID/control project, with a
first-class offline / virtual-twin / hardware separation and a scaffold for a
future Adaptive HyperLIF (neuromorphic) phase. Governing spec: `00_source_brief.md`.

## Repository layout
```
aero2/
  config/        params, gains, sensors, timing, references  (single source of truth)
  models/        base.Model + variants (P3)
  io/            encoders, imu_calibration, state_estimation, sampling (P4)
  identification/excitation, nonparametric, arx, validation, ss_realize (P5)
  control/       base.Controller; linear/ nonlinear/ neuromorphic/ (P7, P10)
  execution/     backend.Backend; offline (live), virtual_twin, hardware (P6)
  applications/  base.Application; reference_tracking, regulation_disturbance (P8)
  benchmarking/  metrics, compare (P11)
  utils/
runners/   thin CLIs driven by configs/ (P12)
configs/   YAML experiment configs (model × mode × controller × application)
data/      raw_logs/ (migrated CSVs), identified_models/
results/   figures/, tables/
tests/     param + interface contract tests
docs/      this folder
```

## The contract (brief §5)
`model × backend × controller × application` compose with no conditionals. See
`07_execution_modes.md`. Swapping `offline → virtual_twin → hardware` is one
config field.

## Honest results (do not "fix")
Strong one-step / weak free-run; PD strongest overall; SMC best nonlinear
pitch-tail; NMPC benchmarkable but not competitive; **yaw is the unresolved axis**.
Timing on the *measured* Δt is the headline lesson. Numbers: `09_benchmarking.md`.

## Status
Phase 1 complete (scaffold, config, four interfaces, offline backend, tests).
Phase map and progress: `../CLAUDE.md`.
