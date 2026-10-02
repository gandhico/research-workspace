# P2 Nengo Capability Seed-Preflight Summary

Date: 2026-07-19

Purpose: record the completed three-seed preflight for the calibrated HyperLIF and Adaptive HyperLIF Nengo/NEF candidates. This supersedes the earlier one-seed smoke as the current seed-sweep evidence artifact.

Status note: the preflight table was integrated into the active P2 manuscript on 2026-07-19; see `P2_MANUSCRIPT_INTEGRATION_2026_07_19.md`.

## Source

Runner:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\experiments\17_capability_seed_sweep.py`

Raw CSV:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\results\csv\17_capability_seed_sweep.csv`

Summary CSV:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\results\csv\17_capability_seed_sweep_summary.csv`

Log:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\results\logs\17_capability_seed_sweep_preflight_20260719.log`

Stderr:

`C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper\results\logs\17_capability_seed_sweep_preflight_20260719.err`

## Command

```powershell
cd C:\00_Research_\Neural_Networks_and_Learning\04_Adaptive_HyperLIF_Nengo\05_Adaptive_HyperLIF_Nengo_Paper
.\.venv\Scripts\python.exe -u experiments\17_capability_seed_sweep.py --preflight
```

## Scope

- Seeds: 1, 2, 3.
- Apps: communication channel, function square, 2D transform, integrator, oscillator, working memory, PES learning.
- Candidates: native LIF `T001`, uncalibrated HyperLIF `T002`, calibrated HyperLIF `T023`, calibrated Adaptive HyperLIF `T033`.
- Completed simulations: 84/84.
- Failures: 0.
- Stderr: empty.

## Aggregate Results

| App | Metric | LIF T001 | T002 uncal. HyperLIF | T023 cal. HyperLIF | T033 cal. Adaptive |
|---|---|---:|---:|---:|---:|
| integrator | hold error to 0.3 | 0.0118 +/- 0.0039, 87.4 Hz | 0.1251 +/- 0.0843, 12.8 Hz | 0.0037 +/- 0.0039, 39.1 Hz | 0.0089 +/- 0.0060, 46.6 Hz |
| oscillator | amplitude error | 0.1543 +/- 0.0042, 114.8 Hz | 0.0463 +/- 0.0186, 8.0 Hz | 0.0672 +/- 0.0310, 38.3 Hz | 0.1656 +/- 0.0066, 60.8 Hz |
| communication | decode RMSE | 0.1934 +/- 0.0003, 120.3 Hz | 0.5092 +/- 0.0140, 6.1 Hz | 0.2030 +/- 0.0013, 33.6 Hz | 0.2037 +/- 0.0012, 63.2 Hz |
| function square | function RMSE | 0.1937 +/- 0.0002, 118.5 Hz | 0.4274 +/- 0.0244, 5.9 Hz | 0.2299 +/- 0.0069, 32.2 Hz | 0.2004 +/- 0.0006, 61.8 Hz |
| 2D transform | transform RMSE | 0.1963 +/- 0.0010, 118.2 Hz | 0.4154 +/- 0.0194, 6.1 Hz | 0.2079 +/- 0.0038, 33.1 Hz | 0.2087 +/- 0.0005, 62.0 Hz |
| working memory | hold error to 0.6 | 0.0292 +/- 0.0039, 103.5 Hz | 0.0820 +/- 0.0197, 7.5 Hz | 0.0368 +/- 0.0169, 40.7 Hz | 0.0291 +/- 0.0086, 54.9 Hz |
| PES learning | late RMSE | 0.0489 +/- 0.0020, 117.9 Hz | 0.5671 +/- 0.0365, 6.0 Hz | 0.4393 +/- 0.0119, 33.9 Hz | 0.1025 +/- 0.0031, 62.9 Hz |

## Interpretation

Safe now:

- The calibrated Nengo candidates complete a three-seed, seven-app NEF preflight with no runtime failures.
- `T023` is the strongest low-rate calibrated HyperLIF candidate for NEF computation/dynamics: it is close to LIF on communication and transform tasks, beats LIF on integrator error, and strongly improves oscillator amplitude error at much lower rate.
- `T033` is the strongest Adaptive HyperLIF candidate for memory and online-learning behavior among the HyperLIF-family candidates: it matches working-memory error with roughly half the LIF rate and is far better than `T023` on PES learning.
- Uncalibrated `T002` is useful as a sparsity/operating-point cautionary baseline, not as the general Nengo candidate.

Still pending:

- Integrate these results into `paper\main_ieee.tex` with a compact table and careful text.
- Decide whether the final manuscript needs the five-seed `--paper` sweep or whether the three-seed preflight is sufficient for a methods/reference paper.
- Add NEF ensemble tuning/decoder validation for the final calibrated candidate.
- Tie every P2 claim to a table, CSV, script, log, and figure/caption.

Readiness effect:

- P2 moves from 83% to 84%. The seed-sweep evidence gap is no longer open at smoke level, but the manuscript still needs integration, final figure/table regeneration, and reviewer-safe claim framing before it should move into the high-80s.
