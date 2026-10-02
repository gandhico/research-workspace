# Nengo neuron-family and 3DOF Hover validation — frozen 2026-09-01

## Executive status

Three distinct evidence layers are complete and must not be conflated:

1. **MuJoCo drone benchmark:** 110/110 matched cells already passed for Skydio X2 and the declared 1.5x-authority Crazyflie rotor design. Each platform used five missions, classical quaternion PD, CMG fixed/PES, and fixed/PES LIF, ALIF, Izhikevich, and LIFRate variants.
2. **Emulated Quanser 3DOF Hover benchmark:** 110/110 cells were executed for nominal and hard-pulse conditions. Ninety-nine completed. All eleven hard-pulse Yaw360 cases reached the same declared ±180° simulation-divergence boundary; those comparisons are masked rather than truncated into misleading percentages.
3. **Connected Q8 integration shadow:** all eleven controllers completed a three-second live encoder/Nengo pass. `armed=False` was hard-coded and every written motor/DAC field was exactly zero at every sample.

Only the previously qualified `pd` and `nengo-pes` controllers are permitted to drive the physical Hover. The added neuron-family paths are rejected when armed.

## Common residual architecture

The baseline is quaternion PD. With desired and measured quaternions
\(q_d,q\), quaternion error \(q_e=q_d\otimes q^{-1}\), vector part
\(\mathbf e_q\), and body rate \(\boldsymbol\omega\),

\[
\boldsymbol\tau_0 = K_q\mathbf e_q-K_\omega\boldsymbol\omega,
\qquad
\boldsymbol\tau_0\in[-\boldsymbol\tau_{\max},\boldsymbol\tau_{\max}].
\]

Each axis is represented by a positive/negative neuron pair. The normalized
baseline torque is \(\bar{\tau}_{0,j}=\tau_{0,j}/\tau_{\max,j}\), and the six
canonical currents are

\[
J_{j,+}=J_b+J_g\max(\bar{\tau}_{0,j},0),\qquad
J_{j,-}=J_b+J_g\max(-\bar{\tau}_{0,j},0).
\]

The natural observable \(\mathbf a\in[0,1]^6\) depends on neuron family:

- CMG: continuous gate-derived activity;
- LIF, ALIF, Izhikevich: calibrated 5 ms low-pass spike trace;
- LIFRate: calibrated 5 ms low-pass rate output.

All families use the same initial signed decoder

\[
W_0=[I_3\;-I_3]\in\mathbb R^{3\times6},
\qquad
\hat{\boldsymbol\tau}_r=\operatorname{clip}(W\mathbf a,-1,1).
\]

Fixed variants hold \(W=W_0\). PES variants update the decoder online using
the normalized teaching target \(\mathbf y^*\):

\[
\mathbf e_{\mathrm{PES}}=\hat{\boldsymbol\tau}_r-\mathbf y^*,
\qquad
\dot W=-\eta\,\mathbf e_{\mathrm{PES}}\mathbf a^\top-\lambda W.
\]

The requested residual torque and total command are

\[
\Delta\boldsymbol\tau=\beta\,oldsymbol\tau_{\max}\odot
\hat{\boldsymbol\tau}_r,
\qquad
\boldsymbol\tau_c=\boldsymbol\tau_0+\Delta\boldsymbol\tau.
\]

For Hover, the residual is mapped into front/back/left/right motor voltage,
then limited to 0.2 V per motor and slewed at 1 V/s. All compared families use
the same \(\beta=0.2\), \(\eta=2\times10^{-4}\), \(k_e=2\), and \(k_\omega=0\).

## Hover simulation matrix

Each cell is 25 s, with a 200 Hz plant/controller loop and a genuine 2 kHz
inner Nengo simulator. Every neural cell stores 50,000 lossless samples.

| Dimension | Values |
|---|---|
| Missions | Roll, Full3, Hard45, Hardstep, Yaw360 |
| Conditions | Nominal, deterministic hard-pulse torque |
| Controllers | PD; CMG fixed/PES; LIF fixed/PES; ALIF fixed/PES; Izhikevich fixed/PES; LIFRate fixed/PES |
| Total cells | 5 × 2 × 11 = 110 |
| Completed | 99 |
| Declared divergence outcomes | 11, all in hard-pulse Yaw360 |
| Neural archives audited | 100/100 |
| Archive audit failures | 0 |

The simulation divergence limit is ±180° pitch/roll. This is deliberately
separate from the physical rig's much tighter safety limits. A run that reaches
the numerical limit is preserved as an abort; its partial error is not used to
claim a matched improvement.

## Nominal Hover findings

Positive values mean lower mean quaternion-angle error than PD.

| Mission | PD mean error | CMG fixed | CMG PES | LIF PES | ALIF PES | Izhikevich PES | LIFRate PES |
|---|---:|---:|---:|---:|---:|---:|---:|
| Roll | 3.26° | **+10.65%** | **+10.15%** | +0.00% | +0.00% | +1.42% | +0.00% |
| Full3 | 20.06° | +0.03% | +0.12% | +0.01% | +0.01% | **+0.41%** | +0.07% |
| Hard45 | 19.79° | +0.10% | −0.00% | +0.01% | +0.01% | +0.11% | −0.02% |
| Hardstep | 22.42° | −0.08% | −0.16% | +0.01% | +0.01% | −0.05% | +0.05% |
| Yaw360 | 6.55° | +1.54% | **+1.77%** | +0.00% | +0.00% | +0.48% | +0.00% |

