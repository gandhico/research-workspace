# Research continuation contract

This is the handoff for Claude, Codex, or another research agent working on P4. Read this file fully
before changing equations, code, experiments, or claims.

## Read order

1. `RESEARCH_PROGRAM.md`
2. `PROGRESS_REGISTER.md`
3. `CLAIM_LEDGER.md`
4. `MATH_CODE_MAP.md`
5. `REPRODUCIBILITY.md`
6. `DECISION_LOG.md`
7. `TASK_BOARD.md`
8. Parent contract: `..\P1_HyperLIF_Learning\AGENTS.md`

## Authorities

- P1 `code/julia/learning/src/HyperLIFLearning.jl` owns canonical HyperLIF dynamics, continuous,
  surrogate-event, and event-time learning semantics.
- P4 `code/src/ViabilityHyperLIF.jl` owns heterogeneity, viability, homeostasis, arbitration, and the
  reference safety shield.
- `CLAIM_LEDGER.md` owns permitted interpretation.
- JSON/CSV output owns numbers. Never quote a number from memory.

P4 depends on P1 by local Julia package path. Do not copy the P1 neuron into P4. If the canonical
equation must change, update P1 with its tests first, then rerun P4.

## Scientific invariants

- Upward crossing and threshold occupancy are different observables.
- A configured “subthreshold” or “high-reactivity” population earns its name only after measured
  activity confirms the intended regime on the declared input distribution.
- High occupancy with near-zero upcrossings is a block/saturation diagnosis, not high spiking.
- Continuous-state learning in a near-silent population is hybrid/analog computation, not spike-only.
- Population homeostasis and plant viability are different layers; log both.
- Low event count is not hardware energy.
- A CBF claim requires stated dynamics, barrier assumptions, feasibility, solver tolerance, and timing.
- Test data are evaluated once after validation checkpoint selection.
- Missing seeds, NaNs, block, and infeasible safety filters remain in the record.

## Agent coordination

1. Claim one task in `TASK_BOARD.md` with agent name, branch, and start time before editing.
2. Use one Git branch per task. Do not edit a file currently owned by another active task.
3. Keep raw outputs immutable. New runs get new timestamped directories.
4. After a run, update `PROGRESS_REGISTER.md`, `CLAIM_LEDGER.md`, and any affected map.
5. Record decisions that change scope, equations, splits, metrics, or claim language in
   `DECISION_LOG.md`.
6. End every session with files changed, commands run, key results, failures, blockers, and next action.
7. Never mark a task done solely because code exists; its acceptance check must pass.

If agents cannot share branches, they may exchange a patch plus a handoff note. The receiving agent
must rerun the acceptance check before merging the claim.

## Commands

From `code`:

```powershell
julia --project=. -e "using Pkg; Pkg.instantiate(); Pkg.test()"
julia --project=. experiments\regime_probe.jl
julia --project=. experiments\calibrate_high_reactivity.jl
julia --project=. experiments\calibrate_dataset_activity.jl `
  C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5
julia --project=. experiments\train_h5.jl `
  --cache=C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5 `
  --smoke --results-root=results\smoke_shd
```

## Definition of a reportable result

A result must include cache hash, exact split sizes, seed, population parameter profile, architecture,
learning/readout semantics, parameter count, optimizer settings, validation-selected checkpoint,
one-shot test metrics, per-population upcrossing and occupancy rates, failure status, device, Julia
environment, command line, and raw output path. Otherwise it is exploratory pipeline evidence.

## Current limitations

- Only the exact SHD HDF5 cache is present locally.
- The old N-MNIST, DVS-Gesture, and SSC binaries must be recovered for exact replication.
- P4 has no matched Julia LIF/PLIF/ALIF controls yet.
- The CBF projection is a reference feasibility check, not a production QP safety certificate.
- The three-epoch pilot is far too small for an accuracy or homeostasis claim.

