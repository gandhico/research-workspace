# Nengo GUI index

All files are self-contained and expose a top-level `model`. Benchmark experiment/controller modules remain the source of truth.

| Experiment | Controller | GUI file | CFG file | Explanation file |
| ---------- | ---------- | -------- | -------- | ---------------- |
| Exp01 | Classical PD | `gui_exp01_altitude_classical.py` | `gui_exp01_altitude_classical.py.cfg` | `gui_exp01_altitude_classical_analysis.md` |
| Exp01 | NEF LIF spiking | `gui_exp01_altitude_nef.py` | `gui_exp01_altitude_nef.py.cfg` | `gui_exp01_altitude_nef_analysis.md` |
| Exp01 | NEF rate | `gui_exp01_altitude_nef_rate.py` | `gui_exp01_altitude_nef_rate.py.cfg` | `gui_exp01_altitude_nef_rate_analysis.md` |
| Exp02 | Classical PD | `gui_exp02_roll_classical.py` | `gui_exp02_roll_classical.py.cfg` | `gui_exp02_roll_classical_analysis.md` |
| Exp02 | NEF LIF spiking | `gui_exp02_roll_nef.py` | `gui_exp02_roll_nef.py.cfg` | `gui_exp02_roll_nef_analysis.md` |
| Exp02 | Classical PD | `gui_exp02_pitch_classical.py` | `gui_exp02_pitch_classical.py.cfg` | `gui_exp02_pitch_classical_analysis.md` |
| Exp02 | NEF LIF spiking | `gui_exp02_pitch_nef.py` | `gui_exp02_pitch_nef.py.cfg` | `gui_exp02_pitch_nef_analysis.md` |
| Exp02 | Classical PD | `gui_exp02_yaw_classical.py` | `gui_exp02_yaw_classical.py.cfg` | `gui_exp02_yaw_classical_analysis.md` |
| Exp02 | NEF LIF spiking | `gui_exp02_yaw_nef.py` | `gui_exp02_yaw_nef.py.cfg` | `gui_exp02_yaw_nef_analysis.md` |
| Exp02 | Classical cascade PD | `gui_exp02_xpos_classical.py` | `gui_exp02_xpos_classical.py.cfg` | `gui_exp02_xpos_classical_analysis.md` |
| Exp02 | NEF LIF spiking | `gui_exp02_xpos_nef.py` | `gui_exp02_xpos_nef.py.cfg` | `gui_exp02_xpos_nef_analysis.md` |
| Exp02 | Classical cascade PD | `gui_exp02_ypos_classical.py` | `gui_exp02_ypos_classical.py.cfg` | `gui_exp02_ypos_classical_analysis.md` |
| Exp02 | NEF LIF spiking | `gui_exp02_ypos_nef.py` | `gui_exp02_ypos_nef.py.cfg` | `gui_exp02_ypos_nef_analysis.md` |
| Exp03 | Classical cascade | `gui_exp03_quadrotor_classical.py` | `gui_exp03_quadrotor_classical.py.cfg` | `gui_exp03_quadrotor_classical_analysis.md` |
| Exp03 | NEF rate cascade | `gui_exp03_quadrotor_nef_rate.py` | `gui_exp03_quadrotor_nef_rate.py.cfg` | `gui_exp03_quadrotor_nef_rate_analysis.md` |
| Exp03 | NEF LIF-spiking cascade | `gui_exp03_quadrotor_nef_spiking.py` | `gui_exp03_quadrotor_nef_spiking.py.cfg` | `gui_exp03_quadrotor_nef_spiking_analysis.md` |
| Exp04 | Classical cascade + allocation | `gui_exp04_trirotor_classical.py` | `gui_exp04_trirotor_classical.py.cfg` | `gui_exp04_trirotor_classical_analysis.md` |
| Exp04 | NEF rate + neural allocation | `gui_exp04_trirotor_nef_rate.py` | `gui_exp04_trirotor_nef_rate.py.cfg` | `gui_exp04_trirotor_nef_rate_analysis.md` |
| Exp04 | NEF LIF-spiking + neural allocation | `gui_exp04_trirotor_nef_spiking.py` | `gui_exp04_trirotor_nef_spiking.py.cfg` | `gui_exp04_trirotor_nef_spiking_analysis.md` |

