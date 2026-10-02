# Gate-Gain Sweep + Adaptive-vs-Plain Probe — 2026-07-03

Fills Paper 1 Table II (`paper/main2.tex`, `tab:gate_sweep`) and closes the
"intermediate G differentiates HyperLIF from Adaptive HyperLIF" open question.

Fixed config: gate mode, `--direct-scale control`, `--blend 0.50`, Hard45,
`--sim-time 45`, dt 0.5 ms, seed 1. Baselines: X2 classical qerr 0.2941, CF2 0.2854.

## CF2 (paper Table II platform)
| G | qerr_mean | qerr_max | score | Δqerr |
|---:|---:|---:|---:|---:|
| 1 | 0.3160 | 0.6321 | 0.3263 | −10.7% |
| 10 | 0.3160 | 0.6321 | 0.3263 | −10.7% |
| 100 | 0.3022 | 0.5943 | 0.3121 | −5.9% |
| 1000 | 0.2933 | 0.5767 | 0.3031 | −2.7% |
| 10000 | 0.2855 | 0.5628 | 0.2951 | −0.0% |
| **100000** | **0.2820** | **0.5586** | **0.2916** | **+1.2%** |

## Skydio X2
| G | qerr_mean | score | Δqerr |
|---:|---:|---:|---:|
| 1 | 0.3453 | 0.3497 | −17.4% |
| 30 | 0.3431 | 0.3475 | −16.7% |
| 100 | 0.2992 | 0.3034 | −1.7% |
| 300 | 0.2943 | 0.2984 | −0.1% |
| 1000 | 0.2887 | 0.2927 | +1.8% |
| **100000** | **0.2753** | **0.2807** | **+6.4%** |

## Key findings
1. **Monotonic in G.** The gate residual is *harmful* at low G (graded gate →
   poorly-signed pair-coded torque) and only helps once G saturates the gate to
   `{0,1}`. Crossover: X2 ≈ G=300, CF2 ≈ G=10^4.
2. **Adaptive HyperLIF ≡ HyperLIF.** Identical to 5 s.f. at every G on both
   platforms. `adaptive_soft_probe.*` shows this survives softening α (50→8) and
   raising gain_scaling (0→1000): mean-gate change < 5e-4, Δqerr = 0. The adaptive
   conductance enters only the membrane update; the residual decodes the gate `r`,
   whose sharp sigmoid target is insensitive to that perturbation.
3. **Reproduces published numbers** exactly (X2 +6.38%, CF2 +1.20% at G=1e5).

## Reproduce
```
python gate_gain_sweep.py --quad skydio_x2          --mission hard45 --sim-time 45 --out sweep_x2_hard45.json
python gate_gain_sweep.py --quad bitcraze_crazyflie_2 --mission hard45 --sim-time 45 \
       --gains 1,10,100,1000,10000,100000 --out sweep_cf2_hard45.json
python adaptive_soft_probe.py --sim-time 20 --gg 100
```
