"""Build a self-contained, shareable advisor package for the ACC 2027 paper.

Everything an advisor needs to read the paper, see the figures, inspect the
numbers, and re-run the code -- at a size that fits on a shared drive.

Full-rate telemetry is NOT included: the canonical traces are downsampled
from 2 kHz to 50 Hz so they open in a spreadsheet. The untouched full-rate
archive stays at share/advisor_reproducibility_2026-09-04/.

Run:  python build_advisor_package.py
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import zipfile
from datetime import date
from pathlib import Path

RESEARCH = Path(r"C:\Research")
ACC = RESEARCH / "papers" / "ACC2027_Gate_Residual_Control"
PAPER_SRC = ACC / "paper" / "v7_2026-09-05"

STAMP = date.today().isoformat()
OUTROOT = ACC / "share" / f"advisor_{STAMP}"
PKG = OUTROOT / f"ACC2027_advisor_{STAMP}"

STRIDE = 40   # MuJoCo logs at 2 kHz -> 50 Hz
STRIDE_HW = 4  # the Hover rig logs at 200 Hz -> 50 Hz

copied: list[tuple[str, int]] = []


def put(src: Path, dst_rel: str) -> None:
    """Copy one file into the package."""
    if not src.is_file():
        print(f"    MISSING  {src}")
        return
    dst = PKG / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    copied.append((dst_rel, dst.stat().st_size))


def put_glob(root: Path, pattern: str, dst_dir: str, flat: bool = True) -> int:
    n = 0
    if not root.exists():
        print(f"    MISSING DIR  {root}")
        return 0
    for f in sorted(root.glob(pattern)):
        if not f.is_file():
            continue
        rel = f.name if flat else str(f.relative_to(root)).replace("\\", "/")
        put(f, f"{dst_dir}/{rel}")
        n += 1
    return n


def downsample(src: Path, dst_rel: str, stride: int = STRIDE) -> None:
    """Keep the header plus every `stride`-th data row."""
    if not src.is_file():
        print(f"    MISSING  {src}")
        return
    dst = PKG / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    with io.open(src, "r", encoding="utf-8", newline="") as fi, \
         io.open(dst, "w", encoding="utf-8", newline="") as fo:
        header = fi.readline()
        fo.write(header)
        for k, line in enumerate(fi):
            if k % stride == 0:
                fo.write(line)
                kept += 1
    copied.append((dst_rel, dst.stat().st_size))
    print(f"    {kept:6d} rows  {dst_rel}")


# ===========================================================================
print(f"building {PKG}")
if PKG.exists():
    shutil.rmtree(PKG)
PKG.mkdir(parents=True)

# --- 1. the manuscript ------------------------------------------------------
print("  [1/6] paper")
put(PAPER_SRC / "ACC2027_v8.pdf", "paper/ACC2027_manuscript.pdf")
put(PAPER_SRC / "ACC2027_v8.tex", "paper/ACC2027_manuscript.tex")
put(PAPER_SRC / "references.bib", "paper/references.bib")
put(PAPER_SRC / "figures/arch/architectures_deck.pdf",
    "paper/architectures/architectures_deck.pdf")
put(PAPER_SRC / "figures/arch/architectures_drawio.pdf",
    "paper/architectures/architectures_drawio.pdf")
put(PAPER_SRC / "figures/arch/architectures.drawio",
    "paper/architectures/architectures.drawio")
put(PAPER_SRC / "figures/arch/README.md", "paper/architectures/README.md")
put_glob(PAPER_SRC / "figures/arch", "arch*.tex", "paper/architectures/tikz")
put(PAPER_SRC / "figures/arch/make_drawio.py",
    "paper/architectures/tikz/make_drawio.py")
put(PAPER_SRC / "figures/arch/preview.tex", "paper/architectures/tikz/preview.tex")

# --- 2. code ----------------------------------------------------------------
print("  [2/6] code")
CODE = [
    (ACC / "experiments/six_dof_expansion_2026-08-31", "six_dof_cascade"),
    (ACC / "experiments/nengo_nef_replication_2026-08-29", "nengo_nef_replication"),
    (RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29", "hover3dof_hardware"),
    (RESEARCH / "eprop_anneal_reproduction", "eprop_anneal"),
]
for root, name in CODE:
    k = put_glob(root, "*.py", f"code/{name}")
    k += put_glob(root, "*.md", f"code/{name}")
    k += put_glob(root, "*.json", f"code/{name}")
    print(f"    {k:4d} files  code/{name}")

k = put_glob(ACC / "src/gra_control", "**/*.py", "code/gra_control", flat=False)
print(f"    {k:4d} files  code/gra_control")
for extra in ("pyproject.toml", "requirements.txt", "README.md"):
    put(ACC / extra, f"code/{extra}")

# --- 3. result tables (CSV) -------------------------------------------------
print("  [3/6] result tables")
TABLES = [
    (ACC / "experiments/nengo_nef_replication_2026-08-29/results/compiled/matched_results.csv",
     "five_mission_matrix_x2_cf2.csv"),
    (ACC / "experiments/nengo_nef_replication_2026-08-29/results/compiled/archived_equivalence.csv",
     "direct_vs_nengo_equivalence.csv"),
    (ACC / "experiments/nengo_nef_replication_2026-08-29/results/neuron_family_compiled/neuron_family_results.csv",
     "nengo_neuron_family_benchmark.csv"),
    (RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29/results/FROZEN_AUDIT_2026-09-02/canonical_physical_matched_pairs.csv",
     "hover3dof_matched_pairs.csv"),
    (RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29/results/FROZEN_AUDIT_2026-09-02/all_saved_run_inventory.csv",
     "hover3dof_run_inventory.csv"),
    (RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29/results/hardware_armed_roll_n3_2026-09-01/armed_roll_n3_paired_trials.csv",
     "hover3dof_armed_roll_n3.csv"),
]
for src, name in TABLES:
    put(src, f"data/tables/{name}")
put_glob(ACC / "experiments/nengo_nef_replication_2026-08-29/results/compiled",
         "*.json", "data/tables")
put(ACC / "experiments/nengo_nef_replication_2026-08-29/results/neuron_family_compiled/neuron_family_results.json",
    "data/tables/nengo_neuron_family_benchmark.json")
put(RESEARCH / "eprop_anneal_reproduction/traces_5missions/all_summaries.json",
    "data/tables/eprop_anneal_5missions.json")
put(RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29/results/DIRECT_NENGO_FINAL_2026-09-01/final_summary_table.json",
    "data/tables/hover3dof_final_summary.json")

# --- 4. downsampled canonical traces ---------------------------------------
print("  [4/6] canonical traces, downsampled 2 kHz -> 50 Hz")
for d in sorted((ACC / "results/plots_data").glob("*")):
    if (d / "trace.csv").is_file():
        downsample(d / "trace.csv", f"data/traces_50hz/mujoco/{d.name}.csv")
HOVER_FINAL = RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29/results/DIRECT_NENGO_FINAL_2026-09-01"
for d in sorted(HOVER_FINAL.glob("*")):
    if (d / "trace.csv").is_file():
        downsample(d / "trace.csv", f"data/traces_50hz/hover3dof/{d.name}.csv", stride=4)
    for meta in ("summary.json", "manifest.json"):
        if (d / meta).is_file():
            put(d / meta, f"data/run_summaries/hover3dof/{d.name}__{meta}")

# --- 5. figures -------------------------------------------------------------
print("  [5/6] figures")
NENGO_PLOTS = ACC / "experiments/nengo_nef_replication_2026-08-29/results/plots"
n = put_glob(NENGO_PLOTS, "*_tracking.png", "figures/01_mujoco_missions")
put(NENGO_PLOTS / "all_missions_mean_improvement.png",
    "figures/01_mujoco_missions/all_missions_mean_improvement.png")
print(f"    {n:4d} mission tracking plots")

n = put_glob(NENGO_PLOTS, "*_neurons.png", "figures/02_neural_activity")
n += put_glob(NENGO_PLOTS / "attitude_detail", "*.png", "figures/02_neural_activity/attitude_detail")
print(f"    {n:4d} neural-activity plots")

NF = ACC / "experiments/nengo_nef_replication_2026-08-29/results/neuron_family_compiled"
n = put_glob(NF, "*.png", "figures/03_nengo_neuron_benchmark")
n += put_glob(NF, "*.pdf", "figures/03_nengo_neuron_benchmark")
n += put_glob(RESEARCH / "hover3dof/nengo_gui_hil_2026-08-29/results/hover_neuron_family_compiled_2026-09-01/representative_neural",
              "*.png", "figures/03_nengo_neuron_benchmark/hover_representative_neural")
print(f"    {n:4d} neuron-family benchmark plots")

n = put_glob(HOVER_FINAL / "plots", "*.png", "figures/04_hover3dof_hardware")
print(f"    {n:4d} 3DOF Hover hardware plots")

SIXDOF = ACC / "experiments/six_dof_expansion_2026-08-31/results/plots"
n = put_glob(SIXDOF, "*.png", "figures/05_six_dof_cascade")
n += put_glob(SIXDOF / "advisor_report", "*.png", "figures/05_six_dof_cascade/advisor_report")
print(f"    {n:4d} 6-DOF cascade plots")

n = put_glob(RESEARCH / "eprop_anneal_reproduction/plots_5missions", "*.png",
             "figures/06_eprop_anneal")
print(f"    {n:4d} eprop/annealed-trace plots")

# --- disturbance rejection and noise sensitivity (2026-09-05) -------------
NENGO_EXP = ACC / "experiments/nengo_nef_replication_2026-08-29/results"
SWEEP = NENGO_EXP / "final_sweep_2026-09-05/compiled"
HOVER45 = NENGO_EXP / "hover_intermittent_2026-09-05"
n = put_glob(SWEEP, "*.png", "figures/07_disturbance_and_noise")
n += put_glob(SWEEP, "*.pdf", "figures/07_disturbance_and_noise")
n += put_glob(HOVER45, "*.png", "figures/07_disturbance_and_noise")
n += put_glob(HOVER45, "*.pdf", "figures/07_disturbance_and_noise")
print(f"    {n:4d} disturbance / noise-sensitivity plots")

for f, dst in ((SWEEP / "noise_sensitivity.csv", "data/tables/noise_sensitivity.csv"),
               (SWEEP / "table_noise.tex", "data/tables/table_noise.tex"),
               (SWEEP / "retention.json", "data/tables/hover_retention.json"),
               (NENGO_EXP / "final_sweep_2026-09-05/raw_results.json",
                "data/tables/final_sweep_raw.json"),
               (NENGO_EXP / "noise_check_2026-09-05/noise_check_summary.json",
                "data/tables/noise_check_summary.json")):
    put(f, dst)

# --- 6. manifest and README -------------------------------------------------
print("  [6/6] manifest")
rows = []
for rel, _size in sorted(copied):
    f = PKG / rel
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    rows.append((rel, f.stat().st_size, h))
with io.open(PKG / "MANIFEST.csv", "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["path", "bytes", "sha256"])
    w.writerows(rows)

total = sum(r[1] for r in rows)
README = f"""# ACC 2027 -- advisor package ({STAMP})

