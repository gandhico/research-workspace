# Datasets & Data Handling — HyperLIF_Learning (HPC)

**Cache-driven workflow.** Every benchmark is one portable file — `{Xtr, ytr, Xte, yte}` as
`[N, T, F]` float tensors in a `.pt` — loaded by:

```bash
python hpc/train_hpc.py --data-file /fs1/scratch/gandhico/HyperLIF_Learning/cache/<dataset>.pt
```

No Tonic / figshare / 19 GB in the training loop. `grid.py` **auto-discovers** every `.pt` in the
cache dir and puts it in the array.

## Layout (all paths overridable via env — see `paths.sh`)

| What | Path |
|---|---|
| Code / project root (`HLL_ROOT`) | `/fs1/home/gandhico/HyperLIF_Learning/` |
| Cache (`HLL_CACHE`) | `/fs1/scratch/gandhico/HyperLIF_Learning/cache` |
| Results (`HLL_RESULTS`) | `/fs1/scratch/gandhico/HyperLIF_Learning/results` |
| Logs (`HLL_LOGS`) | `/fs1/scratch/gandhico/HyperLIF_Learning/logs` |
| Read-only source HDF5 (`HLL_DATA`) | `/fs1/scratch/gandhico/HyperLIF_replication/data` |

`hpc/` holds this Python workflow (+ the vendored `adhyperlif_triage` package); `src/` (the original
Julia HyperLIF) and `experiments/` are left untouched.

## The six benchmarks (source strategy + provenance manifest)

| Dataset | Source | Produce the cache with | Cache file |
|---|---|---|---|
| **SHD wide** | Tonic (zenkelab) | `make_caches.py` (generate/upload) | `shd_wide_T20.pt` |
| **N-MNIST wide** | your `nmnist_34x34.h5` | `extract_h5.py` (reads only needed rows) | `nmnist_wide.pt` |
| **DVS Gesture 32×32 wide** | your `dvs_gesture_32x32.h5` | `extract_h5.py` | `dvsg32_wide.pt` |
| **DVS Gesture 48×48 wide** | your `dvs_gesture_48x48.h5` | `extract_h5.py` | `dvsg48_wide.pt` |
| **SSC wide** | Tonic (zenkelab; split-API fixed) | `make_caches.py --datasets ssc` | `ssc_wide_T20.pt` |
| **CIFAR10-DVS wide** | figshare | `make_caches.py --datasets cifar10dvs` (try) | `cifar10dvs_wide_T20.pt` |

Only **SHD** crosses the 500 MB upload limit concern (it's ~157 MB, fine). Everything else is
produced **on the cluster** and lives in scratch, so size is unconstrained there.

> Each cache keeps its own `T` (extracted HDF5 uses the file's existing time binning; Tonic caches
> use `--T 20`). `train_hpc.py` reads `T` and `F` from the tensor shape, so caches need not match.

## The benchmark grid

`discovered caches × {LIF, HyperLIF, Adaptive HyperLIF} × 6 readouts × 5 seeds`:

| Readout | Feature | Note |
|---|---|---|
| `membrane` | v̄ | voltage |
| `spike_count` | Σ spikes | event count |
| `gate` | r̄ | gate-state (zero for LIF) |
| `hybrid_gr` | [r̄, Ḡ] | gate / conductance (the β-engagement test) |
| `hybrid_vr` | [v̄, r̄] | voltage / gate |
| `hybrid_vr_conductance` | [v̄, r̄, Ḡ] | voltage / gate / conductance |

All six datasets present ⇒ `6 × 3 × 6 × 5 = 540` jobs. Each registry row logs: dataset, neuron,
readout, seed, accuracy, macro_f1, events_per_sample, gate_mean, **stable** (no NaN), nan_batches,
n_classes, T, **provenance** (cache filename), wall time. `aggregate_hpc.py` reduces to seed
mean ± std per (dataset, config) with the stable-fraction and events columns.

## Best practices

1. **Inspect before you extract.** `extract_h5.py --inspect` first — the tool *guesses* the HDF5
   schema assuming `[N, T, …]`. If the printed shapes don't look right, paste them; override with
   `--data-key` / `--label-key`.
2. **The parity gate is the go/no-go.** `setup_env.sh` runs it; it must PASS before any number is
   trusted — it proves the snnTorch neuron *is* the validated model.
3. **Preflight one real job before the array.** `hpc/preflight.sh` runs index 0 for 2 epochs on a
   GPU — catches env/path/import issues for cents, not a 540-job failure.
4. **Balanced + seeded subsets = reproducible.** Extraction takes a fixed count per class with a
   fixed seed; the **SLURM seed is the *training* seed only** — the data subset is fixed across
   seeds (don't re-extract per seed).
5. **Preprocessing provenance matters.** SHD/SSC/CIFAR10-DVS are Tonic-binned; N-MNIST/DVS come from
   your audit HDF5 — different pipelines. Compare **rankings within each dataset**, not matched
   absolute accuracy across them. The `provenance` column keeps this traceable.
6. **Sanity-check each job.** Trust accuracy only when `stable=True` and `events_per_sample` is
   sensible (not 0, not absurd). Both are logged and surfaced by `aggregate_hpc.py`.
7. **Don't write to `HLL_DATA`.** It's the read-only replication source; all outputs go to scratch
   cache/results/logs.
8. **Start results fresh per benchmark sweep.** The registry header is fixed on first write — a new
   scratch `results/` dir avoids ragged CSVs if the schema ever changes.
9. **LIF + gate readouts are intentionally vacuous** (LIF has no gate → zero channels): keep them as
   the honest baseline, but read them as such.
