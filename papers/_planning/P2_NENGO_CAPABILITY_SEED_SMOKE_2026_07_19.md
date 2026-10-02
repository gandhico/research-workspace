# P2 Nengo Capability Seed-Smoke Summary

Date: 2026-07-19

Purpose: add and verify a seed-sweep runner for calibrated HyperLIF and Adaptive HyperLIF candidates across core Nengo/NEF applications.

Status note: superseded on 2026-07-19 by `P2_NENGO_CAPABILITY_SEED_PREFLIGHT_2026_07_19.md`, which records the completed three-seed run.

## Source

Runner:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\experiments\17_capability_seed_sweep.py`

Raw CSV:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\results\csv\17_capability_seed_sweep.csv`

Summary CSV:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\results\csv\17_capability_seed_sweep_summary.csv`

## Commands

The first attempt used the original default three-seed run. It exceeded the 15-minute interactive timeout and wrote no CSV, so the process was stopped and the runner default was changed to a safer one-seed smoke.

Successful smoke:

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper
.\.venv\Scripts\python.exe -u experiments\17_capability_seed_sweep.py --seeds 1
```

Future preflight:

```powershell
.\.venv\Scripts\python.exe -u experiments\17_capability_seed_sweep.py --preflight
```

Future paper-grade run:

```powershell
.\.venv\Scripts\python.exe -u experiments\17_capability_seed_sweep.py --paper
```

## Scope

- Apps: communication channel, function square, 2D transform, integrator, oscillator, working memory, PES learning.
- Candidates: native LIF `T001`, uncalibrated HyperLIF `T002`, calibrated HyperLIF `T023`, calibrated Adaptive HyperLIF `T033`.
- Completed smoke: one seed, 28 Nengo simulations, 0 failures.
- Local runtime: approximately 11.4 minutes for one seed. Full multi-seed evidence should be run as an overnight/HPC-style job.

## Key Smoke Results

| App | Best HyperLIF-family result | LIF reference | Interpretation |
|---|---:|---:|---|
| communication | T023 `0.2015` | T001 `0.1933` | calibrated T023 nearly matches LIF at lower rate |
| function square | T033 `0.2007` | T001 `0.1940` | Adaptive T033 nearly matches LIF |
| 2D transform | T023 `0.2049` | T001 `0.1967` | calibrated T023 close; T002 much worse |
| integrator | T023 `0.0080` | T001 `0.0109` | calibrated HyperLIF beats LIF on this seed |
| oscillator | T002 `0.0283`, T023 `0.0400` | T001 `0.1495` | HyperLIF-family strong on oscillator amplitude |
| working memory | T033 `0.0229` | T001 `0.0262` | Adaptive T033 beats LIF on this seed |
| PES learning | T033 `0.1063` | T001 `0.0466` | Adaptive T033 is much better than T023, but LIF remains faster |

Uncalibrated T002 is not a good general Nengo candidate: it is very sparse and weak on representation, memory, and PES.

## Claim Discipline

Safe now:

- A reusable seed-sweep runner exists and writes raw plus summary CSVs.
- The one-seed smoke reproduces the main calibration thesis: T023/T033 are useful calibrated candidates, while uncalibrated T002 is not adequate for general Nengo apps.
- Adaptive T033 is the stronger HyperLIF-family online-learning candidate in the smoke.

Still pending:

- Three- or five-seed statistics for T001/T002/T023/T033.
- Confidence intervals or paired tests.
- Paper-grade claim that T023/T033 are seed-robust across the six-app suite.

Readiness effect:

- P2 remains at 83%. This closes runner availability and smoke validation, but it does not complete the seed-sweep evidence gate.
