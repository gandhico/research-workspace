# ACC 2027 - advisor code and reproducibility bundle

Scope: code supporting audited manuscript v5: quaternion PD, direct CMG/PES,
Nengo CMG/PES, the five-mission/two-model neuron-family benchmark, the
traceable legacy annealing experiment, and preliminary Hover Nengo tests.
This is not a backup of every historical QCar/Pendulum project or experiment.

## Start here (Windows PowerShell)

Install CPython **3.13.11, 64-bit**, then extract this ZIP. Internet access is
needed for dependencies. From the extracted `ACC2027_CODE` directory:

```powershell
py -3.13 -m venv .venv
$py = "$PWD\.venv\Scripts\python.exe"
& $py -m pip install -r requirements-lock.txt
& $py reproduce.py smoke
```

No activation, editable-project install, or system-wide installation is
necessary; the wrapper sets the packaged source path explicitly. Verify the exact
interpreter with `& $py -V`; `py -3.13` selects an installed 3.13 interpreter
but does not itself guarantee patch version 3.13.11.

The lock records the functioning stack, including MuJoCo 3.12.0, Nengo 4.1.0,
NumPy 2.5.2, Nengo GUI 0.6.0, Matplotlib 3.11.1, and their installed
dependencies. `ENVIRONMENT.json` records the platform and versions. No virtual
environment, Python distribution, wheels, driver, or compiled binary is bundled.
Linux users can create a venv with Python 3.13.11 and use `.venv/bin/python`;
the packaged qualification is Windows, not a claim of cross-OS bitwise identity.

## Reproduce experiments

All following `reproduce.py` tasks are simulation-only. They never arm Q8.

```powershell
# All five missions, X2 and CF2 rotor design, PD + direct PES + Nengo PES:
& $py reproduce.py primary

# One chosen mission/controller; duration defaults to 45 s:
& $py reproduce.py single --platform x2 --mission hard45 --controller nengo-nef-pes
& $py reproduce.py single --platform cf2-rotor --mission yaw360 --controller classical

# Complete 110-cell supplementary neuron-family benchmark:
& $py reproduce.py neurons

# New fixed/conductance/PES ablation campaign, same five missions:
& $py reproduce.py ablation

# The three traceable precursor annealing comparisons (separate architecture):
& $py reproduce.py legacy

# Browser Nengo GUI plus live MuJoCo viewer:
& $py reproduce.py gui --platform x2 --mission hard45
& $py reproduce.py gui --platform cf2-rotor --mission yaw360

# Hover emulation only, NOT physical hardware evidence:
& $py reproduce.py hover-emulated --mission roll --duration 8
```

Mission choices: `roll`, `full3`, `hard45`, `hardstep`, `yaw360`, and equilibrium
`hover`. Use a new `--output` directory for independent repeats. Primary output
folders are protected against accidental overwriting. Original low-level
runners can overwrite output paths; do not point them at the shared records.
Long benchmark runtime depends on the computer and Nengo overhead; 45 seconds
of simulated time is not necessarily 45 seconds of wall time.

Canonical settings: dt=0.0005 s, duration=45 s, beta=0.5, direct-equivalent
eta=0.0008, k_error=8, k_rate=0, seed=1, no injected noise/disturbance.
X2 actuator scale is 1.0; CF2 rotor-design scale is **1.5**, not stock CF2.
The latest runner is preserved; bookkeeping/telemetry can differ from older
files. Numeric comparison, not byte-identical CSV output, is the objective.

For compact new runs, the wrapper saves CSV and JSON but disables optional
full-rate NPZ archives. Add `--full-neural-data` to `primary`, `single`, or
`neurons` to also retain the full neural archive. Default CSV spacing is 5 ms;
integration and summary metrics remain at 0.5 ms. The original matched X2
Hard45 CSV is full-rate; most other matched CSVs are decimated.

## Compare against the supplied results

Extract the results ZIP beside the code folder, giving sibling
`ACC2027_CODE` and `ACC2027_RESULTS` directories. After the full primary run:

```powershell
& $py reproduce.py compare
# Or supply its location explicitly:
& $py reproduce.py compare --results 'D:\Review\ACC2027_RESULTS'
& $py verify_archive.py '..\ACC2027_RESULTS_CSV.zip'
```

