# Omnicopter Virtual Twin — Project Progress Log

**Document status:** Living project record  
**Started:** 2026-09-23  
**Current phase:** Controller-development twin → ROS 2/Linux integration and physical identification  
**Target:** Reproducible, hardware-validated, HIL-capable and publishable virtual twin

## Purpose

This document records the project chronology, decisions, experimental evidence,
unexpected findings and remaining work. It is intended to become the concise factual
history behind the final repository and publication.

### Recording rules

1. Append new dated entries; do not rewrite historical conclusions silently.
2. Label every value as **measured**, **identified**, **configured**, **derived** or
   **unverified**.
3. Keep raw data immutable. Corrections create new derived files and manifests.
4. Link every reported result to its code, configuration, dataset and hashes.
5. Separate controller/software conformance from physical predictive validation.
6. Give every released milestone a version or freeze identifier.

## Team and responsibilities

| Person | Primary responsibility | Current interface |
|---|---|---|
| Gandhi | Controller, MuJoCo twin, identification/validation methodology | Model, missions, controller and scientific evidence |
| Diego | Linux/ROS 2 framework and system interface | ROS graph, transport, launch, timing and integration |
| Fabian | Collaborative hardware/integration role | Exact ownership to be agreed and recorded |

## Current technical baseline

| Area | Current state | Evidence/status |
|---|---|---|
| STL and body registration | STL scaled `0.001` from mm to m; fixed mesh-to-body translation | Configured |
| Rotor geometry | Eight sites at sign combinations of `0.0973 m` | Configured; final metrology pending |
| Rotor frames | Local X follows the beam; local Z is the selected physical face normal | Visually confirmed and regression tested |
| Actuation matrix | Eight reversible rotor forces; complete wrench map has rank six | Verified in software |
| Rigid-body model | 6-DoF dynamics, gravity, ground contact | Implemented |
| Mass | `2.5 kg` | Configured, unverified |
| Centre of mass | `(0.00326881, 0.00071909, 0.00103101) m` in body coordinates | Mesh inferred, unverified |
| Inertia | Full body tensor near `0.086 kg·m²` on each diagonal | Uniform-density mesh inferred, unverified |
| Propulsion | Instantaneous signed thrust, `[-10, 10] N` per rotor | Ideal and unverified |
| Aerodynamics | Density/viscosity disabled; zero wind | Not identified |
| Sensors | Ideal MuJoCo IMU and simulation ground truth | Hardware noise, pose and delay unverified |
| Control rate | `500 Hz` (`dt = 0.002 s`) | Configured |
| Controllers | Geometric PD and its exact Nengo-PD implementation | Implemented and regression tested |
| Missions | 25 staged missions | Direct PD and Nengo-PD completed the nominal campaign |
| ROS 2 integration | Architecture defined conceptually | No ROS 2 package or bridge implemented yet |
| Hardware validation | Protocol, common schema and test card exist | Physical identification data not yet populated |

Public-safe source references:

- [Canonical MuJoCo model](Omnidrone/mujoco%20model=omnidrone.xml)
- [Physics-model status](physics/README.md)
- [Parameter ledger](physics/omnicopter_parameters.json)
- [Geometric PD implementation](control/hover.py)
- [Rotor-frame regression test](review/verify_rotor_frames.py)
- [Common physical/virtual log schema](hardware/COMMON_LOG_SCHEMA.md)

Additional internal methodology, mission and test documents must receive the same
public-safety review before they are copied into the GitHub repository.

## Timeline

### 2026-09-04 — Initial maneuverability baseline

- Implemented the original pose-tracking geometric PD campaign.
- Twenty-three missions passed; the 12-second yaw mission failed its tracking-quality
  gate and the 6-second yaw mission was not escalated.
- **Insight:** the limitation was moving-reference lag caused by damping absolute
  velocity/rate toward zero, not actuator rank or saturation.

### 2026-09-09 — Feedforward controller and complete nominal campaign

- Added analytically differentiated position, velocity, acceleration, angular-rate
  and angular-acceleration references.
- Retained the original gains and bounded 6×8 rotor allocator.
- All 25 nominal missions passed without saturation.
- **Insight:** correcting the reference formulation removed the fast-motion lag without
  increasing feedback gains.

