# Online PES-Adapted Neuromorphic Membrane–Gate Residual Control

This is the clean execution repository. The historical source and raw results remain in
`C:\Research\papers\P3_Gate_Residual` and are not modified.

For a self-contained continuation checkpoint covering current evidence,
mathematics, code paths, honest claim boundaries, and the QDrone/3DOF Hover
roadmap, read `docs\AGENT_HANDOFF_2026-08-27.md` first.

Start with `docs\EXECUTION_AND_CODE_MAP.md` for the current result table,
controller/backend schematics, exact environments, and prescriptive launch
commands for MuJoCo, QLabs pendulum, QCar, and 3DOF Hover.

For independent reproduction in scientific order, including acceptance checks,
artifact auditing, and the preregistered LIF/ALIF/Izhikevich comparison, use
`docs\CMG_REPLICATION_GUIDE.md`.

The detailed LaTeX manuscript is
`paper\acc2027_neuromorphic_gate_residual_draft.tex`. Build it with
`scripts\build_paper.ps1`.

## Terminology

- **Coupled membrane–gate (CMG) unit** is the two-state continuous dynamical
  element with membrane state `v` and decoded gate state `r`. It is not claimed
  to be a new LIF neuron class.
- **CMG residual augmentation** is the target controller:
  `u = sat(u_baseline + beta * delta_u_gate)`.
- **Gate-state neural blending** is the legacy reproduction mode:
  `u = (1-beta)u_baseline + beta*u_neural`.
- **Online PES** means the decoder adapts during a run. It is distinct from
  adaptive CMG conductance.
- Historical files may retain `HyperLIF`, `GateStateAugmentor`, or `GRA` labels.
  In the clean API they are compatibility aliases; new work should use
  `CMGConfig`, `CoupledMembraneGateBank`, and `CMGResidualAugmentor`.

## Install

```powershell
cd C:\Research\papers\ACC2027_Gate_Residual_Control
.\scripts\setup.ps1
```

The project uses its own `.venv`. Every run writes `trace.csv`, `summary.json`, and
`manifest.json`, including the MuJoCo version and model SHA-256.

## MuJoCo examples

```powershell
$py = '.\.venv\Scripts\python.exe'

# Actuator-faithful X2 rotor path
& $py -m gra_control.cli simulate --platform x2 --controller classical --mission hard45 --duration 45
& $py -m gra_control.cli simulate --platform x2 --controller adaptive-residual --mission hard45 --duration 45
& $py -m gra_control.cli simulate --platform x2 --controller online-pes-fixed --mission hard45 --duration 45 --beta 0.5
& $py -m gra_control.cli simulate --platform x2 --controller online-pes-adaptive --mission hard45 --duration 45 --beta 0.5

# CF2 virtual-wrench actuator path, without the historical double-hover input
& $py -m gra_control.cli simulate --platform cf2 --controller classical --mission hard45 --duration 45 --torque-policy model
& $py -m gra_control.cli simulate --platform cf2 --controller adaptive-residual --mission hard45 --duration 45 --torque-policy model

# Reproduce the oversized legacy torque policy only as an explicitly labeled ablation
& $py -m gra_control.cli simulate --platform cf2 --controller online-pes --mission hard45 --duration 45 --torque-policy legacy-learned

# Cross-platform integration surrogates
& $py -m gra_control.cli simulate --platform pendulum --controller adaptive-residual --duration 10
& $py -m gra_control.cli simulate --platform hover3dof --controller adaptive-residual --duration 10
& $py -m gra_control.cli simulate --platform qcar --controller adaptive-residual --duration 20
```

Run all five short smoke tests:

```powershell
.\scripts\smoke_all.ps1
```

Run the matched X2 paper matrix and cross-platform integration matrix:

```powershell
.\scripts\run_x2_paper_matrix.ps1
.\scripts\run_cf2_paper_matrix.ps1
.\scripts\run_cf2_authority_sweep.ps1
.\scripts\run_robustness_matrix.ps1
.\scripts\run_cross_platform_surrogates.ps1
```

## QLabs QUBE pendulum virtual twin

The MuJoCo pendulum is only an integration surrogate. The authoritative QLabs
runner lives in `C:\Research\pendulum` and imports this repository's exact
`gra_control.gate` implementation:

```powershell
cd C:\Research\pendulum
.\scripts\run_acc2027_twin_matrix.ps1 -BalanceDuration 20 -MaxDuration 90 -Trials 3 -Label paper_matched20
```

See `docs\PENDULUM_QLABS_INTEGRATION.md`. The matched 2026-08-27 nominal result
shows stable bounded transfer and active online adaptation, but no meaningful RMS
advantage over LQR. Do not cite the archived fixed-wall-time 14% difference.

Reproduce the exact historical Skydio learned-blending implementation:

```powershell
.\scripts\reproduce_legacy_skydio.ps1
```

This legacy command is intentionally separated because it uses external wrench
injection and online adaptation on the evaluation trajectory. Its output includes a
limitations file and hashes. See `docs\RESULT_AUDIT.md` for the 50%+ result audit.

## Fidelity boundary

The X2 and CF2 use vendored MuJoCo Menagerie models. X2 commands four rotor actuators;
CF2 commands the model's collective-thrust and moment actuators. The pendulum, 3DOF
Hover, and QCar MuJoCo files are **integration surrogates**, not identified digital
twins. They verify the shared controller API and logging before platform parameters are
identified.

Existing QLabs/QUARC/PAL software remains the authoritative digital-twin or hardware
backend. Inspect without arming anything:

```powershell
& $py -m gra_control.cli hardware-status --platform pendulum
& $py -m gra_control.cli hardware-status --platform hover3dof
& $py -m gra_control.cli hardware-status --platform qcar
```

The unified launcher deliberately does not arm hardware. Physical execution requires a
reviewed adapter with voltage/steering bounds, watchdog, kill switch, channel map, and
on-device sign test.

`gra_control.hardware_bridges` provides disarmed-by-default bridges for Qube voltage,
QCar steering, and four 3DOF Hover motor-voltage residuals. These are inserted after the
existing classical controller and before the existing platform safety/post-processing
layer. They do not replace PAL, QLabs, QUARC, watchdogs, or emergency stop logic.

For QCar shadow-mode SNN work, `gra_control.perception.qcar_snn` supplies a
temporal-contrast ON/OFF event encoder and leaky spiking column population. Feed
the front-camera grayscale ROI to it alongside the current HSV estimator and log
both lane errors before allowing it to influence steering. It is an integration
baseline, not a trained convolutional SNN.
