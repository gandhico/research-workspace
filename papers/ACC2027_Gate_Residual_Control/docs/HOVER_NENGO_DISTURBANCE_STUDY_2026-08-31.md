# 3DOF Hover Nengo hard-disturbance study

This is an emulated Hover transfer/robustness experiment, not a new physical
hardware claim. It uses the same quaternion-PD and Nengo CMG--PES path prepared
for Q8 HIL, with four deterministic pulse windows at 4, 9, 14, and 19 seconds.
Injected torque, plant/controller state, and CMG/PES state are archived at 200
Hz and 2 kHz respectively.

## Mission-specific feasibility profile

Pulse severity is identical within each PD/CMG pair. It is mission-specific
because Hard45, Hardstep, and Yaw360 consume substantially different stability
and actuator margins.

| Mission | Pulse scale of declared torque limit | Reference/allocator change |
|---|---:|---|
| Roll | 0.3500 | canonical reference, fixed-bias allocator |
| Full3 | 0.3500 | canonical reference, fixed-bias allocator |
| Hard45 | 0.0175 | canonical reference, fixed-bias allocator |
| Hardstep | 0.0350 | separately named hardware-feasible variant: 0.7 reference scale, 0.5 s smooth transition, stability-priority allocator |
| Yaw360 | 0.0175 | 0.8 reference scale, stability-priority allocator |

These profile changes are not hidden: Hardstep and Yaw360 are not the same
canonical mission used in the 45 s MuJoCo drone matrix.

## Results

Mean and peak are shortest-path quaternion-angle errors. Positive improvement
means lower CMG--PES error.

| Mission | PD mean [deg] | CMG--PES mean [deg] | Improvement | PD peak / CMG peak [deg] | Completion |
|---|---:|---:|---:|---:|---|
| Roll | 4.4247 | 3.9554 | **+10.61%** | 21.9536 / 21.8473 | Both complete, 25 s |
| Full3 | 21.5057 | 21.3179 | **+0.87%** | 42.2596 / 41.7302 | Both complete, 25 s |
| Hard45 | 19.7697 | 19.6847 | +0.43% partial | 35.7681 / 35.7206 | Both later crossed the 55 deg roll boundary; partial pair only |
| Hardstep, shaped | 22.3597 | 22.3860 | **-0.12%** | 65.3924 / 65.4961 | Both complete; effectively neutral/slightly worse |
| Yaw360, 0.8 scale | 8.5310 | 8.3677 | +1.91% partial | 62.8641 / 62.7909 | Both later crossed the 55 deg pitch boundary; partial pair only |

The strongest complete disturbance result is Roll, consistent with the
physical quaternion-PD Hover result where CMG improved Roll by 21.67%. Full3 is
positive but modest. The shaped Hardstep result is an important negative/null
result: online CMG--PES did not improve that experiment. Hard45 and Yaw360 may
be shown only as safety-boundary/partial evidence, never as complete trials.

## Artifacts

- Raw paired runs:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\disturbance_campaign_profiled_2026-08-31`
- Metrics and tracking/pulse figures:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results\disturbance_compiled_profiled_2026-08-31`
- Compiler:
  `C:\Research\hover3dof\nengo_gui_hil_2026-08-29\compile_disturbance_campaign.py`
- Universal neural-state plotter:
  `C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\analyze_neural_archive.py`

Every CMG run has an `analysis` subfolder containing a flattened full-rate CSV,
descriptive-statistics JSON, and PNG/PDF figures for membrane/gate/conductance,
PES target/error, decoder row and update norms, and exact equation terms. The
partial Hard45 and Yaw360 archives stop at their safety boundary and retain the
abort interval; they were analyzed rather than discarded.

`audit_disturbance_campaign.py` passes all ten summaries and all five matched
pairs: configuration fields match within each pair, the reference and injected
disturbance traces agree sample-for-sample over their common horizon, every
neural signal is finite, 2-kHz sample counts equal ten times the 200-Hz control
rows, and every diagnostic artifact exists. Runs used `emulation_realtime=false`;
therefore `deadline_miss_fraction` is intentionally **not** hardware timing
evidence. The table uses shortest-path quaternion error; the separately logged
Euler-error-vector norm is a different diagnostic and must not be substituted.

## Paper interpretation

This experiment supports: (1) identical Nengo CMG/PES software can execute in
the Hover control path; (2) complete emulated hard-pulse rejection improves
strongly on Roll and modestly on Full3; and (3) mission feasibility remains
plant/allocator dependent. It does not replace the existing physical LQR and
PD Hover tables, nor does it validate the emulated plant as an identified
digital twin.