### 2026-09-09 to 2026-09-10 — Rotor-frame registration

- Registered the STL in the MuJoCo body frame.
- Aligned every rotor site's local X axis with its beam and local Z axis with the
  hardware-selected right beam surface.
- Corrected the individual 180-degree mounting ambiguities and verified all eight
  frames geometrically.
- Confirmed a rank-six wrench map and a feasible bounded gravity-balancing solution.
- **Insight:** rotor-site orientation is physical, not cosmetic—the same local Z sets
  both the displayed motor-cylinder axis and the actuator-force direction.

### 2026-09-10 — Direct/Nengo-PD controller conformance

- Implemented direct geometric PD and an exact Nengo-PD realization using the same
  states, references, gains, actuator map, limits and 500 Hz timestep.
- Nengo-PD executes the exact geometric law; it is not a neural approximation.
- Direct and Nengo PD agreed exactly at stored precision in the conformance test.
- **Insight:** backend equivalence validates implementation, not vehicle physics or
  controller superiority.

### 2026-09-10 — Public controller checkpoint

- Direct PD and Nengo-PD completed 25/25 nominal missions with zero reported
  saturation.
- Both implementations produced the same aggregate nominal result: position RMSE
  `0.001029 m` and attitude RMSE `0.0260 deg`.
- The public checkpoint records model, mesh, mission and controller hashes so later
  Linux/ROS 2 results can be compared with the original implementation.
- **Accepted conclusion:** the direct and Nengo implementations are software-equivalent
  for the tested inputs; this does not yet establish physical predictive validity.

### 2026-09-18 — Communication demonstration

- Produced a compact replay of the validated `spin_x_360` mission for communication
  with collaborators and advisors.
- The reference completes a smooth world-X revolution using a continuous quintic
  quaternion trajectory rather than relying only on an equivalent final attitude.
- **Insight:** a 360-degree rotation must be validated by accumulated signed progress;
  its final quaternion alone cannot prove that a revolution occurred.

### 2026-09-23 — Collaboration and ROS 2/HIL architecture

- Defined responsibilities around controller/twin development and Diego's Linux/ROS 2
  integration framework.
- Selected the first integration principle: a ROS-independent controller core with a
  thin ROS 2 interface and explicit stamped state/reference/actuator contracts.
- Defined the intended progression: pure simulation → recorded-data replay → physical
  shadow twin → bench HIL → tethered tests → held-out physical validation.
- Identified ceiling-camera motion capture, onboard IMU and additional sensors as
  state-estimation inputs requiring calibrated transforms and synchronized acquisition
  timestamps.
- Confirmed that the local project folder is not yet initialized as a Git repository.
- **Insight:** adding ROS 2 does not itself create a digital twin. Predictive validity
  requires independently measured parameters and successful held-out prediction.

### 2026-11-04 — ArduPilot 6DoF bring-up, Python ground station, first lift-off

- **Objective:** connect the twin to the real vehicle with onboard ArduPilot control and OptiTrack
  navigation, and reach a first tethered hover without Mission Planner and without an RC link.
- **People involved:** Gandhi (hardware and tests), with Claude Code (tools, source checks, tests).
- **Hardware revision:**
  - **Flight controller:** Cube Orange+ with ArduCopter 4.7.1 (official).
  - **ESCs:** 2× HGLRC SPECTER 60A 4-in-1, BLHeli_32 (`SPECTER60_G_128`), DShot300 on MAIN 1–8
    through the I/O coprocessor.
  - **Link:** Pico W MAVLink Wi-Fi bridge on UDP 14550.
  - **Props:** normal (one-direction), mounted by hover sign.
  - **Motion capture:** OptiTrack Motive:Tracker 3.3.2 on the ground PC (NatNet 4.2, interface
    192.168.2.2, unicast). Rigid body `Aries_Omnidrone` is id 2, at 360 Hz.
  - **Not fitted:** battery monitor.