## Detailed inventory

### `gui_exp01_altitude_classical.py`

- Subsystem: 1-DOF altitude
- Controller: Classical PD
- Equations: zdd=u/m-g; u=mg+Kp e-Kd zdot
- Layout: `gui_exp01_altitude_classical.py.cfg`
- Explanation: `gui_exp01_altitude_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp01_altitude_classical.py`

### `gui_exp01_altitude_nef.py`

- Subsystem: 1-DOF altitude
- Controller: NEF LIF spiking
- Equations: same altitude PD in LIF ensembles
- Layout: `gui_exp01_altitude_nef.py.cfg`
- Explanation: `gui_exp01_altitude_nef_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp01_altitude_nef.py`

### `gui_exp01_altitude_nef_rate.py`

- Subsystem: 1-DOF altitude
- Controller: NEF rate
- Equations: same altitude PD in rate ensembles
- Layout: `gui_exp01_altitude_nef_rate.py.cfg`
- Explanation: `gui_exp01_altitude_nef_rate_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp01_altitude_nef_rate.py`

### `gui_exp02_roll_classical.py`

- Subsystem: roll attitude
- Controller: Classical PD
- Equations: phidd=tau; tau=Kp e-Kd phidot
- Layout: `gui_exp02_roll_classical.py.cfg`
- Explanation: `gui_exp02_roll_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_roll_classical.py`

### `gui_exp02_roll_nef.py`

- Subsystem: roll attitude
- Controller: NEF LIF spiking
- Equations: phidd=tau; tau=Kp e-Kd phidot
- Layout: `gui_exp02_roll_nef.py.cfg`
- Explanation: `gui_exp02_roll_nef_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_roll_nef.py`

### `gui_exp02_pitch_classical.py`

- Subsystem: pitch attitude
- Controller: Classical PD
- Equations: thetadd=tau; tau=Kp e-Kd thetadot
- Layout: `gui_exp02_pitch_classical.py.cfg`
- Explanation: `gui_exp02_pitch_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_pitch_classical.py`

### `gui_exp02_pitch_nef.py`

- Subsystem: pitch attitude
- Controller: NEF LIF spiking
- Equations: thetadd=tau; tau=Kp e-Kd thetadot
- Layout: `gui_exp02_pitch_nef.py.cfg`
- Explanation: `gui_exp02_pitch_nef_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_pitch_nef.py`

### `gui_exp02_yaw_classical.py`

- Subsystem: yaw attitude
- Controller: Classical PD
- Equations: psidd=tau; tau=Kp e-Kd psidot
- Layout: `gui_exp02_yaw_classical.py.cfg`
- Explanation: `gui_exp02_yaw_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_yaw_classical.py`

### `gui_exp02_yaw_nef.py`

- Subsystem: yaw attitude
- Controller: NEF LIF spiking
- Equations: psidd=tau; tau=Kp e-Kd psidot
- Layout: `gui_exp02_yaw_nef.py.cfg`
- Explanation: `gui_exp02_yaw_nef_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_yaw_nef.py`

### `gui_exp02_xpos_classical.py`

- Subsystem: x position via theta
- Controller: Classical cascade PD
- Equations: outer position PD -> atan2 tilt -> inner attitude PD
- Layout: `gui_exp02_xpos_classical.py.cfg`
- Explanation: `gui_exp02_xpos_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_xpos_classical.py`

### `gui_exp02_xpos_nef.py`

- Subsystem: x position via theta
- Controller: NEF LIF spiking
- Equations: outer position PD -> atan2 tilt -> inner attitude PD
- Layout: `gui_exp02_xpos_nef.py.cfg`
- Explanation: `gui_exp02_xpos_nef_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_xpos_nef.py`

