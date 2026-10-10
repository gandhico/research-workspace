# Final conclusion: neuron family and no-neuron basis

This report uses the mathematically corrected, equal normalized PES rate and the final rho=3 PD+desired-rate-feedforward baseline. Positive percentages denote lower mean quaternion-angle error.

## Strict matched result

| Basis | X2 geo. improvement | X2 effort | X2 active | CF2 geo. improvement | CF2 effort | CF2 active |
|---|---:|---:|---:|---:|---:|---:|
| CMG | +37.36% | 0.045 | 99.9% | +22.49% | 0.020 | 99.9% |
| LIF | +0.55% | 0.034 | 4.0% | -0.09% | 0.013 | 3.4% |
| ALIF | +0.33% | 0.035 | 3.7% | -0.08% | 0.014 | 3.2% |
| LIFRate | +0.46% | 0.038 | 4.4% | -0.05% | 0.015 | 3.7% |
| Izhikevich | -19.66% | 0.070 | 99.9% | -5.37% | 0.025 | 99.9% |
| Constant | +10.32% | 0.041 | 100.0% | +4.28% | 0.017 | 100.0% |
| Static paired | +11.94% | 0.039 | 100.0% | +4.75% | 0.015 | 100.0% |

## Threshold-aware conventional families

| Family | Frozen setting (bias, gain, filter) | X2 strict -> tuned all / held-out | CF2 strict -> tuned held-out | Tuned worst mission X2 / CF2 |
|---|---|---:|---:|---:|
| LIF | (0.97, 1.03, 20 ms) | +0.55% -> +14.15% / +10.91% | -0.09% -> +7.40% | +0.0% / -0.3% |
| ALIF | (0.97, 1.03, 20 ms) | +0.33% -> +9.61% / +7.39% | -0.08% -> +4.74% | +0.0% / -0.2% |
| LIFRate | (1.03, 0.97, 5 ms) | +0.46% -> +24.23% / +15.91% | -0.05% -> +11.38% | -0.5% / -0.9% |
| Izhikevich | (0.25, 1.75, 20 ms) | -19.66% -> +7.60% / +6.32% | -5.37% -> +1.45% | +0.0% / -0.3% |

## Mission-level tuned result

X2 Roll and Hard45 are development missions (15 s selection, 45 s confirmation); X2 Full3/Hardstep/Yaw360 and every CF2 mission are held out. Therefore the X2 five-mission geometric mean is descriptive, while the three-mission held-out value in the preceding table is the validation statistic.

| Platform | Family | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Activity |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| x2 | LIF | +0.2% | +28.4% | +33.9% | +1.2% | +0.0% | +14.15% | 23.8% |
| x2 | ALIF | +0.1% | +19.4% | +24.0% | +1.4% | +0.0% | +9.61% | 16.3% |
| x2 | LIFRate | +40.8% | +25.6% | +29.1% | -0.5% | +20.5% | +24.23% | 100.0% |
| x2 | Izhikevich | +0.0% | +16.9% | +18.1% | +1.0% | +0.0% | +7.60% | 13.2% |
| cf2-rotor | LIF | +1.0% | +14.7% | +19.7% | -0.3% | +0.0% | +7.40% | 18.7% |
| cf2-rotor | ALIF | +1.3% | +8.7% | +13.1% | -0.2% | +0.0% | +4.74% | 13.9% |
| cf2-rotor | LIFRate | +20.6% | +12.6% | +14.0% | -0.9% | +9.3% | +11.38% | 100.0% |
| cf2-rotor | Izhikevich | +0.0% | -0.3% | +7.5% | -0.1% | +0.0% | +1.45% | 8.8% |

## Mechanistic reading

- The untuned thresholded families are active on only a few percent of unit-samples and are nearly neutral. This is an operating-point failure, not proof that PES cannot work with them.
- Threshold-aware LIF and ALIF become useful mainly on Full3 and Hard45; they still provide essentially no benefit on the tiny-error Yaw360 case.
- Tuned LIFRate is active essentially continuously and is the strongest conventional alternative. Its persistent continuous feature supports the persistence hypothesis, yet CMG retains the larger cross-mission improvement at comparable residual effort.
- Lowering Izhikevich bias removes the low-error residual floor: Roll and Yaw360 recover the baseline exactly. The cost is inactivity on those missions, so its gains are confined to larger-error trajectories.
- CMG is nearly always active but only about half of its unit-samples are at the activity ceiling; it retains branch-dependent temporal variation. It substantially exceeds both a constant feature and an instantaneous paired feature. The supported mechanism is therefore persistent, bounded, temporally structured activity—not conductance modulation by itself.

## Claim boundary

1. The corrected result can establish whether CMG is a better activity basis under this residual interface; it cannot attribute the advantage specifically to current-dependent conductance because the prior chi ablation remains nearly inactive.
2. A tuned standard family that improves demonstrates feasibility, not equality: it may require a different operating point and may have materially different spike/effort statistics.
3. A no-neuron control that improves confirms that PES and bounded residual learning carry part of the benefit. Only the performance gap between CMG and those controls is evidence associated with CMG temporal state/activation.
4. These simulation conclusions should precede—not be mixed with—the planned controller-family expansion and later hardware evidence.