- **Software/model/parameter version:**
  - **Branch:** `feature/system-identification` (commits 87ebe229 … 1106d8f3 plus this entry).
  - **Code:** `hardware/ardupilot/`.
  - **Twin:** canonical XML unchanged (sha256 6303b7b90a40c15c…). The ArduPilot 6DoF Lua mixer
    is generated from its 6×8 matrix; every column gives a pure wrench in MuJoCo (off-axis
    < 1e-14).
  - **Cube parameter stages:** 1 (OptiTrack EKF), 2 (6DoF frame, forced DShot, BLHeli 3D),
    3 (`AHRS_ORIENTATION 4`), 5 (GCS-only).
- **Change or experiment, in order:**
  1. Read-only parameter audit.
  2. Stage 1 written with a verified loader.
  3. 6DoF frame and Lua mixer.
  4. Motor map and reversal test, props off.
  5. Board orientation from gravity.
  6. 6-face accelerometer calibration.
  7. OptiTrack room calibration.
  8. Ground station `omni_gcs.py`: OptiTrack to the EKF, GUIDED arm/takeoff/land, KILL, safety
     monitor, MuJoCo live twin view.
  9. Props-off arm and KILL checks.
  10. First tethered takeoff.
- **Evidence and file links:**
  - `hardware/ardupilot/audits/`: parameter audits and the motor-test CSVs.
  - `hardware/ardupilot/mocap/omni_mocap_calib.json`.
  - `hardware/ardupilot/flight_logs/` (not in git, keep): telemetry and OptiTrack CSVs, sessions
    18:26, 18:36, 18:45, 18:54 and 19:03.
  - The first lift-off is `telemetry_20261104_190320.csv` / `mocap_20261104_190320.csv`.
- **Measured results:**
  - **Motors:** map Motor1–8 = twin rotors 1–8; all 8 reverse on DShot-3D.
  - **Board orientation:** Yaw180, residual 1.1°.
  - **Accelerometer** readings 988–1005 mg per face.
  - **EKF vs OptiTrack:** 0.1 cm; Cube vs OptiTrack attitude within 0.1°.
  - **Pico link loss:** 1–12 %.
  - **First lift-off** (19:03, second attempt):
    - Every motor on its expected hover side.
    - Lift-off at about 0.08 m, then a tip to the **left**: 46° within about 1 s, 25 cm toward −E.
    - Yaw changed only +7°.
    - Outputs at lift-off: left-back rotors 3 and 7 at 1025/1050 µs (95/90 % of range,
      saturated); left-front 4 and 8 at 1887/1858 µs; right-side rotors 2 and 6 at only
      1333/1387 µs. The controller was trying to raise the left side and ran out of authority.
- **Unexpected behavior** (each one fixed or documented in the tools):
  1. **Mission Planner load-from-file** left the Cube unchanged. Replaced by
     `ap_param_load.py`, which reads every value back.
  2. **Percent motor tests are unsafe on reversible outputs.** "10 %" = 1100 µs ≈ 80 % reverse,
     and "0 %" = full reverse (`motor_test.cpp`, DShot-3D mapping). `motor_test_1.py` was guarded,
     and `motor_test_6dof.py` uses PWM 1500 ± Δ.
  3. **The 6DoF scripting frame never enables DShot** on its motors (boot banner `RCOut: PWM:1-14`):
     the motors are created after boot, and `AP_MotorsMatrix_6DoF_Scripting::init()` skips
     `set_update_rate()`. Forced with `SERVO_BLH_MASK 255` + `SERVO_BLH_OTYPE 5`.
  4. **ArduPilot sends `DSHOT_3D_ON`** (and `DSHOT_REVERSE`) only when `SERVO_DSHOT_ESC` is a
     BLHeli type; it was 0.
  5. **BLHeli pass-through cannot reach outputs driven by the I/O coprocessor.**
  6. **Mission Planner accelerometer calibration fails over the lossy Wi-Fi link**; it works over USB.
  7. **ArduPilot 4.7.1 silently rejects EKF origin 0,0,0** (`Location::is_zero` in
     `set_ekf_origin`): no home, so Guided takeoff FAILED. A non-zero origin is now required.
  8. **Any Guided position target during takeoff cancels it.** The TakeOff sub-mode switches to
     Pos, a landed vehicle is held at ground idle, and `DISARM_DELAY` then disarms it. The app now
     sends no targets until the takeoff height is reached.
  9. **A lost ACCEPTED reply** made the retry return FAILED while the takeoff was running. The app
     now checks the motor outputs.
  10. **Motive 3.3.2 streams only with a Local Interface selected**; loopback did not work.
  11. **The Pico Wi-Fi link drops packets**, so every command needs retries plus a physical kill.
