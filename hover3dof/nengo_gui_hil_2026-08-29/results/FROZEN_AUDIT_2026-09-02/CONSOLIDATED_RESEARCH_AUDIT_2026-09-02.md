# ACC 2027 CMG residual-control project — consolidated frozen audit

Freeze date: 2026-09-02 (America/Denver)

Proposed paper title:

> Online PES-Adapted Neuromorphic Membrane–Gate Residual Control for
> Actuator-Constrained UAV Quaternion Attitude Tracking

## 1. Freeze status

- No Python control process was running at freeze time.
- The last controlled Nengo shutdown reported all four Q8 analog outputs forced
  to zero and the card closed.
- A final attempt to reopen Q8 for a separate zero-output check was unavailable
  (`HILError -108`; cleanup call `-88`). This is recorded as unavailable, not
  represented as a successful final hardware check.
- The canonical direct-Nengo physical dataset passed 144/144 deep integrity
  checks across 12 completed matched runs.
- All three upstream frozen manifests passed a fresh entry-by-entry check:
  1,485 files and 6,327,420,429 bytes rehashed, with zero missing, size, or
  SHA-256 mismatches.
- Two full-scale yaw360 safety aborts are preserved and excluded from matched
  performance statistics.
- Two GUI hover preflights are preserved but explicitly excluded: one contained
  an impossible 1923.75-degree encoder step; the second was an unplanned repeat
  caused by the GUI restarting a completed worker.

## 2. Canonical real-hardware results — Quanser 3DOF Hover

Canonical root:

`C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\DIRECT_NENGO_FINAL_2026-09-01`

Both controllers use the same quaternion-PD plant path, mission reference,
physical motor allocation, safety limits, sample rate, and run duration. CMG-PES
adds the bounded membrane–gate decoder residual using `beta=0.2`, a per-motor
residual cap of 0.2 V, learning rate 0.0002, `k_error=2`, `k_rate=0`, and a
1 V/s residual slew limit. Positive percentages mean CMG-PES reduced error.

| Mission | Scale / duration | PD mean | CMG mean | Mean change | PD max | CMG max | Max change |
|---|---:|---:|---:|---:|---:|---:|---:|
| Hover | 1.00 / 8 s | 0.116 deg | 0.046 deg | +60.38% | 0.224 deg | 0.076 deg | +66.03% |
| Roll | 1.00 / 8 s | 5.498 deg | 5.192 deg | **+5.57%** | 8.150 deg | 9.079 deg | -11.40% |
| Full3 | 0.50 / 12 s | 11.282 deg | 11.644 deg | -3.21% | 17.005 deg | 17.075 deg | -0.41% |
| Hard45 | 0.40 / 12 s | 9.743 deg | 9.689 deg | +0.55% | 14.919 deg | 15.722 deg | -5.38% |
| Hardstep | 0.35 / 12 s | 13.626 deg | 13.497 deg | +0.95% | 33.671 deg | 34.367 deg | -2.07% |
| Yaw360 reduced range | 0.30 / 30 s | 2.731 deg | 2.960 deg | -8.38% | 3.695 deg | 3.890 deg | -5.27% |

The Hover percentage is numerically large only because the baseline is already
near zero; both controllers are within a fraction of a degree. It is not a
robust headline improvement. Roll is the strongest completed hardware tracking
result, although its CMG maximum error is worse in this one final pair.

The row called `yaw360 reduced range` uses the yaw360 smooth reference shape at
`reference_scale=0.3`, so its endpoint is about 108 degrees. It is not a
completed physical 360-degree revolution and must never be labeled as one.

### Full-scale yaw360 safety evidence

Two independent PD attempts used `reference_scale=1.0` and stability-priority
allocation. Both safety-aborted at essentially the same roll magnitude:

| Planned duration | Samples before abort | Abort |
|---:|---:|---|
| 30 s | 3,231 | roll limit, +20.127 deg |
| 50 s | 4,905 | roll limit, -20.127 deg |

The same failure magnitude despite different reference speed suggests an
orientation/mechanical constraint (cable wind-up is a leading hypothesis), not
proof of a controller-tracking limitation. No full-scale CMG yaw360 hardware
run should be claimed because the baseline feasibility condition was not met.

### Physical data captured

- 16,400 samples/controller at 200 Hz across the six canonical profiles;
  32,800 matched physical plant samples in total.