Comparison checks all 20 PD/Nengo mean errors at relative tolerance 1e-5.
It fails if any required result is missing or outside tolerance. This is a
numerical regression check, not statistical replication or a stability proof.

To regenerate the two audited manuscript figures from the supplied CSVs,
copy the result-only `project` subtree into the code's `project` subtree:

```powershell
Copy-Item -Path '..\ACC2027_RESULTS\project\*' -Destination '.\project' -Recurse
& $py project\paper\tools\plot_v5_evidence.py
```

Outputs appear under `project/paper/figures/v5_audit`. This uses saved data,
not new experiments. The family analysis routines that require omitted NPZ
files need newly generated full-neural-data runs instead.

## Structure and interfaces

```text
reproduce.py
  project/src/gra_control/
    math3d.py               quaternion conventions and mission references
    gate.py                 direct membrane/gate dynamics and PES decoder
    platforms/drone.py      PD, models, collective thrust, rotor allocation
  project/experiments/nengo_nef_replication_2026-08-29/
    nengo_cmg.py             custom continuous NeuronType and Nengo PES
    nengo_neuron_family.py   LIF/ALIF/Izhikevich/LIFRate alternatives
    run_mujoco_nef.py        matched plant/controller simulation loop
    launch_gui.py            Nengo dashboard and passive MuJoCo viewer
    feature_calibration.json archived comparator calibration
  project/models/           CF2 rotor-design model
  project/third_party/      required Menagerie X2/CF2 assets and licenses
  legacy/code/              precursor blending/annealing code and its models
  hover3dof/                Nengo Hover engine, PD math, launchers, safety notes
  documentation/           v5 audit plus broader historical ledgers
```

Raw gates r, membrane states v, activity a, and decoder W are different
variables. CMG is continuous/non-spiking. The decoder reads amplified gate
activity, not membrane voltage directly. Annealed activity-trace learning in
the legacy code is not full e-prop and does not establish a canonical AAT
advantage. Read the v5 audit before quoting legacy numbers or earlier ledgers.

## Hardware is optional and requires local qualification

The Hover source is included for review and future laboratory reproduction.
It requires a licensed Quanser QUARC/HIL Python API, installed Q8 drivers,
amplifier/encoder calibration, physical apparatus, and the safety checklist.
Vendor distributions observed in the lab include `quanser-api`,
`quanser-hardware`, `quanser-common`, and related modules at **2026.5.13**.
They are not part of the portable simulation requirements; obtain the vendor
packages and drivers through your licensed Quanser installation. The Python
package version is not proof of the installed driver/QUARC release. Do not infer
that emulation validates hardware or that an arbitrary initial pose is safe.

Use `hover3dof/nengo_gui_hil_2026-08-29/run_hover_headless.py --io emulated`
for computer-only work. The archived direct hardware launcher defaults to Q8
input, although arming requires additional explicit flags. Do not run that
launcher casually. No ready-to-arm automation is provided in this wrapper.
`LAB_RUNBOOK.md` describes the later Nengo workflow; the older standalone
`SAFETY_CHECKLIST.md` is historical and its original statement that no motor
code existed must not be applied to the later armed-capable launchers.

## Preservation and limitations

The two absolute root constants in the **packaged** Hover engine were made
relative. No control equation, gain, neural update, timing, safety threshold,
or I/O logic was changed. Original research files remain untouched.
`SOURCE_MAP.csv` records original file hashes and the exact relocation scope;
`FILES.csv` authenticates the files delivered in this archive.

Older analysis/PowerShell scripts are included as source reference and may
retain original absolute output paths or old mission durations. The portable
`reproduce.py` commands above are the supported entry point for this package.
Do not interpret old document claims as superseding the v5 audit.

One inherited metadata issue is retained transparently: the low-level matched
runner can label `direct-online-pes` as Nengo in `controller_backend`.
The `controller` field and `_build_augmentor` determine the actual backend;
`direct-online-pes` uses the direct NumPy augmentor. No algorithm was changed
to hide this labeling issue. Nengo may also emit high-PES-rate and LIF boundary
warnings during conformance tests; use the numerical test result, and do not
change the prescribed learning rate merely to suppress a warning.

MuJoCo model licenses are retained. This is a private advisor-review package;
no new license or permission to redistribute vendor software is asserted.
The paper itself is shared separately, so PDFs, rendered plots, caches,
duplicate frozen ZIPs, and unrelated historical platforms are excluded.