Gandhi Contreras, Steven Sandoval, Luis Garcia -- New Mexico State University.

Everything needed to read the manuscript, inspect the numbers behind every
table, and re-run the code. {len(rows)} files, {total/1e6:.0f} MB.

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

## Reading the results honestly

Two limitations the numbers do not show on their own, stated in the paper
and repeated here so they travel with the data:

1. **n = 1 per cell** in the MuJoCo matrix. The simulation is
   deterministic, so there is no seed variance -- but there is also no
   robustness evidence. The physical Roll result is n = 3.
2. **Decoder learning, not the neuron model, produces the improvement.**
   Toggling the conductance-modulation switch is numerically
   indistinguishable in the tested regime, and some Izhikevich--PES cells
   beat CMG--PES on mean tracking error. The supported claim is a
   tracking-effort tradeoff, not universal CMG superiority.
"""
io.open(PKG / "README.md", "w", encoding="utf-8").write(README)

# --- zip --------------------------------------------------------------------
zip_path = OUTROOT / f"ACC2027_advisor_{STAMP}.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for f in sorted(PKG.rglob("*")):
        if f.is_file():
            z.write(f, f"ACC2027_advisor_{STAMP}/{f.relative_to(PKG)}")

print(f"\npackage : {PKG}")
print(f"          {len(rows)+2} files, {total/1e6:.1f} MB on disk")
print(f"zip     : {zip_path}")
print(f"          {zip_path.stat().st_size/1e6:.1f} MB")
json.dump({"package": str(PKG), "zip": str(zip_path),
           "files": len(rows) + 2, "bytes_uncompressed": total,
           "bytes_zip": zip_path.stat().st_size},
          io.open(OUTROOT / "BUILD.json", "w", encoding="utf-8"), indent=2)