- Each CMG run contains a 2 kHz `neural_trace_2khz.npz` with ten neural samples
  per hardware sample, totaling 164,000 neural samples over six missions.
- Each CMG neural archive exposes 28 array groups: paired currents, membrane and
  native voltage, gate, normalized activity, raw output, threshold/gate target,
  conductance terms, membrane drive/lambda, raw/clipped decoder output, PES
  error, weights, per-step weight delta, residual torque, baseline torque,
  mission target, disturbance, hardware-step index, substep, and time.
- Every canonical run stayed inside the recorded 5-degree/sample encoder guard
  and 0–24 V written-motor bounds.

## 3. Repeated hardware evidence and historical campaign

The earlier three-pair Roll campaign is valuable as replication evidence:

- PD mean error: 5.4405 +/- 0.0648 deg (sample SD, n=3).
- CMG-PES mean error: 5.2960 +/- 0.0428 deg.
- Paired mean improvement: **2.6508 +/- 1.0765%**.
- Paired maximum-error improvement: 3.4060 +/- 2.3383%.
- All six runs completed without abort.

Path:

`C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hardware_armed_roll_n3_2026-09-01`

The earlier GUI-collected single-pair campaign produced Full3 +0.21%, Hard45
-0.59%, Hardstep -0.87%, and one full-scale Yaw360 PD safety abort. Keep it as
historical corroboration, not pooled with the final direct-Nengo pairs, because
the execution surface and collection session differ.

Path:

`C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\final_hardware_campaign_2026-09-01`

## 4. Emulated 3DOF Hover neuron-family benchmark

Matrix: 5 missions x 11 controllers x 2 conditions = 110 cells, 25 s/cell.
Controllers are PD; CMG fixed/PES; LIF fixed/PES; ALIF fixed/PES;
Izhikevich fixed/PES; and LIFRate fixed/PES.

- 110/110 cells found.
- 99 completed.
- The 11 hard-pulse Yaw360 cells all crossed the declared +/-180-degree
  simulation-divergence boundary; their improvements are deliberately masked.
- 100/100 neural archives passed; no missing, nonfinite, or sample-count fault.

Nominal highlights:

| Mission | CMG fixed | CMG-PES | Best controller |
|---|---:|---:|---|
| Roll | **+10.65%** | +10.15% | CMG fixed (+10.65%) |
| Full3 | +0.03% | +0.12% | Izhikevich-PES (+0.41%) |
| Hard45 | +0.10% | approximately 0% | LIFRate fixed (+0.22%) |
| Hardstep | -0.08% | -0.16% | LIF fixed (+0.06%) |
| Yaw360 | +1.55% | **+1.77%** | CMG-PES (+1.77%) |

Hard-pulse highlights: CMG-PES gives +1.12% on Roll; other feasible missions
are near neutral, and hard-pulse Yaw360 is infeasible for every controller.

This benchmark supports a discriminating CMG advantage on Roll, not a universal
CMG win. Izhikevich and LIFRate can help in particular cells; conventional
families must not be described as universally ineffective.

Paths:

- Raw: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hover_neuron_family_matched_25s_2026-09-01`
- Compiled: `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\hover_neuron_family_compiled_2026-09-01`

## 5. Connected-Q8 neuron-family shadow qualification

All 11 controllers completed a connected-Q8 sensor/telemetry shadow run:

- 600 hardware samples/controller.
- 6,000 neural samples for every neural controller.
- Every one of four physical DAC fields was exactly zero at every sample.
- This proves connected acquisition and telemetry only. It is not motor-driving
  or closed-loop hardware evidence for LIF, ALIF, Izhikevich, or LIFRate.

Path:

`C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\q8_neuron_family_shadow_2026-09-01`

## 6. MuJoCo/Nengo UAV attitude benchmark

The frozen matched neuron-family campaign contains 110 cells:

- 2 vehicle designs: X2 and CF2 rotor-design variant.
- 5 missions: Roll, Full3, Hard45, Hardstep, Yaw360.
- 11 controllers, 45 s/cell.
- Integrity audit passed: 110 expected cells, 100 neural archives, 1,720
  checked signals, zero failures.

CMG fixed versus CMG-PES mean quaternion-angle-error improvement:

| Platform | Roll | Full3 | Hard45 | Hardstep | Yaw360 |
|---|---:|---:|---:|---:|---:|
| X2 CMG fixed | +1.93% | +9.74% | +10.27% | +0.46% | +0.12% |
| X2 CMG-PES | **+17.36%** | **+56.56%** | **+53.07%** | **+20.94%** | **+60.58%** |
| CF2 design CMG fixed | +3.31% | +4.53% | +6.80% | +0.42% | +0.06% |
| CF2 design CMG-PES | **+17.33%** | **+56.14%** | **+53.65%** | **+18.37%** | **+60.60%** |

Important scope: the CF2 entry is a declared controller/actuator co-design
variant using 1.5x rotor authority. It is not a stock Crazyflie 2 hardware
claim. In some cells Izhikevich-PES gives the largest numerical improvement
(especially Roll and Hardstep), so CMG should be argued through consistency,
continuous non-spiking state, interpretability, and cross-platform behavior,
not by claiming it wins every individual cell.

Paths:

- Raw: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_matched_45s`
- Compiled: `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_compiled`

