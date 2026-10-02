# Session index, 2026-08-27/28 — everything, and how to reproduce it

One stop for every path, runner, and result from this session, spanning two
repositories: this one (`ACC2027_Gate_Residual_Control`, MuJoCo simulation +
the paper) and `C:\Research\hover3dof` (physical hardware). Start here;
follow the links out for depth.

## Read first

1. **This file** — orientation and reproduction commands.
2. `docs\RESULTS_EXPLAINED.md` — the deep conceptual + mathematical
   explanation of the CMG unit, the PES rule, and every result below.
3. `C:\Research\hover3dof\docs\PROGRESS_2026-08-27.md` — the hardware
   bring-up narrative: four real bugs found and fixed, verified physical
   facts, the full tuning campaign.
4. `C:\Research\hover3dof\docs\SAFETY_CHECKLIST.md` — read before running
   anything with `--armed` on the physical rig.
5. `paper\acc2027_neuromorphic_gate_residual_draft.tex` /
   `output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf` — the
   manuscript, now including the full mission suite and the hardware
   validation section.

## What happened tonight, in order

1. Recovered `QDrone2_Workspace.rt-win64` and investigated the QLabs
   virtual-twin command channel — closed without a resolution; the earlier
   kinematic-mirror QDrone2 twin stands as that platform's deliverable
   (separate track, not covered further here).
2. Built the 3DOF Hover hardware control stack from zero: safety checklist,
   channel-ID pulse test, the HIL control loop, found and fixed four real
   bugs via actual hardware runs (channel swap, encoder tare + rate filter,
   safety-bridge misuse, tautological learning target).
3. Ran a full parameter sweep to find a non-regressing, genuinely useful
   configuration (`docs\PROGRESS_2026-08-27.md` Section 5d).
4. Extended the MuJoCo validation from the paper's single `hard45` case to
   the full five-mission suite on both X2 and CF2.
5. Added true per-axis Euler tracking + CMG neuron-activity (membrane
   potential, gate state) logging and plotting for every mission on both
   platforms.
6. Wrote the results into the paper (`Full mission-suite validation` and
   `Physical Hardware Validation: Quanser 3DOF Hover` sections), updated
   the abstract, conclusion, limitations, and reproducibility sections, and
   rebuilt the PDF.
7. Published an interactive results table/artifact and this reference set.

## Reproduce: MuJoCo simulation (this repo)

```powershell
cd C:\Research\papers\ACC2027_Gate_Residual_Control
$py = '.venv\Scripts\python.exe'

# Any classical/CMG pair, any of: hover, roll, full3, hard45, hardstep, yaw360
& $py scripts\rerun_with_euler_logging.py --platform x2 --controller classical `
  --mission hard45 --duration 45 --dt 0.0005 --torque-policy model --out results\plots_data\x2_hard45_classical
& $py scripts\rerun_with_euler_logging.py --platform x2 --controller online-pes `
  --mission hard45 --duration 45 --dt 0.0005 --beta 0.5 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --torque-policy model --out results\plots_data\x2_hard45_cmg

# CF2 needs --platform cf2-rotor, --controller online-pes-adaptive, --actuator-scale 1.5

# Plots
& $py scripts\plot_mujoco_drone_results.py --platform X2 `
  --classical results\plots_data\x2_hard45_classical --cmg results\plots_data\x2_hard45_cmg `
  --out results\plots\x2_hard45_classical_vs_cmg.png
& $py scripts\plot_neuron_activity.py --platform X2 --mission hard45 `
  --run-dir results\plots_data\x2_hard45_cmg --out results\plots\x2_hard45_neuron_activity.png
```

All 20 mission plots (5 missions x 2 platforms x {tracking, neuron}) are
already generated at `results\plots\*.png`. Raw traces with every logged
variable (Euler angles, quaternion error, torques, residual norm, gate
mean, and per-neuron `neuron_v_0..5` / `neuron_r_0..5`) are at
`results\plots_data\*\trace.csv`.

## Reproduce: 3DOF Hover hardware (separate repo, real motors)

**Read the safety checklist first.** Nothing below should be run without
physically confirming the rig state per that document.

```powershell
cd C:\Research\hover3dof
$py = '.venv\Scripts\python.exe'

