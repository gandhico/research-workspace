# Decisive neuron-family and non-neural basis study

This experiment isolates the one question left open by the original neuron
benchmark: did LIF/ALIF/LIFRate fail because of an unsuitable operating point,
or because the final residual-learning problem intrinsically favors CMG?

The study does **not** modify or overwrite the frozen paper runs. It reuses the
final `rho=3` PD plus desired-rate-feedforward runner, MuJoCo plant/allocation,
PES teacher, decoder initialization, leak/projection, residual authority, and
saturation-aware output gate. Only the six-dimensional activity basis changes.

## Comparison levels

1. **Strict matched:** archived calibration and identical current encoder for
   CMG, LIF, ALIF, LIFRate, and Izhikevich. The confirmatory result uses the
   mathematically exact normalized PES rate. The older one-scale-factor rate
   is retained only as an explicitly labelled historical reproduction.
2. **Threshold-aware:** tune only the family operating point (current bias and
   gain, with their sum held at 2 so the archived maximum-response calibration
   remains valid). Screen at 15 s on X2 Roll and Hard45, confirm the selected
   setting at 45 s, then validate without retuning.
3. **No neuron:** replace neuron dynamics by either six constant-one features
   or the instantaneous normalized paired-current features. PES and the
   bounded residual interface remain unchanged.

The no-neuron arms are mechanism controls, not neuromorphic controllers.

## One-run example

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\neuron_basis_decisive_2026-09-24'
& $py "$root\run_neuron_basis.py" --platform x2 --controller lif `
  --mission hard45 --duration 45 --beta 0.5 --learning-rate 0.0008 `
  --k-error 8 --k-rate 0 --output-gate torque-saturation-opposition `
  --output "$root\results\strict\x2\hard45\lif"
```

For CF2 use `--platform cf2-rotor --actuator-scale 1.5 --beta 0.2`.

Every residual run saves a decimated `trace.csv`, full-rate compressed neural
telemetry, a signal schema, a numerical summary, and a provenance manifest.

## Completed result

The audited study contains 186 runs and 174 full-rate neural archives. The
strict equal-interface comparison gives CMG geometric-mean error reductions of
37.30% (X2) and 22.42% (CF2), versus 11.88%/4.75% for the stronger non-neural
static paired basis. Threshold-aware LIFRate is the strongest conventional
alternative: 15.77% on held-out X2 missions and 11.37% on held-out CF2.

Read, in order:

1. `TECHNICAL_METHOD.md`
2. `analysis/strict/STRICT_RESULTS.md`
3. `analysis/final/FINAL_NEURON_BASIS_REPORT.md`
4. `PAPER_REVISION_NOTE.md`
5. `analysis/AUDIT_RESULTS.json`

## PES normalization correction

For a conventional feature with native filtered output `p=S*a`, Nengo stores
the connection as `Theta=W/S`. Since `SimPES` applies
`Delta Theta = eta_N*dt/N*(target-y)*p^T`, equal normalized learning
`Delta W=eta*(target-y)*a^T` requires
`eta_N=eta*N/(dt*S^2)`. The archived family adapter used `S` rather than
`S^2`, so its effective normalized step was `S*eta`. The new default is
`--family-learning-normalization exact`; `archived` exists only to reproduce
the earlier result transparently.
