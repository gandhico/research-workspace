# Nengo data and results checkpoint — 2026-08-31

## Outcome

The current research now has a matched, full-rate Nengo evidence layer in
addition to the direct CMG implementation. The final MuJoCo neuron-family
matrix contains **110/110** planned 45-s cells: two platform designs, five
missions, a matched quaternion-PD baseline, and ten family/decoder conditions.
All 100 non-baseline cells retain 2-kHz neural archives and standardized
diagnostic figures.

The 3DOF Hover Nengo code also has a profiled emulated hard-pulse campaign with
five PD/CMG pairs. This is prehardware software/robustness evidence, not an
identified digital twin or a physical result.

## Matched Nengo matrix

| Quantity | Value |
|---|---:|
| Platforms | X2 rotor model; CF2 1.5x rotor-authority design |
| Missions | Roll, Full3, Hard45, Hardstep, Yaw360 |
| Family cases | CMG, LIF, ALIF, Izhikevich, LIFRate |
| Decoder cases | fixed `W0`; online built-in Nengo PES |
| Simulation horizon / step | 45 s / 0.5 ms |
| Total summaries | 110 |
| Full-rate neural NPZ files | 100 |
| Neural sample count per non-baseline run | 90,000 |
| Decoder parameters retained per step | 18 (`3 x 6`) |
| Frozen-tree files / bytes | 871 / 4,065,552,904 |
| Standardized diagnostic PNG/PDF files | 170 / 170 |

`audit_neuron_family_campaign.py` passes with 110 expected cells, 100 checked
neural archives, 1,720 checked archive signals, exact 0.5-ms timing, finite
values, invariant fixed decoders, valid `3 x 6` weight shapes, bounded decoded
outputs/residual authority, and no missing standard diagnostic figures.

### Five-mission average

| Platform | Family | Fixed improvement | PES improvement | PES normalized residual RMS |
|---|---|---:|---:|---:|
| X2 | CMG | 4.50% | 41.70% | 0.12 |
| X2 | LIF | 0.65% | 1.72% | 0.04 |
| X2 | ALIF | 0.63% | 1.49% | 0.04 |
| X2 | Izhikevich | 3.00% | 47.28% | 0.37 |
| X2 | LIFRate | 0.86% | 3.71% | 0.05 |
| CF2 design | CMG | 3.02% | 41.22% | 0.12 |
| CF2 design | LIF | 0.43% | 1.50% | 0.03 |
| CF2 design | ALIF | 0.45% | 1.44% | 0.03 |
| CF2 design | Izhikevich | 2.19% | 46.28% | 0.37 |
| CF2 design | LIFRate | 0.68% | 1.71% | 0.03 |

CMG-PES improves all ten platform/mission cells and occupies the lower-effort
point. Izhikevich-PES also improves all ten and has the larger average gain,
but uses about three times the normalized residual RMS, approximately an order
of magnitude more decoder movement, and more saturation. LIF/ALIF/LIFRate are
mostly unexcited under the frozen canonical-current mapping, but activate and
benefit from PES on Hardstep. Therefore the architecture generalizes beyond
CMG, while CMG's supported advantage is continuous availability and
authority-efficient consistency—not exclusive learnability.

## What is retained per neural step

- cross-rate indices and time;
- quaternion-PD baseline torque and bounded PES teaching target;
- six canonical currents and, where adapted, six native neuron currents;
- raw spikes/rate output and the calibrated natural decoder feature;
- CMG membrane, gate, threshold, sigmoid argument/target, conductance gain,
  conductance, exponential decay, and drive;
- family-specific voltage, refractory, adaptation, and recovery states exposed
  by Nengo;
- raw/clipped decoder output, PES error, all 18 weights, and all 18 per-step
  changes;
- bounded residual torque; and
- adjacent schema, summary, manifest, readable plant trace, and dependency
  provenance.

The repository-level deep catalog contains 687 run summaries, 555 visual
artifacts, and 2,333 signal-level records with shape, dtype, sample rate, finite
check, range, mean, standard deviation, RMS, occupancy, elements, and bytes.