# Dry run (zero output, sanity-check only)
& $py runners\hover3dof_hil_cmg_control.py --controller classical --mission hard45 --duration 5

# Vendor LQR baseline, armed
& $py runners\hover3dof_hil_cmg_control.py --controller classical --armed --mission hard45 --duration 25

# CMG-PES, the non-regressing configuration found in the Section 5d sweep
& $py runners\hover3dof_hil_cmg_control.py --controller online-pes-adaptive `
  --beta 0.4 --max-residual-volts 3.0 --learning-rate 0.0003 --k-error 4 --k-rate 0 `
  --armed --mission hard45 --duration 25

# Pull every result into one table
& $py runners\summarize_hardware_results.py --armed-only

# Plot any classical/CMG pair (outputs / error / inputs)
& $py runners\plot_hardware_results.py --classical hard45=<run_dir> --cmg hard45=<run_dir> --out-dir results\plots\<name>
```

83+ hardware runs (every `trace.csv`/`summary.json`/`manifest.json` from
tonight) are at `results\hardware\*\`.

## Reproduce: the paper

```powershell
cd C:\Research\papers\ACC2027_Gate_Residual_Control
powershell -File scripts\build_paper.ps1
```

Output: `output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf`.

## Full file map

| What | Where |
|---|---|
| Paper source | `paper\acc2027_neuromorphic_gate_residual_draft.tex` |
| Paper PDF | `output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf` |
| Deep results explanation | `docs\RESULTS_EXPLAINED.md` |
| This index | `docs\SESSION_INDEX_2026-08-27.md` |
| MuJoCo rerun-with-logging script | `scripts\rerun_with_euler_logging.py` |
| MuJoCo tracking plotter | `scripts\plot_mujoco_drone_results.py` |
| CMG neuron-activity plotter | `scripts\plot_neuron_activity.py` |
| MuJoCo traces (all 5 missions x 2 platforms) | `results\plots_data\*\` |
| MuJoCo plots (20 PNGs) | `results\plots\*.png` |
| Interactive results table (published artifact) | https://claude.ai/code/artifact/4336b6cb-a424-45ea-b8de-2c4c92ab8f93 |
| Presentation (10 slides, PPTX) | `presentation\CMG_PES_Results.pptx` |
| Presentation build script | `presentation\build_deck.py` |
| Canonical CMG controller (shared, unmodified) | `src\gra_control\gate.py` |
| MuJoCo drone controller (shared, unmodified) | `src\gra_control\platforms\drone.py` |
| Hover safety checklist | `C:\Research\hover3dof\docs\SAFETY_CHECKLIST.md` |
| Hover bring-up narrative | `C:\Research\hover3dof\docs\PROGRESS_2026-08-27.md` |
| Hover hardware control loop | `C:\Research\hover3dof\runners\hover3dof_hil_cmg_control.py` |
| Hover results table script | `C:\Research\hover3dof\runners\summarize_hardware_results.py` |
| Hover tracking plotter | `C:\Research\hover3dof\runners\plot_hardware_results.py` |
| Hover neuron-activity plotter | `C:\Research\hover3dof\runners\plot_neuron_activity.py` (needs a run recorded after 2026-08-28's logging fix) |
| Hover hardware traces (83+ runs) | `C:\Research\hover3dof\results\hardware\*\` |
| Hover plots | `C:\Research\hover3dof\results\plots\*.png` |

## Honest caveats carried forward from every source doc

- All Hover hardware numbers are **n=1**; MuJoCo numbers are single seeded
  runs, not repeated-trial statistics (see robustness matrix scripts for
  the existing multi-seed protocol used elsewhere in the paper).
- `roll` and `hardstep` have not been run on physical hardware yet.
- The Hover's residual authority (~13% of total) is a deliberate safety
  choice, not a tuning ceiling — see `RESULTS_EXPLAINED.md` Part 6 before
  comparing hardware and simulation magnitudes directly.
- The QDrone2 virtual-twin command-channel investigation was closed
  unresolved this session; not covered further here.
