# Legacy Code Archive Notes

This folder documents legacy experimental code preserved in the parent directory.
All files remain available at their original locations under `../code/`.

## Archived Code Locations

### `../code/quaternion_quad/`

| File                                    | Status    | Notes |
|-----------------------------------------|-----------|-------|
| quad_att_control.py                     | Essential | Pure quaternion attitude ODE (paper baseline). Clean, no MuJoCo. |
| quaternion_mujoco.py                    | Legacy    | Motor mixer prototype for X2. Hardcoded XML path. Reference for mixer math. |
| quaternion_mujoco_hover_roll.py         | Legacy    | Hover + roll with external forces. Functional but outdated API. |
| mujoco_hover_nengo_controller.py        | Legacy    | Early Nengo MuJoCo controller prototype. |
| mujoco_nengo_controller_benchmark.py   | Archived  | Early Nengo benchmark. Superseded by controller_benchmarks/ |
| paper_gain_sweep_replication.py         | Archived  | Paper gain sweep validation. |
| paper_ode_replication.py                | Archived  | Python ODE replication. |
| paper_ode_replication.jl                | Archived  | Julia ODE replication. |
| quaternion_euler_singularity_demo.py    | Archived  | Euler singularity visualization demo. |
| nengo_torque_decoder_benchmark.py       | Archived  | Early Nengo decoder. |

### `../code/controller_benchmarks/`

| File                             | Status       | Notes |
|----------------------------------|--------------|-------|
| neuron_dynamics.py               | Superseded   | Neuron models. Clean copy in `src/controllers/neuron_dynamics.py` |
| neural_torque_controllers.py     | Superseded   | Controllers. Clean copy in `src/controllers/` |
| benchmark_metrics.py             | Superseded   | Metrics. Clean copy in `src/logging_utils/logger.py` |
| mujoco_classical_vs_neural.py    | Superseded   | Main runner. Superseded by `runners/run_rotor_level.py` |
| run_quick_benchmark.py           | Superseded   | Sweep runner. Superseded by `runners/run_benchmark_sweep.py` |

### `../code/stn_pid_pes_optional/`

| File                                  | Status   | Notes |
|---------------------------------------|----------|-------|
| stn_pid_attitude_controller.py        | Optional | STN-PID architecture. Not integrated in v2_clean. |
| mujoco_classical_vs_neural_stn.py     | Optional | STN benchmark runner. |
| test_stn_pid_attitude_core.py         | Optional | STN unit tests. |

### `../code/mujoco_bridge/`
Empty directory. Bridge functionality is in `src/quad/bridge.py`.

## Key Differences: Legacy vs v2_clean

1. **Path handling**: Legacy code uses hardcoded absolute paths. v2_clean uses
   `PROJECT_ROOT / "models" / "mujoco_menagerie" / ...`.

2. **Quaternion convention**: Same [w,x,y,z] convention throughout v2_clean.
   Legacy code was consistent but duplicated utilities across every file.

3. **Control paths**: Legacy uses `xfrc_applied` exclusively. v2_clean supports
   both `xfrc_applied` (body_torque fallback) and `mj_data.ctrl` (rotor4/wrench4).

4. **Hover support**: Legacy hover force was always applied. v2_clean routes through
   `compute_hover_force()` and `apply_body_torque()` as explicit named functions.

5. **Dashboard**: Legacy had no live visualization. v2_clean has `src/viz/dashboard.py`.

## Important Experimental Results (from docs/imported_notes/)

See `../docs/imported_notes/2026_04_29_hyperlif_controller_progress_exhaustive.md`
for detailed results of the best HyperLIF configurations:

- Best controller: direct_adaptive_hyperlif, gate mode, control scale
- Best gate_gain: 100000
- Best blend: 0.50
- Mission: hard45, 45s, bitcraze_crazyflie_2
- Result: ~7.35% qerr_mean improvement over classical baseline
