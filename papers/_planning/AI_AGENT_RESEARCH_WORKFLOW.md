# AI-Agent Research Workflow for HyperLIF

Created: 2026-07-19

Purpose: define the operating system for using an AI agent as a research collaborator across paper editing, experiments, figure/table generation, folder management, evidence audits, and publication decisions. This methodology is also intended to become a reusable contribution for future AI-managed research projects.

## North Star

The AI agent should keep the project moving from scattered results to submission-ready IEEE papers while preserving scientific honesty. It should make the project easier to resume, easier to audit, and harder to accidentally overclaim.

The agent's job is not only to write text or run scripts. It is to maintain a living chain:

```
reviewer concern -> research question -> experiment -> raw result -> aggregate table -> figure -> manuscript claim -> readiness decision
```

## Portfolio State

Current manuscript structure:

1. **P1 - HyperLIF Learning**: learning/architecture/statistical evidence.
2. **P2 - Nengo/NEF Reference**: implementation parity, stability, calibration, NengoCore capability, backend limits.
3. **P3 - Fused Control**: gate-state residual control plus adaptive/learned gate extensions.

Gate-state residual control should be mentioned in P1/P2 only as a brief bridge. The full controller belongs to P3.

## Control Plane

Every research folder should maintain these ledgers or equivalents:

| Ledger | Purpose |
|---|---|
| `PROGRESS_REGISTER.md` | Readiness percentages, open tasks, current status, and next actions. |
| `REVIEWER_ADVISOR_AUDIT.md` | Reviewer concerns and advisor guidance converted into concrete requirements. |
| `PAPER_PORTFOLIO_DECISION.md` | Paper split, venue strategy, and submission order. |
| `FIGURE_TABLE_MAP.md` | Every figure/table, source script, source CSV/log, caption, and manuscript section. |
| `MATH_CODE_MAP.md` | Every equation, code implementation, parameters, and validation script. |
| `REPRODUCIBILITY.md` | Commands, environments, seeds, and expected outputs. |
| `DECISION_LOG.md` | Major choices, alternatives rejected, and why. |

The current proposal folder contains the first three ledgers. Each paper folder should maintain its own detailed figure/table, math/code, and reproducibility maps.

## Feedback Cycle

Use this cycle after each experiment or manuscript edit.

### 1. Audit

Inputs:

- New CSVs/logs/results.
- Manuscript changes.
- Advisor comments.
- Reviewer constraints.
- Figure/table outputs.

Agent actions:

- Summarize what changed.
- Detect stale claims.
- Identify missing source paths.
- Check whether new evidence affects the paper split or readiness.

### 2. Claim Classification

Every claim must be classified:

| Class | Meaning | Manuscript handling |
|---|---|---|
| Safe | Backed by repeatable scripts, CSV/logs, figures, and current manuscript text. | Main result. |
| Qualified | Supported but limited by calibration, seed count, backend, or scope. | Result with caveat. |
| Exploratory | Interesting but not enough for main claim. | Discussion/future work. |
| Unsafe | Contradicted, stale, unverified, or overclaimed. | Remove or rewrite. |

### 3. Decision

Choose the next action using this priority order:

1. Directly addresses a reviewer concern.
2. Increases submission readiness.
3. Reduces overclaiming risk.
4. Generates a missing figure/table required by the manuscript.
5. Improves reproducibility or folder clarity.

### 4. Execute

The agent should prefer small, finishable work units:

- one experiment script;
- one aggregation table;
- one figure regeneration;
- one manuscript section;
- one validation pass;
- one progress-register update.

Long runs should have a preflight smoke test, expected outputs, and a restart/resume plan.

### 5. Aggregate

After execution:

- write/update CSV summary;
- regenerate figures/tables;
- update figure/table map;
- update logs;
- write a short result note.

No result should be used from memory alone.

### 6. Verify

Verification checklist:

- script ran without hidden failures;
- row counts and seeds match the design;
- figure labels and captions match the data;
- manuscript claim references the correct table/figure;
- limitations are explicit;
- no old TNNLS-unsafe claims re-enter the paper.

### 7. Report

Every session should end with:

- files changed;
- experiments run;
- key numbers;
- readiness change;
- remaining blockers;
- next recommended action.

## Paper-Specific Automation Roles

### P1 Agent Role

Focus:

- APEX cross-framework run;
- modern baseline integration;
- final statistics;
- IEEE LaTeX conversion;
- claim discipline around temporal state and sparse efficiency.

Do not let P1 become a control paper. Gate-state residual control is only a bridge/future-work insight.

### P2 Agent Role

Focus:

- update `main_ieee.tex`;
- capability matrix integration;
- PES rate-matched figure;
- backend portability section;
- NEF ensemble validation;
- exact equation-to-code traceability.

Do not claim hardware acceleration unless a backend actually supports HyperLIF.

### P3 Agent Role

Focus:

- fixed gate-state residual control as the core;
- adaptive/learned gate control as the extension;
- repeated trials;
- timing-shuffled/frozen-gate/energy-matched ablations;
- X2 rotor-level rows;
- controller-to-Nengo reference alignment.

Do not claim Adaptive HyperLIF contributes if gate-mode saturation makes it identical to plain HyperLIF.

## Folder Discipline

Recommended structure inside each active paper folder:

```
paper/
  main.tex
  sections/
  figures/
  tables/
results/
  raw/
  csv/
  logs/
  figures/
experiments/
  run_*.py
  aggregate_*.py
docs/
  FIGURE_TABLE_MAP.md
  MATH_CODE_MAP.md
  REPRODUCIBILITY.md
  DECISION_LOG.md
  CLAIM_LEDGER.md
```

The proposal folder remains the cross-paper command center. Individual paper folders hold paper-specific data and reproducibility artifacts.

## Methodology Contribution

This workflow can become a reusable contribution for future AI-assisted research projects:

- reviewer comments are converted into testable requirements;
- every claim is evidence-linked;
- manuscripts and experiments co-evolve through a controlled feedback loop;
- AI assistance is documented as a research-operations method, not hidden as informal labor;
- decisions are reversible because the rationale is recorded.

Possible future artifact:

> An AI-assisted research operations template for neuromorphic engineering projects, with claim ledgers, reproducibility maps, figure/table provenance, and reviewer-driven experiment queues.

