# Matched Nengo neuron-family benchmark

**Purpose:** determine whether the additive bounded residual plus online PES
benefits conventional neuron families, and whether CMG retains an advantage
under matched control and decoder assumptions.

## Controlled architecture

Every condition keeps fixed:

- the MuJoCo plant, quaternion-PD baseline, altitude loop, mission reference,
  actuator mixer/ranges, torque policy, initial condition, and time step;
- three residual outputs and six signed directional units;
- canonical external currents in `[0.75,2.0]`, `W0=[I,-I]`, `beta=0.5`,
  `eta=8e-4`, `k_error=8`, `k_rate=0`, decoder leak `1e-6`, projection, and
  final additive torque saturation;
- one natural scalar feature per directional unit and therefore the same
  `3 x 6` decoder capacity; and
- five nontrivial missions: Roll, Full3, Hard45, Hardstep, and Yaw360, for both
  Skydio X2 and the explicitly labeled 1.5x-authority CF2 rotor design.

Every neuron is tested twice: fixed `W0` and online Nengo built-in PES.
Quaternion PD is rerun as the matched zero-residual baseline.

## Honest family-specific adaptation

| Family | Natural decoder feature | Native Nengo states archived | Calibration/adaptation |
|---|---|---|---|
| CMG | Continuous gate-derived activity | membrane `v`, gate `r` plus every CMG equation term in the canonical controller | No rate scaling; feature already bounded `[0,1]`. |
| LIF | 5 ms low-pass spike trace | voltage and refractory time | Normalize by steady maximum-current training response. |
| ALIF | 5 ms low-pass spike trace | voltage, refractory time, adaptation | Same calibration method. Adaptation is diagnostic, not a second decoder channel in this representation-controlled comparison. |
| Izhikevich | 5 ms low-pass spike trace | voltage and recovery | Canonical current is multiplied by 10 only at the native neuron port because Nengo Izhikevich does not spike over canonical `J=[0.75,2]`; this mapping and both currents are logged. |
| LIFRate | 5 ms low-pass continuous rate | rate output; no dynamic state exposed by Nengo | Included to separate LIF rate dynamics from discrete spike timing. |

The 5 ms filter matches the CMG gate time constant. Calibration is performed
once at canonical `J=2` for two seconds; the mean over the second half is frozen
before mission tests. Frozen scales are in `feature_calibration.json`.

For conventional families, Nengo PES must connect directly to `Neurons`; it
cannot learn from an intermediate normalization Node. Therefore the calibrated
scale is folded analytically into the initial transform and learning rate:

\[
W_{\rm native}(0)=W_0/s_f,\qquad
\eta_{\rm Nengo}=\frac{6\eta}{\Delta t\,s_f},\qquad
W_{\rm normalized}=s_f W_{\rm native}.
\]

This gives the intended normalized update

\[
\Delta W_{\rm normalized}
=\eta\,(y^\star-y)a_{\rm normalized}^{\mathsf T}
\]

while retaining Nengo's built-in PES operator and the natural spike/rate
observable. Raw and normalized weights are not silently interchanged.

## Frozen feature calibration

| Family | Feature scale | Native current scale | Training observable |
|---|---:|---:|---|
| CMG | 1.0000 | 1 | gate activity |
| LIF | 63.0239 Hz | 1 | filtered spikes |
| ALIF | 46.9180 Hz | 1 | filtered spikes |
| Izhikevich | 42.6021 Hz | 10 | filtered spikes at native `J=20` |
| LIFRate | 63.0400 Hz | 1 | filtered rate |

## Preliminary 5 s Hard45 pilot on X2

This pilot validated signal flow; it is not the final 45 s claim table.

| Controller | Mean q-error [rad] | Change from PD | Mean residual [Nm] |
|---|---:|---:|---:|
| PD | 0.292620 | 0.00% | 0.000000 |
| CMG fixed | 0.267001 | +8.75% | 0.036110 |
| CMG PES | 0.172293 | +41.12% | 0.126239 |
| LIF fixed | 0.291630 | +0.34% | 0.000943 |
| LIF PES | 0.291375 | +0.43% | 0.001241 |
| ALIF fixed | 0.291501 | +0.38% | 0.001073 |
| ALIF PES | 0.291232 | +0.47% | 0.001426 |
| Izhikevich fixed | 0.279183 | +4.59% | 0.209087 |
| Izhikevich PES | 0.163457 | +44.14% | 0.284186 |
| LIFRate fixed | 0.291573 | +0.36% | 0.000983 |
| LIFRate PES | 0.291208 | +0.48% | 0.001267 |

The pilot shows that another neuron can benefit strongly: Izhikevich-PES
slightly exceeded CMG-PES over five seconds. It also used 2.25 times CMG's mean
residual torque. The full mission must determine whether that gain persists,
saturates, destabilizes, or reflects a control-effort trade. We will not claim
CMG is intrinsically superior if the matched full results do not support it.

## Final matched 45 s result

All **110/110** planned cells completed: two platform designs, five missions,
one matched quaternion-PD baseline per mission, and ten family/decoder cases.
The tables below report percentage reduction of mean quaternion-angle error
relative to the mission- and platform-matched PD baseline.

### Online PES improvement by mission

