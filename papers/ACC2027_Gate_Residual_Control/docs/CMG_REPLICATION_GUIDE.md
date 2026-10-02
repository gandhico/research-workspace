# CMG ACC 2027 replication guide

This is the prescriptive execution record for independently reproducing the
current coupled membrane–gate (CMG) results. Run the stages in order and do not
reuse a partially completed output directory.

## 1. Know which claim each experiment can support

The canonical controller is

\[
u_k=\operatorname{sat}_{\ell}\left(u_{0,k}+\beta
\left[\operatorname{clip}(W_k a_k,-1,1)\odot\ell\right]\right),
\qquad a_k=\operatorname{clip}(10^5 r_k,0,1).
\]

The six CMG activities are continuous states, not output spikes. The fixed and
adaptive-conductance CMG conditions test an internal conductance term. The PES
conditions adapt the external `3 x 6` decoder `W` online. These are different
adaptation mechanisms.

The current evidence permits these claims:

- online PES reduces nominal Hard45 mean quaternion error by about 53% on the
  X2 rotor model and on the declared CF2 1.5x rotor-authority design;
- the compared runs have zero rotor saturation;
- fixed and adaptive CMG conductance are numerically indistinguishable in the
  present amplified-gate regime;
- the stock CF2 XML moment interface is saturated and cannot support the same
  aggressive-mission claim; and
- the QLabs QUBE transfer is bounded and stable but does not improve nominal
  LQR accuracy meaningfully.

Do not claim yet that CMG is inherently superior to LIF, ALIF, or Izhikevich.
The historical implementations used different output signals and a legacy
50/50 blend. No saved ALIF result artifact is currently present on the active
`C:` research drive.

## 2. Create and verify the clean environment

Open a new PowerShell window. Do not use the historical P3 environment for the
canonical runs.

```powershell
Set-Location C:\Research\papers\ACC2027_Gate_Residual_Control
.\scripts\setup.ps1
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
& $py --version
& $py -c "import mujoco,numpy; print('MuJoCo',mujoco.__version__); print('NumPy',numpy.__version__)"
& $py -m unittest discover -s tests -v
```

The setup script installs this repository in editable mode and runs a 0.25-s X2
smoke simulation. Every scientific run must contain:

- `trace.csv`: time history;
- `summary.json`: metrics and configuration values; and
- `manifest.json`: source/model provenance, package versions, and hashes.

Stop immediately if tests fail, a manifest is absent, the requested model path
is not the path shown in the manifest, or any output contains NaN/Inf.

## 3. Run all backend smoke tests

```powershell
Set-Location C:\Research\papers\ACC2027_Gate_Residual_Control
.\scripts\smoke_all.ps1
```

This exercises stock CF2, CF2 rotor design, X2, pendulum surrogate, 3DOF Hover
surrogate, and QCar surrogate. The last three are integration surrogates, not
identified digital twins.

## 4. Reproduce one X2 comparison manually

Run the baseline first, then the fixed decoder, then PES. Use explicit output
paths so the pair can be inspected without guessing which timestamp is newest.

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = "$root\.venv\Scripts\python.exe"
$out = "$root\results\runs\manual_x2_hard45"

& $py -m gra_control.cli simulate --platform x2 --controller classical `
  --mission hard45 --duration 45 --dt 0.0005 --beta 0.5 `
  --output "$out\classical"

& $py -m gra_control.cli simulate --platform x2 --controller fixed-residual `
  --mission hard45 --duration 45 --dt 0.0005 --beta 0.5 `
  --output "$out\fixed-residual"

& $py -m gra_control.cli simulate --platform x2 --controller online-pes-fixed `
  --mission hard45 --duration 45 --dt 0.0005 --beta 0.5 `
  --learning-rate 0.0008 --k-error 8 --k-rate 0 `
  --output "$out\online-pes-fixed"

& $py "$root\scripts\summarize_run_tree.py" $out
Import-Csv "$out\aggregate.csv" | Format-Table controller,qerr_mean_rad,saturation_fraction
```

Reference values for the same deterministic configuration are approximately:

| Controller | Mean quaternion error | Rotor saturation |
|---|---:|---:|
| classical | 0.294082 | 0.0000 |
| fixed residual | 0.263890 | 0.0000 |
| online PES, fixed conductance | 0.138007 | 0.0000 |

Investigate rather than silently accepting a difference larger than `5e-4` in
mean error. Compare the manifests, model hashes, time step, duration, beta,
learning rate, and torque policy.

## 5. Run the full X2 paper matrix

```powershell
Set-Location C:\Research\papers\ACC2027_Gate_Residual_Control
.\scripts\run_x2_paper_matrix.ps1 -Dt 0.0005 -Beta 0.5
```

This produces 20 runs: five controllers on Hard45, full3, roll, and hardstep.
Copy the final output path printed by the script, then aggregate it:

```powershell
$run = 'PASTE_THE_PRINTED_X2_MATRIX_PATH_HERE'
& .\.venv\Scripts\python.exe .\scripts\summarize_run_tree.py $run
```

Never select a result merely because it is favorable. The primary mission,
metric, beta, learning rate, and comparison set are fixed before inspection.

## 6. Establish the Crazyflie actuator boundary

First reproduce the stock XML boundary. It is expected to fail Hard45 through
near-continuous moment saturation; this is an important negative result.

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py = "$root\.venv\Scripts\python.exe"
& $py -m gra_control.cli simulate --platform cf2 --controller classical `
  --mission hard45 --duration 45 --dt 0.0005 --torque-policy model `
  --output "$root\results\runs\manual_cf2_stock\classical"
& $py -m gra_control.cli simulate --platform cf2 --controller fixed-residual `
  --mission hard45 --duration 45 --dt 0.0005 --beta 0.5 --torque-policy model `
  --output "$root\results\runs\manual_cf2_stock\fixed-residual"
```

Reference stock results are about `2.458662` mean error and `99.88%` saturation
for PD. Do not interpret the residual comparison as controller quality in this
regime.

Next run the declared four-rotor design study:

```powershell
.\scripts\run_cf2_authority_sweep.ps1 -Duration 5 -Dt 0.0005 -Beta 0.5
.\scripts\run_cf2_paper_matrix.ps1 -ActuatorScale 1.5 -Dt 0.0005 -Beta 0.5
```

The authority sweep is a 5-s screening study. The full matrix supplies the
45-s Hard45 result. At 1.5x authority the reference values are:

| Controller | Mean quaternion error | Rotor saturation |
|---|---:|---:|
| classical | 0.285449 | 0.0000 |
| fixed residual | 0.266050 | 0.0000 |
| online PES, fixed conductance | 0.132319 | 0.0000 |

Always write “CF2 four-rotor authority design at 1.5x assumed maximum thrust.”
Do not write “stock Crazyflie” or “validated motor upgrade.”

## 7. Run robustness before promoting the nominal result

```powershell
.\scripts\run_robustness_matrix.ps1 -Duration 45 -Dt 0.0005 -Beta 0.5
```

This produces 30 runs: three controllers, five seeds, and two rotor platforms.
It includes a 10-degree initial attitude, deterministic sinusoidal disturbance,
measurement noise, and platform-scaled disturbance torque. Aggregate the exact
printed directory. Report mean, standard deviation, worst seed, saturation,
and failures for every controller; do not report only average improvement.

## 8. Run the cross-platform integration checks

```powershell
.\scripts\run_cross_platform_surrogates.ps1 -Duration 10 -Beta 0.5
```

These runs verify API dimensions and logging only. They do not establish that
the MuJoCo pendulum, Hover, or QCar models are identified digital twins.

For the authoritative pendulum virtual twin, start QLabs and use its Quanser
Python 3.11 environment:

```powershell
Set-Location C:\Research\pendulum
.\scripts\run_acc2027_twin_matrix.ps1 `
  -BalanceDuration 20 -MaxDuration 90 -Trials 3 `
  -ResidualCapV 0.35 -Label paper_matched20
