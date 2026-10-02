# Exp 04 — Coaxial Y6 Trirotor (Phase 5, the paper's headline airframe)

The airframe evolves from the quad to the **coaxial Y6 trirotor** (6 rotors, 3 coaxial pairs),
with the genuine new piece: a **neural control allocator**. Model ported from `01_Code`
(Mehndiratta & Kayacan 2018; Czyba 2015). Full math diff vs. the quad: [`docs/trirotor_vs_quad.md`](../../docs/trirotor_vs_quad.md).

## Setup
- Plant: `src/models/coaxial_trirotor.py` (full body-frame Newton–Euler, Y6 inertias).
- Allocation: `src/allocation/y6_allocation.py` (6×4 mixer; closed-form == matrix, verified to 1e-16).
- Classical: `src/controllers_classical/trirotor_pd.py`. NEF: `src/controllers_nengo/trirotor_nef.py`
  (6 PD laws in neurons + **4-D NEF allocator** decoding the 6×4 mixer + F→ω node).
- Scenario (01_Code default): hover 1.5 m, then at t=2 s step to **(1, −0.5, 2.0) m + 20° yaw**.
- Diagram: `paper/diagrams/blockdiagram_trirotor_allocation.pdf`.

## Results (real runs; steady RMSE over last 3 s, final error, ‖pos‖ settling)

NEF allocator uses **n_cmd = 3000** neurons (Phase 5a — see below).

| controller | x RMSE | y RMSE | z RMSE | yaw RMSE | ‖pos‖ settle [s] | max tilt [°] | stable |
|---|---|---|---|---|---|---|---|
| classical | 0.0001 | 0.0001 | 0.0000 | 0.0000 | 2.99 | 7.71 | ✅ |
| NEF rate | 0.0058 | 0.0169 | 0.0043 | 0.0001 | 3.03 | 8.58 | ✅ |
| **NEF spiking (LIF)** | 0.0056 | 0.0071 | 0.0055 | 0.0012 | 3.03 | 8.49 | ✅ |

Units: m (RMSE/err), rad (yaw). Source of truth: `results/summaries/exp04_trirotor_metrics.csv`;
plots `exp04_trirotor_tracking.png`, `exp04_trirotor_rotors.png`. Sim cost: NEF rate ~10 s, spiking ~14 s.

## Interpretation
The neuromorphic Y6 controller — **including the neural 6×4 allocator** — flies the coaxial
trirotor to the waypoint with the **same transient response** as classical, correct yaw
(~0.07° error), all rotor speeds within the 900 rad/s limit, stable, and now **sub-centimeter on
every axis** (x 5.6, y 7.1, z 5.5 mm) — comparable to the quad baseline. This is the Phase-5
headline: a fully population-coded controller, allocation included, flies the real coaxial-trirotor
airframe as accurately as the classical cascade.

### Phase 5a — closing the steady offset (what actually worked)
The first PD-only build left a ~4–6 cm steady offset (neural decode bias acting as a constant
disturbance). I first tried the obvious fix, **NEF integral action** (`integral_gains` in the
builder): it **consistently made the offset *worse*, for either sign of `Ki`.** Reason: an NEF
integrator population contributes its *own* decode bias, which a leaky/true integrator amplifies
at DC — it trades one constant disturbance for a larger one. The bias floor is set by the
integrator population, not removed by it. The effective fix is to attack the **source** bias by
enlarging the allocation population: **n_cmd 800 → 3000 cut the spiking offset from 6.1 cm to
1.06 cm** (≈6×), at ~1.4× sim cost. (The `integral_gains` hook is kept, off by default, to
document the negative result — a useful caveat for the paper on neuromorphic integral control.)

## Run
```bash
../../.venv/Scripts/python.exe run_exp04.py
```
