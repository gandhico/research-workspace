# Project Map — HyperLIF Gate-State Residual Quadrotor Control

## Directory Structure

```
v2_clean/
├── src/
│   ├── quad/
│   │   ├── math_utils.py       Canonical quaternion utilities [w,x,y,z]
│   │   ├── models.py           DroneParams: mass, inertia, mixer from MuJoCo XML
│   │   ├── reference.py        Reference trajectories (hover, roll, hard45, yaw360, ...)
│   │   └── bridge.py           MuJoCo state extraction + control application
│   │
│   ├── controllers/
│   │   ├── classical.py        ClassicalPD: tau = -kq*e_q - kw*omega
│   │   ├── neuron_dynamics.py  LIF, HyperLIF, Adaptive HyperLIF, Izhikevich
│   │   ├── neural_controllers.py DirectNeuronTorqueController, RotorResidualController, Nengo
│   │   └── factory.py          make_controller(name, params, dt, ...)
│   │
│   ├── rotor/
│   │   └── mixer.py            wrench_to_motors, motors_to_wrench, hover_wrench
│   │
│   ├── logging_utils/
│   │   └── logger.py           CSV, JSON, NPZ, run config logging
│   │
│   └── viz/
│       └── dashboard.py        Real-time matplotlib dashboard
│
├── runners/
│   ├── run_rotor_level.py      MAIN: single-run controller benchmark
│   └── run_benchmark_sweep.py  Multi-controller sweep + comparison table
│
├── models/                     Symlinked from ../models/mujoco_menagerie/
│   └── (managed externally)
│
├── results/
│   ├── logs/                   CSV, JSON summaries, run configs
│   ├── figures/                PNG plots
│   └── videos/                 Optional video output
│
├── docs/
│   ├── project_map.md          This file
│   ├── math_formulation.md     Full mathematical derivation
│   ├── rotor_level_plan.md     Rotor-level control architecture
│   ├── visualization_plan.md   Dashboard description
│   ├── runner_commands.md      Quick-start command reference
│   └── paper_narrative.md      Scientific story for IEEE paper
│
└── archive/
    └── legacy_notes.md         Summary of archived legacy code
```

## Model Architecture Layers

```
Layer 1: Quaternion math      quad/math_utils.py
Layer 2: Drone parameters     quad/models.py      (DroneParams)
Layer 3: Reference trajectory quad/reference.py
Layer 4: Controller           controllers/
Layer 5: Rotor mixer          rotor/mixer.py
Layer 6: MuJoCo bridge        quad/bridge.py
Layer 7: Logging + viz        logging_utils/ + viz/
Layer 8: Runner               runners/run_rotor_level.py
```

## Supported Drones

| Drone                 | Actuator Mode | Mixer | Hover Thrust | Max Motor |
|-----------------------|---------------|-------|--------------|-----------|
| skydio_x2             | rotor4        | 4×4 B | 3.25 N/motor | 13 N      |
| bitcraze_crazyflie_2  | wrench4       | virtual | 0.26 N total | 0.35 N  |

## Supported Controllers

| Name                             | Type                    | Target    |
|----------------------------------|-------------------------|-----------|
| classical                        | Quaternion PD           | both      |
| direct_lif                       | Standard LIF residual   | both      |
| direct_hyperlif                  | HyperLIF gate residual  | both      |
| direct_adaptive_hyperlif         | Adaptive HyperLIF       | both      |
| direct_izhikevich                | Izhikevich residual     | both      |
| rotor_residual_hyperlif          | HyperLIF on rotors      | X2 only   |
| rotor_residual_adaptive_hyperlif | Adaptive on rotors      | X2 only   |
| nengo_lifrate                    | Nengo ensemble          | both      |
| nengo_lif                        | Nengo LIF               | both      |
| nengo_adaptive_lif               | Nengo adaptive          | both      |

## Key Design Decisions

1. **Two control paths** are kept explicit:
   - `xfrc_applied` (external force injection) = legacy body-torque path
   - `mj_data.ctrl` actuator commands = rotor-level / virtual wrench path

2. **HyperLIF gate state** `r` is the primary residual signal. When `activity_mode="gate"`,
   the gate state output is used directly as control activity. The `gate_gain` scales it
   before decoding to torque or rotor-command residuals.

3. **Rotor-level control** targets the Skydio X2. CF2 does not have 4-motor actuators in
   the menagerie model (uses virtual body torques), but can run all body-torque controllers.

4. **Safety bounds**: motor commands always clipped to [ctrl_min, ctrl_max]. Torques always
   clipped to tau_limit. Collective thrust clipped to 2.5× hover thrust.
