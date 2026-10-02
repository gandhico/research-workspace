# HPC Event-Vision Benchmark — Adaptive HyperLIF (snnTorch) · HyperLIF_Learning

Cache-driven, full-scale benchmark for the **parity-validated snnTorch HyperLIF** neuron, packaged
for a SLURM cluster. Each array task trains one `(dataset × neuron × readout × seed)` config on a
GPU; results aggregate into per-dataset rankings + a cross-dataset table.

> Local de-risk is **done**: the snnTorch neuron is parity-validated to machine precision and trains
> stably. This package runs the heavy training the local CPU can't.

## Cluster layout

| What | Path | Env |
|---|---|---|
| Project root (this repo) | `/fs1/home/gandhico/HyperLIF_Learning/` | `HLL_ROOT` |
| Cache (`.pt` benchmarks) | `/fs1/scratch/gandhico/HyperLIF_Learning/cache` | `HLL_CACHE` |
| Results | `/fs1/scratch/gandhico/HyperLIF_Learning/results` | `HLL_RESULTS` |
| Logs | `/fs1/scratch/gandhico/HyperLIF_Learning/logs` | `HLL_LOGS` |
| Read-only source HDF5 | `/fs1/scratch/gandhico/HyperLIF_replication/data` | `HLL_DATA` |

`hpc/` holds the Python workflow. The packages are resolved from `../src` (the repository's
`code/src` directory) or from the explicit `HLL_PKG` / `HLL_ARCH` overrides. They are not vendored
inside `hpc/`. All paths come from `paths.sh` and are env-overridable.

## Pieces

| file | role |
|---|---|
| `paths.sh` | canonical, env-overridable paths + `PYTHONPATH` + helpers (sourced by all shell scripts) |
| `train_hpc.py` | entry point — trains ONE config (`--data-file`), logs metrics + registry row |
| `grid.py` | **auto-discovers** `$HLL_CACHE/*.pt` → maps `SLURM_ARRAY_TASK_ID` to args |
| `make_caches.py` | produce `.pt` caches from Tonic (SHD / SSC / CIFAR10-DVS) → `$HLL_CACHE` |
| `extract_h5.py` | produce the **same** caches from your existing HDF5 (N-MNIST / DVS Gesture) |
| `run_array.slurm` | SBATCH array (1 GPU/task; logs under `$HLL_LOGS`) |
| `preflight.sh` | parity gate + discover caches + run one real job before the full array |
| `setup_env.sh` | one-time venv + GPU torch + snntorch/tonic/h5py + parity gate + scratch dirs |
| `aggregate_hpc.py` | combine registry → `$HLL_RESULTS/HPC_RESULTS.md` |
| **`DATA.md`** | **dataset plan, provenance manifest, best practices — read this** |
| `../src/.../models/snntorch_net.py` | the configurable snnTorch classifier (6 readouts) |
| `../src/.../neurons/snntorch_hyperlif.py` | the parity-validated HyperLIF neuron |

## The grid (`grid.py`)

`discovered caches × {lif, hyperlif, adaptive} × 6 readouts × 5 seeds`. Readouts:
`membrane, spike_count, gate, hybrid_gr, hybrid_vr, hybrid_vr_conductance` (for LIF the gate/
conductance channels are zero — the honest baseline). All six datasets ⇒ `6×3×6×5 = 540` jobs.
Run `python hpc/grid.py --list` to see caches + count, then size `--array`.

## Run sequence (on the cluster)

```bash
cd /fs1/home/gandhico/HyperLIF_Learning

# 0. one-time: venv + deps + parity gate (edit module/CUDA lines in setup_env.sh first)
bash hpc/setup_env.sh
# EACH login: prepare the shell — sets HLL_* + PYTHONPATH AND activates .venv.
# (setup_env.sh activates the venv only inside the script; you must activate it in your shell.)
source hpc/paths.sh           # -> if torch is still "not found", run: source .venv/bin/activate

# 1. create scratch folders (setup_env.sh also does this; explicit here)
mkdir -p "$HLL_CACHE" "$HLL_RESULTS" "$HLL_LOGS"

# 2. upload the one upload-sized cache from your laptop (run locally):
#    scp hpc/upload_data/shd_wide_T20.pt gandhico@<cluster>:$HLL_CACHE/

# 3. inspect the existing HDF5 (confirm layout before extracting)
python hpc/extract_h5.py --h5 nmnist_34x34.h5      --inspect
python hpc/extract_h5.py --h5 dvs_gesture_32x32.h5 --inspect
python hpc/extract_h5.py --h5 dvs_gesture_48x48.h5 --inspect

# 4. extract N-MNIST + both DVS Gesture caches  -> $HLL_CACHE/*.pt
python hpc/extract_h5.py --h5 nmnist_34x34.h5      --out nmnist_wide.pt
python hpc/extract_h5.py --h5 dvs_gesture_32x32.h5 --out dvsg32_wide.pt
python hpc/extract_h5.py --h5 dvs_gesture_48x48.h5 --out dvsg48_wide.pt

# 5. generate SSC cache on the cluster
python hpc/make_caches.py --datasets ssc --mode wide --T 20

# 6. attempt CIFAR10-DVS cache on the cluster (figshare)
python hpc/make_caches.py --datasets cifar10dvs --mode wide --T 20 || \
  echo "CIFAR10-DVS unavailable — array will simply omit it"

# 7. preflight: parity + discover + ONE real job (ideally on a GPU node)
srun --gres=gpu:1 --pty bash hpc/preflight.sh

# 8. submit (BUNDLED: 1 job per dataset x neuron, loops readouts x seeds; fits small submit caps)
N=$(python hpc/grid.py --bundle-count)        # e.g. 15 (5 caches x 3 neurons), 18 with CIFAR10-DVS
sbatch --partition=normal --array=0-$((N-1))%10 hpc/run_array.slurm   # %10 = Discovery normal cap
#   resumable: re-submitting skips configs already in the registry (train_hpc --skip-existing)

# 9. aggregate when the array finishes
python hpc/aggregate_hpc.py            # -> $HLL_RESULTS/HPC_RESULTS.md
```

## What it validates

Whether the cluster, at full scale, reproduces the local-harness ranking — **HyperLIF ≥ LIF**, the
**hybrid gate/conductance readout strongest**, and the β / readout-scope findings (`gate` vs
`hybrid_gr` directly tests the structural-blindness hypothesis). Per-config `stable` (no NaN) and
sampled activity carry numerical and activity information. For historical snnTorch
HyperLIF/Adaptive runs, the legacy key `events_per_sample` is **threshold occupancy**, not an
upward-crossing count. It must not be interpreted as a spike count or an energy measurement.
Report `activity_semantics`, seed standard deviation, and split sizes; hardware energy remains
unmeasured.

## Notes
- `train_hpc.py` auto-uses CUDA if present. Per-task budget: 30 epochs, hidden 256, batch 64.
- Resumable at the array level — re-`sbatch` only the failed `--array` indices.
- The `adhyperlif_triage` package is found via `HLL_PKG` and then repository `../src`; the parity
  scripts live in `hpc/scripts/`.