```

Verify that all 15 trials accumulate 20 s of actual balance and report zero
amplifier faults and stalls. The expected interpretation is equivalence to LQR,
not improved nominal accuracy. Do not reuse the invalid fixed-wall-time dataset.

## 9. Inspect a run before accepting it

For each candidate paper run:

1. Open `manifest.json` and record commit/source state, Python, MuJoCo, model path,
   and model SHA-256.
2. Open `summary.json` and check duration, time step, mission, controller, beta,
   learning rate, actuator scale/policy, mean and maximum error, and saturation.
3. Plot or inspect `trace.csv`; reject NaN/Inf, state discontinuities, unlogged
   restarts, or an incorrect reference.
4. Confirm that PD and CMG conditions use the same model, mission, initial state,
   controller gains, actuator limits, and seed.
5. Confirm that online PES updates `W` only after decoding the current sample.
6. Preserve all failed and negative runs. Never overwrite them with a rerun.
7. Record why a rerun was necessary in the lab notebook.

## 10. Build figures and the manuscript

`build_validation_report.py` reads the curated `results/validation` tree, not an
arbitrary newly printed matrix. Only replace curated validation artifacts after
the corresponding manifests have been audited.

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
& $py C:\Research\papers\ACC2027_Gate_Residual_Control\scripts\build_validation_report.py
Set-Location C:\Research\papers\ACC2027_Gate_Residual_Control
.\scripts\build_paper.ps1
```

The compiled draft is copied to
`output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf`.

## 11. Preregister the fair neuron-family validation

This study must use the canonical additive residual architecture. Do not use the
historical direct controller as the final comparison because it decoded
different signals and used a 50/50 blend.

For every model use the same:

- three residual outputs and six signed input channels;
- bounded pair currents and number of dynamical units;
- additive residual equation, beta, saturation, mixer, and actuator bounds;
- decoder dimensions, initial weights, PES update, projection, and leakage;
- calibration trajectory and feature-normalization procedure;
- hyperparameter-search budget and validation split; and
- missions, disturbances, seeds, metrics, and failure definitions.

Run two complementary comparisons:

### A. Representation-controlled comparison

Expose one normalized continuous feature per signed channel:

- CMG: `r`;
- LIF: normalized membrane voltage and, separately, low-pass spike trace;
- ALIF: normalized adaptation/threshold state and low-pass spike trace;
- Izhikevich: normalized recovery state and low-pass spike trace; and
- non-neural control: a bandwidth-matched first-order low-pass state.

Fit feature calibration on training trajectories only. Store calibration
constants and never recompute them on the held-out test mission.

### B. Capacity-controlled two-state comparison

Permit two features per signed channel for every two-state model and keep the
total decoder parameter count equal. Compare CMG `[v,r]`, ALIF membrane plus
adaptation state, and Izhikevich `[v,u]`. LIF must receive a matched auxiliary
filter state or be identified explicitly as the one-state baseline.

### Required CMG mechanism ablations

1. Decode `r` only, `v` only, and `[v,r]`.
2. Set `gamma=0` to remove gate-dependent threshold feedback.
3. Set gate-dependent conductance to zero.
4. Replace `r` with a low-pass state matched in variance, autocorrelation, and
   bandwidth.
5. Sweep gate gain and current bias so conclusions do not depend only on
   activity clipping.
6. Freeze learned weights, reset the plant, and test held-out frequencies,
   amplitudes, initial states, and disturbances.

Use “CMG exhibited an intrinsic representational advantage under matched
conditions” only if it remains superior after these controls. Until then use:

> Archived comparisons motivate the CMG mechanism, while the present paper
> attributes the large improvement to the combination of CMG state
> representation and online PES decoder adaptation.

## 12. Final reproducibility checklist

- [ ] Clean `.venv` created from this repository.
- [ ] Unit tests and six-platform smoke tests pass.
- [ ] X2 full matrix completed and aggregated.
- [ ] Stock CF2 saturation boundary reproduced.
- [ ] CF2 authority sweep and 1.5x full matrix completed.
- [ ] Five-seed robustness matrix completed.
- [ ] Candidate manifests and traces manually audited.
- [ ] QLabs protocol uses equal accumulated balance time.
- [ ] Negative results retained.
- [ ] Fair neuron-family study described as pending until implemented.
- [ ] Paper rebuilt from audited curated artifacts.

