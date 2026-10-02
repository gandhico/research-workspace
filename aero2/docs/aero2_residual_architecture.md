# Aero2 Residual Augmentation — Architecture (2026-06-14)

Port of the hardware-validated Qube/Servo-Pendulum gate-state residual to Quanser Aero 2.
The classical Aero2 controller stays the **stability anchor**; a bounded HyperLIF /
Adaptive HyperLIF gate-state residual is optional, demand-triggered assistance.

## 1. Where it plugs in (reuses the clean controller, does not bypass it)

Per control tick (500 Hz), the clean M8 chain is:
```
sample = io.read()                      # theta(pitch), psi(yaw), rates, gyro, motor I
x = [theta, theta_rate_f, psi, psi_rate_f]
u_pitch, u_yaw = controller.step(x, theta_ref, psi_ref, dt)     # VIRTUAL pitch/yaw commands
u0_raw, u1_raw = output_mapping(mode, u_pitch, u_yaw)           # -> motor channels
u0, u1 = clamp(u0_raw, +/-Vlim), clamp(u1_raw, +/-Vlim)
io.write(u0, u1)
```
The residual is injected at the **virtual pitch/yaw level** and re-mapped through the same
`output_mapping`, so the controller structure is preserved:
```
u_pitch_total = u_pitch + pitch_residual_applied
u_yaw_total   = u_yaw   + yaw_residual_applied
u0, u1 = clamp(output_mapping(mode, u_pitch_total, u_yaw_total), +/-Vlim)
io.write(u0, u1)
```
(`motor_pair` channel instead adds left/right residual directly to the mapped channels.)

## 2. Residual command
```
u_total = clip( u_classical + sign * scale * g_d(t) * Δu(z(t)) ,  ±residual_max_voltage per channel )
motor   = clip( u_classical_channels + residual_channels , ±voltage_limit )
```
- Residual applied **only during active control** (`control_mode == "active"`).
- Capped to `±residual_max_voltage` per channel, then the **total** is clipped to the motor
  voltage limit (24 V HIL / 15 V PAL).

## 3. Demand score (drives the gate)
Normalized, in [0,1], from the controller's own signals (`aero2_residual/residual_gate.py`):
```
pitch_demand = clip(0.5·|e_pitch|/E_p + 0.3·|pitch_rate|/R + 0.2·sat, 0,1)
yaw_demand   = clip(0.5·|e_yaw|/E_y   + 0.3·|yaw_rate|/R   + 0.2·sat, 0,1)
combined     = max(pitch_demand, yaw_demand)         # either-channel transient opens the gate
sat          = max(|u_pitch|,|u_yaw|) / voltage_limit
```
`E_p = 15°, E_y = 30°, R = 3 rad/s` (fixed refs so the equilibrium mission, ref = 0, still normalizes).

## 4. Gate neuron (identical internals to the validated Qube build)
Demand-driven leaky membrane → HyperLIF gate `r ∈ [0,1]` → Eq.7 conductance readout → events.
`τ=50 ms, τ_r=20 ms, α=8, γ=0 (clean release), g_base=20, β=5 (Adaptive)/0 (HyperLIF)`.
The candidate per virtual channel:
```
pitch_cand = residual_max_voltage · tanh(k_p·e_pitch) · gate · combined_demand
yaw_cand   = residual_max_voltage · tanh(k_y·e_yaw)   · gate · combined_demand
```
bounded by construction (`|tanh|,gate,demand ≤ 1`).

## 5. Modes (`--residual-mode`) and channels (`--residual-channel`)
| Mode | Applied | Purpose |
|---|---|---|
| none | 0 | classical only |
| shadow_gate | 0 (logged) | verify timing before applying |
| gate | `sign·scale·candidate` | demand-triggered assist (the method) |
| always_on | `sign·scale·Vmax·tanh(k·e)` (ungated) | tests whether selectivity matters |
| shuffled_gate | candidate with **time-misaligned** gate/demand | tests whether timing matters |

Channels: `pitch` (default first applied), `yaw`, `pitch_yaw`, `motor_pair`.

## 6. Hypothesis (to validate per mission)
Low demand → residual dormant; pitch/yaw transient or manual perturbation → demand rises,
gate opens, residual activates; recovery → residual returns to ~0. Gate should match
always_on tracking at far lower residual energy/activity, and beat shuffled_gate in
high-demand bins (timing). See `aero2_lab_test_plan.md`.
