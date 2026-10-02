# Qube residual condition comparison

- Generated: 2026-06-14 21:47:10
- Conditions: shadow_gate, gate, gate_2, shuffled_gate, always_on

## Per-condition summary (active balance)
| condition | mean_abs_err_deg | max_abs_err_deg | high_demand_mean_abs_err_deg | high_demand_max_abs_err_deg | mean_abs_u_total | max_abs_u_total | residual_active_fraction | applied_active_fraction | low_demand_applied_active_fraction | applied_residual_energy | amplifier_fault_count |
|---|---|---|---|---|---|---|---|---|---|---|---|
| shadow_gate | 0.4372 | 11.95 | 6.832 | 11.95 | 0.392 | 5 | 0.02016 | 0 | 0 | 0 | 0 |
| gate | 0.7227 | 9.316 | 5.348 | 9.316 | 0.4392 | 4.87 | 0.0305 | 0.02207 | 0.0003275 | 4.145e-05 | 0 |
| gate_2 | 0.4753 | 11.78 | 6.365 | 11.78 | 0.3347 | 4.999 | 0.03706 | 0.03153 | 0 | 0.0001927 | 0 |
| shuffled_gate | 0.4512 | 11.95 | 5.117 | 11.95 | 0.4561 | 5 | 0.03699 | 0.04439 | 0.04063 | 3.361e-05 | 0 |
| always_on | 0.4518 | 9.492 | 4.941 | 9.492 | 0.28 | 4.701 | 0.02142 | 0.525 | 0.5052 | 0.0002805 | 0 |

## Decision logic (H1 timing, H2 event/actuation cost)
- gate vs shuffled_gate (high-demand mean |err|): shuffled=5.12, gate=5.35, gate-better-by=-0.23 deg -> **timing weak (gate ~ shuffled)**.
- gate vs always_on (cost): applied energy gate=4.14e-05 vs always_on=0.00028; applied active fraction gate=0.0221 vs always_on=0.525. gate err=5.35 vs always_on err=4.94. (gating saves actuation at similar error).

> Interpretation rules: gate < shuffled in high-demand bins => demand-triggered timing is doing the work (H1). gate ~ always_on on high-demand error but with lower applied energy/active fraction => demand gating earns its place (H2). gate ~ shuffled => timing claim is weak and should not be made.

## Sources
- shadow_gate: `results\online\qube3_shadow_simulink_balance_20260614_210649.csv`
- gate: `results\online\qube3_gate_cap010_simulink_balance_20260614_213926.csv`
- gate_2: `results\online\qube3_gate_cap020_simulink_balance_20260614_214011.csv`
- shuffled_gate: `results\online\qube3_shuffled_gate_cap010_simulink_balance_20260614_214202.csv`
- always_on: `results\online\qube3_always_on_cap010_simulink_balance_20260614_214258.csv`