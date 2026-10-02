# Next focused PD/CMG hardware ladder

This protocol follows the successful Roll design: one fresh PD baseline followed
by CMG residual-cap levels 0.3, 0.6, and 1.2 V. The MuJoCo PD law, CMG/PES
equations, beta, learning rate, teaching signal, neural timestep, reference, and
duration remain fixed inside each ladder.

The runner for this round has SHA-256
`E641B3BD2B2C43D206DDA11FF8FFAB9730849B4CDC68662BDF9C23E4F7C474D2`.
It adds provenance and metric safeguards, not a controller-law change:

- accumulated raw encoder home in every trace and summary;
- optional absolute yaw-home guard before arming;
- wrapped yaw error and per-axis MAE/RMSE;
- Yaw360-only durations up to 60 s;
- unchanged 55 degree pitch/roll aborts;
- the same complete six-neuron and 18-weight log.

## Common setup

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28'
$runner = "$root\runners\hover3dof_hil_pd_cmg_control.py"
```

Return the rig to the same level configuration before every command. Do not
automate commands back-to-back: inspect each run and physically reset first.

## Hard45 ladder, 25 s

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hard45 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission hard45 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission hard45 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 0.6 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission hard45 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review
```

## Full3 ladder, 25 s

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission full3 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission full3 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission full3 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 0.6 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission full3 --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review
```

## Hardstep ladder

Hardstep is more aggressive than Hard45 because it changes the three-axis
reference discontinuously every two seconds after the first second. The largest
commands are yaw 0.90 rad = 51.6 degrees, roll 0.80 rad = 45.8 degrees, and
pitch 0.55 rad = 31.5 degrees. The abrupt coupled transitions can still drive
measured roll beyond the unchanged 55 degree abort. Do not begin with the full
armed mission.

First execute a full-cycle, zero-output shadow calculation:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 9
& $py $runner --controller pd-cmg --pd-profile mujoco --mission hardstep --duration 9 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10
```

Inspect the computed voltages, reference transitions, timing, and predicted
saturation. If the shadow traces are clean, qualify only the first step with PD:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 3 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review
```

If that run is stable and comfortably inside the pitch/roll limits, run one
complete eight-second pattern plus the initial one-second hold:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 9 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review
```

Only after both qualifications complete should the publishable 25 s ladder be
run. Return the rig to the same level home before every command:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission hardstep --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission hardstep --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 0.6 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission hardstep --duration 25 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 --armed --confirm-pd-review
```

Any abort invalidates that run. Do not raise the 55 degree limit or selectively
shorten only one controller. If the PD baseline cannot complete, Hardstep stays
a qualification/limitation result rather than a performance comparison.

## Yaw360 recovery ladder

The failed 30 s pair began from absolute raw yaw homes separated by 226.58
degrees, and both violated the roll limit. The next ladder first freezes the
absolute home, then slows the same smooth 360 degree reference to 45 s. This is
a declared mission-duration adaptation applied equally to PD and PD-CMG; it is
not a neural/controller-law retune.

First place the rig in a physically neutral, unwound yaw configuration and run
this zero-output home probe:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hover --duration 0.25
$probe = Get-ChildItem "$root\results\hardware\pd_dryrun_*" |
  Sort-Object LastWriteTime | Select-Object -Last 1
$yawHome = [double]((Get-Content "$($probe.FullName)\summary.json" |
  ConvertFrom-Json).raw_home_ypr_deg[0])
"Frozen yaw home = $yawHome deg"
```

Before every following command, manually return the rig to that same physical
home. The runner refuses to arm if the accumulated yaw encoder differs by more
than 5 degrees.

Run the 45 s PD baseline first:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission yaw360 --duration 45 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review
```

If PD does not complete all 9,000 samples with an empty abort reason, do not run
CMG at 45 s. Return to the same home and repeat PD at 60 s. If 60 s also fails,
stop for a mechanical/cable/yaw-roll coupling review; do not raise the roll
limit.

If the 45 s PD baseline completes, run the CMG cap ladder, returning to the
frozen raw home before every command:

```powershell
& $py $runner --controller pd-cmg --pd-profile mujoco --mission yaw360 --duration 45 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission yaw360 --duration 45 `
  --beta 0.5 --motor-residual-cap-volts 0.6 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review

& $py $runner --controller pd-cmg --pd-profile mujoco --mission yaw360 --duration 45 `
  --beta 0.5 --motor-residual-cap-volts 1.2 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review
```

For a 60 s ladder, replace every `--duration 45` with `--duration 60` and use a
fresh 60 s PD baseline. Never compare a 45 s CMG run with a 60 s PD run.

## Compile and audit all data

```powershell
& $py "$root\tools\compile_pd_cmg_campaign.py" `
  --hardware-root "$root\results\hardware" `
  --out-dir "$root\results\compiled"

Import-Csv "$root\results\compiled\campaign_pairs.csv" |
  Format-Table mission,duration_s,motor_residual_cap_V,pd_run,cmg_run,pair_valid,home_match_ok,wrapped_error_mean_deg_improvement_pct,qerr_mean_rad_improvement_pct
```

The compiler retains aborted/incomplete runs for audit but marks them invalid.
For Yaw360 it also refuses a valid pair unless both runs saved raw-home data and
their home difference is inside the declared tolerance. Every CMG result must
contain six membrane states, six gate states, six activities, six currents, and
all 18 decoder weights.
