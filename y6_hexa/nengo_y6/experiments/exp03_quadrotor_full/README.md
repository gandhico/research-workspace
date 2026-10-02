# Exp 03 — Full Quadrotor (Phase 4, the full system)

The capstone of Paper 1's baseline: the **complete 12-state quadrotor** under the full cascaded
controller, classical vs. neuromorphic, tracking a 50 s 3-D trajectory.

## Model & controller (faithful port of Victor's baseline)
- Plant: `src/models/quadrotor.py` — García-Carrillo eqs. 2.30–2.35 (Springer 2013), the exact
  model in `Quad_control_2026.py`. State `[x,ẋ,y,ẏ,z,ż,ψ,ψ̇,θ,θ̇,φ,φ̇]`.
- Classical: `src/controllers_classical/quadrotor_pd.py` — Victor's exact gains and cascade.
- NEF: `src/controllers_nengo/quadrotor_nef.py` — six PD laws in neuron populations; the three
  nonlinear inversions (`u`, `θ_d`, `φ_d`) in nodes. Architecture:
  `paper/diagrams/blockdiagram_quad_architecture.pdf`.
- Trajectory: x,y slow sinusoid `sin(0.1t)`, z ramp→1→ramp→0.5 (Victor's reference); 50 s.

## Results (real runs; tracking, t > 3 s)

| controller | x RMSE [m] | y RMSE [m] | z RMSE [m] | ctrl energy ∫u² | max tilt [°] | stable |
|---|---|---|---|---|---|---|
| classical | 0.0046 | 0.0025 | 0.0056 | 3662.1 | 2.84 | ✅ |
| NEF rate | 0.0046 | 0.0073 | 0.0056 | 3662.2 | 3.17 | ✅ |
| **NEF spiking (LIF)** | 0.0052 | 0.0029 | 0.0051 | 3662.2 | 3.05 | ✅ |

Source of truth: `results/summaries/exp03_quad_metrics.csv`; plots `exp03_quad_tracking.png`,
`exp03_quad_path.png`. Sim cost: NEF rate 13 s, NEF spiking 26 s wall for 50 s sim.

## Interpretation
**The full spiking neuromorphic quadrotor controller matches the classical baseline to within
~1.5 mm RMSE on every axis** over a 50 s 3-D trajectory (x 5.2 vs 4.6 mm, y 2.9 vs 2.5 mm,
z 5.1 vs 5.6 mm), at **identical control energy** and comparable peak tilt, and it is stable
throughout. This is the headline Paper-1 result: a population-coded NEF controller driving the
*entire* underactuated 12-state vehicle is performance-equivalent to the conventional cascaded
PD controller. It validates the whole methodology (Phases 2→4) before we evolve the airframe to
the coaxial trirotor (Phase 5), where the model and allocation — not the controller recipe —
are what change.

## Run
```bash
../../.venv/Scripts/python.exe run_exp03.py
```
