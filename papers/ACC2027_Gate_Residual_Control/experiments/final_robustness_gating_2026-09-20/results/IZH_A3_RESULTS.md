# Izhikevich-PES vs CMG-PES under the CMG protocol (amendment A3, reduced grid)

## Nominal (45 s, no noise): 45-s mean true-attitude error [mrad] and reduction vs PD+ff rho=3 [%]

| platform | mission | PD+ff | CMG gated | Izh. gated | Izh. ungated | CMG red. | Izh. gated red. | Izh. ungated red. | Izh. gate blocked | Izh. effort (norm. rms) | CMG effort |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| X2 | Roll | 0.342 | 0.074 | 3.120 | 3.120 | +78.4 | -811.6 | -811.6 | 0.000 | 0.370 | 0.003 |
| X2 | Full3 | 10.085 | 8.834 | 9.509 | 9.555 | +12.4 | +5.7 | +5.3 | 0.001 | 0.370 | 0.023 |
| X2 | Hard45 | 10.537 | 9.080 | 9.503 | 9.817 | +13.8 | +9.8 | +6.8 | 0.000 | 0.372 | 0.023 |
| X2 | Hardstep | 265.912 | 271.354 | 269.860 | 310.737 | -2.0 | -1.5 | -16.9 | 0.180 | 0.327 | 0.109 |
| X2 | Yaw360 | 0.200 | 0.117 | 3.115 | 3.115 | +41.8 | -1454.9 | -1454.9 | 0.000 | 0.370 | 0.001 |
| CF2 | Roll | 0.563 | 0.226 | 1.034 | - | +59.9 | -83.5 | - | 0.000 | 0.140 | 0.005 |
| CF2 | Full3 | 7.056 | 6.675 | 6.613 | - | +5.4 | +6.3 | - | 0.000 | 0.150 | 0.010 |
| CF2 | Hard45 | 8.653 | 8.018 | 8.073 | - | +7.3 | +6.7 | - | 0.000 | 0.153 | 0.012 |
| CF2 | Hardstep | 262.588 | 263.187 | 263.804 | 2081.487 | -0.2 | -0.5 | -692.7 | 0.125 | 0.139 | 0.049 |
| CF2 | Yaw360 | 0.084 | 0.067 | 0.943 | - | +20.3 | -1025.7 | - | 0.000 | 0.138 | 0.000 |

## Hardstep: every arm, both airframes (mrad; reduction vs PD+ff)

| platform | arm | beta | error | reduction | blocked share | rotor sat. | box sat. |
|---|---|---:|---:|---:|---:|---:|---:|
| X2 | CMG ungated (table beta) | 0.5 | 311.073 | -17.0 | 0.000 | 0.035 | 0.392 |
| X2 | CMG gated | 0.5 | 271.354 | -2.0 | 0.205 | 0.094 | 0.420 |
| X2 | Izhikevich ungated | 0.5 | 310.737 | -16.9 | 0.000 | 0.043 | 0.449 |
| X2 | Izhikevich gated | 0.5 | 269.860 | -1.5 | 0.180 | 0.110 | 0.431 |
| CF2 | CMG ungated (table beta) | 0.05 | 265.927 | -1.3 | 0.000 | 0.003 | 0.182 |
| CF2 | CMG gated | 0.2 | 263.187 | -0.2 | 0.145 | 0.003 | 0.321 |
| CF2 | Izhikevich ungated | 0.05 | 266.056 | -1.3 | 0.000 | 0.003 | 0.205 |
| CF2 | Izhikevich ungated | 0.2 | 2081.487 | -692.7 | 0.000 | 0.790 | 0.834 |
| CF2 | Izhikevich gated | 0.2 | 263.804 | -0.5 | 0.125 | 0.004 | 0.321 |

## Realistic noise (0.020 rad / 0.050 rad/s), seeds 1-3, paired with PD+ff: geometric-mean reduction [%] and per-seed values

