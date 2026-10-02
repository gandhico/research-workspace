# ACC 2027 research handoff — 2026-08-27

## Update 2026-08-27/28, later same session: read `docs\SESSION_INDEX_2026-08-27.md` first

Everything the "immediate plan" below describes as future work happened
this same session: the full MuJoCo mission suite (not just Hard45), the
3DOF Hover physical hardware validation, and the paper section/PDF rebuild
covering both. `docs\SESSION_INDEX_2026-08-27.md` is the up-to-date entry
point — every path, runner, and reproduction command — with
`docs\RESULTS_EXPLAINED.md` for the full mathematical/conceptual writeup.
The plan below is kept for history; treat it as superseded.

## Read this first

This file is the self-contained checkpoint for continuing the research without
the preceding chat. The immediate plan is:

1. finish and audit the MuJoCo drone results and manuscript;
2. extend the canonical controller to the Quanser QDrone/QDrone2 virtual twin;
3. later return to the lab for a carefully staged 3DOF Hover experiment.

The primary repository is:

```text
C:\Research\papers\ACC2027_Gate_Residual_Control
```

Historical source and raw artifacts remain under
`C:\Research\papers\P3_Gate_Residual`; do not modify or silently merge them.
The QDrone branch is `C:\Research\qdrone`. The authoritative pendulum QLabs
runner is under `C:\Research\pendulum`.

## Canonical paper identity

Title:

> Online PES-Adapted Neuromorphic Membrane–Gate Residual Control for
> Actuator-Constrained UAV Quaternion Attitude Tracking

Paper-facing terminology:

- **coupled membrane–gate (CMG) dynamical unit**, not HyperLIF;
- **CMG residual augmentation** for the baseline-preserving additive law;
- **online PES** for decoder adaptation at every sample;
- **adaptive conductance** for the separate current-dependent CMG term; and
- **gate-state neural blending** only for the historical convex-blend ablation.

The manuscript source is
`paper\acc2027_neuromorphic_gate_residual_draft.tex`; the current compiled
nine-page draft is
`output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf`.

## Verified software state

Verified on 2026-08-27 after the title update:

- five unit tests pass;
- six short MuJoCo backends complete: stock CF2, CF2 rotor design, X2,
  pendulum surrogate, 3DOF Hover surrogate, and QCar surrogate;
- the paper builds successfully in two LaTeX passes; and
- the title page was rendered and visually inspected with no clipping or
  collision.

Recheck with:

```powershell
Set-Location C:\Research\papers\ACC2027_Gate_Residual_Control
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\scripts\smoke_all.ps1
.\scripts\build_paper.ps1
```

The build script compiles under a timestamped temporary job name, so an open
source PDF does not prevent LaTeX from running. It writes the canonical output
PDF when that destination is available and otherwise uses a timestamped output.

## Current validated results

| Evidence | Platform and condition | Classical | Fixed CMG | Online CMG–PES | Saturation | Correct interpretation |
|---|---|---:|---:|---:|---:|---|
| Paper candidate | Skydio X2, MuJoCo four-rotor interface, Hard45, 45 s | 0.294082 | 0.263890 (10.27%) | 0.138007 (53.07%) | 0% | Strong nominal additive-residual result; PES adapts on the evaluated trajectory. |
| Design study | CF2 explicit four-rotor model, 1.5× assumed rotor authority, Hard45, 45 s | 0.285449 | 0.266050 (6.80%) | 0.132319 (53.65%) | 0% | Controller/actuator co-design simulation, not stock CF2 validation. |
| Authority boundary | Stock Menagerie CF2 virtual-moment XML, Hard45 | 2.458662 | 2.516808 | not defensible | 99.88–99.89% | Actuator authority is infeasible for this mission; it cannot rank controllers fairly. |
| Transfer result | QUBE Servo 3 QLabs, three matched 20-s balance trials | 1.0581° RMS | 1.0590° RMS | 1.0566–1.0570° RMS | n/a | Stable bounded transfer, zero faults/stalls, but nominal performance is equivalent to LQR. |
| Historical only | Skydio external-wrench neural blend | 0.294079 | 0.275307 | 0.122051 (58.50%) | not rotor-faithful | Confirms the remembered 50%+ result, but uses online blending and external wrench injection. |

For the drone table, “fixed CMG” means fixed decoder. Fixed and adaptive
conductance are numerically identical at the displayed precision. The large
improvement comes from online decoder adaptation under the present parameters,
not from adaptive conductance.

