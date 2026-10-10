# 3DOF Hover Nengo GUI lab runbook

Read `C:\Research\hover3dof\docs\SAFETY_CHECKLIST.md` first.

For the complete real-time GUI, headless, Q8-shadow, and qualified-hardware
commands for every mission and neuron family, use:

`C:\Research\hover3dof\nengo_gui_hil_2026-08-29\docs\COMMAND_CATALOG_2026-09-01.md`

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29'

# Offline audit and emulation.
& $py "$root\verify_nengo_hover_equivalence.py"
& $py "$root\launch_hover_nengo_gui.py" --io emulated --controller pd --mission hover --duration 5
& $py "$root\launch_hover_nengo_gui.py" --io emulated --controller nengo-pes --mission hover --duration 5

# Q8 zero-output dry-runs. No --armed flag is present.
& $py "$root\launch_hover_nengo_gui.py" --io q8 --controller pd --mission hover --duration 5
& $py "$root\launch_hover_nengo_gui.py" --io q8 --controller nengo-pes --mission hover --duration 5
```

Before progressing, confirm tare and axis signs, finite signals, zero DAC writes,
no deadline/heartbeat abort, and complete files. A 5 s Nengo dry-run must have
1000 hardware rows and 10,000 neural samples.

```powershell
$paperpy = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$tool = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\analyze_neural_archive.py'
$archive = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware\RUN_FOLDER\neural_trace_2khz.npz'
& $paperpy $tool $archive --export-csv
```

Armed operation requires a separate same-session review of the rig, emergency
stop, tare, signs, mission, limits, baseline, and residual authority.
