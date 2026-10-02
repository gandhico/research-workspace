# Full Nengo telemetry for CMG--PES experiments

**Checkpoint:** 2026-08-31  
**Scope:** MuJoCo batch runs, the live MuJoCo/Nengo GUI, and the Quanser 3DOF Hover Nengo GUI/HIL runner.

The telemetry layer records every scientifically meaningful input, internal
CMG state, state-equation term, PES signal, decoder parameter, controller
output, and synchronized plant/actuator signal. It does not dump Nengo builder
scratch buffers because those are implementation memory rather than model
variables and are not stable across Nengo versions. The CMG unit is
non-spiking, so there is no spike train to log.

## Files and rates

| Execution path | Control/plant file | Lossless neural file | Rate |
|---|---|---|---:|
| MuJoCo batch `run_mujoco_nef.py` | `trace.csv` | `neural_trace_full_rate.npz` | default 2 kHz |
| Live MuJoCo/Nengo GUI | plant and controller states are inside the NPZ | `neural_trace_full_rate.npz` | 2 kHz |
| Hover Nengo GUI/HIL | `trace.csv` | `neural_trace_2khz.npz` | 200 Hz + 2 kHz |

Every archive has an adjacent `neural_trace_schema.json`. NPZ is the canonical,
lossless source. Flattened CSV and MATLAB files are optional derivatives.

## Neural archive schema

All arrays begin with sample dimension `N`; there are six directional units
and all `3 x 6 = 18` decoder parameters are retained.

| Signal | Shape after `N` | Meaning |
|---|---:|---|
| `t` | scalar | Neural simulation time. |
| `plant_step` or `hardware_step`, `substep` | scalar | Exact cross-rate alignment. |
| `baseline_tau[/_ypr]` | 3 | Baseline quaternion-PD torque entering the residual block. |
| `target[/_ypr]` | 3 | Bounded PES teaching target. |
| `current` | 6 | Paired directional currents. |
| `voltage`, `gate`, `activity` | 6 each | CMG states `v,r` and decoder activity `a`. |
| `effective_threshold` | 6 | `v_th-gamma r`. |
| `gate_argument`, `gate_target` | 6 each | Sigmoid argument and `r_inf`. |
| `conductance_gain`, `conductance` | 6 each | `g_0+g_s abs(J)` and `g(J)r^2`. |
| `membrane_lambda`, `membrane_drive` | 6 each | Exact exponential membrane decay and drive terms. |
| `decoded_raw`, `decoded_clipped` | 3 each | `Wa` and `clip(Wa,-1,1)`. |
| `pes_error` | 3 | `decoded_clipped-target` (times learning enable in the GUI). |
| `weights`, `weight_delta` | 3 x 6 each | All decoder coefficients and every neural-step update. |
| `residual_torque[/_ypr]` | 3 | Bounded residual torque. |

Matched conventional-neuron archives add `native_current`, `raw_output`, and
the Nengo-exposed states `state_voltage`, `state_refractory_time`,
`state_adaptation`, and `state_recovery` as applicable. `state_gate` preserves
the CMG gate through the same generic schema. Thus a later analysis can recover
raw spike timing, the filtered decoder feature, family-specific state dynamics,
and the exact normalized PES transform without rerunning the plant.

The live MuJoCo GUI additionally records both twin-plant outputs: quaternion,
body rates, altitude, vertical rate, four normalized rotors, saturation, both
errors and baseline torques, command, reference, beta, and learning enable.

The Hover CSV additionally records raw encoders, measured/reference Euler
angles, wrapped errors, quaternions, body rates, PD/requested/realized torques,
baseline/computed/written motor voltage, DAC write, allocator scales, loop
execution time, deadline flags, and the neural state synchronized at 200 Hz.

## Record a MuJoCo batch run

Full-rate neural recording is on by default even when `--log-every 10` reduces
the readable CSV to 200 Hz.

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29'

& $py "$root\run_mujoco_nef.py" `
  --platform x2 --controller nengo-nef-pes --mission hard45 `
  --duration 45 --dt 0.0005 --beta 0.5 `
  --learning-rate 0.0008 --k-error 8 --k-rate 0 `
  --actuator-scale 1.0 --log-every 10 `
  --output "$root\results\manual\x2_hard45_nengo_full_telemetry"
```

For `cf2-rotor`, retain the declared `--actuator-scale 1.5` design assumption.
Use `--no-neural-archive` only when intentionally discarding mechanism data.

## Record a live MuJoCo + Nengo GUI session

Recording is on by default, is capped at one mission duration, and saves when
that cap is reached or the GUI closes normally.

```powershell
& $py "$root\launch_gui.py" --platform x2 --mission hard45 `
  --duration 45 --mujoco-viewer neural --realtime --viewer-fps 30
```

Default output: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\gui_sessions\`.
Use `--max-log-seconds` or `--telemetry-output-root` when needed. An abrupt
process kill before the cap can bypass the close hook, so stop the GUI normally.

## Record Hover

The Hover worker saves from `finally`, including controlled aborts. A PD run has
no neural NPZ because it executes no neural controller; its 200 Hz CSV remains
complete. A Nengo-PES run writes both rates.

```powershell
$pyh = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$hover = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29'

# Emulated; no hardware access.
& $pyh "$hover\launch_hover_nengo_gui.py" `
  --io emulated --controller nengo-pes --mission hard45 --duration 25

# Q8 zero-output dry-run. No --armed flag means all four outputs remain zero.
& $pyh "$hover\launch_hover_nengo_gui.py" `
  --io q8 --controller nengo-pes --mission hover --duration 5
```

## Validate, plot, and export any archive

```powershell
$tool = "$root\analyze_neural_archive.py"
$archive = 'C:\path\to\neural_trace_full_rate.npz'

& $py $tool $archive
& $py $tool $archive --export-csv
# Optional after SciPy is installed in this environment:
& $py $tool $archive --export-mat
```

The tool rejects inconsistent sample counts and NaN/Inf. It writes statistics,
two PNG figures, and two PDFs covering `v`, `r`, `r_inf`, current, activity,
conductance, membrane equation terms, raw/clipped decoding, PES target/error,
decoder/update norms, and residual torque.

For a repository-wide inventory, `scripts/catalog_experiment_data.py
--deep-neural-stats` writes a run catalog, visual-artifact catalog, and a
signal-level CSV/JSON containing every archive key's path, shape, dtype, sample
rate, finite check, minimum, maximum, mean, standard deviation, RMS, nonzero
fraction, element count, and uncompressed byte count. This is an index, not a
replacement for the lossless NPZ source.

## Verified at this checkpoint

| Check | Result |
|---|---|
| Direct CMG/PES vs Nengo, 2000 steps | Passed; maximum residual difference `1.687e-8`; `v`, `r`, activity differences zero. |
| Expected Nengo raw-weight scheduling skew | `7.198e-4`, below the one-update bound `8.1e-4`. |
| Hover emulated 0.2 s smoke | 40 hardware rows and exactly 400 finite neural samples, 22 signal groups. |
| MuJoCo batch 0.1 s smoke | Exactly 200 finite neural samples, 21 signal groups. |
| Live GUI X2 and CF2-design 0.05 s smoke | Exactly 100 samples each; 34 signal groups. |
| Connected Q8 zero-output qualification | PD and Nengo complete at 200 Hz; 1,000 rows each, Nengo 10,000 finite neural samples, zero deadline misses, and all four DAC outputs exactly zero. |
| Connected Q8 five-mission Nengo shadow set | 26,000 control rows, 260,000 neural samples, all five runs complete, isolated deadline misses 0.12--0.34%, maximum physical DAC exactly zero. |
