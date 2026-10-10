# ACC 2027 -- advisor package (2026-09-05)

Gandhi Contreras, Steven Sandoval, Luis Garcia -- New Mexico State University.

Everything needed to read the manuscript, inspect the numbers behind every
table, and re-run the code. 340 files, 83 MB.

## paper/

* `ACC2027_manuscript.pdf` -- the 9-page manuscript.
* `ACC2027_manuscript.tex`, `references.bib` -- LaTeX source.
* `architectures/` -- ten architecture diagrams in two synced formats:
  `architectures_deck.pdf` (rendered), `architectures.drawio` (editable in
  diagrams.net, one page per architecture), and `tikz/` (LaTeX sources used
  by the manuscript). `architectures/README.md` maps the ten IDs.

## code/

| Directory | What it runs |
|---|---|
| `six_dof_cascade/` | 6-DOF Option-A cascade: outer position loop, inner quaternion-attitude loop, shared allocator |
| `nengo_nef_replication/` | Nengo/NEF realization, the five-mission matrix, and the neuron-family benchmark |
| `hover3dof_hardware/` | Quanser 3DOF Hover hardware-in-the-loop, 200 Hz Q8 with ten 0.5 ms neural substeps |
| `eprop_anneal/` | Annealed activity-trace (e-prop style) reproduction |
| `gra_control/` | The shared controller package (quaternion PD, CMG unit, PES, allocation) |

## data/

* `tables/` -- the result tables behind the paper, as CSV and JSON:
  * `five_mission_matrix_x2_cf2.csv` -- Table II (10 matched MuJoCo cases)
  * `nengo_neuron_family_benchmark.csv` -- CMG vs LIF / ALIF / Izhikevich / LIFRate
  * `direct_vs_nengo_equivalence.csv` -- the 2.013e-6 agreement check
  * `hover3dof_*.csv` -- physical matched pairs, run inventory, armed Roll n=3
  * `eprop_anneal_5missions.json`, `hover3dof_final_summary.json`
* `traces_50hz/` -- canonical per-run time series, **downsampled from 2 kHz
  to 50 Hz** so they open in a spreadsheet. `mujoco/` holds the simulation
  runs, `hover3dof/` the physical runs.
* `run_summaries/` -- per-run `summary.json` and `manifest.json` for the
  physical campaign, including the configuration each run actually used.

Full-rate (2 kHz) telemetry is deliberately excluded to keep this package
shareable. The untouched archive is
`share/advisor_reproducibility_2026-09-04/ACC2027_RESULTS_CSV.zip`
(883 MB, 677 files, sha256 in `RESULTS_BUILD.json`).

## figures/

| Directory | Contents |
|---|---|
| `01_mujoco_missions/` | Baseline vs CMG--PES tracking, both models x six missions, plus the mean-improvement summary |
| `02_neural_activity/` | Membrane, gate, and clipped-activity traces for the same runs, plus attitude detail |
| `03_nengo_neuron_benchmark/` | Neuron-family heatmaps, accuracy/authority tradeoff, mechanism dashboards, online-PES bars, and representative per-family neural traces from the Hover rig |
| `04_hover3dof_hardware/` | Physical 3DOF Hover: tracking and mechanism panels for all six missions |
| `05_six_dof_cascade/` | 6-DOF cascade results, including the `advisor_report/` set |
| `06_eprop_anneal/` | Annealed activity-trace study across five missions |

## Verifying

`MANIFEST.csv` lists every file with its SHA-256.

```bash
python -c "import csv,hashlib,io,sys;from pathlib import Path;bad=[r for r in csv.DictReader(io.open('MANIFEST.csv',encoding='utf-8')) if hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()!=r['sha256']];print('mismatches:',len(bad))"
```

## Running this on another machine

The package is location-independent. Extract it anywhere, on Windows, macOS
or Linux, rename the folder if you like — nothing inside contains an
absolute path.

### 1. Set up

From the package root (the folder holding `README.md` and `pyproject.toml`):

