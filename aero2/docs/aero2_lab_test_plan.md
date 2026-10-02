# Aero2 Residual — Lab Test Plan (2026-06-14)

## Stage A — audit findings (baseline selection)
- **Single hardware runner:** `aero2_clean/M8_Aero2_Nonlinear_Controllers/src/M8_aero2_hardware_2dof_nonlinear.py`
  (controllers: smc / backstepping / nmpc; launched by `run_demo_live_*.ps1`).
- **References:** `simulink_square(t, freq, amp)` square waves (pitch ±20° @0.05 Hz, yaw ±45° @0.04 Hz). Equilibrium mission = amplitudes 0.
- **Errors:** `pitch_error = theta_ref − theta`, `yaw_error = psi_ref − psi`.
- **Commands:** controllers output **virtual** `[u_pitch, u_yaw]` → `output_mapping` → channels → `clamp` → `io.write(u0,u1)`.
- **Hardware write:** `DirectHilAero2IO.write` (HIL) / `PalAero2IO.write` (PAL) in the M7 module.
- **Logs:** clean runner → `M8/.../data/raw/*.csv`; our residual runner → `04_Aero2_SNNs/results/residual/*.csv`.
- **Voltage limit:** 24 V (HIL), 15 V (PAL). **Safety stops:** |θ|>0.90, |ψ|>1.40 rad, |gyro_y|,|gyro_z|>8, sample-overrun fraction>0.35.
- **Direct vs virtual:** virtual pitch/yaw commands exist → residual injected there (preferred), re-mapped by `output_mapping`.
- **Baseline chosen: SMC `yawboost`** — robust, boundary-layer-smoothed (no chatter), low overrun, the workhorse across the missions. Backstepping `yawboost` is the alternate; NMPC avoided as residual baseline (heavier compute / overrun risk).

## Missions
- **Mission 1 — tracking:** `--mission tracking` (square-wave pitch/yaw). Tests residual during reference transitions / high-demand transients.
- **Mission 2 — equilibrium:** `--mission equilibrium` (refs = 0; hold + manual perturbation). Mirrors the Qube result: dormant → perturb → gate opens → recovery → closes.

## Staged protocol (do NOT skip stages)
1. **Classical baseline** (residual none) — both missions. Confirm clean tracking / hold, no faults.
2. **shadow_gate** — both missions. Confirm `u_total == u0`, demand rises on transients/perturbations, gate opens, candidate bounded. **Gate to applied.**
3. **gate, cap 0.5 V, channel pitch** — confirm stable, residual stays within cap, activates on demand.
4. **gate, cap 1.0 V** if 0.5 V is stable. (2.0 V only if commands/limits show it is still modest.)
5. **always_on** and **shuffled_gate** at the matched cap — controls for selectivity and timing.
6. Start **pitch-only**; extend to `pitch_yaw` only after channel-wise behavior is verified.

## Suggested first dataset (tonight)
- baseline tracking ×1–2, shadow tracking ×1–2, gate tracking (0.5 then 1.0) ×2–3
- baseline equilibrium ×1–2, shadow equilibrium ×1–2, gate equilibrium (0.5) ×2–3
- if time: always_on ×2–3, shuffled_gate ×2–3 (both missions)

## Analysis
After each block: `python tools/analyze_aero2_residual_conditions.py --log <csv> --log <csv> ...`
→ `analysis/aero2_residual_comparison_*/` (summary, demand-binned, report, overlays, comparison/activity/error/energy figures).

## Pass / interpretation
- gate quiet at low demand + active in high-demand bins → selective/demand-triggered.
- gate ≈ always_on tracking at **lower** residual energy/activity → selectivity earns its place.
- gate < shuffled_gate high-demand error → timing matters. gate ≈ shuffled → do not claim timing.
- Classical controller remains responsible for stability throughout (residual is bounded assistance).
