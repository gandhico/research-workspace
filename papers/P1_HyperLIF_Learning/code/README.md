# Adaptive HyperLIF — Local Triage Benchmark (PyTorch + Tonic)

Local, reproducible benchmark to decide **which Adaptive HyperLIF architectures deserve HPC
scaling** — before spending HPC time. Substrate: PyTorch (surrogate-gradient training allowed)
with Tonic neuromorphic datasets. The validated Julia/Nengo line stays the *exact-dynamics
reference*; this project re-validates against it (see the parity gate).

> Companion to the progress report in `../06_Progress_Report_Since_Submission/`. This is the
> Phase-0 foundation: the runnable parity gate plus the skeleton the experiment matrix plugs into.

## The question (per dataset, before HPC)

> Which architecture **learns fastest, stays stable, stays sparse**, and gives promising
> accuracy under small-data / short-training / stress conditions — and does swapping
> LIF → HyperLIF → Adaptive(+origin) extract *more per spike* from each circuit?

## Status

| Piece | State |
|---|---|
| PyTorch neuron (HyperLIF, Adaptive, +origin hook, LIF baseline) | ✅ `src/adhyperlif_triage/neurons/hyperlif_torch.py` |
| Vendored validated reference (parity target) | ✅ `…/neurons/reference_numpy.py` |
| **Parity gate** (PyTorch == Nengo reference to machine precision) | ✅ `scripts/run_parity.py` → `docs/PARITY.md` |
| Reproducible run IO + dynamics metrics + seeding | ✅ `…/utils/`, `…/metrics/` |
| Config-driven runner (`parity` / `smoke` / `tiny`) | ✅ `…/runner.py` |
| Neuron roster: + ALIF, surrogate-LIF, adaptive-θ_event | ✅ `…/neurons/` (parity preserved) |
| Readouts + feedforward model + surrogate-BPTT trainer | ✅ `…/models/`, `…/train/` |
| Synthetic temporal task + **full roster smoke verified** | ✅ `…/data/synthetic.py` → `results/smoke_synthetic/` |
| Tonic adapter (N-MNIST / SHD / SSC / CIFAR10-DVS) | ✅ `…/data/tonic_adapter.py` (frame→feature path unit-tested; first real run downloads) |
| Real 3-dataset spine runs + conv/reservoir/WTA + origin (1b) | ⛏ next |

## Quick start

```powershell
# 1. environment (CPU torch is enough for the parity gate)
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install numpy pyyaml torch --index-url https://download.pytorch.org/whl/cpu
# (torch line: use the pytorch CPU index; numpy/pyyaml come from PyPI)

# 2. run the parity gate
.\.venv\Scripts\python.exe scripts\run_parity.py
#   -> results/parity/parity_metrics.csv + docs/PARITY.md  (must PASS before any benchmark)

# 3. run the full roster on the synthetic temporal task (no download)
.\.venv\Scripts\python.exe scripts\run_smoke.py --seeds 0,1,2 --epochs 5
#   -> results/smoke_synthetic/{summary.md, ranking.csv, _registry.csv}

# 4. first REAL dataset (downloads on first run; SHD = the temporal test)
.\.venv\Scripts\python.exe -m pip install tonic     # note: pins numpy<2
.\.venv\Scripts\python.exe scripts\run_smoke.py --dataset shd --mode smoke --epochs 5 --T 20
```

## The experiment matrix (Phase 1)

All four research threads are axes of **one** config-driven harness:

| Axis | Values | Idea |
|---|---|---|
| neuron | LIF, A-LIF, HyperLIF, Adaptive HyperLIF, **+origin** (`delta_reset>0`) | 1 (origin) |
| readout | spike-count, filtered-event, voltage, gate, `[v,r]`, `[v,r,dr/dt]`, `[v,r,tanh(G/20)]` | prior work |
| architecture | feedforward, conv (APEX-style), **reservoir/LSM**, **lateral-inhibition/WTA**, FF/FB E/I | 3 (survey) |
| input rep | event frames, voxel grid, time surface, ON/OFF DoG | 3 (survey) |
| training | surrogate-BP, e-prop (annealed ψ), FORCE/RLS, STDP+readout | surrogates OK |
| dataset / mode | spine → fan-out · smoke / tiny / stress | 2 (benchmark) |

**Apples-to-apples rule:** the "original" architecture is **re-run inside this harness**, never
compared to the previously reported numbers (those were a surrogate-LIF pipeline; see the audit).

## Reproducibility layout

```text
results/<dataset>/<architecture>/seed<seed>/<timestamp>/{metrics.csv, summary.json, *.png}
results/_registry.csv          # one row per run → aggregation + ranking
docs/{PARITY, METHODS, SAFE_CLAIMS, UNSAFE_CLAIMS}.md
```

## HPC deployment (`HyperLIF_Learning`)

The full-scale event-vision benchmark is packaged in `hpc/` for the cluster project
`/fs1/home/gandhico/HyperLIF_Learning/` (scratch cache/results/logs under
`/fs1/scratch/gandhico/HyperLIF_Learning/`, read-only source HDF5 under
`…/HyperLIF_replication/data/`). It is **cache-driven**: each benchmark is a portable
`{Xtr,ytr,Xte,yte}.pt` (`[N,T,F]`) that `grid.py` auto-discovers from `$HLL_CACHE`. Six datasets
(SHD, N-MNIST, DVS Gesture 32/48, SSC, CIFAR10-DVS) × {LIF, HyperLIF, Adaptive} × 6 readouts × 5
seeds. See [`hpc/README.md`](hpc/README.md) for the run sequence and [`hpc/DATA.md`](hpc/DATA.md)
for the source strategy + best practices.

## Roadmap

- **Phase 0 (this):** neuron + parity gate + repro skeleton.
- **Phase 1:** Tonic adapter + surrogate trainer; 3-dataset spine (N-MNIST, **SHD**, CIFAR10-DVS), smoke→tiny.
- **Phase 2:** origin variants (idea 1) + reservoir / lateral-inhibition (idea 3) as axes.
- **Phase 3:** stress + robotics streams (DSEC/MVSEC/EVIMO2) — bridge to control.
- **Phase 4:** rank (decision-rule score) → HPC shortlist.