### `gui_exp02_ypos_classical.py`

- Subsystem: y position via phi
- Controller: Classical cascade PD
- Equations: outer position PD -> atan2 tilt -> inner attitude PD
- Layout: `gui_exp02_ypos_classical.py.cfg`
- Explanation: `gui_exp02_ypos_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_ypos_classical.py`

### `gui_exp02_ypos_nef.py`

- Subsystem: y position via phi
- Controller: NEF LIF spiking
- Equations: outer position PD -> atan2 tilt -> inner attitude PD
- Layout: `gui_exp02_ypos_nef.py.cfg`
- Explanation: `gui_exp02_ypos_nef_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp02_ypos_nef.py`

### `gui_exp03_quadrotor_classical.py`

- Subsystem: full 12-state quadrotor
- Controller: Classical cascade
- Equations: 3-D translation + normalized attitude dynamics + cascaded PD
- Layout: `gui_exp03_quadrotor_classical.py.cfg`
- Explanation: `gui_exp03_quadrotor_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp03_quadrotor_classical.py`

### `gui_exp03_quadrotor_nef_rate.py`

- Subsystem: full 12-state quadrotor
- Controller: NEF rate cascade
- Equations: six PD channels in rate ensembles
- Layout: `gui_exp03_quadrotor_nef_rate.py.cfg`
- Explanation: `gui_exp03_quadrotor_nef_rate_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp03_quadrotor_nef_rate.py`

### `gui_exp03_quadrotor_nef_spiking.py`

- Subsystem: full 12-state quadrotor
- Controller: NEF LIF-spiking cascade
- Equations: six PD channels in LIF ensembles
- Layout: `gui_exp03_quadrotor_nef_spiking.py.cfg`
- Explanation: `gui_exp03_quadrotor_nef_spiking_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp03_quadrotor_nef_spiking.py`

### `gui_exp04_trirotor_classical.py`

- Subsystem: full coaxial Y6 trirotor
- Controller: Classical cascade + allocation
- Equations: rigid body + PD cascade + 6x4 allocation
- Layout: `gui_exp04_trirotor_classical.py.cfg`
- Explanation: `gui_exp04_trirotor_classical_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp04_trirotor_classical.py`

### `gui_exp04_trirotor_nef_rate.py`

- Subsystem: full coaxial Y6 trirotor
- Controller: NEF rate + neural allocation
- Equations: rate PD commands + 4-D neural allocator
- Layout: `gui_exp04_trirotor_nef_rate.py.cfg`
- Explanation: `gui_exp04_trirotor_nef_rate_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp04_trirotor_nef_rate.py`

### `gui_exp04_trirotor_nef_spiking.py`

- Subsystem: full coaxial Y6 trirotor
- Controller: NEF LIF-spiking + neural allocation
- Equations: LIF PD commands + 4-D neural allocator
- Layout: `gui_exp04_trirotor_nef_spiking.py.cfg`
- Explanation: `gui_exp04_trirotor_nef_spiking_analysis.md`
- Launch: `python -m nengo_gui src/gui/gui_exp04_trirotor_nef_spiking.py`

## Conventions and scope

- Classical controllers use labeled Nengo Nodes for transparent algebraic stages.
- Direct classical feedback uses `synapse=0` (one simulator-tick scheduling delay) to avoid a Nengo algebraic dependency cycle without adding low-pass dynamics.
- Exp01 rate, Exp03 rate, and Exp04 rate use `nengo.RectifiedLinear()`.
- Exp01 spiking, all Exp02 NEF controllers, Exp03 spiking, and Exp04 spiking use `nengo.LIF()`.
- Full quadrotor GUIs use the benchmark inertia-normalized angular-command abstraction.
- Full Y6 GUIs retain the rigid-body model and exact 6×4 allocator; NEF Y6 GUIs retain the normalized 3000-neuron allocation population.
- CFG spike rasters are present only for LIF-spiking models.
