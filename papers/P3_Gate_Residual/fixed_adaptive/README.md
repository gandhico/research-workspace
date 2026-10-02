# HyperLIF Gate-State Residual — Quadrotor Control

MuJoCo quadrotor control with HyperLIF / Adaptive HyperLIF gate-state residual
augmentation. Targets Skydio X2 (rotor-level) and Crazyflie 2 (virtual wrench).

## Scientific Story

```
Classical quaternion PD baseline
+ Direct LIF residual
+ HyperLIF gate-state residual
+ Adaptive HyperLIF gate-state residual
+ Rotor-level HyperLIF residual (Skydio X2)
```

**Key insight**: The HyperLIF internal gate state r ∈ [0,1] is a continuous,
bounded signal encoding "neuronal readiness to fire." When used in gate mode,
it acts as a smooth, interpretable residual control signal without requiring
explicit spike event detection.

## Quick Start

```powershell
# Install dependencies
pip install mujoco numpy matplotlib

# Classical hover baseline (Skydio X2, rotor-level)
cd v2_clean
python runners\run_rotor_level.py --quad skydio_x2 --controller classical --mission hover --sim-time 20 --viewer --dashboard

# Best HyperLIF configuration (CF2, gate mode)
python runners\run_rotor_level.py --quad bitcraze_crazyflie_2 --controller direct_adaptive_hyperlif --mission hard45 --sim-time 45 --blend 0.50 --direct-scale control --activity-mode gate --gate-gain 100000 --viewer --dashboard --save-csv --save-figures

# Rotor-level residual (X2)
python runners\run_rotor_level.py --quad skydio_x2 --controller rotor_residual_adaptive_hyperlif --mission hard45 --sim-time 45 --residual-blend 0.10 --gate-gain 100000 --viewer --dashboard --save-csv

# Benchmark sweep
python runners\run_benchmark_sweep.py --preset smoke --quad skydio_x2 --missions roll,hard45 --sim-time 20
```

## Project Structure

```
v2_clean/
├── src/
│   ├── quad/               Quaternion math, drone models, reference, MuJoCo bridge
│   ├── controllers/        Classical PD, LIF/HyperLIF/Adaptive neurons, factory
│   ├── rotor/              Wrench-to-motor mixer
│   ├── logging_utils/      CSV, JSON, NPZ logging
│   └── viz/                Real-time matplotlib dashboard
├── runners/
│   ├── run_rotor_level.py  Main runner (single experiment)
│   └── run_benchmark_sweep.py  Multi-controller sweep
├── docs/                   Math, rotor plan, runner commands, paper narrative
├── results/                Auto-created: logs/, figures/, videos/
└── archive/                Legacy notes
```

## Supported Drones

| Drone                   | Mode    | Motors | Max Thrust |
|-------------------------|---------|--------|------------|
| skydio_x2               | rotor4  | 4 real | 13 N each  |
| bitcraze_crazyflie_2    | wrench4 | virtual | 0.35 N total |

## Supported Controllers

| Name                             | Description                          |
|----------------------------------|--------------------------------------|
| classical                        | Quaternion PD baseline               |
| direct_lif                       | Standard LIF body-torque residual    |
| direct_hyperlif                  | HyperLIF gate-state body residual    |
| direct_adaptive_hyperlif         | Adaptive HyperLIF body residual      |
| rotor_residual_hyperlif          | HyperLIF residual on rotors (X2)     |
| rotor_residual_adaptive_hyperlif | Adaptive residual on rotors (X2)     |
| nengo_lifrate                    | Nengo LIFRate ensemble               |
| nengo_lif / nengo_adaptive_lif   | Nengo ensemble variants              |

## Published Best Result

Hard45, 45s, Crazyflie 2:
- direct_adaptive_hyperlif, gate mode, scale=control, gate_gain=100000, blend=0.50
- qerr_mean improvement: **7.35%** over classical
- qerr_max improvement:  **10.06%** over classical
- score improvement:     **7.40%** over classical
- z_std improvement:     **15.19%** over classical

## Documentation

- [Project Map](docs/project_map.md)
- [Mathematical Formulation](docs/math_formulation.md)
- [Rotor-Level Plan](docs/rotor_level_plan.md)
- [Runner Commands](docs/runner_commands.md)
- [Visualization Plan](docs/visualization_plan.md)
- [Paper Narrative](docs/paper_narrative.md)
- [Legacy Archive Notes](archive/legacy_notes.md)