- **Insight/decision:**
  - **Onboard ArduPilot control** with a twin-derived mixer. The twin's hover attitude (body −x up)
    is the most efficient one: 5.36 N per rotor.
  - **Normal props are acceptable only when mounted by hover sign**, with `ATC_ANGLE_MAX 20`. The
    twin keeps every rotor on its strong side up to 35° of tilt.
  - **GCS-only flight** with `ARMING_SKIPCHK 64` (RC checks only), `FS_THR_ENABLE 0` and
    `FS_GCS_ENABLE 5` / `FS_GCS_TIMEOUT 3`.
- **Assumptions and limitations:**
  - Mass (2.5 kg), inertia and 10 N/rotor are still unverified.
  - The weak-side thrust of normal props and the propeller reaction torque are not in the twin.
  - The kill travels over a lossy link, so a physical battery kill and a tether are required.
- **Next gate:**
  1. Check the propellers, rotors 3, 4, 7 and 8 first, with the props-on strong-side test
     (`motor_test_6dof.py --props-on --delta 50`, hover-plan step B, not yet run).
  2. Check the centre of mass left/right (battery position).
  3. Strapped spool-up (step E): left and right outputs should be balanced.
  4. Then a second tethered hover.

## Main scientific insights to preserve

1. An STL supplies geometry, not the true mass distribution.
2. Visual rotor alignment and physical thrust direction must use the same site frame.
3. Full actuation comes from the measured 6×8 wrench map, not merely from having eight
   motors.
4. Moving-reference feedforward should be corrected before retuning feedback gains.
5. Direct/Nengo agreement establishes software conformance only.
6. Motion-capture pose is a timestamped measurement with latency, covariance and
   possible occlusion—not perfect ground truth.
7. A shadow twin must not be continuously reset to the measured trajectory when its
   predictive accuracy is being evaluated.
8. MuJoCo is not CFD. Rotor inflow, wake interaction and ground effect require measured
   reduced-order models or external aerodynamic co-simulation.
9. High fidelity means held-out predictive accuracy with uncertainty, not simply a
    larger number of simulated effects.

## Workstreams and next gates

| Workstream | Present state | Next deliverable | Exit criterion | Owner |
|---|---|---|---|---|
| Repository | Local files are not a Git worktree; remote repository contains only its initial README | Public-safe import and contribution rules | Clean clone reproduces validation scripts | Team |
| Linux environment | Windows research environment currently used | Pinned Ubuntu/ROS 2/MuJoCo/Nengo environment | Reproducible build on Diego's system | Diego + Gandhi |
| ROS interfaces | Conceptual architecture | `omnicopter_interfaces` messages and frame/topic contract | Schema review accepted by all collaborators | Diego + Gandhi |
| MuJoCo bridge | Standalone Python simulation | ROS 2 node for state, commands and `/clock` in simulation | Hover and `spin_x_360` reproduce through ROS 2 | Gandhi + Diego |
| Motion capture | Hardware available in the room | Driver, marker rigid body and calibrated transforms | Static/moving pose error and latency characterized | Team |
| Rigid-body ID | Provisional STL-derived values | Measured mass, CoM and inertia with uncertainty | Ledger populated and model compiled from measured set | Gandhi + hardware lead |
| Propulsion ID | Ideal ±10 N force | Eight bidirectional thrust/torque/delay datasets | Repeatable identified actuator models | Hardware lead + Gandhi |
| Sensor/latency ID | Ideal sensor assumptions | IMU/camera noise, bias, pose and end-to-end delay | Timing and uncertainty budget frozen | Team |
| Aerodynamics | Disabled | Identified drag, then higher-order effects if required | Held-out prediction improves without overfitting | Gandhi |
| Shadow validation | Protocol only | Real commands and initial state replayed in MuJoCo | Pre-registered physical/virtual error gates pass | Team |
| HIL | Planned | Flight hardware closes loop around MuJoCo with motors safe | Timing, failure and fallback tests pass | Diego + team |
| Flight validation | Planned | Tethered PD followed by the approved Nengo controller | Safety and paired performance gates pass | Team |
| Publication | Methods draft exists | Final paper, dataset, release and reproducibility package | Independent clean reproduction and archived release | Team |

