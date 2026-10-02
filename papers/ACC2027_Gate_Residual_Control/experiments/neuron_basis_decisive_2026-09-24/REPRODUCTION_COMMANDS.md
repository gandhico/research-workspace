# Reproduction commands

## Complete audited study

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\neuron_basis_decisive_2026-09-24\reproduce_all.ps1'
```

The launcher uses the project environment at
`C:\Research\papers\ACC2027_Gate_Residual_Control\.venv` and ten workers.
Completed cases are cached by `summary.json`; it does not erase prior runs.

## One strict case

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$study = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\neuron_basis_decisive_2026-09-24'

& $py "$study\run_neuron_basis.py" `
  --platform x2 `
  --controller lifrate `
  --mission hard45 `
  --duration 45 `
  --beta 0.5 `
  --learning-rate 0.0008 `
  --k-error 8 `
  --k-rate 0 `
  --output-gate torque-saturation-opposition `
  --output "$study\results\manual\x2\hard45\lifrate"
```

Valid controllers are `classical`, `cmg`, `lif`, `alif`, `lifrate`,
`izhikevich`, `constant-one`, and `paired-current`.

For CF2, replace the platform/authority arguments with

```powershell
--platform cf2-rotor --actuator-scale 1.5 --beta 0.2
```

## One threshold-aware case

The frozen LIFRate setting is `(bias,gain,tau_f)=(1.03,0.97,0.005 s)`:

```powershell
& $py "$study\run_neuron_basis.py" `
  --platform x2 `
  --controller lifrate `
  --mission yaw360 `
  --duration 45 `
  --beta 0.5 `
  --learning-rate 0.0008 `
  --k-error 8 `
  --k-rate 0 `
  --output-gate torque-saturation-opposition `
  --family-current-bias 1.03 `
  --family-current-gain 0.97 `
  --family-feature-tau 0.005 `
  --output "$study\results\manual\x2\yaw360\lifrate_tuned"
```

The other frozen settings are stored in
`analysis\development\selected_settings.json`.

## Archived-scaling reproduction only

`--family-learning-normalization archived` intentionally reproduces the old
one-scale-factor implementation. It must not be mixed with the confirmatory
equal-rate matrix. The default `exact` option is the paper-valid comparison.
