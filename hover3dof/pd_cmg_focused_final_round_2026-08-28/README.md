# 3DOF Hover PD/CMG focused final round

Created 2026-08-28 as an isolated, offline-safe design package. No file in
`C:\Research\hover3dof\runners`, `docs`, or `results` was edited by this work.
Nothing in this folder imports `quanser.hardware`, opens a Q8 board, or writes an
analog output.

## Read this first

1. `AUDIT_FINDINGS.md` — evidence-backed audit of the MATLAB-to-Python LQR,
   current CMG/PES signal path, and the recorded hardware results.
2. `PD_BASELINE_DESIGN.md` — the exact mathematical relationship between the
   vendor LQR and a MuJoCo-style PD controller.
3. `CMG_3DOF_ALIGNMENT.md` — what is and is not yet architecture-equivalent to
   the MuJoCo implementation.
4. `FOCUSED_FINAL_ROUND.md` — prescriptive next experiment protocol. It treats
   Sets K/L/M as already executed and separates tuning evidence from validation.
5. `READ_ONLY_SNAPSHOT.json` — hashes of the source files audited.
6. `PD_HARDWARE_RUNBOOK.md` — staged commands for the new explicit-PD and
   three-axis torque-space CMG experiment.
7. `PD_BUILD_VALIDATION.md` — offline equivalence and frozen-trace replay
   evidence collected before any hardware use.
8. `MUJOCO_HOVER_CONFORMANCE.md` — normative equations, coordinate transform,
   signal architecture, exact reproduction boundary, hardware adaptations, and
   complete neuron/decoder logging schema.
9. `OFFLINE_VALIDATION_2026-08-28.json` — machine-readable hashes, frozen
   parameters, test status, and replay results for session handoff.
10. `SHADOW_RUN_REVIEW_2026-08-28_1255.md` — audit of the first two user-run Q8
    dry runs and why they remain pre-conformance checks rather than results.
11. `SHADOW_RUN_REVIEW_2026-08-28_1313.md` — final-runner Hard45 shadow audit,
    including actuator saturation, neuron/PES behavior, timing, and the staged
    physical-test decision.
12. `NEXT_FOCUSED_LADDER_2026-08-28.md` — matched Hard45/Full3/Hardstep
    authority ladders, guarded slower Yaw360 recovery, and campaign compilation
    commands.

`tools\compile_pd_cmg_campaign.py` audits every run and produces
`results\compiled\campaign_runs.csv`, `campaign_pairs.csv`, and `campaign.json`.

13. `STABILITY_PRIORITY_RECOVERY_2026-08-28.md` — evidence, equations, offline
    replay, and staged commands for the motor-floor/pitch-roll-priority allocator
    used to recover Yaw360 and Hardstep without altering CMG/PES.

## Offline commands

Run the controller-equivalence tests:

```powershell
C:\Research\hover3dof\.venv\Scripts\python.exe C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28\tests\test_pd_baseline.py
```

The hardware runner defaults to the canonical MuJoCo quaternion-PD profile.
The earlier LQR-equivalent profile remains an explicitly named software bridge,
not the default experiment.

Re-analyze every existing hardware `summary.json`/`trace.csv` without touching
the rig:

```powershell
C:\Research\hover3dof\.venv\Scripts\python.exe C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28\tools\analyze_existing_runs.py
```

Regenerate the yaw-duration diagnostic plot:

```powershell
C:\Research\hover3dof\.venv\Scripts\python.exe C:\Research\hover3dof\pd_cmg_focused_final_round_2026-08-28\tools\plot_yaw_duration_confound.py
```

## Boundary

The Python module in `src` is controller mathematics only. The separate runner
in `runners` is disarmed by default, writes results only under this experiment
folder, requires a second acknowledgement flag when armed, and adds pitch/roll
and deadline-miss aborts. It still does not configure a hardware watchdog; the
physical E-stop and reviewed laboratory procedure remain mandatory.

No hardware command was executed while creating or validating this package.
