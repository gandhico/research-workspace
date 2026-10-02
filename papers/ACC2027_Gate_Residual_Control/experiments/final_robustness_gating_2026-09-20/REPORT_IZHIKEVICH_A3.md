# Izhikevich-PES under the CMG protocol — complete report (amendment A3, 2026-09-21)

**Question.** The paper's Izhikevich rows were on the weak fixed-PD baseline, where Izhikevich looked better than CMG. Does that survive when the
rival basis is tested *in the same circumstances as CMG*: tuned PD+ff (rho = 3), true-attitude error, paired noise seeds, hover bursts, the same
saturation-aware output gate, both airframes?

**Answer, in five lines** (all numbers below are computed by `analyze_izh_a3.py`, `rail_fraction_izh.py`, `floor_izh.py`; the paper's audit `audit_v14.py` recomputes them independently).
1. *Multi-axis missions:* level with or below CMG. Full3/Hard45: X2 +5.7/+9.8 % vs CMG +12.4/+13.8 %; CF2 +6.3/+6.7 % vs +5.4/+7.3 % (CF2 differences are inside the single-run scatter).
2. *Single-axis missions:* far worse than the baseline. Roll/Yaw360: X2 -812/-1455 %, CF2 -84/-1026 % (CMG: +78/+42 and +60/+20 %).
   Five-mission geometric-mean error: **x2.62 (X2) and x1.79 (CF2) the baseline's** (CMG: x0.63 and x0.78).
3. *Effort:* 0.362 (X2) / 0.144 (CF2) of the axis bound against 0.032 / 0.015 for CMG — x11.4 and x9.5. On the fixed-PD baseline the ratio was only x3.
4. *The gate is not CMG-specific:* X2 Hardstep -16.9 % ungated -> -1.5 % gated; on CF2 at beta .2 the ungated Izhikevich residual diverges (119 deg mean error, rotors at a bound in 79 % of samples) and the gate turns it into -0.5 %.
5. *Noise and hover bursts:* the error floor persists (realistic noise, Roll -135 % X2, -25 % CF2; hover quiet phase x4.8 / x2.4 the baseline's) while the burst-phase reduction is close to CMG's (+12.2 vs +14.4 % X2; +5.5 vs +5.9 % CF2).

**Why.** The Izhikevich readout chatters between the authority rails: the realized residual sits at |r| >= 0.98 beta*l in 35-48 % of the samples on every mission (CMG: at most 0.8 %), so its effort does not depend on the mission
(max/min over the five missions: 1.1), whereas the CMG effort spans a factor 120-220 and orders the missions exactly as the baseline error does (Spearman rho = +1.00 on both airframes).
Interpretation (not separately tested): where the baseline error is well above the chatter floor the loop averages the chatter and the learned mean can still help (Full3, Hard45); where the baseline is already accurate (Roll, Yaw360) the chatter *is* the error.
Persistent activity is necessary for PES adaptation (Prop. 2; a silent basis stalls the update) but not sufficient for low effort.

## 1. Protocol identity with the CMG study

| item | CMG study | Izhikevich here |
|---|---|---|
| baseline | PD + desired-rate feedforward, bandwidth x3 (`--baseline backstepping --bw-scale 3 --rate-ff left-neg --no-model-ff`) | same |
| runner | `run_final_robustness.py` (sealed, SHA-256 in PREREGISTRATION.md) | `run_izh_robustness.py` = sealed runner + one controller choice (diff verified minimal) |
| residual | u = sat(u0 + beta*l*s), PES eta 8e-4, k_e 8, exact-saturation gate, load threshold 1.0 | same; s from the archived `NengoNeuronFamilyAugmentor(family="izhikevich")` (feature scale 42.602, native current scale 10, feature tau 5 ms), via `izh_adapter.py` |
| beta | X2 0.5, CF2 0.2 (A2 selection) | same |
| score | true-attitude 45-s mean error | same |
| noise | realistic 0.020 rad / 0.050 rad/s, paired seeds | same definition; seeds 1-3 only |
| disturbance | hover, intermittent bursts, 1x amplitude | same |

## 2. Validation and the CF2 caveat

* X2 Hard45 and Hardstep (beta 0.5): new runner vs archived runner, relative error **0.0** (bit-exact).
* CF2 Hard45 (beta 0.2): relative error 3.05e-4 — **missed the declared 1e-9 tolerance** (amendment A3.1). Diagnosis (`diagnose_cf2_short.py`, saved output below): the classical baseline is bit-identical between the runners; the only difference is that the sealed runner rebuilds the residual as beta*l*d (needed to audit the gate) while the archived augmentor applies its own command — equal unless beta*l is inexact in floating point (X2: beta 0.5, scale 1 -> difference 0.0; CF2: beta 0.2, scale 1.5 -> 5.4e-20 N m). Smooth CMG does not amplify that (|d omega| <= 4e-15 rad/s in 1 s); the spiking cell does.
* Sensitivity to numerical dust (`sensitivity_izh.py`): an initial-attitude offset of 1e-12 deg changes the CF2 Hard45 mean by 5.3e-3 (relative), X2 Hard45 by 8.3e-3 — larger than the 3e-4 validation gap.
* Floor ensemble (`floor_izh.py`, 24 runs; offsets k*1e-12 deg = 2.3e-14 k rad, k = 1..6, plus the A3 run): single-run scatter of the 45-s mean = **1.4 % of the error at worst (s.d.), 1.3 points of the PD+ff error**; amendment A3.2 sets the reading threshold to 3 s.d. = **4 points**. Differences between single Izhikevich runs, or between Izhikevich and CMG, below that are called *level*.

```
Single-run floor of the Izhikevich cells: 45-s mean error over the A3 run + 6 perturbed initial attitudes (k * 1e-12 deg)

cell                     A3 run     mean      sd  sd/mean     min     max  sd in pp of PD+ff   [mrad]
x2 full3                  9.509    9.522   0.130    1.36%   9.395   9.753              1.29
x2 hard45                 9.503    9.644   0.098    1.02%   9.503   9.774              0.93
cf2-rotor full3           6.613    6.660   0.051    0.76%   6.597   6.740              0.72
cf2-rotor hard45          8.073    8.038   0.016    0.20%   8.030   8.073              0.19
```

Sensitivity test output:
```
CF2 Hard45, beta 0.2, Izhikevich-PES: 45-s mean error [mrad] for initial-attitude perturbations
  perturbation        0 deg   mean 8.073354   relative change vs unperturbed 0.00e+00
  perturbation    1e-12 deg   mean 8.030859   relative change vs unperturbed 5.26e-03
  perturbation    1e-10 deg   mean 8.068951   relative change vs unperturbed 5.45e-04
archived-runner value 8.070892  (new runner unperturbed 8.073354; gap 3.05e-04)
X2 Hard45, beta 0.5, perturbation 1e-12 deg: mean 9.735302  (unperturbed 9.816749)  relative change 8.30e-03
```

## 3. Results (reduced grid, 33 runs)

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


Residual on the rails, and effort against the baseline error (`rail_fraction_izh.py`):
```
Fraction of samples (t >= 2 s, all three axes) with |realized residual| >= 0.98 beta l  |  median |residual|/(beta l)  |  fraction <= 0.02 (idle)

platform  mission     CMG rails  CMG med  CMG idle  Izh rails  Izh med  Izh idle
x2        roll            0.000    0.001     1.000      0.443    0.783     0.043
x2        full3           0.000    0.013     0.633      0.437    0.772     0.050
x2        hard45          0.000    0.009     0.782      0.439    0.780     0.041
x2        hardstep        0.008    0.001     0.682      0.348    0.451     0.249
x2        yaw360          0.000    0.000     1.000      0.440    0.783     0.048
cf2-rotor roll            0.000    0.000     0.784      0.412    0.623     0.138
cf2-rotor full3           0.000    0.015     0.696      0.460    0.835     0.071
cf2-rotor hard45          0.000    0.015     0.626      0.484    0.919     0.041
cf2-rotor hardstep        0.000    0.000     0.730      0.412    0.621     0.210
cf2-rotor yaw360          0.000    0.000     1.000      0.403    0.559     0.152

Effort (normalized rms) against the PD+ff error of the mission, ten cells (2 airframes x 5 missions):
  CMG        x2         effort by mission [0.003, 0.023, 0.023, 0.109, 0.001]   max/min     119.5   Spearman rho vs PD+ff error +1.00
  CMG        cf2-rotor  effort by mission [0.005, 0.01, 0.012, 0.049, 0.0]   max/min     219.6   Spearman rho vs PD+ff error +1.00
  Izhikevich x2         effort by mission [0.37, 0.37, 0.372, 0.327, 0.37]   max/min       1.1   Spearman rho vs PD+ff error -0.10
  Izhikevich cf2-rotor  effort by mission [0.14, 0.15, 0.153, 0.139, 0.138]   max/min       1.1   Spearman rho vs PD+ff error +0.40
```

## 4. Priors declared before the runs (PREREGISTRATION section 10), read with the rule of section 12

Floor ensemble (7 runs per cell: the A3 run + 6 initial-attitude perturbations of k * 1e-12 deg), s.d. in points of the PD+ff error: x2/full3 1.29, x2/hard45 0.93, cf2-rotor/full3 0.72, cf2-rotor/hard45 0.19.  Threshold = 3 x max = 3.9 points.

## P1 - Izhikevich reduction below CMG's in every nominal cell

| cell | Izh. [%] | CMG [%] | Izh. - CMG [pp] | reading |
|---|---:|---:|---:|---|
| x2/roll | -811.6 | +78.4 | -890.0 | below CMG |
| x2/full3 | +5.7 | +12.4 | -6.7 | below CMG |
| x2/hard45 | +9.8 | +13.8 | -4.0 | below CMG |
| x2/hardstep | -1.5 | -2.0 | +0.6 | level |
| x2/yaw360 | -1454.9 | +41.8 | -1496.7 | below CMG |
| cf2-rotor/roll | -83.5 | +59.9 | -143.4 | below CMG |
| cf2-rotor/full3 | +6.3 | +5.4 | +0.9 | level |
| cf2-rotor/hard45 | +6.7 | +7.3 | -0.6 | level |
| cf2-rotor/hardstep | -0.5 | -0.2 | -0.2 | level |
| cf2-rotor/yaw360 | -1025.7 | +20.3 | -1046.0 | below CMG |

P1: 6 cells below CMG by more than the threshold, 4 level, 0 above.  P1 is not contradicted.

## P2 - under realistic noise Izhikevich degrades Roll and does not beat CMG on Hard45 (per seed, 3 seeds)

| cell | seed | PD+ff [mrad] | CMG red. [%] | Izh. red. [%] | Izh. - CMG [pp] |
|---|---:|---:|---:|---:|---:|
| x2 roll | 1 | 1.44 | -4.1 | -131.1 | -127.0 |
| x2 roll | 2 | 1.51 | -5.1 | -122.9 | -117.8 |
| x2 roll | 3 | 1.32 | -3.7 | -151.2 | -147.5 |
| **x2 roll: mean Izh. - CMG** | | | | | **-130.8** (all three seeds same sign) |
| x2 hard45 | 1 | 10.55 | +10.7 | +6.0 | -4.7 |
| x2 hard45 | 2 | 10.76 | +10.7 | +6.8 | -3.9 |
| x2 hard45 | 3 | 10.66 | +10.6 | +6.3 | -4.3 |
| **x2 hard45: mean Izh. - CMG** | | | | | **-4.3** (all three seeds same sign) |
| x2 hardstep | 1 | 266.84 | -2.3 | -2.0 | +0.3 |
| x2 hardstep | 2 | 267.00 | -2.2 | -2.6 | -0.4 |
| x2 hardstep | 3 | 266.95 | -2.3 | -2.2 | +0.1 |
| **x2 hardstep: mean Izh. - CMG** | | | | | **-0.0** (all three seeds mixed) |
| cf2-rotor roll | 1 | 1.51 | -0.6 | -26.1 | -25.5 |
| cf2-rotor roll | 2 | 1.58 | -0.8 | -22.6 | -21.7 |
| cf2-rotor roll | 3 | 1.41 | -0.2 | -25.3 | -25.1 |
| **cf2-rotor roll: mean Izh. - CMG** | | | | | **-24.1** (all three seeds same sign) |
| cf2-rotor hard45 | 1 | 8.81 | +4.0 | +4.5 | +0.5 |
| cf2-rotor hard45 | 2 | 8.88 | +4.0 | +5.4 | +1.4 |
| cf2-rotor hard45 | 3 | 8.77 | +4.0 | +5.4 | +1.3 |
| **cf2-rotor hard45: mean Izh. - CMG** | | | | | **+1.1** (all three seeds same sign) |
| cf2-rotor hardstep | 1 | 263.30 | -0.3 | -0.2 | +0.1 |
| cf2-rotor hardstep | 2 | 263.40 | -0.3 | -0.5 | -0.2 |
| cf2-rotor hardstep | 3 | 263.50 | -0.3 | -0.5 | -0.1 |
| **cf2-rotor hardstep: mean Izh. - CMG** | | | | | **-0.1** (all three seeds mixed) |

The noise cells carry their own scatter (seed to seed); the noise-free threshold is not applied to them.  Reading: Roll is degraded on both airframes (large effects); on Hard45 the paired per-seed difference is given above.

## P3 / P4

- P3: X2 Hardstep ungated -16.9 % -> gated -1.5 % (effect 15.4 points, far above the threshold); not a gain: holds.
- P4: CF2 beta 0.2 gated stayed safe in 9/9 noisy cells (see IZH_A3_RESULTS.md).


## 5. What was *not* run (declared in A3)

Moderate noise level; noise seeds 4-10; Full3 and Yaw360 under noise; 0.5x / 2x disturbance amplitude; CF2 at beta 0.5; the fixed-decoder Izhikevich variant at rho = 3; the other neuron families (LIF, ALIF, LIFRate) at rho = 3.
The full grid would be about 415 runs (2-3 h at 4 workers); the reduced grid took 512 s (33 runs) plus about 12 min for the 24-run floor ensemble. The gap to the full grid is stated in the paper's Table II footnote.

## 6. Disclosures

* The X2 nominal, ungated, beta 0.5 Izhikevich results (exploratory supplement, archived runner) were seen before amendment A3 was written.
* A3.2 (reading rule from a 3-sigma floor instead of the 1 % of A3.1) was written after the campaign and after the X2 half of the floor ensemble had been seen; the CF2 half was read afterwards. The reason is stated in the amendment: a nearly inert gate (0.011 % of steps) changed the X2 Hard45 mean by 3.2 %, so the two-run estimate of the floor was too small.
* Two slips of mine were corrected the same day, in the open (PREREGISTRATION section 12): the loss factors of Roll/Yaw360 were first written as "10-25" (the values are 1.8 to 16), and the perturbation size was first described as 1.7e-14 rad (the runner applies the Euler triple (theta, -0.7 theta, 0.5 theta); the ensemble offsets are 2.3e-14 to 1.4e-13 rad).
* Hardstep and Hard45 cells of a spiking model are single realizations; the paper quotes the scatter and does not interpret differences below 4 points.

## 7. Figures (title-free, `figures_out/izh_a3/`; attitude-detail and neuron-activity formats)

`{x2,cf2}_{hard45,hardstep,roll}_attitude.pdf` — error + roll/pitch/yaw in one window: PD+ff, CMG-PES ungated (wide translucent), CMG-PES gated, Izhikevich-PES gated (dark purple), and Izhikevich-PES ungated (light purple, wide) where it was run (Hardstep).
`..._attitude_zoom.pdf` (Hardstep) — log error axis, 6-s window: the CF2 ungated Izhikevich run leaves the plot at 10.2 s (divergence), the gated run stays with PD+ff.
`..._neurons.pdf`, `..._neurons_zoom.pdf` — one column per arm (membrane, gate/recovery, activity, residual, decoder norm); the residual and decoder rows share their y axis across columns, so effort and decoder movement compare directly. The zoom versions (6 s) make the Izhikevich rail-to-rail chatter readable.

## 8. Files and how to reproduce (about 10 min at 4 workers)

```
python run_campaign_izh.py all          # 33 cases, resumable
python analyze_izh_a3.py                # tables -> results/IZH_A3_RESULTS.md, izh_a3_numbers.json
python rail_fraction_izh.py             # rails and effort-vs-error -> results/izh_a3_rails.txt|json
python floor_izh.py                     # 24-run floor ensemble (about 10 min)
python priors_a32.py                    # priors under the A3.2 rule
python make_izh_figures.py / make_izh_a3_figures.py   # reference figures
python make_izh_report.py               # this file
python audit_v14.py                     # paper-side audit (after building the paper)
```
Code: `izh_adapter.py`, `run_izh_robustness.py`, `validate_izh_runner.py`, `diagnose_cf2_*.py`, `sensitivity_izh.py`. Data: `results/izh_a3/`, `results/results_izh_a3_all.csv`, `results_validation_izh/`.

### Appendix: 1-second bit-level comparison of the two runners on CF2 (`diagnose_cf2_short.py`)
```
=== classical   rows archived/new: 2001/2001
column          first exact diff (row)    t [s]  #rows differing   max |diff|
qerr                                -1      nan                0    0.000e+00
tau0_x                              -1      nan                0    0.000e+00
tau0_y                              -1      nan                0    0.000e+00
tau0_z                              -1      nan                0    0.000e+00
omega_x                             -1      nan                0    0.000e+00
omega_y                             -1      nan                0    0.000e+00
omega_z                             -1      nan                0    0.000e+00
residual_x                          -1      nan                0    0.000e+00
residual_y                          -1      nan                0    0.000e+00
z                                   -1      nan                0    0.000e+00
activity_0                          -1      nan                0    0.000e+00
decoder_w_0                         -1      nan                0    0.000e+00

=== nengo-nef-pes   rows archived/new: 2001/2001
column          first exact diff (row)    t [s]  #rows differing   max |diff|
qerr                               992   0.4960              671    3.001e-16
tau0_x                             978   0.4890             1007    2.697e-18
tau0_y                             978   0.4890             1017    3.043e-18
tau0_z                             978   0.4890             1002    2.052e-18
omega_x                            983   0.4915              992    4.000e-15
omega_y                            739   0.3695             1078    4.108e-15
omega_z                            999   0.4995              749    3.220e-15
residual_x                         152   0.0760              969    3.388e-20
residual_y                         330   0.1650              746    5.421e-20
z                                   -1      nan                0    0.000e+00
activity_0                          -1      nan                0    0.000e+00
decoder_w_0                         -1      nan                0    0.000e+00

=== nengo-izhikevich-pes   rows archived/new: 2001/2001
column          first exact diff (row)    t [s]  #rows differing   max |diff|
qerr                               167   0.0835             1155    4.007e-16
tau0_x                             237   0.1185             1742    3.564e-18
tau0_y                             777   0.3885             1066    9.999e-17
tau0_z                             164   0.0820             1646    5.483e-18
omega_x                            237   0.1185             1673    6.301e-15
omega_y                            112   0.0560             1565    8.715e-15
omega_z                            241   0.1205             1433    7.883e-15
residual_x                         161   0.0805              970    3.944e-18
residual_y                         361   0.1805              829    3.284e-17
z                                   -1      nan                0    0.000e+00
activity_0                          -1      nan                0    0.000e+00
decoder_w_0                        296   0.1480             1696    8.882e-15
```
