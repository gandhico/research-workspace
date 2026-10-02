# Exp 02 — Attitude & Position Subsystems (Phase 3)

Extends the Phase-2 methodology to Victor's decoupled quad subsystems, one channel at a time.

## Plants
- **Attitude axis** (roll φ, pitch θ, yaw ψ): double integrator `a'' = τ` (inertia folded
  into gains, as in `Quad_control_2026.py`).
- **Position→attitude cascade** (x via pitch, y via roll): `p'' = s·g·tan(a)`, `a'' = τ`,
  with `s = +1` (x) / `−1` (y). The outer loop emits a **virtual tilt command**
  `a_des = atan2(s·u_pos, g)`; the inner loop tracks it. Time-scale separation:
  inner ωₙ = 6 ≫ outer ωₙ ≈ 1.3.

Gains designed for clean step responses (ζ ≈ 0.7); Victor's originals noted in
`src/controllers_classical/subsystem_pd.py`.

## Block diagrams
- Single-axis attitude = the Phase-2 NEF pattern (`paper/diagrams/blockdiagram_nef_altitude.pdf`, minus gravity FF).
- Cascade (outer/inner + virtual command): `paper/diagrams/blockdiagram_cascade.pdf`.

## Results (real runs; steps at t = 1 s)

| subsystem · controller | rise [s] | settling [s] | overshoot [%] | SSE | IAE | tracking RMSE |
|---|---|---|---|---|---|---|
| roll · classical | 0.354 | 0.994 | 4.60 | ~0 | 0.053 | 0.0375 |
| roll · **NEF** | 0.306 | 0.925 | 4.90 | −0.001 | 0.056 | 0.0383 |
| pitch · classical | 0.354 | 0.994 | 4.60 | ~0 | 0.053 | 0.0375 |
| pitch · **NEF** | 0.306 | 0.925 | 4.90 | −0.001 | 0.056 | 0.0383 |
| yaw · classical | 0.802 | 2.258 | 4.63 | ~0 | 0.304 | 0.1412 |
| yaw · **NEF** | 0.766 | 2.191 | 4.22 | −0.001 | 0.304 | 0.1425 |
| x-pos · classical | 1.433 | 2.682 | 0.12 | ~0 | 2.512 | 0.585 |
| x-pos · **NEF** | 1.367 | 2.681 | 0.00 | 0.002 | 2.538 | 0.590 |
| y-pos · classical | 0.761 | 3.090 | 11.39 | ~0 | 1.943 | 0.512 |
| y-pos · **NEF** | 0.691 | 3.428 | **24.997** | 0.003 | 2.275 | 0.531 |

All 10 controllers stable. Source of truth: `results/summaries/exp02_metrics.csv`;
plots `results/plots/exp02_attitude.png`, `exp02_cascade.png`.

**Theory check:** attitude overshoot 4.6 % = analytic value for ζ = 0.7; settling 0.99 s ≈ 4/(ζωₙ).

## Interpretation
On the **single-axis attitude** loops (roll, pitch, yaw) and the **gentle x-cascade**, the spiking
NEF controller is **performance-equivalent** to classical (within a few % on every metric). The
one honest exception is the **more aggressive y-cascade** (outer ωₙ = 1.73): the extra neural
latency in the *nested* loop roughly doubles overshoot (11 % → 25 %) and lengthens settling
(3.09 → 3.43 s), though it remains stable with sub-cm SSE. This localizes *where* the
neuromorphic cost appears — fast nested loops — and motivates either mild outer-loop detuning
or integral action for the trirotor. The cascade plots also confirm the **virtual-command**
methodology: position error → desired tilt `a_des` → angle tracking.

## Run
```bash
../../.venv/Scripts/python.exe run_exp02.py
```
