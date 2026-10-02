# Stability-priority recovery for Yaw360 and Hardstep

Status: implemented and offline-validated 2026-08-28. No hardware was opened or
commanded while implementing this revision.

## Evidence motivating the change

- Fresh Hard45 and Full3 PD/CMG ladders completed normally.
- The 45 s Yaw360 PD baseline aborted at 24.35 s with roll = -55.15 degrees.
- The 25 s Hardstep PD and 0.3 V CMG runs both aborted near 10.5 s with roll
  approximately +55.1 degrees.
- The failures therefore exist in the classical PD/actuator path and are not
  caused by CMG.
- During yaw, clipping turns some motors off. That destroys pitch/roll moment
  authority exactly when cross-axis stabilization is required.

Hard45 did not abort after 25 seconds: all new Hard45 runs completed 5,000
samples and then the runner intentionally forced outputs to zero. The runner now
prints `MISSION COMPLETE` before normal shutdown to make this distinction clear.

## Allocator equation

For the verified motor map (G), let

\[
d_{pr}=G^\dagger[0,\tau_p,\tau_r]^T,
\qquad d_y=G^\dagger[\tau_y,0,0]^T.
\]

Because (G\mathbf 1=0), adding common voltage (c\mathbf 1) changes motor
operating point without changing ideal generalized torque. With floor
(V_f=2\) V and maximum (V_m=24\) V, the available differential span is
(V_m-V_f=22\) V.

Pitch/roll is scaled only if it is itself infeasible:

\[
s_{pr}=\min\left(1,\frac{V_m-V_f}{\operatorname{range}(d_{pr})}\right).
\]

Yaw receives the largest feasible factor

\[
s_y=\max\{s\in[0,1]:
\operatorname{range}(s_{pr}d_{pr}+s d_y)\le V_m-V_f\}.
\]

The differential and common mode are

\[
d=s_{pr}d_{pr}+s_y d_y,
\]

\[
c=\operatorname{clip}
\left(V_{bias},V_f-\min(d),V_m-\max(d)\right),
\qquad u=d+c\mathbf1.
\]

Thus all motors remain in `[2,24] V`. When saturation is unavoidable,
pitch/roll stabilization is preserved before yaw tracking. The quaternion PD,
CMG membrane/gate equations, PES law, beta, learning rate, target, and 0.5 ms
neural timestep are unchanged. This allocator is a declared Hover-only actuator
adaptation and is applied identically to PD and PD-CMG.

## Offline replay evidence

Replay uses recorded states and does not predict the new closed-loop path.

| Source failure | Old pitch/roll torque-error RMS | New pitch/roll torque-error RMS | Change | Motor floor |
|---|---:|---:|---:|---:|
| Yaw360 PD, 45 s aborted | 0.017673 N m | approximately 0 | approximately -100% | 2 V |
| Hardstep PD, 25 s aborted | 0.266240 N m | 0.062542 N m | -76.5% | 2 V |
| Hardstep CMG 0.3 V aborted | 0.263258 N m | 0.062195 N m | -76.4% | 2 V |

On the Yaw360 trace, pitch/roll remained fully feasible and yaw scale averaged
0.999996 (minimum 0.9822). The common mode ranged from 2.0 to 14.61 V.

On Hardstep, pitch/roll scale averaged approximately 0.927 and yaw was reduced
more strongly because the simultaneous step demand was infeasible. Common mode
reached approximately 18.49 V. These values motivate staged armed segments.

## First physical stability-priority results

Two 10 s Yaw360 qualification segments completed normally. Mean combined error
was 3.04 and 3.08 degrees, maximum error was 5.39 and 5.30 degrees, and both yaw
and pitch/roll allocation scales remained exactly 1.0. The allocator therefore
fixed the initial motor-headroom problem over the tested interval.

The second segment was started after freezing a new raw home approximately 40
degrees away from the first. That is not a valid continuation. A yaw segment
must be followed by manually returning to the single frozen physical home; the
home must not be redefined at the segment endpoint.

Hardstep with stability-priority allocation improved the first 3 s mean error
from 22.64 to 19.09 degrees. The 9 s segment completed, but the 25 s run reached
roll +55.06 degrees near 6 s. Preserving the original discontinuous pitch/roll
demand more faithfully is not sufficient because the reference transition
itself is too aggressive for this hardware. The next Hardstep generation is
therefore explicitly shaped and scaled, identically for PD and PD-CMG.

## New logged data

Every future trace additionally saves:

- `allocator_yaw_scale`;
- `allocator_pitch_roll_scale`;
- `allocator_common_mode_V`;
- `allocator_motor_floor_V`;
- raw accumulated yaw/pitch/roll encoder positions;
- wrapped-yaw and per-axis tracking errors;
- full/partial mission completion status in `summary.json`.