```
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS / Linux

pip install -e ".[sim]"           # code + everything needed to re-run sims
pip install -e .                  # or: just numpy/matplotlib, to read results
```

This installs `gra_control` from `code/`, so it resolves to *this* package and
cannot pick up a copy from anywhere else. The distribution is named
`acc2027-advisor-package`, deliberately different from the working-tree
project, so it cannot replace a development checkout of that one.

If you would rather not install anything, set the path instead:

```
set PYTHONPATH=%CD%\code          # Windows
export PYTHONPATH=$PWD/code       # macOS / Linux
```

### 2. Check what will work here

```
python code/check_environment.py
```

It reports your Python and platform, which packages are present, which parts
of the package were found, and a plain list of what can and cannot run here.

Then confirm the simulation stack end to end (about three seconds):

```
python code/six_dof_cascade/run_6dof_cascade.py \
    --mission hover3d --duration 3 --controller online-pes-adaptive \
    --platform x2 --output outputs/smoke
```

It should print a line like `pos_err_mean=0.3273m  qerr_mean=7.303deg` and
write `summary.json` and `trace.csv` into `outputs/smoke/`.

### 3. How paths work

Every script asks `code/acc2027_paths.py` instead of hard-coding a location.
That module finds the package root from its own file position, so the
working directory does not matter. Scripts import it with a two-line
bootstrap:

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from acc2027_paths import DATA, FIGURES, out_dir
```

Run `python code/acc2027_paths.py` to print every root and whether it exists.

Regenerated output goes to `outputs/`, never on top of the shipped figures.

### 4. Pointing at data that is too large to ship

Three trees were left out for size. Set an environment variable to use your
own copy; everything else works without them.

| Variable | What it should point at |
|---|---|
| `ACC2027_HOVER_PROJECT` | the full `nengo_gui_hil_2026-08-29` tree |
| `ACC2027_MUJOCO_RESULTS` | the full MuJoCo `results/` tree |
| `ACC2027_LAB_ROOT` | the lab machine's research root, for hardware entry points |

Two more are available if you want to relocate things:
`ACC2027_ROOT` (override root detection) and `ACC2027_OUT` (output directory).

```
set ACC2027_HOVER_PROJECT=D:\archive\hover3dof\nengo_gui_hil_2026-08-29
export ACC2027_HOVER_PROJECT=/mnt/archive/hover3dof/nengo_gui_hil_2026-08-29
```

### 5. What runs out of the box

| | Needs |
|---|---|
| Read the tables and 50 Hz traces | numpy |
| Re-plot from the shipped traces | numpy, matplotlib |
| Reproduce the annealed-trace study | numpy, mujoco (the legacy code it depends on is shipped in `code/legacy_p3_learned/`) |
| Re-run the MuJoCo five-mission matrix | numpy, mujoco |
| Re-run the Nengo neuron-family benchmark | numpy, mujoco, nengo |
| Campaign-wide hardware audits | `ACC2027_HOVER_PROJECT` set to the full archive |
| Drive the physical 3DOF Hover rig | the Quanser HIL SDK and the rig itself |

### How this was verified

Not by inspection. The package was copied to a temporary directory under a
different name, and every module was imported from an unrelated working
directory with all `ACC2027_*` variables cleared. Result: the root resolved
to the copy, no path pointed back at the original tree, and no module failed
for a path-related reason — only for third-party packages that were absent
from that bare interpreter.

Two defects were found and fixed while preparing this, both worth knowing
about if you diff against the working tree:

* Three matplotlib titles used non-raw f-strings containing LaTeX, so
  `$\theta_e$` was silently compiled to `$<TAB>heta_e$` and
  `$\rightarrow$` to a carriage return. Python does not warn about this
  because `\t` and `\r` are valid escapes. The strings are now raw.
* Five legacy source files began with a UTF-8 BOM, which CPython tolerates
  but `ast.parse` and several linters do not. The BOMs were removed.
