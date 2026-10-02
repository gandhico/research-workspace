# Stage 3 local plant-model identification report

Date: 2026-07-12 (America/Denver)

## Scope

These models apply only near the frozen Stage-2 operating condition: EHEKATL
BWB G33 scale model, X-Plane 12.4.3-r2, 14 lb, approximately 1700 m and 39
KIAS, Manual/Clear weather, no failures, and the recorded artificial-stability
configuration. They are local, short-horizon models for offline controller
design. They do not establish global aircraft dynamics or recovery capability.

The structure and three-sample input delay were selected using only the two
training runs per axis. The two held-out runs per axis were opened only after
the structure, trim convention, states, inputs, delay, and fit window were
frozen. Exact machine-readable results are in `configs/stage3_models.json`.

## Frozen model form

For angle perturbation `eta`, body-rate perturbation `omega`, and realized
total-control perturbation `u`:

```text
eta_dot   = omega
omega_dot = a_eta eta + a_omega omega + b u(t - 0.3 s)
```

Units are degrees, degrees/second, and normalized X-Plane total-control ratio.
Each run is referenced to its measured 0--10 second pre-excitation mean. The
fit uses the 10--50 second excitation interval at nominal 10 Hz.

## Identified continuous-time matrices

Roll, with state `[roll_deg, p_deg_s]` and input `total_roll_ratio`:

```text
A = [[ 0,          1        ],
     [-1.799965,  -0.035987]]
B = [[   0       ],
     [-286.518155]]
```

Coefficient standard errors are `0.220518`, `0.082407`, and `9.357965`.
Continuous poles are `-0.017994 +/- 1.341507j` rad/s. Controllability rank is
2/2; regression condition number is 127.39.

Pitch, with state `[pitch_deg, q_deg_s]` and input `total_pitch_ratio`:

```text
A = [[ 0,          1        ],
     [-4.699647,  -0.202786]]
B = [[   0       ],
     [-210.642895]]
```

Coefficient standard errors are `0.135430`, `0.079855`, and `5.559480`.
Continuous poles are `-0.101393 +/- 2.165495j` rad/s. Controllability rank is
2/2; regression condition number is 72.93.

The negative input coefficients are the measured sign convention for the
realized X-Plane total-control ratios. They must not be reversed during LQR
implementation.

## Independent prediction results

Each cell is angle RMSE in degrees / rate RMSE in degrees per second. Horizons
are reset from the measured state and use the recorded realized input.

| Axis/data | 0.1 s | 0.5 s | 1.0 s | 2.0 s |
|---|---:|---:|---:|---:|
| Roll training 1 | .00149/.01354 | .01427/.05473 | .04135/.06758 | .07255/.08500 |
| Roll training 2 | .00164/.01368 | .01551/.05253 | .04009/.05729 | .05876/.06924 |
| Roll validation 1 | .00166/.01360 | .01593/.05149 | .03946/.05714 | .05840/.06910 |
| Roll validation 2 | .00187/.01312 | .01600/.04944 | .03860/.05622 | .05808/.06874 |
| Pitch training 1 | .00159/.01482 | .01448/.05716 | .03846/.06413 | .04341/.09254 |
| Pitch training 2 | .00176/.01479 | .01602/.05257 | .03776/.05987 | .04019/.09218 |
| Pitch validation 1 | .00207/.01476 | .01589/.05392 | .03893/.05980 | .04096/.09669 |
| Pitch validation 2 | .00170/.01503 | .01585/.05362 | .03723/.06201 | .04010/.09179 |

Held-out performance closely matches training performance and does not show
training-only reproduction. This passes independent short-horizon prediction
validation for the declared local envelope.

## Residual and uncertainty limitations

Normalized rate-acceleration residual RMSE is 0.501 for roll and 0.511 for
pitch. Lag-1 residual correlations are 0.823 and 0.777; residuals are therefore
not white. Residual/input correlation is -0.012 for roll and -0.232 for pitch.
The rate-damping coefficients also have substantial relative uncertainty,
especially roll damping whose standard-error interval includes zero.

Consequences:

- Treat the models as low-order deterministic local models with colored
  unmodeled dynamics, not complete stochastic models.
- Stage 4 must sweep coefficient uncertainty, especially damping and input
  effectiveness, and reject gains that depend on nominal damping.
- Offline LQR replay must use the measured delay, magnitude/slew limits, and
  held-out logs.
- No gain from these matrices is authorized for X-Plane until Stage 4 passes.

## Stage decision

Stage 3 passes for local short-horizon controller synthesis because the frozen
models are controllable, have recorded uncertainty and residual diagnostics,
and reproduce both independent held-out runs at training-comparable error.
The colored residuals limit the claim and become mandatory robustness cases in
Stage 4; they are not concealed as white measurement noise.