## GitHub repository plan

**Repository:** [Fabianjac/Omnidrone](https://github.com/Fabianjac/Omnidrone)  
**Observed baseline:** `main` contains only the initial `README.md`, so no legacy
history needs to be cleaned.

### Public/private boundary

The public repository may contain the MuJoCo geometry and rigid-body model, geometric
PD, the exact Nengo-PD implementation, missions, ROS 2 interfaces, identification
methodology and publishable validation tools. CAD/STL redistribution remains subject
to ownership and license confirmation.

Unreleased controller research, private source code, internal parameter studies and
unpublished results must remain in a separate private repository or an untracked
sibling directory. Never commit confidential material to the public repository and
then delete it: Git history retains the original content. Any present file that mixes
public and private implementations must be split and reviewed before its public copy
is created.

### Recommended folders

```text
Omnidrone/
  README.md
  LICENSE
  CITATION.cff
  CONTRIBUTING.md
  .gitignore
  .github/
    workflows/                # Linux build, tests and model checks
    pull_request_template.md
    CODEOWNERS
  docs/
    PROJECT_PROGRESS_LOG.md
    methodology/
    architecture/
    validation/
  ros2_ws/
    src/
      omnidrone_interfaces/   # stamped state/reference/actuator messages
      omnidrone_control/      # geometric PD and public Nengo-PD
      omnidrone_mujoco/       # MJCF, permitted meshes and simulation node
      omnidrone_bridge/       # hardware/autopilot and motion-capture adapters
      omnidrone_bringup/      # launch files and operating-mode configurations
  identification/
    protocols/
    parameter_schema/
    calibration/
  tests/
    geometry/
    controller/
    integration/
  experiments/
    manifests/                # small metadata only; no large raw bags
  tools/                      # conversion, validation and reporting utilities
  data/README.md              # external dataset locations, hashes and licenses
```

Use `omnidrone` consistently for repository, package and ROS namespace names; use
“fully actuated omnicopter” as the technical platform description.

### Branch and review strategy

- `main`: protected, reproducible and always safe to share.
- Short-lived branches created from current `main`, such as:
  - `feature/ros2-interfaces`
  - `feature/mujoco-node`
  - `feature/mocap-bridge`
  - `feature/nengo-pd`
  - `feature/system-identification`
  - `docs/methodology-progress`
- Open a pull request for every merge; require at least one collaborator review and
  passing automated checks.
- Do not maintain permanent branches per person. Ownership belongs in issues,
  pull requests and `CODEOWNERS`, while branches describe one bounded change.
- Use a temporary `release/vX.Y` branch only when stabilizing a release; publish the
  immutable result as a tag such as `v0.1.0-geometry`, `v0.2.0-ros2-sil` or
  `v1.0.0-hardware-validated`.
- Experimental branches are disposable; preserve successful experiments through a
  manifest, commit hash, parameter hash and external dataset reference.

### GitHub Project board

Use one project board with `Backlog`, `Ready`, `In progress`, `Review`, `Blocked` and
`Done`. Add fields for workstream, owner, milestone, hardware revision, evidence link
and safety relevance. Every task that changes model physics or controller behavior
must state its acceptance test before implementation.

## Proposed ROS 2 package structure

```text
ros2_ws/src/
  omnidrone_interfaces/   # stamped state, reference, actuator and status messages
  omnidrone_control/      # ROS-independent PD and Nengo-PD core plus node wrappers
  omnidrone_mujoco/       # model, simulation node, sensors and /clock
  omnidrone_bridge/       # Diego's hardware/autopilot transport interface
  omnidrone_bringup/      # launch files, parameters and operating modes
```

Operating modes must be explicit and logged:

- `simulation`: MuJoCo publishes simulated time and sensors.
- `replay`: recorded sensor data drives the estimator/controller offline.
- `shadow`: the physical platform has authority; MuJoCo predicts in parallel.
- `hil`: physical controller hardware drives the MuJoCo plant with motors disabled.
- `flight`: physical sensors and actuators are active under an independent safety layer.

## Roadmap to publication

- [ ] **R0 — Repository baseline:** import source and documentation; add license,
  README, `.gitignore`, contribution policy and immutable release conventions.
- [ ] **R1 — Linux/ROS 2 simulation:** reproduce the frozen model/controller behavior
  through the ROS 2 interface and rosbag2 logs.
- [ ] **R2 — Geometry and timing calibration:** freeze frame transforms, marker layout,
  rotor numbering, clock synchronization and transport latency.
- [ ] **R3 — Physical parameter set:** measure mass, CoM, inertia and all eight
  propulsion channels; publish uncertainty and raw-data hashes.
- [ ] **R4 — Predictive shadow twin:** validate held-out physical trajectories without
  continuously forcing MuJoCo to the measured pose.
- [ ] **R5 — Bench HIL:** close the controller/hardware loop against MuJoCo; verify
  deadlines, dropouts, saturation, E-stop and PD fallback.
- [ ] **R6 — Tethered validation:** progress from direct PD to the approved Nengo
  controller under pre-registered safety limits.
- [ ] **R7 — Confirmatory experiments:** randomized paired controller trials on data not
  used for model identification or tuning.
- [ ] **R8 — Published release:** tagged source, frozen parameter set, model hashes,
  documentation, selected data, reproducible figures and archived DOI.

## Open decisions

| Decision | Options/notes | Responsible | Due | Status |
|---|---|---|---|---|
| Linux and ROS 2 distribution | Must match Diego's framework and be pinned | Diego | TBD | Open |
| Physical hardware revision ID | Required before identification | Team | Before measurements | Open |
| Ceiling-camera system and driver | Record vendor, rate, timestamp source and covariance | Team | Before ROS bridge | Open |
| Marker/sensor arrangement | Must be rigid, asymmetric and surveyed in body coordinates | Team | Before mocap calibration | Open |
| Autopilot/ESC transport | ROS 2, MAVLink, serial, CAN or existing framework | Diego + team | Before HIL | Open |
| 500 Hz execution location | Flight computer/real-time process versus ROS node | Diego + Gandhi | Before HIL | Open |
| Dataset storage | Git LFS, GitHub release or external immutable archive | Team | Before first push | Open |
| Public license and STL redistribution | Confirm code/data/CAD permissions | Team | Before public release | Open |

## New progress-entry template

Copy this section for every material change or experiment.

```markdown
### YYYY-MM-DD — Short milestone title

- **Objective:**
- **People involved:**
- **Hardware revision:**
- **Software/model/parameter version:**
- **Change or experiment:**
- **Evidence and file links:**
- **Measured result with units and uncertainty:**
- **Unexpected behavior:**
- **Insight/decision:**
- **Assumptions and limitations:**
- **Next gate:**
```

## Experiment record template

| Field | Value |
|---|---|
| Experiment ID | |
| Date/operator | |
| Hardware revision | |
| Git commit/tag | |
| Model/parameter hashes | |
| Controller and configuration | |
| Mission and environment | |
| Identification, pilot or confirmatory dataset | |
| Raw rosbag/data path and SHA-256 | |
| Frame-calibration version | |
| Clock synchronization and measured delay | |
| Pre-registered gates | |
| Results | |
| Deviations/aborts | |
| Interpretation | |

## Definition of a finished, functional and publishable twin

The project is complete only when:

- a clean Linux/ROS 2 checkout reproduces the simulation and controllers;
- geometry, frames, time and actuator signs are independently verified;
- mass, CoM, inertia, propulsion and sensor parameters are measured with uncertainty;
- model identification and validation use disjoint datasets;
- the twin predicts held-out physical trajectories within pre-registered limits;
- shadow, bench-HIL and tethered safety stages pass;
- direct and Nengo-controller comparisons use paired, reproducible experiments;
- raw data, conversions, hashes, parameters and deviations are traceable;
- the repository has a tagged release, documentation, license and archived dataset;
- publication claims remain inside the demonstrated fidelity envelope.
