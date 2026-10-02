# MuJoCo-matched PD / torque-space CMG hardware runbook

This is a new experiment track. The frozen LQR results and
`C:\Research\hover3dof\results\plots\final_best` remain untouched.

## 1. What is reproduced exactly

The default `--pd-profile mujoco` follows canonical
`gra_control.platforms.drone.run_drone`:

1. Construct reference and measured quaternions.
2. Compute shortest-path quaternion error vector.
3. Use body-axis quaternion PD with
   `wn_xyz=[4,4,3.5]`, `kq=2*J*wn^2`, and
   `kw=2*0.95*wn*J`.
4. Clip baseline torque with the same model/inertia policy
   `J_xyz*[12,12,10]`.
5. Feed that three-axis torque directly to the canonical
   `CMGResidualAugmentor`.
6. Use the independent PES target
   `clip(k_error*eq-k_rate*omega,-1,1)` after the documented Hover coordinate
   transform.
7. Decode before updating PES; the new weights affect the next neural sample.
8. Use `beta=.5`, `eta=8e-4`, `k_error=8`, `k_rate=0`.
9. Advance CMG/PES at `dt=.0005 s`: ten internal substeps per 5 ms hardware
   measurement/control interval.
10. Add the residual in three-axis torque space before four-actuator allocation.

The alternative `--pd-profile lqr-equivalent` remains only to prove the bridge
to the frozen LQR. It is not the requested MuJoCo PD experiment, and the runner
refuses to combine that profile with `pd-cmg`.

## 2. Declared Hover adaptations

These differences are necessary and are logged/reported:

| Difference | MuJoCo drones | 3DOF Hover implementation |
|---|---|---|
| Attitude source | simulator quaternion | encoder yaw/pitch/roll converted to quaternion |
| Angular rate | MuJoCo rigid-body rate | vendor-filtered Euler rates converted to body rate |
| Controller coordinates | xyz = roll/pitch/yaw | ypr internally, with explicit reorder/sign transform |
| Allocation | collective + body moments to XML rotors | 2 V common bias + four positive motor voltages |
| Actuator bounds | XML rotor ranges | 0–24 motor-equivalent volts |
| Residual safety | actuator mixer/XML clipping | additional ±1.2 V per-motor projection and 4 V/s slew |
| Sampling | new state every 0.5 ms | encoder state held for ten 0.5 ms neural/PES substeps |
| Plant freedom | free 6-DOF with altitude loop | fixed-base 3 rotational DOFs |

The ±1.2 V residual cap and 4 V/s slew are safety-motivated improvements, not
features present in the MuJoCo runs. Requested and realized residual torque are
both saved so their effect cannot be hidden.

## 3. Saved data

Every PD-CMG hardware trace saves:

- measured and reference yaw/pitch/roll;
- filtered Euler rates and converted body angular rates;
- quaternion angle error and three quaternion-error vector components;
- MuJoCo PD torque per axis;
- PES learning target per axis;
- requested residual torque and realized post-allocation residual torque;
- raw/clipped baseline motor voltages;
- requested/applied motor residuals and final written voltages;
- lower/upper saturation flags;
- all six membrane states `neuron_v_0..5`;
- all six gate states `neuron_r_0..5`;
- all six amplified decoder activities `neuron_activity_0..5`;
- all six CMG input currents `neuron_current_0..5`;
- all 18 decoder weights `decoder_w_0..17` at every 200 Hz logged sample;
- loop time, wall time, deadline misses and abort reason.

The CMG internally advances ten times per logged hardware sample. The saved
neuron values are the post-substep states at each 200 Hz control boundary. This
keeps files manageable while preserving the control-relevant state trajectory.

## 4. Frozen first comparison

| Mission | Duration | beta | eta | k-error | k-rate | Neural substeps | Motor cap |
|---|---:|---:|---:|---:|---:|---:|---:|
| hard45 | 25 s | .5 | 8e-4 | 8 | 0 | 10 | 1.2 V |
| full3 | 25 s | .5 | 8e-4 | 8 | 0 | 10 | 1.2 V |
| yaw360 | 30 s | .5 | 8e-4 | 8 | 0 | 10 | 1.2 V |

Do not reuse the mission-specific LQR-Hover tuning (`beta=.4`, smaller learning
rates, k-error 2/4) for this first experiment. That would no longer reproduce the
MuJoCo controller. It may later be tested as a clearly named Hover-tuned variant.

## Phase 0 — offline checks

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28'
$runner = "$root\runners\hover3dof_hil_pd_cmg_control.py"

& $py "$root\tests\test_pd_baseline.py"
& $py "$root\tests\test_plotters.py"
& $py "$root\tools\validate_pd_against_classical_trace.py" `
  'C:\Research\hover3dof\results\hardware\classical_armed_20260828_123415' `
  'C:\Research\hover3dof\results\hardware\classical_armed_20260827_232303' `
  'C:\Research\hover3dof\results\hardware\classical_armed_20260828_123653'
```

The trace-equivalence command validates only the labeled LQR-equivalent profile.
It proves the motor map; it does not claim MuJoCo PD and LQR use the same gains.

