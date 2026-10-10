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
