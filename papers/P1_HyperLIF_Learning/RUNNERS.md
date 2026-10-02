# P1 — Runners / Launchers, mapped to the paper

Every table/figure in `main.tex`, matched to the script that generates it and the result
folder(s) it reads. Confidence noted per row — most are confirmed by matching exact numbers
in `main.tex` against the raw registry files; two are not currently traceable (see §4).

## 1. Confirmed: table ↔ script ↔ result folder

| Paper item | Script | Command | Result folder | Confidence |
|---|---|---|---|---|
| Table `tab:baseline-shortlist` (PLIF/ALIF reviewer baselines, §"Reviewer Baselines") | `scripts/run_p1_baseline_preflight.py` (N-MNIST tiny) + `scripts/run_p1_shd_wide_arch_shortlist.py` (SHD-wide, all 3 architectures) | see `results/p1_plif_alif_ff_nmnist_tiny_20260719/` and `results/p1_baseline_arch_shortlist_shd_wide_20260719/HPC_RESULTS.md` for exact invocation notes | `p1_plif_alif_ff_nmnist_tiny_20260719/`, `p1_baseline_arch_shortlist_shd_wide_20260719/` (both dated 2026-07-19) | **Confirmed** — numbers match main.tex to 3-4 decimals |
| Table `tab:arch-transfer` + Fig. 4 (`fig4_arch_transfer_gap.png`), §"Architecture Transfer" | `hpc/train_hpc.py` via `hpc/run_array.slurm` (SLURM cluster array), aggregated by `hpc/aggregate_hpc.py` | `sbatch --array=0-$((N-1))%10 hpc/run_array.slurm` per `hpc/README.md` §"Run sequence" | `results/roster60/` (2759 runs, 5 datasets, 129 configs) | **Confirmed** — `conv.lif.membrane`=0.7693, `conv.hyperlif.membrane`=0.8514 match the paper's conv/DVS-32 row exactly. Figure is dated 3 days before the registry's final timestamp — it used a near-final snapshot of the same in-progress cluster run, not a separate dataset. |
| `spine_summary.md` (cross-dataset summary, NOT cited in the current paper) | `scripts/aggregate_spine.py`, fed by `scripts/run_phase1b.py`/`run_phase2.py`/`run_smoke.py` | `python scripts/aggregate_spine.py --mode tiny` | `results/phase1b_shd/`, `phase1b_nmnist/`, `phase2res_*/`, `smoke_*/`, `tiny_*/` | Confirmed by script docstring, but **this is superseded/exploratory data the paper does not cite** — don't confuse with current results (see prior review notes). |

## 2. Supporting pipeline (not itself paper numbers)

| Script | Role |
|---|---|
| `hpc/grid.py` | Auto-discovers `.pt` caches, maps SLURM array index → run config |
| `hpc/make_caches.py` / `extract_h5.py` | Build the `.pt` training caches from Tonic / existing HDF5 |
| `hpc/preflight.sh` | Parity gate + one real job before submitting the full array |
| `scripts/run_parity.py` / `run_parity_snntorch.py` | Neuron parity gate (validates the snnTorch port against the reference math before any training run counts) |
| `scripts/download_dataset.py` | Dataset acquisition |
| `scripts/salvage_registry.py` | Recovers a registry from partial/crashed runs |

**Note**: `scripts/run_attitude.py`, `run_control.py`, and `run_gate_sweep.py` are present in
this folder but their docstrings ("gate-state residual", control language) indicate they're
vendored from the P3 control-project codebase, not scripts that generated any P1 paper result.

## 3. Reproducing the full pipeline

```powershell
# Local (CPU, what the current paper tables actually used):
conda activate hyperlif
python scripts\run_p1_baseline_preflight.py         # -> results\p1_plif_alif_ff_nmnist_tiny_YYYYMMDD\
python scripts\run_p1_shd_wide_arch_shortlist.py     # -> results\p1_baseline_arch_shortlist_shd_wide_YYYYMMDD\

# Cluster (SLURM, for the architecture-transfer table/figure — needs the HPC cluster, not this laptop):
#   see hpc\README.md "Run sequence" section, steps 0-9
```

## 4. Resolved tonight — `tab:ff-temporal` and `tab:gate-readout`

**Found and confirmed.** Both were missing from every local/D: source, but existed on the HPC
cluster itself (SLURM job **559182**, matching the previously-empty local `hpc_559182\` folder)
inside a fresh compressed backup you pulled down tonight
(`/fs1/scratch/gandhico/_download_archives/HyperLIF_Learning_2026-08-13.tar.gz`, cluster job
`pack_hll`). The source file is `results\_registry_ff_559182.csv`, now copied into
`results\hpc_559182\`.

Verified by direct aggregation, not just eyeballing — averaging the 5 per-seed rows for
`shd_wide_T20, lif, spike_count` gives 0.4835, matching the paper's LIF/SHD value
(0.484±0.008) to 3 decimals. All 12 DVS-32 readout×neuron combinations in
`tab:gate-readout` matched the aggregated registry to 3-4 decimals (e.g. `lif, gate` → 0.1314
vs. paper's 0.131±0.023; `hyperlif, spike_count` → 0.8179 vs. paper's 0.818).

**Command** (per `hpc/README.md`'s array-submission pattern, this specific run being job
559182): the feedforward-only slice of the same `hpc/train_hpc.py` / `run_array.slurm`
pipeline described in §1, run separately from the `roster60` architecture-transfer campaign.

## 5. Resolved — Julia/APEX validation code

**Julia/APEX validation** (`tab:apex-validation`, `tab:apex-v2-traceability`): source code found
in your own Downloads folder (not the `julia_depot*` cluster archives — those are just the
package depot) and is now at `code\apex_julia\`: `src\HyperLIF.jl`, `HyperLIFadapt.jl`,
`HyperSNN.jl`, `HebbianLearning.jl`, `DVSLoader.jl`, plus the environment definition
(`Project.toml`: Flux, CUDA, Zygote, ForwardDiff, DifferentialEquations, MLDatasets) and one
set of failed-run logs (`failed_run_logs_567440\`, job errored on `CONVRES_CONFIG_FILE`
unset — kept for debugging context, not a success log). To run: instantiate the environment
first (`julia --project=code/apex_julia -e "import Pkg; Pkg.instantiate()"`), matching the
convention in `C:\Research\ENVIRONMENTS.md`.
