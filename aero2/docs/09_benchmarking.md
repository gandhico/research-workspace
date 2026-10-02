# 09 — Benchmarking (targets to reproduce)

Code lands in Phase 11 (`aero2/benchmarking/`); the numbers below are the
ground-truth targets carried verbatim from the papers. **Do not alter them.**

## Identification — DARX models (Ref 3, Table II)
| Case | Output | Ts [s] | Order | Fit [%] |
|---|---|---|---|---|
| Pitch SISO | θ | 0.005571 | na=1, nb=3 | 98.231 |
| Yaw-rate SISO | ω_z,c | 0.005581 | na=2, nb=2, nk=2 | 91.431 |
| Coupled pitch | θ | 0.011272 | na=1, nb=1 | 99.263 |
| Coupled yaw-rate | ω_z,c | 0.005610 | na=3, nb=4, nk=2 | 87.892 |

## Validation — one-step vs free-run (Ref 2, Table I)
| Case | One-step fit [%] | Free-run fit [%] |
|---|---|---|
| Pitch SISO | 97.31 | very poor |
| Yaw SISO | 87.02 | 16.93 |
| Coupled pitch | 99.14 | very poor |
| Coupled yaw | 90.99 | poor |

## Hardware controller benchmark (Ref 3, Table IV)
Metrics: pitch/yaw RMS error [rad], tail MAE [rad], mean realized loop rate [Hz],
pitch saturation fraction.

| Controller | Pitch RMS | Yaw RMS | Tail pitch MAE | Tail yaw MAE | Mean fs | Pitch sat |
|---|---|---|---|---|---|---|
| **PD baseline** | **0.1544** | **0.4215** | 0.0263 | **0.4003** | 382.9 | 0.058 |
| LQR | 0.3337 | 0.6509 | 0.2571 | 0.6668 | 382.0 | 0 |
| LQG | 0.3074 | 0.7706 | 0.2851 | 0.7286 | 380.8 | 0 |
| Linear MPC | 0.3724 | 0.6782 | 0.3379 | 0.6793 | 381.9 | 0 |
| Backstepping | 0.1818 | 0.7778 | 0.0518 | 0.7842 | 383.2 | 0.005 |
| Backstepping yawboost | 0.1914 | 0.6044 | 0.0583 | 0.6246 | 384.1 | 0.011 |
| SMC | 0.1941 | 0.7586 | **0.0110** | 0.8328 | 381.3 | 0.103 |
| SMC yawboost | 0.1922 | 0.7413 | 0.0139 | 0.8627 | 380.4 | 0.113 |
| NMPC fast | 0.1970 | 0.7637 | 0.0803 | 0.7892 | 303.0 | 0.786 |
| NMPC realtime | 0.1842 | 0.7970 | 0.0582 | 0.8107 | 304.1 | 0.836 |

### Conclusions to preserve (Ref 3)
1. **PD baseline best overall** (lowest pitch & yaw RMS).
2. **SMC best nonlinear tail-pitch** (0.0110).
3. Yawboost increases yaw motion but does not fix yaw tracking → not just an
   authority problem (sign/mapping/phase/coupling suspect).
4. NMPC is benchmarkable but **not competitive** (~303 Hz, pitch-sat 0.79/0.84).
5. Mean realized loop ≈ 380 Hz despite a commanded 500 Hz → loops run on measured Δt.

`compare.py` (P11) regenerates the linear-vs-nonlinear waveform + tail-bar figures
and this table.