## 7. Broader 6-DOF MuJoCo evidence

These experiments answer a different question from the attitude-only matched
family matrix and must remain separate in the paper.

- Fully actuated X2 wrench testbed, Full6 stress: +3.96% position and +49.17%
  attitude improvement.
- Real rotor-mixed X2 cascade: Waypoint +11.5%/+13.2%, Circle
  +65.1%/+68.1%, and Full6 stress +76.1%/+65.8% (position/attitude).
- The stock/earlier CF2 cascade did not reproduce the X2 benefit and was
  negative on demanding missions. This motivated the explicitly labeled 1.5x
  rotor-authority design study; the two result families must not be conflated.
- Nengo/NEF implementation validation: isolated Nengo versus frozen NumPy
  relative command error about 1.05e-7; closed-loop mission metrics matched to
  three or four significant figures.

Primary progress record:

`C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\PROGRESS_2026-08-31.md`

## 8. Complete saved-run inventory

Within the Nengo/Hover result tree, 228 `summary.json` records were indexed:

| Classification | Count |
|---|---:|
| Emulated | 158 |
| Physical completed | 28 |
| Physical safety abort | 20 |
| Q8 shadow, zero output | 20 |
| Invalid instrumentation exclusion | 1 |
| Unplanned-repeat exclusion | 1 |

The 28 completed physical summaries include historical/verification campaigns
and should not be treated as 28 independent matched paper trials. The canonical
paper set is the 12-run direct-Nengo matrix plus the earlier Roll n=3 replicate
study reported separately.

Full machine-readable inventory:

`C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\FROZEN_AUDIT_2026-09-02\all_saved_run_inventory.csv`

## 9. Claims that are supported now

1. CMG-PES works both inside Nengo and in the earlier NumPy implementation.
2. Online PES decoder adaptation is the dominant source of the large MuJoCo
   improvement in the amplified-gate regime; fixed CMG remains useful in
   selected missions, especially emulated Hover Roll.
3. Real 3DOF Hover hardware validates bounded CMG-PES execution at 200 Hz with
   internal 2 kHz neural dynamics and complete neuron/decoder telemetry.
4. Hardware benefit is mission-dependent: strongest and repeated on Roll;
   near-neutral on Hard45/Hardstep; worse on Full3 and reduced-range Yaw in the
   final pair.
5. A full physical 360-degree yaw revolution is not validated. Two baseline
   attempts safety-aborted; only the 108-degree reduced-range shape completed.
6. LIF/ALIF/Izhikevich/LIFRate are validated in emulation and connected-Q8
   zero-output shadow, not as armed hardware controllers.

## 10. Frozen artifacts

- Deep physical audit: `canonical_physical_deep_audit.json`
- Canonical pair table: `canonical_physical_matched_pairs.csv` and `.json`
- Every saved Nengo/Hover summary: `all_saved_run_inventory.csv` and `.json`
- Cross-campaign registry: `campaign_registry.json`
- Audit headline: `AUDIT_SUMMARY.json`
- Immutable hashes: `FROZEN_SHA256_MANIFEST.json`
- Reverification of upstream freezes: `UPSTREAM_MANIFEST_VERIFICATION.json`

To repeat the read-only audit (no Q8 access):

```powershell
& 'C:\Research\hover3dof\.venv\Scripts\python.exe' `
  'C:\Research\hover3dof\nengo_gui_hil_2026-08-29\audit_and_freeze_all_2026_09_02.py'
```
