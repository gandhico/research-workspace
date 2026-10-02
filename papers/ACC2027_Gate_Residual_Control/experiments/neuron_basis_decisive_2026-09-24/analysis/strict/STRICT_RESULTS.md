# Decisive neuron-family and non-neural basis result

All rows use the final rho=3 PD+desired-rate-feedforward baseline, the same six signed channels, W0=[I3,-I3], PES target/update, beta, actuator limits, and saturation-opposition output gate. Only the activity basis changes.

## Skydio X2

| Basis | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Effort | Active | Rail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.342 | 10.085 | 10.537 | 265.912 | 0.200 | 4.544 | 0.000 | 0.0% | 0.0% |
| CMG | 0.074 | 8.834 | 9.080 | 271.354 | 0.117 | 2.850 | 0.046 | 99.9% | 0.1% |
| LIF | 0.342 | 10.116 | 10.322 | 262.934 | 0.200 | 4.518 | 0.034 | 4.0% | 1.3% |
| ALIF | 0.342 | 10.116 | 10.367 | 264.535 | 0.200 | 4.528 | 0.036 | 3.7% | 1.5% |
| LIFRate | 0.340 | 10.142 | 10.398 | 264.046 | 0.200 | 4.524 | 0.038 | 4.4% | 0.3% |
| Izhikevich | 0.507 | 9.499 | 10.063 | 268.786 | 0.353 | 5.401 | 0.070 | 99.9% | 2.8% |
| Constant basis | 0.295 | 8.854 | 9.314 | 271.267 | 0.170 | 4.075 | 0.042 | 100.0% | 0.0% |
| Static paired basis | 0.287 | 8.755 | 9.029 | 268.285 | 0.169 | 4.005 | 0.039 | 100.0% | 0.1% |

Improvements relative to the baseline (positive is better):

- CMG: +37.30% geometric-mean; worst mission -2.05%.
- LIF: +0.57% geometric-mean; worst mission -0.31%.
- ALIF: +0.37% geometric-mean; worst mission -0.31%.
- LIFRate: +0.45% geometric-mean; worst mission -0.56%.
- Izhikevich: -18.85% geometric-mean; worst mission -76.27%.
- Constant basis: +10.34% geometric-mean; worst mission -2.01%.
- Static paired basis: +11.88% geometric-mean; worst mission -0.89%.

## Crazyflie 2.0, 1.5x rotors

| Basis | Roll | Full3 | Hard45 | Hardstep | Yaw360 | Geo. mean | Effort | Active | Rail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 0.563 | 7.056 | 8.653 | 262.588 | 0.084 | 3.765 | 0.000 | 0.0% | 0.0% |
| CMG | 0.226 | 6.675 | 8.018 | 263.187 | 0.067 | 2.921 | 0.020 | 99.9% | 0.1% |
| LIF | 0.563 | 7.074 | 8.665 | 262.554 | 0.084 | 3.768 | 0.013 | 3.4% | 1.1% |
| ALIF | 0.563 | 7.074 | 8.665 | 262.476 | 0.084 | 3.768 | 0.014 | 3.2% | 1.6% |
| LIFRate | 0.561 | 7.081 | 8.670 | 262.734 | 0.084 | 3.767 | 0.015 | 3.7% | 0.7% |
| Izhikevich | 0.560 | 6.963 | 8.581 | 263.803 | 0.112 | 3.969 | 0.025 | 99.9% | 2.1% |
| Constant basis | 0.530 | 6.741 | 8.272 | 263.175 | 0.078 | 3.604 | 0.017 | 100.0% | 0.0% |
| Static paired basis | 0.523 | 6.716 | 8.168 | 264.852 | 0.078 | 3.586 | 0.015 | 100.0% | 0.0% |

Improvements relative to the baseline (positive is better):

- CMG: +22.42% geometric-mean; worst mission -0.23%.
- LIF: -0.08% geometric-mean; worst mission -0.25%.
- ALIF: -0.07% geometric-mean; worst mission -0.25%.
- LIFRate: -0.03% geometric-mean; worst mission -0.35%.
- Izhikevich: -5.41% geometric-mean; worst mission -33.26%.
- Constant basis: +4.29% geometric-mean; worst mission -0.22%.
- Static paired basis: +4.75% geometric-mean; worst mission -0.86%.

## Interpretation contract

- If a conventional family improves after threshold-aware tuning, its original failure was an operating-point mismatch, not an impossibility result.
- If the constant basis matches CMG, persistent PES features explain the result without neuron dynamics.
- If the static paired basis matches CMG but the constant basis does not, input-dependent paired encoding matters while temporal neuron dynamics do not.
- Only a consistent CMG advantage over both controls supports a dynamics-specific CMG claim.
- These controls retain PES and the residual interface; they test the basis, not whether learning itself is needed.

## Automatically computed comparison

CMG geometric-mean improvements: X2 +37.30%, CF2 +22.42%.
Constant-basis improvements: X2 +10.34%, CF2 +4.29%.
Static-paired improvements: X2 +11.88%, CF2 +4.75%.

The scientific conclusion must be written after checking the full mission pattern and effort/rail metrics; a geometric mean alone is not sufficient.