Authoritative values and figures:

```text
results\reports\validation_summary.md
results\reports\validation_summary.csv
results\reports\x2_hard45_qerr.png
results\reports\cf2_authority_sweep.png
results\reports\pendulum_qlabs_matched20.md
paper\tables\hard45_results.tex
docs\RESULT_AUDIT.md
```

## Controller mathematics and exact code behavior

For `m` residual channels, the bounded classical command is normalized and
positive/negative pair encoded:

```math
u_{0,k}=\operatorname{sat}_{\ell}(u^{\mathrm{raw}}_{0,k}),
\qquad \bar u_k=u_{0,k}\oslash\ell,
```

```math
I_k^+=I_b\mathbf 1+I_g\max(\bar u_k,0),\qquad
I_k^-=I_b\mathbf 1+I_g\max(-\bar u_k,0).
```

Thus there are `2m` CMG units. For each unit:

```math
\dot r_j=\frac{\sigma\!\left(\alpha_h[v_j-(v_{th}-\gamma r_j)]\right)-r_j}{\tau_r},
```

```math
\dot v_j=-\frac{v_j-v_{rest}}{\tau}+\frac{I_j}{\tau}
-c_j(v_j-v_{reset}),
\qquad
c_j=(g_0+\mathbf 1_{adapt}g_1|I_j|)r_j^2.
```

Both `v` and `r` participate in the dynamics. The current decoder feature is
the amplified continuous gate state

```math
a_k=\operatorname{clip}_{[0,1]}(G r_{k+1}),\qquad G=10^5,
```

not a spike train and not currently `[v,r]`. The initial decoder and additive
control law are

```math
W_0=[I_m\;-I_m],\qquad
s_k=\operatorname{clip}_{[-1,1]}(W_k a_k),
```

```math
u_k=\operatorname{sat}_{\ell}
\left(u_{0,k}+\beta(s_k\odot\ell)\right).
```

For the drones, the PES target and projected update are

```math
y_k^*=\operatorname{clip}_{[-1,1]}(-k_e e_{q,k}-k_\omega^*\omega_k),
\qquad \varepsilon_k=y_k^*-s_k,
```

```math
W_{k+1}=\Pi_{[-6,6]}\left(
W_k+\eta\varepsilon_k a_k^T-\lambda_W W_k\right).
```

Hard45 uses `eta=8e-4`, `k_error=8`, `k_rate=0`, `beta=0.5`, and
`dt=5e-4 s`. The code decodes with `W_k` first and then updates `W_{k+1}`;
the new weights affect the next sample. This causal order is important.

Canonical implementation:

```text
src\gra_control\gate.py
```

Important implementation detail: because `G=1e5` and the mean gate state is
approximately 0.963 in the online run, activity is usually clipped near one.
This suppresses the visible difference between fixed and adaptive conductance.
The correct current claim is “PES decoder adaptation matters in the amplified-
gate regime,” not “adaptive CMG conductance caused the 53% improvement.”

## Drone control and MuJoCo connection

The drone loop is implemented in `src\gra_control\platforms\drone.py` and
launched by `src\gra_control\cli.py`.

For X2 and the CF2 rotor design:

1. MuJoCo supplies rigid-body position, quaternion, linear velocity, and angular
   velocity, and integrates contact-free rigid-body dynamics.
2. The code computes shortest-path quaternion error and a diagonal quaternion
   PD body-torque command.
3. CMG–PES supplies three bounded torque residual channels: roll, pitch, yaw.
4. A `4×4` collective/body-moment mixer maps collective thrust and body moments
   to four nonnegative rotor commands.
5. Rotor commands are clipped to the actuator ranges declared in the XML and
   passed to `data.ctrl`; MuJoCo advances one integration sample.
6. `trace.csv`, `summary.json`, and `manifest.json` record the state, controller,
   saturation, versions, configuration, model path, and model SHA-256.

The stock CF2 Menagerie model instead exposes one collective-thrust and three
abstract moment actuators. Its XML moment limit is `1e-5 N m` per axis. The
historical learned runner's torque floor `[0.03,0.03,0.02] N m` is 3000, 3000,
and 2000 times that XML authority, and 104.38, 104.38, and 61.83 times the
project inertia-derived bound. These two comparisons must not be conflated;
the XML README says its moment limits are arbitrary and they are not measured
physical CF2 motor limits.

## Exact MuJoCo reproduction order

