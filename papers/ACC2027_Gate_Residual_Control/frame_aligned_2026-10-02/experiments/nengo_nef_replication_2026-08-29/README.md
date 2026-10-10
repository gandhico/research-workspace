# Nengo/NEF replication of online-PES CMG residual control

This isolated experiment reproduces the paper's matched quaternion-PD baseline
and online-PES adaptive coupled membrane--gate (CMG) residual controller inside
Nengo 4.1.0, using the same MuJoCo Crazyflie rotor-design and Skydio X2 plants.

The frozen pre-Nengo paper and Hover results are not overwritten.

## Environment

Use:

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
```

Verified versions:

- Python 3.13.11
- MuJoCo 3.12.0
- Nengo 4.1.0
- Nengo GUI 0.6.0
- NumPy 2.5.2
- Matplotlib 3.11.1
- pandas 3.0.5

Nengo, Nengo GUI, and pandas were added to the existing paper virtual
environment.

## Interactive Nengo GUI

The experiment now includes a live twin-plant dashboard. It runs the matched
quaternion-PD baseline and PD + CMG + online Nengo PES controller side by side,
while exposing attitude, quaternion error, normalized torque, all four rotor
commands, paired currents, membrane voltage, gate, decoder activity and online
decoder norms.

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29'

& $py "$root\launch_gui.py" --platform x2 --mission hard45
& $py "$root\launch_gui.py" --platform cf2-rotor --mission yaw360

# Nengo GUI and live neural-plant MuJoCo window
& $py "$root\launch_gui.py" --platform x2 --mission hard45 `
  --mujoco-viewer neural --realtime --viewer-fps 30
```

See `GUI_GUIDE_2026-08-29.md` for the panel map, equations, fair-comparison
procedure and smoke-test command. The GUI is exploratory; the validated batch
campaign below remains the source of paper metrics.

## What is represented in Nengo

The quaternion-PD baseline, MuJoCo plant, altitude loop, actuator mixer, limits,
mission references, and disturbances are unchanged. The neural addition is a
six-unit paired population (`+x,+y,+z,-x,-y,-z`) with the paper's continuous
membrane--gate state equations. A 3 x 6 decoder maps its gate-derived activity
to normalized residual torque, and Nengo's built-in PES operator adapts that
decoder online.

The population receives explicitly constructed positive/negative currents at
the neuron ports. This is a deliberate conformance design: the learned decoder
and PES update are Nengo/NEF-native, but the encoding is not a conventional
randomly tuned LIF representation. Describing it as a **Nengo-native NEF/PES
decoder realization of the paired CMG population** is accurate; describing the
six units as a generic LIF ensemble would not be.

## One matched experiment

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29'

& $py "$root\run_mujoco_nef.py" `
  --platform x2 --controller classical --mission hard45 `
  --duration 45 --dt 0.0005 --actuator-scale 1.0 `
  --log-every 10 `
  --output "$root\results\manual\x2_hard45_classical"

& $py "$root\run_mujoco_nef.py" `
  --platform x2 --controller nengo-nef-pes --mission hard45 `
  --duration 45 --dt 0.0005 --beta 0.5 `
  --learning-rate 0.0008 --k-error 8 --k-rate 0 `
  --actuator-scale 1.0 --log-every 10 `
  --output "$root\results\manual\x2_hard45_nengo_nef_pes"
```

Use `--actuator-scale 1.5` for `cf2-rotor`; the increased rotor authority is a
declared design variant and must remain explicit in reporting.

## Reproduce or resume the complete campaign

```powershell
& $py "$root\run_campaign.py" `
  --output-root "$root\results\matched_45s" `
  --duration 45 --log-every 10

& $py "$root\compile_and_plot.py"

& $py "$root\verify_archived_equivalence.py"

& $py -W ignore -m unittest "$root\test_nengo_cmg.py" -v
```

The campaign runner skips complete summaries, so the command is safe to resume.
Metrics use all 90,000 control steps per run. `--log-every 10` writes the
readable controller CSV at 200 Hz without downsampling reported metrics. New
Nengo runs additionally preserve lossless full-rate neural telemetry at 2 kHz.

## Outputs

- Matched raw runs: `results\matched_45s\`
- Paper-facing table: `results\compiled\matched_results.csv`
- JSON table: `results\compiled\matched_results.json`
- All tracking and neuron plots: `results\plots\`
- Equations, audit, and conclusions: `PROGRESS_2026-08-29.md`
- Full telemetry schema, live-GUI recording, plots, audit, and CSV/MAT export:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\docs\NENGO_FULL_TELEMETRY_2026-08-31.md`

The live MuJoCo GUI saves a full-rate session archive on normal close or after
one mission duration. Its default output is `results\gui_sessions\`. Run
`analyze_neural_archive.py` on any batch, GUI, or Hover neural NPZ.
