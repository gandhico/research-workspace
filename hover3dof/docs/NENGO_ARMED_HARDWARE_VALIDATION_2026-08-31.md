# Armed Nengo CMG-PES hardware validation — 2026-08-31

## Outcome

The first staged physical Quanser 3DOF Hover validation of the genuine inner-Nengo CMG-PES controller completed without a safety abort. The experiment used the MuJoCo-matched quaternion-PD baseline and a matched eight-second `roll` mission.

| Controller | beta | Per-motor residual cap | Mean attitude error | Maximum attitude error | Mean improvement vs PD | Maximum improvement vs PD |
|---|---:|---:|---:|---:|---:|---:|
| PD baseline | 0 | 0 V | 5.4630 deg | 8.1942 deg | — | — |
| Nengo CMG-PES, low authority | 0.10 | 0.10 V | 5.3869 deg | 8.1051 deg | 1.394% | 1.087% |
| Nengo CMG-PES, moderate authority | 0.20 | 0.20 V | 5.3449 deg | 8.1233 deg | **2.162%** | 0.866% |

These are single trials (`n=1`) and should be described as preliminary staged hardware validation, not a statistical performance estimate. Repeat each matched cell before using uncertainty claims.

## Staged sequence and exact commands

All runs used Q8 hardware I/O, amplifier gain 3, expected raw yaw home 0±5 deg, a 200 Hz hardware loop, and the GUI heartbeat interlock. The GUI model must be loaded and its Run button pressed after launching each command.

### Zero-reference PD qualification (5 s)

```powershell
& 'C:\Research\hover3dof\.venv\Scripts\python.exe' `
  'C:\Research\hover3dof\nengo_gui_hil_2026-08-29\launch_hover_nengo_gui.py' `
  --io q8 --armed --confirm-hardware-review --controller pd --mission hover `
  --duration 5 --expected-raw-home-yaw-deg 0 --raw-home-yaw-tolerance-deg 5 `
  --max-abs-pitch-deg 20 --max-abs-roll-deg 20
```

Result: completed, 1,000 samples, mean error 0.1041 deg, maximum error 0.1584 deg, one isolated deadline miss.

### Matched PD Roll baseline (8 s)

```powershell
& 'C:\Research\hover3dof\.venv\Scripts\python.exe' `
  'C:\Research\hover3dof\nengo_gui_hil_2026-08-29\launch_hover_nengo_gui.py' `
  --io q8 --armed --confirm-hardware-review --controller pd --mission roll `
  --duration 8 --expected-raw-home-yaw-deg 0 --raw-home-yaw-tolerance-deg 5 `
  --max-abs-pitch-deg 15 --max-abs-roll-deg 25
```

### Nengo CMG-PES Roll, low authority (8 s)

```powershell
& 'C:\Research\hover3dof\.venv\Scripts\python.exe' `
  'C:\Research\hover3dof\nengo_gui_hil_2026-08-29\launch_hover_nengo_gui.py' `
  --io q8 --armed --confirm-hardware-review --controller nengo-pes --mission roll `
  --duration 8 --beta 0.1 --motor-residual-cap-volts 0.1 `
  --learning-rate 0.0002 --k-error 2 --k-rate 0 --residual-slew-v-per-s 1 `
  --expected-raw-home-yaw-deg 0 --raw-home-yaw-tolerance-deg 5 `
  --max-abs-pitch-deg 15 --max-abs-roll-deg 25
```

### Nengo CMG-PES Roll, moderate authority (8 s)

Same command as above with `--beta 0.2 --motor-residual-cap-volts 0.2`.

## Safety and timing audit

All three matched Roll runs completed 1,600/1,600 control samples and returned all four Q8 analog outputs to zero in the runner's `finally` path. No attitude or deadline safety condition fired.

| Controller | Max |yaw| | Max |pitch| | Max |roll| | Deadline-miss fraction | Longest consecutive misses |
|---|---:|---:|---:|---:|---:|
| PD | 0.088 deg | 0.220 deg | 7.075 deg | 0% | 0 |
| CMG-PES beta=0.10 | 0.088 deg | 0.264 deg | 7.383 deg | 3.563% | 2 |
| CMG-PES beta=0.20 | 0.088 deg | 0.220 deg | 7.471 deg | 2.063% | 3 |

The configured abort threshold was 20 consecutive deadline misses. The Nengo timing burden is visible and must continue to be reported; neither run approached the abort threshold.

## Neural interpretation

The six signed units are ordered `[+yaw,+pitch,+roll,-yaw,-pitch,-roll]`. In both physical Roll runs, only the signed Roll pair activated materially:

- beta=0.10 mean gates: `[5.0e-6, 3.8e-6, 0.9065, 5.2e-6, 4.4e-6, 0.2648]`.
- beta=0.20 mean gates: `[5.1e-6, 3.8e-6, 0.9034, 5.5e-6, 4.3e-6, 0.2580]`.
- Decoder Frobenius changes were 0.1830 and 0.1840, respectively.
- Applied residual RMS values were 0.0750 V and 0.1536 V.
- The residual touched its cap in 30.56% and 26.13% of individual motor samples, confirming that both trials were authority-limited.

This selective signed-axis activation is consistent with the architecture and is stronger evidence than a performance number alone: the unused yaw/pitch units stayed effectively closed during a single-axis Roll mission.

## Data and figures

- Compiled table, figures, and SHA-256 manifest: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware_armed_roll_validation_2026-08-31`
- PD raw run: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware\pd_roll_none_armed_20260831_184229`
- Low-authority raw run: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware\nengo-pes_roll_none_armed_20260831_184341`
- Moderate-authority raw run: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware\nengo-pes_roll_none_armed_20260831_184512`

Each Nengo run contains the 200 Hz `trace.csv`, lossless 2 kHz `neural_trace_2khz.npz`, schema, summary, dependency manifest, flattened neural CSV, statistics JSON, and neural/equation-term figures in PNG and PDF.

The optional MATLAB export was not generated because SciPy is not installed in `C:\Research\hover3dof\.venv`. This does not affect the lossless NPZ or CSV archives.

## Next experiment

Repeat the exact three matched Roll cells at least three times. Freeze mean±standard deviation and paired per-trial improvements before increasing residual authority or advancing to `full3`, `hard45`, `hardstep`, or `yaw360`. The current result supports feasibility and selective neural operation; it does not yet support a population-level hardware improvement claim.
