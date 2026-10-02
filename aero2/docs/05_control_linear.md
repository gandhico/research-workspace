# 05 — Linear Control (Ref 3)

Code: `aero2/control/linear/`. Gains: `config.gains`. All controllers use the
**actual measured Δt** (`Backend.dt_actual()`), clip to ±24 V, and (PD) share the
second-order derivative filter (`ω_n=100, ζ=1`).

## Shared derivative filter (Ref 3, Eqs. 28-30) — `control.filters.SecondOrderDerivative`
Exact replica of the original `SimulinkSecondOrderDerivative`. Explicit Euler with
measured Δt; `filtered_rate = ω_n·x2`. **Read the rate, compute the command, THEN
`update(angle, dt)`** — this read-then-update ordering and the measured-Δt rule are
the project's headline lesson (the PD only became the strongest controller after this).

## PD baseline (Ref 3, Eqs. 39-41) — **done** — `control.linear.pd.PD2DOF`
```
e_θ = θ_ref − θ,  e_ψ = ψ_ref − ψ
u_p = Kp_θ·e_θ − Kd_θ·θ̇_f      (θ̇_f, ψ̇_f = filtered rates)
u_y = Kp_ψ·e_ψ − Kd_ψ·ψ̇_f      then clip ±24 V
```
Gains (`config.gains`): `Kp_θ=116.2420, Kd_θ=99.6990, Kp_ψ=35.8626, Kd_ψ=38.0289`.
No integral term (no anti-windup). Returns the virtual `u=[u_p,u_y]`; motor mixing
is an IO concern (Phase 4/6), not in the controller.

**Offline validation:** on `helicopter_2dof` (offline, 200 Hz, 40 s square-wave),
PD gives pitch RMS **0.170**, yaw RMS **0.370** rad — close to the hardware Table IV
PD baseline (0.1544 / 0.4215) and with **yaw the weaker axis**, reproducing the
project's honest result. Run: `python runners/run_control.py` (or `--config
configs/experiments/helicopter_offline_pd_tracking.yaml`).

## LQR / LQG / Linear MPC — **next (Phase 7)**
Ground-truthed from `aero2_minimal_control/src/controllers/linear_2dof.py`:
- **LQR** (Eqs. 43-44): CARE on `(A,B)` with `Q=diag(180,4,60,2)`, `R=diag(.30,.30)`;
  `u = clip(u_ff − K(x−x_r))`, `u_ff` by least squares for zero accel at ref.
- **LQG** (Eq. 45): LQR gain + Luenberger observer (CARE on `(Aᵀ,Cᵀ)`, process
  `diag(2e-3,3e-2,2e-3,3e-2)`, meas `diag(6e-4,8e-4)`), Euler-integrated with measured Δt.
- **Linear MPC** (Eqs. 46-47): unconstrained finite-horizon **first-move** gain `K0`
  + final clip (NOT an online QP). Code tuning `Q=diag(220,3,90,1.5)`, `R=diag(.45,.45)`,
  horizon 120 @ 0.02 s.

## What works / what doesn't
PD tracks pitch well and reproduces the hardware ranking offline; yaw remains the
weaker axis (kept visible). LQR/LQG/MPC are expected to be more conservative
(under-drive vs PD), per Table IV — to be confirmed once implemented.
