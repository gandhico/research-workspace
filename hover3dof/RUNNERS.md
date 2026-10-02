# 3DOF Hover — Runners & Launchers Index

Single place to find "how do I run X" for the 3DOF Hover platform. Companion
docs: `docs\SAFETY_CHECKLIST.md` (read first, before anything hardware-related),
`docs\AGENT_HANDOFF_2026-08-27.md` in the ACC2027 repo (staged rollout
sequence). Vendor material lives under `3DOF_Hover\` (Simulink/MATLAB
courseware, no Python).

**Maturity: offline surrogate only, as of 2026-08-27.** No hardware code
exists yet, no QUARC/PAL adapter has been written or reviewed. Everything
in this repository is disarmed and touches no hardware.

---

## 1. Python — offline (no hardware, no QUARC)

Uses its own `.venv` (`C:\Research\hover3dof\.venv`), isolated from system
Python, with the ACC2027 repo's `gra_control` installed editable.

| Script | Command | Purpose |
|---|---|---|
| `runners\offline_acc2027_cmg_residual.py` | `.\.venv\Scripts\python.exe .\runners\offline_acc2027_cmg_residual.py --controller online-pes-adaptive --mission vendor-demo --duration 20` | Imports the exact `gra_control.gate.CMGResidualAugmentor` from the ACC2027 repo (not reimplemented). Plant equations of motion, state vector `[yaw,pitch,roll,yaw_dot,pitch_dot,roll_dot]`, control vector `[Vf,Vb,Vr,Vl]`, and the positive-voltage-only control law all match the vendor Laboratory Guide's Eqs. 2.1-2.5 exactly. **Physical constants (Kf, Kt, L, inertias) are placeholders** — the Laboratory Guide defers those to a separate User Manual not present on this machine; see the module docstring and `docs\SAFETY_CHECKLIST.md`. `--mission vendor-demo` reproduces the guide's own step-command demo (yaw ±5° @ 0.04Hz, pitch ±4° @ 0.10Hz, roll ±4° @ 0.08Hz). Output → `results\offline\<controller>_<mission>_<timestamp>\` with the same `trace.csv`/`summary.json`/`manifest.json` provenance discipline as the ACC2027 MuJoCo runs. **Verified working 2026-08-27**: 10,000-step run, zero NaN, all four channels stayed within `[0, v_max]` (positive-voltage-only constraint enforced). |

## 2. Python — physical hardware

**As of 2026-08-27, the rig is connected and the channel map is verified**
(see `docs\SAFETY_CHECKLIST.md`): AO0→Front, AO1→Back, AO2→Left, AO3→Right,
ENC0→Pitch, ENC1→Roll, ENC2→Yaw, amplifier gain=3. Uses `quanser.hardware`
(installed from QUARC's own Python wheels, `C:\Program Files\Quanser\QUARC\python\*.whl`,
into this project's `.venv`), not the QLabs-only `pal`/`qvl` packages.

| Script | Command | Purpose |
|---|---|---|
| `runners\hil_identify.py` | `.\.venv\Scripts\python.exe .\runners\hil_identify.py` | Read-only board identity query (serial number). Zero channel I/O. |
| `runners\single_channel_motor_test.py` | `... --channel 0 --volts 4.0 --hold 1.5 --ramp 0.5` | Vendor Section 4.1.1 bring-up test: ramps one Analog Output channel briefly, zeros all 4 unconditionally on exit. Used to derive the verified channel map above. |
| `runners\hover3dof_hil_cmg_control.py` | `... --controller online-pes-adaptive --beta 0.1 --armed --duration 5` | Real closed-loop control: vendor's exact LQR baseline (K matrix reproduced via MATLAB from `setup_lab_hover.m`) + the canonical `gra_control.hardware_bridges.SafeGateBridge`/`CMGResidualAugmentor` residual, same code as every other platform. Defaults to **not armed** (zero output), `--controller classical`, `--beta 0`, 30s duration cap per invocation. Every run writes `trace.csv`/`summary.json`/`manifest.json` under `results\hardware\`. |

`gra_control.hardware_bridges.hover3dof_bridge()` (the reviewed 4-channel
disarmed-by-default residual bridge) is used indirectly via
`hover3dof_hil_cmg_control.py`, which constructs the equivalent
`SafeGateBridge` directly so the online-PES learning rate is configurable.

| `runners\summarize_hardware_results.py` | `.\.venv\Scripts\python.exe .\runners\summarize_hardware_results.py --armed-only` | Reads every `results\hardware\*\summary.json` (+ per-run `trace.csv` for residual/gate stats) into one table, with a grouped mean/std/range comparison by (mission, controller, beta, max_residual_volts). Pure file reads, no hardware access. |
| `runners\plot_hardware_results.py` | `.\.venv\Scripts\python.exe .\runners\plot_hardware_results.py --classical hard45=<run_dir> ... --cmg hard45=<run_dir> ... --out-dir results\plots\<name>` | Renders a 6-panel classical-vs-CMG comparison per mission (outputs: angle tracking vs. reference; error: combined tracking-error magnitude over time; inputs: all four motor voltages), reading `trace.csv`/`summary.json` only, no hardware access. |
| `runners\plot_neuron_activity.py` | `.\.venv\Scripts\python.exe .\runners\plot_neuron_activity.py --run-dir <run_dir> --out <path.png>` | Plots CMG membrane potential (`v`) and gate state (`r`) for all 8 neurons (2 current-sign branches x 4 motor channels) from one CMG run's `trace.csv`. Needs a run recorded after the 2026-08-28 neuron-logging fix (`neuron_v_0..7`/`neuron_r_0..7` columns). No hardware access. |
| `runners\plot_neuron_activity.py` | `.\.venv\Scripts\python.exe .\runners\plot_neuron_activity.py --mission hard45 --run-dir results\hardware\<cmg_run> --out results\plots\<name>.png` | CMG membrane-potential (`v`) and gate-state (`r`) activity, all 8 units (4 channels x +/- branch), full mission + zoomed activation transient. **Needs `neuron_v_*`/`neuron_r_*` trace columns, added to `hover3dof_hil_cmg_control.py` 2026-08-28 -- only present in runs recorded after that date.** No hardware access. |

See `docs\PROGRESS_2026-08-27.md` for the full narrative: bugs found and
fixed, verified physical facts, and the current results table/analysis.

## 3. Julia — direct HIL bridge

`julia\Hover3DOFHIL.jl` now provides the same direct `ccall -> hil.dll`
connection family used by the Qube and Aero 2. The safe V0/V1 smoke test never
opens the Q8:

```powershell
julia --startup-file=no .\julia\hover_bridge_smoke.jl
```

It covers the verified motor/encoder mapping, unit conversion, vendor rate
filter, amplifier conversion, and final nonnegative voltage clamps. A live
closed-loop Julia runner is intentionally gated on the same sensor-only and
baseline-only validation ladder as the Python path.

---

## Known gaps

- No QUARC/PAL hardware entrypoint.
- No identified physical constants (Kf, Kt, L, Jyaw, Jpitch, Jroll) — the
  "3 DOF Hover User Manual" referenced by the Laboratory Guide hasn't been
  located on this machine.
- No motor channel / DAQ wiring verification against the physical unit.