Interpretation:

- Roll is the discriminating nominal mission. CMG fixed and CMG-PES are an order of magnitude stronger than the best conventional spiking result.
- The conventional LIF/ALIF/LIFRate PES paths often learn nonzero decoder changes but have negligible control effect because their calibrated activities/residual authority remain near zero in these operating currents.
- Izhikevich-PES is the strongest conventional spiking alternative and does help some missions, so the honest claim is not that other neurons can never work.
- CMG's advantage is mission-dependent, not universal. Full3 and Hard45 are nearly tied across families, and CMG slightly degrades Hardstep under this common parameter set.
- Fixed CMG beating PD in Roll shows that the membrane–gate observable itself is useful. PES is an additional online decoder mechanism; it is not what creates the gate dynamics.

## Hard-pulse findings

| Mission | PD mean error | Best neural result | CMG PES |
|---|---:|---:|---:|
| Roll | 16.30° | CMG-PES, **+1.12%** | +1.12% |
| Full3 | 47.88° | LIFRate fixed, +0.94% | +0.01% |
| Hard45 | 19.72° | LIFRate fixed, +0.25% | −0.13% |
| Hardstep | 22.29° | LIFRate fixed, +0.06% | −0.17% |
| Yaw360 | divergence | all 11 variants diverged | not comparable |

The hard-pulse Yaw360 outcome identifies a testbench/plant-envelope limit.
It does not support ranking neuron families because the matched PD reference and
every neural controller failed the full-duration feasibility condition.

## Connected Q8 shadow

All eleven controllers passed:

- 600 Q8 samples per controller;
- 6,000 Nengo samples per neural controller;
- live encoder taring from the current physical pose;
- complete trace, summary, neural schema, and manifest;
- maximum absolute written motor or DAC value: exactly 0.0.

These are interface and telemetry validations only. They are not closed-loop
hardware results and must never be plotted as controller-performance evidence.

## Previously frozen physical Hover evidence

| Mission | PD mean | CMG-PES mean | Mean change | Peak change | Status |
|---|---:|---:|---:|---:|---|
| Roll, n=3 | 5.441° | 5.296° | **+2.65 ± 1.08%** | **+3.41 ± 2.34%** | complete |
| Full3, 50% reference | 11.439° | 11.415° | +0.21% | +2.63% | complete |
| Hard45, 40% reference | 9.977° | 10.036° | −0.59% | −1.10% | complete |
| Hardstep, 35% reference | 13.315° | 13.431° | −0.87% | −0.58% | complete |
| Yaw360 | 7.953° until abort | not run | not comparable | not comparable | PD roll safety abort at −20.083° |

Every physical run uses its measured startup pose as local zero and records the
raw encoder home. The full Yaw360 CMG hardware run remains intentionally absent
because its baseline could not safely complete.

## Canonical locations

- Hover raw 110-cell matrix:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hover_neuron_family_matched_25s_2026-09-01`
- Hover compiled tables, heatmaps, rankings, representative neuron figures, and frozen manifest:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hover_neuron_family_compiled_2026-09-01`
- Q8 zero-output family shadow:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\q8_neuron_family_shadow_2026-09-01`
- Physical hardware compilation:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\final_hardware_campaign_2026-09-01`
- Roll n=3 physical aggregate:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware_armed_roll_n3_2026-09-01`
- MuJoCo 110-cell raw matrix:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_matched_45s`
- MuJoCo compiled family benchmark:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_compiled`

## Reproduce or resume

The complete per-mission command catalog and universal launcher are:

- `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\docs\COMMAND_CATALOG_2026-09-01.md`
- `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\launch_hover_experiment.ps1`

```powershell
$py = 'C:\Research\hover3dof\.venv\Scripts\python.exe'
$root = 'C:\Research\hover3dof\nengo_gui_hil_2026-08-29'

# Resumable; completed cells are not rerun.
& $py "$root\run_hover_neuron_family_campaign.py" --workers 3

# Re-audit, compile figures/tables, and rebuild SHA-256 manifest.
& $py "$root\compile_hover_neuron_family_campaign.py"

# Re-audit an existing connected zero-output shadow.
& $py "$root\audit_q8_neuron_family_shadow.py"

# Rebuild the physical PD/CMG campaign package without commanding hardware.
& $py "$root\compile_final_hardware_campaign_2026_09_01.py"
```

## Reporting rules for ACC 2027

1. Call the CMG realization a **Nengo-native NEF/PES decoder realization of a paired continuous membrane–gate population**, not a generic LIF ensemble.
2. Report fixed and PES results separately. `adaptive` refers to online PES decoder adaptation; conductance adaptation is an internal CMG property and must not be conflated with PES.
3. Label Hover family runs as emulated digital-twin results, Q8 family runs as zero-output shadows, and only the qualified PD/CMG runs as physical closed-loop results.
4. Keep the Crazyflie 1.5× rotor-authority design explicit; do not describe it as stock-CF2 hardware.
5. Do not compute improvement percentages for safety-aborted or divergence-aborted pairs.
6. Present the strongest honest claim: CMG is particularly effective in Roll and nominal Yaw360, conventional PES neurons can sometimes help, and no single common parameterization dominates every mission.
