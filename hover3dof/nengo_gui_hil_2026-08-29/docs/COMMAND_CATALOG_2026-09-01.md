# Complete 3DOF Hover Nengo command catalog

This is the canonical command reference for reproducing any Hover mission.

## 1. Environment and universal launcher

Open PowerShell and define:

```powershell
$root = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29'
$launch = "$root\launch_hover_experiment.ps1"
```

The launcher selects the frozen mission profile, Nengo parameters, output
directory, and safety policy. It accepts:

```text
Missions:
  hover, roll, full3, hard45, hardstep, yaw360

Controllers:
  pd
  nengo-cmg-fixed, nengo-nef-pes
  nengo-lif-fixed, nengo-lif-pes
  nengo-alif-fixed, nengo-alif-pes
  nengo-izhikevich-fixed, nengo-izhikevich-pes
  nengo-lifrate-fixed, nengo-lifrate-pes

Modes:
  gui         real-time emulated plant + live Nengo GUI
  headless    accelerated emulated plant, same saved data
  q8-shadow   live Q8 encoders + GUI, all four outputs hard-coded zero
  hardware    physical closed loop; only pd and nengo-pes
```

`nengo-pes` is the hardware-qualified CMG-PES controller name.
`nengo-nef-pes` is its paper-facing emulated benchmark alias.

## 2. Real-time GUI — recommended interactive workflow

General form:

```powershell
& $launch -Mission MISSION -Controller CONTROLLER -Mode gui
```

The browser opens the dashboard. Press the Nengo **Play** button to start. The
plant/controller loop runs in real time, saves the 200 Hz trace, and saves all
2 kHz neural signals. Closing the GUI stops the session safely and preserves
the data accumulated to that point.

### CMG-PES, every mission

```powershell
& $launch -Mission hover    -Controller nengo-nef-pes -Mode gui
& $launch -Mission roll     -Controller nengo-nef-pes -Mode gui
& $launch -Mission full3    -Controller nengo-nef-pes -Mode gui
& $launch -Mission hard45   -Controller nengo-nef-pes -Mode gui
& $launch -Mission hardstep -Controller nengo-nef-pes -Mode gui
& $launch -Mission yaw360   -Controller nengo-nef-pes -Mode gui
```

### PD baseline, every mission

```powershell
& $launch -Mission hover    -Controller pd -Mode gui
& $launch -Mission roll     -Controller pd -Mode gui
& $launch -Mission full3    -Controller pd -Mode gui
& $launch -Mission hard45   -Controller pd -Mode gui
& $launch -Mission hardstep -Controller pd -Mode gui
& $launch -Mission yaw360   -Controller pd -Mode gui
```

### Any conventional family

Replace the controller with any of:

```powershell
& $launch -Mission roll -Controller nengo-lif-fixed        -Mode gui
& $launch -Mission roll -Controller nengo-lif-pes          -Mode gui
& $launch -Mission roll -Controller nengo-alif-fixed       -Mode gui
& $launch -Mission roll -Controller nengo-alif-pes         -Mode gui
& $launch -Mission roll -Controller nengo-izhikevich-fixed -Mode gui
& $launch -Mission roll -Controller nengo-izhikevich-pes   -Mode gui
& $launch -Mission roll -Controller nengo-lifrate-fixed    -Mode gui
& $launch -Mission roll -Controller nengo-lifrate-pes      -Mode gui
& $launch -Mission roll -Controller nengo-cmg-fixed        -Mode gui
```

The GUI panels are family-neutral:

- paired currents;
- membrane/native voltage;
- CMG gate or conventional auxiliary state;
- normalized activity used by the decoder;
- decoder output and row norms;
- PES target/error and update norms;
- quaternion error, Euler tracking, rates, torques, allocator, and motors.

For non-CMG neurons, the CMG gate-target and conductance panels are explicitly
zero and labeled as CMG-only quantities.

## 3. Hard-perturbation GUI

Add `-Disturbance hard-pulses`. Mission-specific pulse scaling is selected
automatically:

```powershell
& $launch -Mission roll     -Controller nengo-nef-pes       -Mode gui -Disturbance hard-pulses
& $launch -Mission full3    -Controller nengo-lifrate-fixed -Mode gui -Disturbance hard-pulses
& $launch -Mission hard45   -Controller nengo-izhikevich-pes -Mode gui -Disturbance hard-pulses
& $launch -Mission hardstep -Controller nengo-nef-pes       -Mode gui -Disturbance hard-pulses
& $launch -Mission yaw360   -Controller pd                  -Mode gui -Disturbance hard-pulses
```

The frozen hard-pulse Yaw360 matrix reached the ±180° simulation-divergence
boundary for all eleven controllers. Re-running it is valid for diagnosis, but
it is not expected to complete under the frozen profile.

## 4. Accelerated headless reproduction

Use the same mission/controller selections with `-Mode headless`:

