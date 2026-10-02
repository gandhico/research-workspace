# Aero2 Residual — Math ↔ Code Match (2026-06-14)

New code lives in `04_Aero2_SNNs`; the working hardware control is **reused unmodified** from
`aero2_clean` (imported via `sys.path`, path overridable with `AERO2_CLEAN`).

## Reused (untouched) from aero2_clean
| Element | File |
|---|---|
| Sensor read / motor write (HIL + PAL) | `M7_Aero2_Linear_Controllers/src/M7_aero2_simulink_2dof_pd_replicate.py` (`DirectHilAero2IO`, `PalAero2IO`) |
| `output_mapping(mode, u_pitch, u_yaw)` | same (`direct`→(u_p,u_y); `mixed`→(u_p−u_y,u_p+u_y)) |
| `clamp`, `simulink_square` (refs) | same |
| Filtered rate `SimulinkSecondOrderDerivative` | same |
| Controllers `.step(x, θ_ref, ψ_ref, dt)→([u_pitch,u_yaw], aux)` | `M8_.../controllers/{sliding_modes,backstepping,nmpc}.py` |
| Live plot | `aero2_common/live_plot.py` |

## New residual code
| Element | File:symbol |
|---|---|
| Demand score (pitch/yaw/combined) | `aero2_residual/residual_gate.py:Aero2GateResidual.demand_scores` |
| Gate neuron (Eq.4 gate, Eq.7 conductance) | `…:step_gate` |
| Corrective directions / candidates | `…:correctives`, `…:candidates` |
| Shuffle source (timing control) | `…:ShuffleSource` |
| Injection + routing + clipping + logging | `runners/run_aero2_residual.py:main` |

## Equations → code
- **Gate (Eq.4, γ=0 here):** `r⁺ = clip(r·e^(−dt/τ_r) + σ(α(v−v_thresh))·(1−e^(−dt/τ_r)), 0,1)` — `residual_gate.py:step_gate`.
- **Membrane (demand-driven leaky low-pass):** `v⁺ = v·e^(−dt/τ) + (DRIVE_GAIN·combined)·(1−e^(−dt/τ))` — `step_gate`.
- **Conductance readout (Eq.7):** `g_eff = (g_base + β·|drive|)·r²` — `step_gate` (β: adaptive 5 / hyperlif 0).
- **Demand:** §3 of `aero2_residual_architecture.md` — `demand_scores`.
- **Candidate:** `cand_ch = Vmax · tanh(k_ch·e_ch) · r · combined` — `candidates`.
- **Injection (virtual pitch/yaw):** `u_total = clip(output_mapping(u_p+pitch_res, u_y+yaw_res), ±Vlim)` — runner.
- **Applied gating:** `applied ≠ 0` only if `mode ∈ {gate,always_on,shuffled_gate}` **and** `control_mode=="active"`; each channel clipped to `±Vmax` before the total `±Vlim` clip — runner.

## Logged columns (run_aero2_residual.py)
`residual_mode, residual_channel, residual_scale, residual_max_voltage, residual_sign,
pitch_demand_score, yaw_demand_score, combined_demand_score, gate_state, conductance_state,
event_activity, residual_active_flag, pitch_residual_candidate, yaw_residual_candidate,
left_residual_candidate, right_residual_candidate, pitch_residual_applied, yaw_residual_applied,
left_residual_applied, right_residual_applied, base_left_voltage, base_right_voltage,
total_left_voltage, total_right_voltage, saturation_proximity, applied_residual_energy,
applied_residual_active_flag` — plus classical signals (theta/psi, refs, errors, rates,
u_pitch/u_yaw, gyro, motor current, control_mode).

## Invariants (verified offline)
- `none`/`shadow_gate`: all `*_residual_applied = 0`, `total_* == base_*` (motor = classical).
- Applied candidate is bounded: offline test gave pitch perturbation → `|cand| ≤ Vmax`, dormant
  at low demand, release on recovery (`tools` / module self-tests).
