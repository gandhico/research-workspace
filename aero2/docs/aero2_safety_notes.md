# Aero2 Residual — Safety Notes (2026-06-14)

The classical controller is the stability anchor. The residual is **bounded, optional,
demand-triggered assistance**. Enforced boundaries (in `runners/run_aero2_residual.py`):

## Hard rules
1. **Applied only in active control.** Residual is nonzero only when `control_mode == "active"`.
   It is exactly 0 during `startup` (first `--residual-settle-s`, default 1 s) and
   `invalid_sensor` (any non-finite signal). `none`/`shadow_gate` never apply.
2. **Per-channel cap.** Each applied residual channel is clipped to `±residual_max_voltage`
   (default 0.5 V) — independent of the motor limit.
3. **Total clip.** `total_channel = clip(base_channel + residual, ±voltage_limit)` (24 V HIL /
   15 V PAL). Residual can never push the command past the motor limit.
4. **Controller structure preserved.** Residual is added at the virtual pitch/yaw level and
   re-mapped by the existing `output_mapping`; the controller is never bypassed.
5. **Unmodified safety stops.** The clean safety checks are kept verbatim: |θ|>0.90 rad,
   |ψ|>1.40 rad, |gyro_y|>8, |gyro_z|>8, sample-overrun fraction>0.35 → stop + zero output.
6. **Defensive fallback.** Any exception in the residual block → classical command only
   (`total = base`); the loop never crashes and the motor never gets an unsafe value.
7. **Always zero on exit.** `finally` writes (0,0) and terminates the card (Ctrl+C, fault, or
   normal end), inherited from the clean runner.

## Shadow → applied gate
Do not run an applied mode until `shadow_gate` shows: `u_total == u0`, dormant at low demand,
gate opens on transients/perturbations, candidate within cap. Then `gate` at 0.5 V, then 1.0 V.

## Startup banner (printed every run)
mode, channel, neuron, whether residual is applied to motors, scale, sign,
`residual_max_voltage`, `apply_active_only`, settle time, thresholds. Applied modes print
`RESIDUAL APPLIED TO MOTORS: *** YES ***`.

## Operator checklist
- First run of any new condition: keep a hand on Ctrl+C / E-stop.
- Start pitch-only, cap 0.5 V; escalate only after a clean run.
- Equilibrium mission: apply only small manual perturbations; watch θ/ψ safe limits.
- `--residual-apply-active-only false` is recorded but active-only remains **enforced**.
- Never raise `--voltage-limit` above 24 V (HIL) / 15 V (PAL) — refused by the runner.