```powershell
& $launch -Mission roll -Controller pd            -Mode headless
& $launch -Mission roll -Controller nengo-nef-pes -Mode headless
& $launch -Mission roll -Controller nengo-lif-pes -Mode headless

& $launch -Mission full3 -Controller nengo-izhikevich-pes -Mode headless -Disturbance hard-pulses
```

Headless mode saves the same trace and neural archive but does not wait for wall
clock time and does not open a browser.

## 5. Reproduce/resume the complete 110-cell Hover matrix

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'

& $py "$root\run_hover_neuron_family_campaign.py" --workers 3
& $py "$root\compile_hover_neuron_family_campaign.py"
```

The runner is resumable. A cell with a complete summary is not rerun. The
compiler audits all 100 neural archives, regenerates tables and figures, masks
non-comparable aborts, and rebuilds the SHA-256 manifest.

## 6. Connected Q8 GUI shadow — no motor output

Keep the E-stop engaged. Do **not** add `-ConfirmHardwareReview`:

```powershell
& $launch -Mission hover -Controller pd                    -Mode q8-shadow
& $launch -Mission hover -Controller nengo-cmg-fixed       -Mode q8-shadow
& $launch -Mission hover -Controller nengo-nef-pes         -Mode q8-shadow
& $launch -Mission hover -Controller nengo-lif-fixed       -Mode q8-shadow
& $launch -Mission hover -Controller nengo-lif-pes         -Mode q8-shadow
& $launch -Mission hover -Controller nengo-alif-fixed      -Mode q8-shadow
& $launch -Mission hover -Controller nengo-alif-pes        -Mode q8-shadow
& $launch -Mission hover -Controller nengo-izhikevich-fixed -Mode q8-shadow
& $launch -Mission hover -Controller nengo-izhikevich-pes  -Mode q8-shadow
& $launch -Mission hover -Controller nengo-lifrate-fixed   -Mode q8-shadow
& $launch -Mission hover -Controller nengo-lifrate-pes     -Mode q8-shadow
```

In this mode, the current encoder pose is tared as the initial condition. The
controller and GUI compute normally, but all four written Q8 outputs are zero
on every step and again in `finally`.

## 7. Physical closed-loop Hover

Read `C:\Research\hover3dof\docs\SAFETY_CHECKLIST.md`, confirm the E-stop, clear
the rig, and run one controller at a time. Only `pd` and `nengo-pes` are accepted.

### Hover qualification

```powershell
& $launch -Mission hover -Controller pd        -Mode hardware -ConfirmHardwareReview
& $launch -Mission hover -Controller nengo-pes -Mode hardware -ConfirmHardwareReview
```

### Roll

```powershell
& $launch -Mission roll -Controller pd        -Mode hardware -ConfirmHardwareReview
& $launch -Mission roll -Controller nengo-pes -Mode hardware -ConfirmHardwareReview
```

### Full3 — 50% reference

```powershell
& $launch -Mission full3 -Controller pd        -Mode hardware -ConfirmHardwareReview
& $launch -Mission full3 -Controller nengo-pes -Mode hardware -ConfirmHardwareReview
```

### Hard45 — 40% reference

```powershell
& $launch -Mission hard45 -Controller pd        -Mode hardware -ConfirmHardwareReview
& $launch -Mission hard45 -Controller nengo-pes -Mode hardware -ConfirmHardwareReview
```

### Hardstep — 35% reference, 0.3 s smoothed transition

```powershell
& $launch -Mission hardstep -Controller pd        -Mode hardware -ConfirmHardwareReview
& $launch -Mission hardstep -Controller nengo-pes -Mode hardware -ConfirmHardwareReview
```

### Physical Yaw360

The universal launcher deliberately blocks this mission in hardware mode. The
matched PD trial exceeded the −20.083° roll safety limit. Use GUI/headless
simulation until the mechanical imbalance and stability-priority allocation
are redesigned and requalified.

## 8. Analyze any neural archive

```powershell
$analyzer = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\analyze_neural_archive.py'
$familyPlot = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\plot_neuron_family_archive.py'
$archive = 'FULL_PATH_TO_RUN\neural_trace_2khz.npz'

& $py $analyzer $archive --output-prefix 'FULL_PATH_TO_RUN\analysis\neural' --export-csv
& $py $familyPlot $archive --output-prefix 'FULL_PATH_TO_RUN\analysis\family'
```

## 9. Result locations

```text
Manual GUI/headless runs:
C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\gui_and_manual_runs

Complete Hover family matrix:
C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hover_neuron_family_matched_25s_2026-09-01

Compiled tables and figures:
C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hover_neuron_family_compiled_2026-09-01

Q8 GUI shadows:
C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\q8_gui_shadow

Qualified physical runs:
C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware
```

## 10. Frozen parameters

```text
hardware/plant step       0.005 s (200 Hz)
inner Nengo step          0.0005 s (2 kHz, 10 substeps)
beta                      0.2
per-motor residual cap    0.2 V
residual slew             1 V/s
PES learning rate         0.0002
k_error                   2
k_rate                    0
startup coordinates       current measured yaw/pitch/roll are tared to zero
```