| Platform | Mission | CMG | LIF | ALIF | Izhikevich | LIFRate |
|---|---|---:|---:|---:|---:|---:|
| X2 | Roll | 17.36% | 0.00% | 0.00% | 51.13% | 0.00% |
| X2 | Full3 | 56.56% | 0.02% | 0.02% | 52.25% | 0.04% |
| X2 | Hard45 | 53.07% | 0.05% | 0.05% | 49.69% | 0.05% |
| X2 | Hardstep | 20.94% | 8.51% | 7.35% | 22.65% | 18.46% |
| X2 | Yaw360 | 60.58% | 0.00% | 0.00% | 60.68% | 0.00% |
| CF2 1.5x rotor design | Roll | 17.33% | 0.00% | 0.00% | 51.46% | 0.00% |
| CF2 1.5x rotor design | Full3 | 56.14% | 0.04% | 0.04% | 51.90% | 0.06% |
| CF2 1.5x rotor design | Hard45 | 53.65% | 0.05% | 0.06% | 50.27% | 0.09% |
| CF2 1.5x rotor design | Hardstep | 18.37% | 7.39% | 7.08% | 21.35% | 8.38% |
| CF2 1.5x rotor design | Yaw360 | 60.60% | 0.00% | 0.00% | 56.40% | 0.00% |

### Five-mission average and authority cost

`Residual utilization` is the RMS of residual torque divided axiswise by each
platform's declared torque limits; it is dimensionless and comparable across
the X2 and CF2 design.

| Platform | Family | Fixed improvement | PES improvement | PES residual utilization |
|---|---|---:|---:|---:|
| X2 | CMG | 4.50% | 41.70% | 0.12 |
| X2 | LIF | 0.65% | 1.72% | 0.04 |
| X2 | ALIF | 0.63% | 1.49% | 0.04 |
| X2 | Izhikevich | 3.00% | 47.28% | 0.37 |
| X2 | LIFRate | 0.86% | 3.71% | 0.05 |
| CF2 1.5x rotor design | CMG | 3.02% | 41.22% | 0.12 |
| CF2 1.5x rotor design | LIF | 0.43% | 1.50% | 0.03 |
| CF2 1.5x rotor design | ALIF | 0.45% | 1.44% | 0.03 |
| CF2 1.5x rotor design | Izhikevich | 2.19% | 46.28% | 0.37 |
| CF2 1.5x rotor design | LIFRate | 0.68% | 1.71% | 0.03 |

The result is stronger and more honest than the original hypothesis:

- CMG-PES is positive in all ten platform/mission cells, with a 17.33--60.60%
  range and nearly identical five-mission averages on the two designs.
- Izhikevich-PES also learns strongly and has the larger mean reduction. It
  uses about three times CMG's normalized residual RMS (`0.37` versus `0.12`),
  roughly an order of magnitude more decoder movement, and somewhat more
  actuator saturation. It is therefore not a free superiority result.
- LIF, ALIF, and LIFRate are effectively silent in four missions under the
  fixed canonical-current mapping. They activate on Hardstep and then PES helps,
  which shows that the residual/PES architecture can work with them when their
  natural feature is excited.
- The defensible CMG claim is **consistent, authority-efficient online residual
  learning with a continuously available non-spiking state**, not exclusive
  learnability or universal tracking dominance.

The complete 100 non-baseline records, including absolute and normalized
effort, saturation, altitude variation, activity, decoder drift/update RMS,
spike counts/rates, PES error, and clipping incidence, are in
`results/neuron_family_compiled/neuron_family_results.csv` and JSON.

## Archive and figure coverage

Every non-baseline cell retains the 2-kHz natural observable, canonical and
native currents, raw spikes/rates, exposed native states, decoded raw/clipped
outputs, PES error/target, all 18 decoder weights and per-step changes, and
bounded residual torque. Standardized diagnostic PNG/PDF files are written in
each run's `analysis` folder. The compiled directory contains:

- family-by-mission improvement heatmaps;
- online-PES comparison bars;
- performance/effort/activation/decoder-movement dashboards;
- accuracy-versus-normalized-authority plots; and
- the matched architecture schematic.

## Reproduction

```powershell
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29'

& $py "$root\calibrate_neuron_features.py"
& $py "$root\run_neuron_family_campaign.py" `
  --output-root "$root\results\neuron_family_matched_45s" `
  --duration 45 --log-every 10
& $py "$root\compile_neuron_family_benchmark.py"
```

Each Nengo run contains `trace.csv`, `summary.json`, `manifest.json`, a
full-rate neural NPZ, and schema. `plot_neuron_family_archive.py` produces a
spike raster or native output, filtered feature, native states, decoder/PES,
all weight/update norms, and residual torque for any selected run.

## Claim gate

The paper may say the architecture generalizes beyond CMG because Izhikevich
and the Hardstep LIF/ALIF/LIFRate cases improve with PES. It may say CMG gives
the most consistent low-authority continuous-state solution in this matched
matrix. A claim of intrinsic neuron superiority still requires repeated seeds
or disturbances, held-out frozen-decoder evaluation, and the CMG readout/state
ablations listed above. This matrix establishes feasibility, effort-aware
comparison, and mechanism evidence—not universal neuron superiority.
