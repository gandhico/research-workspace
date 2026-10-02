# Coaxial TriRotor (Y6) — GitHub Notes

**Date:** 2026-06-05

Reference for where the Coaxial TriRotor code lives and what was shared.

---

## Where the code lives

| Location | Path / repo | Contents |
|----------|-------------|----------|
| Local master (source) | `C:\00_Research_\Neuromorphic_Embodied_AI\02_Coaxial_TriRotor_Nengo\01_Code` | Full working set — all experiments and variants |
| Personal monorepo (private) | `Neuromorphic-Embodied-AI` → `Coaxial-TriRotor-UAV/` | Curated, release-ready files only |
| Collaboration (private) | `esteedeq/UAV_Nengo` → `Nengo/Coaxial_TriRotor/` | Model + runner + README (PR #1) |

The local master stays the full set; the monorepo holds only curated files.

---

## What was shared vs. kept private

Only release-ready files were committed. **Keepers** (curated set):

- `y6_model.py` — Y6 dynamics, parameters/gains, RK4 integrator, baseline controller
- `run_baseline.py` — runs the baseline simulation and plots results (imports `y6_model`)
- `Readme.md`, `PROGRESS.md`, `RUNNERS.md`, `CITATION.cff`, `.gitignore`

**Left out (preliminary / scratch, kept local only):** all the `*_fixed.py`,
`*_patched.py`, `*_stageN` variants, the `gui_y6_stage*` GUIs, and the `.cfg` files.

> Import check confirmed: `run_baseline.py` and `y6_model.py` depend only on each
> other plus numpy/matplotlib — no scratch modules — so they run standalone.

---

## Collaboration contribution

- **Repo:** `esteedeq/UAV_Nengo` (folders: `Matlab/`, `Nengo/`)
- **Branch:** `add-coaxial-nengo` (off `main`)
- **Placement:** new subfolder `Nengo/Coaxial_TriRotor/` to keep it separate from
  the existing `Quad1_X_T1.py` model
- **Commit:** `feat: add coaxial tri-rotor (Y6) Nengo baseline model and runner`
- **Pull request:** **#1**, into `main`, reviewers requested (esteedeq, JMBA12, Aolivares24)
- **Repo-root README:** intentionally NOT added here — that's a project-wide doc
  for esteedeq to own; raise separately.

---

## Commands used (for reference)

```powershell
cd "C:\00_Research_\_github\UAV_Nengo"
git checkout main
git pull
git checkout -b add-coaxial-nengo
mkdir Nengo\Coaxial_TriRotor
Copy-Item "C:\00_Research_\_github\Neuromorphic-Embodied-AI\Coaxial-TriRotor-UAV\y6_model.py" ".\Nengo\Coaxial_TriRotor\"
Copy-Item "C:\00_Research_\_github\Neuromorphic-Embodied-AI\Coaxial-TriRotor-UAV\run_baseline.py" ".\Nengo\Coaxial_TriRotor\"
notepad .\Nengo\Coaxial_TriRotor\README.md   # paste README, save
git status
git add Nengo/Coaxial_TriRotor
git commit -m "feat: add coaxial tri-rotor (Y6) Nengo baseline model and runner"
git push -u origin add-coaxial-nengo
# then open PR on GitHub
```

---

## Next steps

- Let reviewers merge PR #1 (don't self-merge).
- Confirm with esteedeq whether `Nengo/Coaxial_TriRotor/` is the right home.
- When this paper is accepted: split into its own public repo with a clean history.
