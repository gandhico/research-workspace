# Results Summary — Phases 2–4 (classical vs. neuromorphic)

Consolidated, **real-run** benchmark across the staged build, from a 1-DOF anchor to the full
12-state quadrotor. Every number traces to a runner under `experiments/` and a CSV under
`results/summaries/`. Plant of record: Victor's García-Carrillo quad (m = 0.9 kg).

## The progression

| Phase | Experiment | System | Controllers compared | Headline |
|---|---|---|---|---|
| 2 | exp01 | 1-DOF altitude | classical, NEF rate, NEF spiking | NEF ≈ classical within a few % |
| 3 | exp02 | roll, pitch, yaw, x/y cascades | classical vs NEF (LIF) | equiv. on attitude + x; y-cascade overshoots more |
| 4 | exp03 | **full 12-state quad** | classical, NEF rate, NEF spiking | **spiking NEF matches classical to ~1.5 mm RMSE** |
| 5 | exp04 | **coaxial Y6 trirotor** | classical, NEF rate, NEF spiking | **neural 6×4 allocator** flies it **sub-cm** (n_cmd=3000); NEF integral *hurts* (own-bias) |

## Headline numbers

**Altitude (exp01, 1 m step):** classical vs NEF-spiking — overshoot 2.98 % vs 2.67 %,
settling 1.94 s vs 1.80 s, SSE < 1 mm; +9 % control effort from spike ripple.

**Subsystems (exp02, steps):** attitude axes NEF≈classical (overshoot 4.6 %, = ζ=0.7 theory);
x-cascade equivalent; **y-cascade NEF overshoot 25 % vs 11 %** — neural latency in the fast
nested loop (the one honest degradation).

**Full quad (exp03, 50 s 3-D trajectory):** tracking RMSE per axis —

| axis | classical | NEF spiking |
|---|---|---|
| x | 4.6 mm | 5.2 mm |
| y | 2.5 mm | 2.9 mm |
| z | 5.6 mm | 5.1 mm |

identical control energy (∫u² ≈ 3662), all stable.

## What the neuromorphic controller contributes (honest read)
1. **Equivalence, not superiority.** Across 1-DOF, single-axis, cascaded, and full-system, the
   NEF/spiking controller reproduces the classical PD response — it does **not** beat it. The
   contribution is *feasibility + fidelity* of a population-coded controller for the whole vehicle.
2. **Where the cost shows.** Spiking adds high-frequency ripple (≈ +9 % control effort at 1-DOF)
   and, in **fast nested loops** (y-cascade), measurable overshoot growth. Single loops and the
   full trajectory absorb it to sub-cm accuracy.
3. **Pipeline is trustworthy.** Classical metrics match 2nd-order theory at every stage
   (overshoot/rise/settling), so the comparisons are sound.

## Methodology (reused at every stage)
shared plant model → classical PD → NEF equivalent (error+rate ensembles → PD-decoded command;
nonlinear inversions in nodes) → real run → CSV + plots + metrics → block diagram. The NEF recipe
is identical from 1-DOF to 12-state; only the plant and the number of channels grow.

**Coaxial Y6 trirotor (exp04, waypoint + 20° yaw):** classical reaches the waypoint exactly;
the NEF controller — **including the neural 6×4 allocator** — matches the transient and yaw and
now tracks **sub-centimeter on every axis** (spiking: x 5.6, y 7.1, z 5.5 mm; yaw 0.07°), stable,
rotors within limits. **Phase 5a finding:** the PD-only build left a 4–6 cm offset from neural
decode bias; **NEF integral action made it worse** (the integrator injects its own decode bias,
amplified at DC), so the fix was to attack the source — enlarging the allocation population
(n_cmd 800→3000 cut the offset ~6×). Math diff: `docs/trirotor_vs_quad.md`.

## Reproduce

```bash
& "c:\02_Research\00_Code_Ecosystem\neuromorphic-robotics-control\.venv\Scripts\python.exe" experiments\exp01_altitude_1dof\run_exp01.py
.venv/Scripts/python.exe
python experiments/exp01_altitude_1dof/run_exp01.py
python experiments/exp01_altitude_1dof/run_exp01.py
python experiments/exp02_attitude_subsystems/run_exp02.py
python experiments/exp03_quadrotor_full/run_exp03.py
python experiments/exp04_coaxial_trirotor/run_exp04.py
```

## Next — Phase 6 (paper assembly)
Distill Phases 2–5 into `paper/main.tex` (ComRob, IEEE two-column, ~6 pages, English): quad
baseline + coaxial-trirotor headline, classical-vs-NEF benchmark, the compiled TikZ diagrams and
result plots. The neuromorphic-integral negative result (Phase 5a) is a nice discussion point on
the limits of NEF integral control.