## Hover hard-pulse result

| Mission | PD mean | CMG-PES mean | Result | Completion |
|---|---:|---:|---:|---|
| Roll | 4.4247 deg | 3.9554 deg | +10.61% | complete pair |
| Full3 | 21.5057 deg | 21.3179 deg | +0.87% | complete pair |
| Hard45 | 19.7697 deg | 19.6847 deg | +0.43% partial | both later hit roll safety boundary |
| shaped Hardstep | 22.3597 deg | 22.3860 deg | -0.12% | complete neutral/slight regression |
| scaled Yaw360 | 8.5310 deg | 8.3677 deg | +1.91% partial | both later hit pitch safety boundary |

Every CMG Hover run includes its full 2-kHz NPZ, 200-Hz HIL-style CSV,
statistics, flattened neural CSV, and equation/mechanism PNG/PDF. Partial runs
are explicitly labeled and preserved.

`audit_disturbance_campaign.py` passes all ten summaries: within each pair the
mission configuration, reference, and disturbance sequence match; sample-rate
alignment and finite values pass; all diagnostics exist. These fast emulations
did not enforce real-time execution, so logged deadline misses are not hardware
timing results.

## Connected Q8 zero-output qualification

After this checkpoint was assembled, the physically connected Q8 path was run
in a new hard-coded unarmed headless mode. PD and Nengo Hover qualifications
completed with 1,000 control rows each, zero deadline misses, and exactly zero
DAC output. Five Nengo shadow missions then completed with 26,000 real-time
control rows and 260,000 neural samples. All physical DAC commands remained
zero; isolated deadline misses were 0.12--0.34%. This validates the real
Q8/encoder, compute, telemetry, and shutdown path, not closed-loop tracking.
The authoritative report is
`C:\Research\hover3dof\docs\CONNECTED_Q8_NENGO_SHADOW_2026-08-31.md`.

## Authoritative paths

- Raw matched matrix:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_matched_45s`
- Compiled matched tables/figures:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\results\neuron_family_compiled`
- Deep run/signal/visual catalog:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\docs\data_catalog_2026-08-31`
- Hover profiled raw pairs:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\disturbance_campaign_profiled_2026-08-31`
- Hover compiled figures/table:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\disturbance_compiled_profiled_2026-08-31`
- Updated manuscript source/PDF:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\paper\acc2027_neuromorphic_gate_residual_draft.tex`
  and `C:\Research\papers\ACC2027_Gate_Residual_Control\output\pdf\acc2027_neuromorphic_gate_residual_draft.pdf`

## Integrity and compact bundles

- MuJoCo raw-tree SHA-256 manifest:
  `...\neuron_family_matched_45s\FROZEN_SHA256_MANIFEST.json`
- Hover raw-tree SHA-256 manifest:
  `...\disturbance_campaign_profiled_2026-08-31\FROZEN_SHA256_MANIFEST.json`
- Compact code/docs/compiled bundle:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\frozen_archives\nengo_neuron_family_INDEX_CODE_COMPILED_FROZEN_2026-08-31.zip`
- Compact Hover prehardware bundle:
  `C:\Research\hover3dof\frozen_archives\hover_nengo_disturbance_PREHARDWARE_INDEX_CODE_COMPILED_FROZEN_2026-08-31.zip`

The compact ZIPs intentionally do not duplicate the 4.68 GB raw telemetry.
The raw roots plus their SHA-256 manifests are the canonical frozen data.

## Remaining scientific gates

1. Repeat seeds/disturbances and report uncertainty, not only deterministic
   nominal cells.
2. Train online, freeze `W`, reset the plant, and evaluate held-out missions.
3. Run CMG readout/state ablations: `r`, `v`, `[v,r]`, `gamma=0`, and removal of
   gate-dependent conductance.
4. Keep the Izhikevich native-current factor of 10 visible in every comparison.
5. Do not call the CF2 design a stock-Crazyflie hardware result.
6. Do not arm the Hover Nengo GUI before the Q8 zero-output dry-run, baseline
   qualification, and staged-authority safety procedure.
