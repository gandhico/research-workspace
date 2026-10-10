# Decisive neuron-family and non-neural basis result

All rows use the final rho=3 PD+desired-rate-feedforward baseline, the same six signed channels, W0=[I3,-I3], PES target/update, beta, actuator limits, and saturation-opposition output gate. Only the activity basis changes.

## Skydio X2

| Basis | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Effort | Active | Rail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.342 | 10.043 | 10.606 | 265.912 | 0.200 | 4.547 | 0.000 | 0.0% | 0.0% |
| CMG | 0.074 | 8.812 | 9.081 | 271.354 | 0.117 | 2.848 | 0.045 | 99.9% | 0.1% |
| LIF | 0.342 | 10.092 | 10.382 | 262.934 | 0.200 | 4.521 | 0.034 | 4.0% | 1.3% |
| ALIF | 0.342 | 10.101 | 10.427 | 264.535 | 0.200 | 4.532 | 0.035 | 3.7% | 1.5% |
| LIFRate | 0.340 | 10.110 | 10.453 | 264.046 | 0.200 | 4.526 | 0.038 | 4.4% | 0.3% |
| Izhikevich | 0.525 | 9.511 | 10.228 | 268.786 | 0.347 | 5.441 | 0.070 | 99.9% | 2.8% |
| Constant basis | 0.295 | 8.807 | 9.392 | 271.267 | 0.170 | 4.077 | 0.041 | 100.0% | 0.0% |
| Static paired basis | 0.287 | 8.708 | 9.067 | 268.285 | 0.169 | 4.004 | 0.039 | 100.0% | 0.1% |

Improvements relative to the baseline (positive is better):

- CMG: +37.36% geometric-mean; worst mission -2.05%.
- LIF: +0.55% geometric-mean; worst mission -0.49%.
- ALIF: +0.33% geometric-mean; worst mission -0.59%.
- LIFRate: +0.46% geometric-mean; worst mission -0.67%.
- Izhikevich: -19.66% geometric-mean; worst mission -73.36%.
- Constant basis: +10.32% geometric-mean; worst mission -2.01%.
- Static paired basis: +11.94% geometric-mean; worst mission -0.89%.

## Crazyflie 2.0, 1.5x rotors

| Basis | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Effort | Active | Rail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.563 | 7.058 | 8.633 | 262.588 | 0.084 | 3.764 | 0.000 | 0.0% | 0.0% |
| CMG | 0.226 | 6.661 | 7.980 | 263.187 | 0.067 | 2.917 | 0.020 | 99.9% | 0.1% |
| LIF | 0.563 | 7.078 | 8.647 | 262.554 | 0.084 | 3.767 | 0.013 | 3.4% | 1.1% |
| ALIF | 0.563 | 7.079 | 8.647 | 262.476 | 0.084 | 3.767 | 0.014 | 3.2% | 1.6% |
| LIFRate | 0.561 | 7.086 | 8.653 | 262.734 | 0.084 | 3.766 | 0.015 | 3.7% | 0.7% |
| Izhikevich | 0.560 | 6.960 | 8.552 | 263.803 | 0.112 | 3.966 | 0.025 | 99.9% | 2.1% |
| Constant basis | 0.530 | 6.741 | 8.259 | 263.175 | 0.078 | 3.603 | 0.017 | 100.0% | 0.0% |
| Static paired basis | 0.523 | 6.718 | 8.151 | 264.852 | 0.078 | 3.585 | 0.015 | 100.0% | 0.0% |

Improvements relative to the baseline (positive is better):

- CMG: +22.49% geometric-mean; worst mission -0.23%.
- LIF: -0.09% geometric-mean; worst mission -0.28%.
- ALIF: -0.08% geometric-mean; worst mission -0.29%.
- LIFRate: -0.05% geometric-mean; worst mission -0.39%.
- Izhikevich: -5.37% geometric-mean; worst mission -33.23%.
- Constant basis: +4.28% geometric-mean; worst mission -0.22%.
- Static paired basis: +4.75% geometric-mean; worst mission -0.86%.

## Interpretation contract

- If a conventional family improves after threshold-aware tuning, its original failure was an operating-point mismatch, not an impossibility result.
- If the constant basis matches CMG, persistent PES features explain the result without neuron dynamics.
- If the static paired basis matches CMG but the constant basis does not, input-dependent paired encoding matters while temporal neuron dynamics do not.
- Only a consistent CMG advantage over both controls supports a dynamics-specific CMG claim.
- These controls retain PES and the residual interface; they test the basis, not whether learning itself is needed.

## Automatically computed comparison

CMG geometric-mean improvements: X2 +37.36%, CF2 +22.49%.
Constant-basis improvements: X2 +10.32%, CF2 +4.28%.
Static-paired improvements: X2 +11.94%, CF2 +4.75%.

The scientific conclusion must be written after checking the full mission pattern and effort/rail metrics; a geometric mean alone is not sufficient.