| platform | mission | PD+ff [mrad] (seeds 1-3) | Izh. gated [mrad] | Izh. per-seed red. | Izh. GM red. | CMG GM red. (same 3 seeds) | CMG GM red. (10 seeds) | Izh. vs CMG ratio (GM) |
|---|---|---|---|---|---:|---:|---:|---:|
| X2 | Roll | 1.44, 1.51, 1.32 | 3.33, 3.36, 3.33 | -131.1, -122.9, -151.2 | -134.8 | -4.3 | -4.2 | 2.25 |
| X2 | Hard45 | 10.55, 10.76, 10.66 | 9.91, 10.03, 9.98 | +6.0, +6.8, +6.3 | +6.4 | +10.7 | +10.8 | 1.05 |
| X2 | Hardstep | 266.84, 267.00, 266.95 | 272.12, 274.07, 272.85 | -2.0, -2.6, -2.2 | -2.3 | -2.3 | -2.6 | 1.00 |
| CF2 | Roll | 1.51, 1.58, 1.41 | 1.90, 1.94, 1.77 | -26.1, -22.6, -25.3 | -24.6 | -0.5 | -0.4 | 1.24 |
| CF2 | Hard45 | 8.81, 8.88, 8.77 | 8.42, 8.40, 8.30 | +4.5, +5.4, +5.4 | +5.1 | +4.0 | +4.0 | 0.99 |
| CF2 | Hardstep | 263.30, 263.40, 263.50 | 263.87, 264.70, 264.77 | -0.2, -0.5, -0.5 | -0.4 | -0.3 | -0.3 | 1.00 |

## Hover, intermittent torque bursts (1x amplitude), gated: burst-phase and quiet-phase mean error [mrad] and reduction vs PD+ff

| platform | PD+ff burst | PD+ff quiet | CMG burst red. | CMG quiet red. | Izh. burst | Izh. quiet | Izh. burst red. | Izh. quiet red. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X2 | 28.145 | 0.723 | +14.4 | +14.7 | 24.702 | 3.466 | +12.2 | -379.1 |
| CF2 | 39.674 | 0.618 | +5.9 | +19.8 | 37.493 | 1.472 | +5.5 | -138.3 |

## Five-mission summaries (noise-free, rho = 3)

| platform | geo PD+ff [mrad] | geo CMG gated | geo Izh. gated | CMG geo red. [%] | Izh. geo red. [%] | mean effort CMG | mean effort Izh. | Izh. effort / CMG effort |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| X2 | 4.54 | 2.85 | 11.88 | +37.3 | -161.5 | 0.032 | 0.362 | 11.4 |
| CF2 | 3.77 | 2.92 | 6.72 | +22.4 | -78.6 | 0.015 | 0.144 | 9.5 |

## Gate blocked fraction of the Izhikevich gated nominal runs (more digits)

| platform | Roll | Full3 | Hard45 | Hardstep | Yaw360 |
|---|---:|---:|---:|---:|---:|
| X2 | 0.00000 | 0.00144 | 0.00011 | 0.18019 | 0.00000 |
| CF2 | 0.00000 | 0.00024 | 0.00000 | 0.12476 | 0.00000 |

## First reading of the priors (raw ranking, before amendment A3.2; superseded by izh_a3_priors.md, which applies the floor)

- **P1** (Izhikevich reduction below CMG's in every nominal cell): fails in 2/10: x2/hardstep: Izh -1.5 vs CMG -2.0; cf2-rotor/full3: Izh +6.3 vs CMG +5.4
- **P2** (noise: degrades Roll; does not beat CMG on Hard45): Roll degraded on both airframes: True; Hard45 not beaten: no - cf2-rotor/hard45: Izh +5.1 vs CMG +4.0
- **P3** (gate reduces the X2 Hardstep loss, does not make it a gain): ungated -16.9 -> gated -1.5: holds
- **P4** (CF2 beta .2 stays safe under noise; safe = every mean error < 1 rad and rotor saturation < 0.5, the sweep criterion): 9/9 cells safe
