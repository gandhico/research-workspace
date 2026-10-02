# research-workspace (private)

Source-only snapshot of `C:\Research\` taken 2026-10-01, before handing back a rented laptop.
Everything needed to **re-run** the work is here (code, math, LaTeX, models, configs, environment specs);
heavy raw outputs live on the external backup drive and are indexed by `DATA_MANIFEST.csv` files.

Folder names match `C:\Research\` one-to-one, so `git clone` into `C:\Research\` restores the tree, and
copying `research_full\` from the backup drive on top restores the data.

## What is in this repository

- All code (`.py`, `.m`, `.jl`, `.ipynb`, `.slx`, `.sh`, `.ps1`, C/C++), LaTeX (`.tex`, `.bib`, `.cls`), Markdown docs
- MuJoCo / URDF / STL models, YAML/TOML/JSON configs
- Small result summaries (CSV/JSON <= 1 MB) and figures (<= 3 MB) inside `fig*/plots/paper/images` folders
- `environments/` - `pip freeze` of every project `.venv`, `conda env export` of `hyperlif`, global Julia Project/Manifest
- `_patches/` - uncommitted local changes in nested third-party clones (apply with `git apply`)
- Root docs: `SETUP.md` (machine rebuild), `CODE_MAP.md` (how to run what), `ENVIRONMENTS.md`, `WORKFLOW.md`

## What is NOT in this repository (and where it is)

| Excluded | Where |
|---|---|
| Raw run outputs (CSV/NPZ/H5/BIN/PT > 1 MB, zips, videos) - listed per project in `DATA_MANIFEST.csv` | `D:\NMSU_backups\laptop_2026-10-01\research_full\` |
| ACC2027 paper snapshots v7-v11, advisor share bundles, review evidence copies | same, under `papers\ACC2027_Gate_Residual_Control\` |
| ACC2027 git history (single checkpoint commit `67e7e03`, 60 GB with data) and every `.venv` under `papers\` | `D:\NMSU_backups\laptop_2026-10-01\research_full\papers\` (papers are backed up complete) |
| Presentations (`.pptx`) | `research_full\presentations\` |
| `.venv`, caches, third-party papers, licenses | rebuild from `environments/` and `SETUP.md` |

The ACC2027 public release (code + reproduction package) is its own private repository:
`gandhico/online-pes-neuromorphic-residual-control`.

## Nested third-party clones (not copied; re-clone)

| Path | Remote | Commit | Local changes |
|---|---|---|---|
| `papers/P3_Gate_Residual/learned/code/third_party/mujoco_menagerie` | https://github.com/google-deepmind/mujoco_menagerie | da76818 | - |
| `papers/P3_Gate_Residual/models/mujoco_menagerie` | https://github.com/google-deepmind/mujoco_menagerie | da76818 | - |
| `qcar/SNN-Controller-for-Qcar2-with-SLAM` | https://github.com/hmirh/SNN-Controller-for-Qcar2-with-SLAM | 97728f0 | - |
| `qcar/01_Code/hardware/artgmap_vcs/artgmap_vcs` | https://github.com/hmirh/SNN-Controller-for-Qcar2-with-SLAM | f16f222 | `_patches/qcar_artgmap_vcs.patch` |
| `qcar/01_Code/hardware/qcar/quanser_state_estimator` | https://github.com/hmirh/SNN-Controller-for-Qcar2-with-SLAM | f2eea94 | `_patches/qcar_quanser_state_estimator.patch` |
| `y6_hexa/UAV_Nengo_repo` | https://github.com/esteedeq/UAV_Nengo | 05f4e44 | - |

## Restore on a new machine

1. Follow `SETUP.md` (MATLAB, QUARC, QLabs, Miniconda, Julia, Git).
2. `git clone https://github.com/gandhico/research-workspace C:\Research`
3. `conda env create -f environments\conda_hyperlif.yml`; per project:
   `python -m venv .venv && .venv\Scripts\pip install -r ..\environments\pip_<project>.txt`
4. Copy the data you need back from `D:\NMSU_backups\laptop_2026-10-01\research_full\<project>\`.
