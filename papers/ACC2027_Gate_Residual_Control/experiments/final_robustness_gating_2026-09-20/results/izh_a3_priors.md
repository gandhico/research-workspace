# Priors of section 10 read with the rule of section 12

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