Replay the MuJoCo-matched PD-CMG path over frozen measured states:

```powershell
& $py "$root\tools\replay_pd_cmg_on_trace.py" 'C:\Research\hover3dof\results\hardware\classical_armed_20260828_123415'
& $py "$root\tools\replay_pd_cmg_on_trace.py" 'C:\Research\hover3dof\results\hardware\classical_armed_20260827_232303'
& $py "$root\tools\replay_pd_cmg_on_trace.py" 'C:\Research\hover3dof\results\hardware\classical_armed_20260828_123653'
```

Every replay must show `all_bounds_pass: true`, neural dt 0.0005 s, motor
residual no greater than 1.2 V, slew no greater than 4 V/s, and commands in
0–24 V. Replay verifies the signal/safety envelope, not closed-loop performance.

## Phase 1 — Q8 sensor/shadow only

These open the Q8 but continually write zero:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hover --duration 5
& $py $runner --controller pd-cmg --pd-profile mujoco --mission hover --duration 5
```

Inspect tare, quaternion error, body rates, MuJoCo PD torque, computed motor
voltages, neuron states, decoder weights, deadline fraction and abort reason.

## Phase 2 — short armed qualification

Only after the physical checklist, E-stop, guards, board identity and operator
positions are confirmed. The default 55-degree pitch/roll aborts must be inside
the verified mechanical envelope; otherwise pass lower verified limits.

The MuJoCo PD gains are not the LQR gains. Therefore qualify them conservatively:

```powershell
& $py $runner --controller pd --pd-profile mujoco --mission hover --duration 5 --armed --confirm-pd-review
```

Stop if level regulation, signs, timing, or voltage behavior is not correct.
Do not proceed by silently substituting LQR gains.

Then test CMG at reduced residual authority while keeping the MuJoCo neural
parameters unchanged:

```powershell
& $py $runner --controller pd-cmg --pd-profile mujoco --mission hover --duration 5 --motor-residual-cap-volts 0.3 --armed --confirm-pd-review
```

If clean, repeat at 0.6 V and then the frozen 1.2 V cap. The cap escalation is a
hardware safety procedure; `beta=.5`, eta, target gains and neural dt do not
change.

## Phase 3 — first matched mission set

Run a fresh PD baseline immediately before each PD-CMG condition.

```powershell
# hard45
& $py $runner --controller pd --pd-profile mujoco --mission hard45 --duration 25 --armed --confirm-pd-review
& $py $runner --controller pd-cmg --pd-profile mujoco --mission hard45 --duration 25 --armed --confirm-pd-review

# full3
& $py $runner --controller pd --pd-profile mujoco --mission full3 --duration 25 --armed --confirm-pd-review
& $py $runner --controller pd-cmg --pd-profile mujoco --mission full3 --duration 25 --armed --confirm-pd-review

# yaw360: do not reuse the unguarded 30 s commands after the paired roll aborts.
# Follow NEXT_FOCUSED_LADDER_2026-08-28.md for matched raw-home guarding and
# the predeclared 45 s / fallback 60 s recovery sequence.
```

## Phase 4 — contamination and quality review

```powershell
& $py "$root\tools\inspect_trace_steps.py" '<PD_RUN_DIR>' '<PD_CMG_RUN_DIR>'
```

Require matched mission/duration/code hash, empty abort reason, acceptable
deadline fraction, no unlogged contact, and predeclared exclusion rules. For
yaw360, pitch/roll single-sample jumps are useful contact evidence; do not reuse
that same threshold for faster hard45/full3 dynamics.

Compile the complete campaign and validate the neuron schema:

```powershell
& $py "$root\tools\compile_pd_cmg_campaign.py" `
  --hardware-root "$root\results\hardware" `
  --out-dir "$root\results\compiled"
```

The compiler keeps aborted and historical runs for audit but marks them invalid.
Yaw360 pairs additionally require saved, tolerance-matched absolute yaw homes.

## Phase 5 — tracking and neuron plots

```powershell
& $py "$root\plotters\plot_pd_tracking.py" --pd '<PD_RUN_DIR>' --pd-cmg '<PD_CMG_RUN_DIR>' --out "$root\results\plots\<mission>_pd_vs_pd_cmg.png"
& $py "$root\plotters\plot_pd_neurons.py" --run-dir '<PD_CMG_RUN_DIR>' --out "$root\results\plots\<mission>_pd_cmg_neurons.png"
```

The first set is qualification. Paper-quality evidence requires at least three
interleaved clean pairs per mission and all-run sensitivity reporting.

## Yaw360 / Hardstep recovery generation

The fixed-bias allocator produced repeated pitch/roll safety aborts in Yaw360
and Hardstep because motor clipping removed cross-axis authority. Do not repeat
those full armed commands unchanged. Follow
`STABILITY_PRIORITY_RECOVERY_2026-08-28.md`, starting with disarmed and partial
PD segments. The optional allocator must be applied identically to PD and
PD-CMG; the 55 degree abort remains unchanged.