All six neuron states, six gates, six activities, six currents, and 18 decoder
weights continue to be saved.

## Common setup

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28'
$runner = "$root\runners\hover3dof_hil_pd_cmg_control.py"
```

Runner SHA-256 for the current allocation + shaped-Hardstep generation:
`679180F559D449DBB671A4F9E0B725EB0EDF23CE1F91E64288EDCE2095059359`.

## Yaw360 staged verification

Place the rig in the physically neutral/unwound home and record it:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hover --duration 0.25
$probe = Get-ChildItem "$root\results\hardware\pd_dryrun_*" |
  Sort-Object LastWriteTime | Select-Object -Last 1
$yawHome = [double]((Get-Content "$($probe.FullName)\summary.json" |
  ConvertFrom-Json).raw_home_ypr_deg[0])
"Frozen yaw home = $yawHome deg"
```

Run a zero-output calculation first:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission yaw360 --duration 45 `
  --allocation-policy stability-priority --motor-floor-volts 2
```

For each armed command below, manually return to the frozen home. First run 10 s
of the same 45 s reference, then 20 s, then the full mission:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission yaw360 --duration 45 --stop-after 10 `
  --allocation-policy stability-priority --motor-floor-volts 2 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review

& $py $runner --controller pd --pd-profile mujoco --mission yaw360 --duration 45 --stop-after 20 `
  --allocation-policy stability-priority --motor-floor-volts 2 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review

& $py $runner --controller pd --pd-profile mujoco --mission yaw360 --duration 45 `
  --allocation-policy stability-priority --motor-floor-volts 2 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review
```

Do not run CMG until the full PD mission completes with stable pitch/roll. Then
repeat the 10 s segment with CMG at 0.3 V:

```powershell
& $py $runner --controller pd-cmg --pd-profile mujoco --mission yaw360 --duration 45 --stop-after 10 `
  --beta 0.5 --motor-residual-cap-volts 0.3 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --neural-substeps 10 `
  --allocation-policy stability-priority --motor-floor-volts 2 `
  --expected-raw-home-yaw-deg $yawHome --raw-home-yaw-tolerance-deg 5 `
  --armed --confirm-pd-review
```

If clean, run the full 45 s CMG mission at 0.3 V. Only afterward test 0.6 and
1.2 V, one at a time, always returning to the same raw home.

## Hardstep staged verification

First run a zero-output full-cycle shadow:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 --stop-after 9 `
  --allocation-policy stability-priority --motor-floor-volts 2
```

Then qualify PD at 3 s, 9 s, and finally 25 s, resetting level before each:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 --stop-after 3 `
  --allocation-policy stability-priority --motor-floor-volts 2 --armed --confirm-pd-review

& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 --stop-after 9 `
  --allocation-policy stability-priority --motor-floor-volts 2 --armed --confirm-pd-review

& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 `
  --allocation-policy stability-priority --motor-floor-volts 2 --armed --confirm-pd-review
```

Do not run CMG unless PD completes 25 s. Then qualify CMG at 0.3 V over 3 s,
9 s, and 25 s before considering 0.6 or 1.2 V.

### Actuator-feasible Hardstep after the original mission failed

Use reference scale 0.7 and a 0.5 s cubic transition. This retains the same four
three-axis targets and two-second phase schedule, but reduces amplitude and
removes the command discontinuity. It must be named `Hardstep-0.7-shaped` in
tables and figures; it is not the canonical discontinuous Hardstep.

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 --stop-after 9 `
  --reference-scale 0.7 --hardstep-transition-s 0.5 `
  --allocation-policy stability-priority --motor-floor-volts 2

& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 --stop-after 3 `
  --reference-scale 0.7 --hardstep-transition-s 0.5 `
  --allocation-policy stability-priority --motor-floor-volts 2 --armed --confirm-pd-review

& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 --stop-after 9 `
  --reference-scale 0.7 --hardstep-transition-s 0.5 `
  --allocation-policy stability-priority --motor-floor-volts 2 --armed --confirm-pd-review

& $py $runner --controller pd --pd-profile mujoco --mission hardstep --duration 25 `
  --reference-scale 0.7 --hardstep-transition-s 0.5 `
  --allocation-policy stability-priority --motor-floor-volts 2 --armed --confirm-pd-review
```

Only after the full PD run completes should CMG be tested at 0.3 V under the
identical scale, transition, allocation policy, motor floor, and duration.

## Scientific boundary

Results from `fixed-bias` and `stability-priority` allocation are separate
hardware generations. Do not compare a fixed-bias PD run against a
stability-priority CMG run. If this allocator succeeds for Yaw360/Hardstep, a
final uniform paper table should rerun both PD and PD-CMG under the same
stability-priority policy for every platform mission selected for that table.