```powershell
$acc = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = Join-Path $acc '.venv\Scripts\python.exe'
Set-Location $acc

# Preflight
& $py -m unittest discover -s tests -v
.\scripts\smoke_all.ps1

# Highest-priority unfinished evidence
.\scripts\run_robustness_matrix.ps1 -Duration 45 -Dt 0.0005 -Beta 0.5

# Full paper matrices
.\scripts\run_x2_paper_matrix.ps1 -Dt 0.0005 -Beta 0.5
.\scripts\run_cf2_authority_sweep.ps1 -Duration 5 -Dt 0.0005 -Beta 0.5
.\scripts\run_cf2_paper_matrix.ps1 -ActuatorScale 1.5 -Dt 0.0005 -Beta 0.5

# Aggregate the exact output directory printed by a matrix
& $py .\scripts\summarize_run_tree.py <absolute-result-directory>

# Rebuild curated reports and manuscript only after audit
& $py .\scripts\build_validation_report.py
.\scripts\build_paper.ps1
```

The robustness matrix has five seeds, two platforms, and three controllers,
with initial attitude, disturbance torque, and measurement noise. Report mean,
standard deviation, worst seed, saturation, and failures. Do not select only
the favorable seeds.

## Claims allowed and claims prohibited

Allowed now:

- approximately 53% nominal Hard45 mean quaternion-error reduction on the
  X2 four-rotor model and declared CF2 1.5× rotor-authority design;
- zero modeled rotor saturation in those matched nominal comparisons;
- fixed/adaptive CMG conductance is a null ablation in the current
  amplified-gate regime;
- stock CF2 XML authority cannot execute Hard45; and
- QLabs QUBE transfer is bounded and safe but nominally equivalent to LQR.

Not allowed yet:

- zero-shot, frozen-weight, or cross-mission generalization;
- inherent superiority of CMG over LIF, ALIF, or Izhikevich;
- stock Crazyflie hardware feasibility at 1.5× thrust;
- a calibrated QDrone, QCar, Hover, or pendulum MuJoCo digital twin;
- QDrone or 3DOF Hover hardware validation; or
- neuromorphic hardware energy-efficiency claims.

The fair neuron-family study is preregistered in
`docs\CMG_REPLICATION_GUIDE.md`. It must compare matched dimensions, continuous
features, decoder capacity, PES, actuator path, tuning budget, seeds, and held-
out missions. Required CMG feature ablations include `r`, `v`, and `[v,r]`.

## QDrone/QDrone2 virtual-twin extension

Current QDrone repository:

```text
C:\Research\qdrone
```

Current maturity, verified from `C:\Research\qdrone\RUNNERS.md`:

- the offline hover abstraction runs;
- a telemetry checker exists but is read-only and does not arm hardware;
- no QLabs/QDrone digital-twin runner exists yet;
- the previous-machine vendor paths under `C:\Quanser\...\qdrone2` are absent
  on this rebuilt laptop; and
- the needed Quanser `pal` and `qvl` packages must be recovered or installed
  and their actual new locations verified.

The offline abstraction uses

```text
x = [phi, phi_dot, theta, theta_dot, psi, psi_dot, z, z_dot]
u = [roll_cmd, pitch_cmd, yaw_cmd, thrust_delta]
```

This proposes four residual channels and eight CMG units. The current ACC drone
implementation uses three attitude-torque channels and six units; therefore a
QDrone integration must explicitly decide whether the virtual API accepts
attitude/thrust commands, body torques, rotor commands, or position setpoints.
Do not guess the channel semantics from the offline abstraction.

Prescribed QDrone integration sequence:

1. Recover/install the Quanser Academic Resources containing `pal` and `qvl`.
2. Locate and run the vendor QDrone2 **virtual position-control** example
   unchanged; record interpreter, package versions, QLabs scene, ports, command
   units, state ordering, rates, and shutdown behavior.
3. Create a read-only/logger wrapper first. Verify quaternion/Euler convention,
   frame signs, timestamps, stale-packet handling, and virtual emergency stop.
4. Import the canonical `gra_control.gate` implementation from the ACC
   environment or install the ACC package into the Quanser-compatible
   interpreter. Do not copy a second divergent CMG implementation.
5. Run **shadow mode**: calculate fixed CMG and online PES residuals, but apply
   the unmodified Quanser baseline command. Log baseline, proposed residual,
   proposed final command, CMG `v/r/activity`, decoder weights, state error, and
   all platform limits.
