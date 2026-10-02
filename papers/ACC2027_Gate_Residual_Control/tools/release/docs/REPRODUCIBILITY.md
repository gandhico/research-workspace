# Reproducibility

Three levels, from seconds to hours. Everything runs from this `code/` folder; paths below are relative to it.

## 0. Install

```bash
python -m venv .venv && .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install numpy==2.5.2 mujoco==3.12.0 nengo==4.1.0 matplotlib pandas pyyaml
```

The published runs used Python 3.13, NumPy 2.5.2, MuJoCo 3.12.0, Nengo 4.1.0 (recorded in every `manifest.json`).
MuJoCo Menagerie models (Skydio X2, Crazyflie 2) are included under `third_party/` with their licenses; the 1.5× CF2 rotor
design is `models/cf2_rotor_design/`.

## 1. Check every number in the paper — seconds, no simulation

```bash
python reproduce/verify_acc2027_claims.py
```

Recomputes the 59 numbers the paper reports (abstract, Table II, Sec. VI) from the shipped run summaries and prints paper value
vs. recomputed value for each; writes `reproduce/claims_check.md`. Expected: **59/59 match**. Two checks are computed from
per-step traces, which are not distributed ([`../DATA.md`](../DATA.md)); they read `reproduce/trace_derived.json`, which the
same script rewrites whenever the traces are present (e.g. after re-running the campaigns).

## 2. Re-run any mission — about a minute each

```bash
python reproduce/run_mission_viewer.py --platform x2 --mission hard45 --arm cmg        # live MuJoCo viewer
python reproduce/run_mission_viewer.py --platform cf2 --mission hardstep --arm pdff --no-viewer
python reproduce/record_mission.py --platform x2 --mission roll --arm cmg               # pose + full neural trace
```

Both wrap the paper's sealed runner (`experiments/final_robustness_gating_2026-09-20/run_final_robustness.py`) without changing
it and end with **MATCH / DIFFERS** against the published number. All 20 primary runs (2 platforms × 5 missions × 2 arms)
were re-run this way for the figures and the video: relative difference 0.0 in every case.

## 3. Re-run whole campaigns — minutes to hours

```powershell
powershell -File reproduce/reproduce_all.ps1 -Stage validation   # must print PASS first (new runner vs archived table, 5e-15)
powershell -File reproduce/reproduce_all.ps1 -Stage primary      # ~60 runs, ~10 min (4 workers)
powershell -File reproduce/reproduce_all.ps1 -Stage robustness   # noise + bursts, ~470 runs, ~100 min
powershell -File reproduce/reproduce_all.ps1 -Stage portability  # six controller families, ~140 runs, ~30 min
powershell -File reproduce/reproduce_all.ps1 -Stage neuronbasis  # neuron and non-neural bases, 186 runs, ~1 h (10 workers)
powershell -File reproduce/reproduce_all.ps1 -Stage figures      # paper figures and Table II block
```

Campaigns resume from existing `summary.json` files and never overwrite archived runs. (The stage runner is PowerShell; each
stage is a short list of Python commands that run unchanged on Linux/macOS.)

## The claim → code map

[`REPRODUCE_ACC2027.md`](REPRODUCE_ACC2027.md) lists every paper number with the script that produced the runs, the script that
builds the number, the output file and its verifier row.

## Integrity guarantees

* **Pre-registration.** Protocol, metrics and decision rules sealed (SHA-256) before any campaign result; amendments A1–A5
  dated in place: `experiments/final_robustness_gating_2026-09-20/PREREGISTRATION.md`, checked by `verify_seal.py`.
* **Provenance.** Every run writes `manifest.json` with the SHA-256 of every source and model file, the configuration hash, the
  git commit and the library versions. The files in this folder are byte-identical to those recorded by the published runs
  (`RELEASE_MANIFEST.json` lists every shipped file with its hash).
* **No silent edits.** Archived runners are never modified; every changed runner is a copy with a verified minimal diff.
* **Cross-checks.** New runner vs. archived Table II block: $5.0\times10^{-15}$. Nengo vs. direct NumPy controller: $2.0\times10^{-6}$.
  Exact recovery at $\beta=0$: relative difference 0.

## What is not here

Per-step traces (`trace.csv`, `neural_trace_full_rate.npz`, ≈ 57 GB) are not distributed; any run regenerates them
(level 2 above, [`../DATA.md`](../DATA.md)). Exploratory plots of the working repository are omitted; the curated figures are in
[`../figures`](../figures).
