# Reproducibility

## Environment

- Julia: 1.12.7
- Project: `code/Project.toml`
- Manifest: `code/Manifest.toml`
- Canonical model dependency: `..\P1_HyperLIF_Learning\code\julia\learning`
- Local GPU discovered by workspace audit: NVIDIA RTX A500 Laptop, 4 GB, compute capability 8.6.
- The current P4 recognition runner is intentionally CPU-only.

## Install and test

```powershell
cd C:\Research\papers\P4_Viability_Heterogeneous_HyperLIF\code
julia --project=. -e "using Pkg; Pkg.instantiate(); Pkg.test()"
```

## Mechanism runs

```powershell
julia --project=. experiments\regime_probe.jl
julia --project=. experiments\calibrate_high_reactivity.jl
julia --project=. experiments\calibrate_dataset_activity.jl `
  C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5
```

```powershell
julia --project=. experiments\reachable_rate_envelope.jl `
  C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5
julia --project=. experiments\horizon_probe.jl
julia --project=. experiments\shared_gain_sweep.jl `
  C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5
```

Expected outputs:

- `code/results/regime_atlas.csv`
- `code/results/high_reactivity_calibration.csv`
- `code/results/dataset_activity_calibration.csv` (superseded; retained as record)
- `code/results/reachable_rate_envelope.csv`
- `code/results/shared_gain_sweep.csv`
- `code/results/horizon_probe.csv`

`horizon_probe.jl` and `shared_gain_sweep.jl` each print a `VERDICT` line. The horizon
probe's verdict must continue to name `burst`, which is what makes finding F2 a statement
about the input statistics rather than the cache horizon.

`shared_gain_sweep.jl` prints a `VERDICT` line naming the gain that satisfies all four
acceptance conditions at once. It must agree with the default in `shd_shared_gain_regimes`;
if it does not, the profile is stale relative to its evidence.

## Recognition smoke

```powershell
julia --project=. experiments\train_h5.jl `
  --cache=C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5 `
  --smoke --results-root=results\smoke_shd
```

## Budget-matched model triple

```powershell
bash experiments/run_matched_triple.sh
```

Runs `heterogeneous`, `ensemble`, and `homogeneous` at seeds 1-3 with equal total hidden
state (64), equal epoch and optimizer budgets, the shared-gain regime profile, and
homeostasis off. Aggregate with:

```powershell
julia --project=. experiments\aggregate_matched.jl results\matched_triple
```

## Paired tiny pilot (superseded)

The paired pilot below is retained for provenance only. Both of its runs selected epoch 1
and are byte-identical on the test split; see finding F4 in `PROGRESS_REGISTER.md`. The
runner now reports `homeostasis_effective` and warns when this occurs.

```powershell
julia --project=. experiments\train_h5.jl `
  --cache=C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5 `
  --epochs=3 --hidden-per-population=3 --batch-size=8 `
  --max-train=48 --max-test=40 --patience=0 --homeostasis=true `
  --results-root=results\pilot_shd

julia --project=. experiments\train_h5.jl `
  --cache=C:\Research\papers\P1_HyperLIF_Learning\code\hpc\upload_data\shd_wide_T20.h5 `
  --epochs=3 --hidden-per-population=3 --batch-size=8 `
  --max-train=48 --max-test=40 --patience=0 --homeostasis=false `
  --results-root=results\pilot_shd
```

The runner imports the P1 HDF5 normalization, seeded class-stratified capping, validation split,
one-hot encoding, and cache hashing functions. It chooses checkpoints by validation accuracy and
evaluates the capped test split once.

## Data inventory

| Dataset/cache | Local | Status |
|---|---:|---|
| `shd_wide_T20.h5` | yes | exact local Julia cache; hash recorded |
| `shd_wide_T20.pt` | yes | historical PyTorch cache |
| `nmnist_wide.pt` / source HDF5 | no | recover exact binary before replication |
| `dvsg32_wide.pt` | no | recover exact binary before replication |
| `dvsg48_wide.pt` | no | recover exact binary before replication |
| `ssc_wide_T20.pt` | no | recover exact binary before replication |

Do not silently regenerate a missing cache and reuse the historical dataset identity. Record a new
hash, preprocessing version, and split identity if regeneration becomes necessary.