6. Replay shadow logs offline and confirm boundedness, correct signs, absence of
   NaN/Inf, and sensible PES weight evolution.
7. Enable virtual residuals incrementally: roll/pitch first with a small beta;
   then yaw; keep thrust/altitude residual disabled until attitude is stable.
8. Compare classical, fixed decoder, online-PES fixed conductance, and
   online-PES adaptive conductance using identical initial state, reference,
   mission duration, bounds, and reset protocol.
9. Freeze the learned decoder, reset the virtual plant, and run held-out
   waypoint frequencies, amplitudes, initial attitudes, and disturbances.
10. Only after these virtual results are audited should a separate physical
    QDrone plan be considered.

Suggested new files belong in the QDrone repository, not inside the MuJoCo
platform module, for example:

```text
C:\Research\qdrone\runners\twin_acc2027_cmg_residual.py
C:\Research\qdrone\scripts\run_acc2027_twin_matrix.ps1
C:\Research\qdrone\tools\summarize_acc2027_twin.py
C:\Research\qdrone\docs\ACC2027_QDRONE_TWIN_PROTOCOL.md
```

The runner should import the canonical ACC controller and record its source
SHA-256, following the successful pendulum QLabs pattern.

## Later 3DOF Hover laboratory phase

**Update 2026-08-27, same day, later session: this phase happened.** The
physical rig was connected, a reviewed Python/HIL adapter was built and
run, and real baseline-vs-CMG-PES comparison data was collected. Full
narrative, verified channel map, four real bugs found and fixed via actual
hardware runs, and the results table/analysis:
`C:\Research\hover3dof\docs\PROGRESS_2026-08-27.md`. Read that before
touching this platform again — the state described just below (no adapter,
no sign-checked channel map) is now stale.

Original pre-lab state (superseded, kept for history):

- `models\hover3dof_surrogate.xml` is only a MuJoCo integration surrogate;
- vendor MATLAB/Simulink/QUARC assets are under
  `C:\Research\hover3dof\3DOF_Hover`;
- `hover3dof_bridge()` computes bounded four-channel voltage residuals but
  returns zero unless armed; and
- no reviewed Python/QLabs/QUARC adapter connects CMG to the physical Hover.

Before any physical command, document and independently sign-check:

- four motor channel order and polarity;
- hover bias voltage for every motor;
- allowed voltage range and residual headroom;
- encoder/IMU ordering, units, frame convention, and sample rate;
- watchdog, stale-data behavior, kill switch, and emergency stop;
- baseline-only stable hover; and
- a zero-output/sensor-only logging run.

Then use the same staged sequence: shadow residual, recorded-log replay,
low-beta attitude-only residual, one axis at a time, and only then a matched
multi-axis experiment. Never let CMG bypass the existing vendor safety layer.

## Manuscript work still open

1. Run and audit the five-seed robustness matrix.
2. Run frozen-weight/reset hold-out experiments before any generalization claim.
3. Decide whether the QDrone virtual-twin evidence will fit the ACC paper or be
   supplementary/future work.
4. Implement the fair CMG/LIF/ALIF/Izhikevich study only if time permits; do not
   promote archived unmatched comparisons.
5. Fix the duplicated wording near the start of the abstract before submission.
6. Move from the current generic `article` draft to the official ACC 2027
   template and verify the official page/format rules when released.
7. Reduce the present nine-page working draft to the permitted submission
   length only after preserving the full technical version.

## Repository and provenance warning

At this checkpoint the Git repository had no prior commit and the project files
were all untracked. Generated scientific run directories are excluded by
`.gitignore`; stable reports, source, models, documentation, and the curated
paper PDF should be checkpointed. Never delete negative results or overwrite a
candidate run. Every accepted run must retain `trace.csv`, `summary.json`, and
`manifest.json`.

## Recommended next-agent order

1. Read this file, `docs\RESULT_AUDIT.md`, and
   `docs\CMG_REPLICATION_GUIDE.md`.
2. Verify tests and smoke simulations.
3. Start the robustness matrix and aggregate it.
4. Audit manifests and traces; update reports only after acceptance.
5. Finish the MuJoCo-drone manuscript edits.
6. Discover/recover the QDrone Quanser environment and run the vendor virtual
   example unchanged.
7. Build QDrone shadow mode around the canonical CMG source.
8. Leave 3DOF Hover physical actuation for the lab session and safety checklist.

