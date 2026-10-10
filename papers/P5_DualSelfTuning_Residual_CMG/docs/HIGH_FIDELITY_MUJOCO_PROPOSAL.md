# Proposal: high-fidelity MuJoCo models for CF2, X2 and the Omnicopter (v0, 2026-09-12)

**Active scope update (2026-10-06):** Complete the X2 and CF2 variants first, then use the existing MuJoCo racing world as a stress test and QDrone2 as a separate, physically identified hardware endpoint. Do not transfer QDrone2 motor parameters to X2/CF2. The readiness/validation gates are in `QUAD_TWINS_QDRONE2_STABILITY_2026-10-06.md`. This original three-vehicle proposal remains the historical design basis.

## 0. Question and short answer

**Can MuJoCo reproduce a virtual twin of these vehicles?** Yes, for everything a flight controller "sees":
- rigid-body 6-DOF dynamics and contact;
- motor, ESC and propeller dynamics, including rotor inertia and reaction torque;
- battery sag;
- reduced-order aerodynamics (rotor drag, body drag, ground effect);
- IMU and estimator effects.

The prerequisite is that every parameter is identified and every effect is validated on held-out flight data.

**No, for flow physics.** MuJoCo is not CFD. Propeller wakes, rotor–rotor interference inside the Omnicopter
cage, and vortex-ring state need identified correction models or co-simulation.

So the achievable target is a **predictive control-level twin**: prediction intervals that cover held-out
trajectories. It is not a first-principles aerodynamic twin. This matches the Omnicopter
`DIGITAL_TWIN_METHODOLOGY.md` and `TWIN_HARDWARE_VALIDATION_PROTOCOL.md`, which already set the validation
standard. This proposal extends that standard to CF2 and X2 and adds the propulsion and animation layers.

**Governing rule (inherited).** The canonical ideal models stay untouched as the regression layer. Fidelity is
added as **model variants**. A variant carries only parameters that are measured or sourced, each with units,
uncertainty, source and hash. Unknowns stay `null`, never a generic constant.

## 1. Fidelity levels and acceptance gates

| Level | Adds | Gate to pass before the next level |
|---|---|---|
| **L0** (today) | Rigid body, gravity, contact, ideal instantaneous thrust (CF2/X2: rotor forces plus reaction gear; Omnicopter: 8 signed site forces) | Existing regression suites (ACC 2027 matched runs; Omnicopter 25-mission campaign) |
| **L1** propulsion | ESC/motor dynamics, thrust and torque as functions of rotor speed, rotor inertia and gyroscopic coupling, deadband, bidirectional maps (Omnicopter) | Simulated vs bench step response of each propulsion unit within the pre-registered tolerance; hover throttle within ±3% |
| **L2** electrical | Battery open-circuit voltage vs state of charge, internal resistance, voltage sag feeding the motor model | Hover-throttle drift over a full pack within tolerance |
| **L3** aerodynamics | Rotor drag / H-force (linear in the in-plane velocity), MuJoCo fluid body drag, ground effect | Free-decay and forward-flight acceleration residuals within tolerance on held-out data |
| **L4** sensing | IMU noise, bias random walk, bandwidth and delay; estimator delay; control transport delay | Shadow-mode attitude and position prediction intervals cover held-out trajectories |

Tolerances are pre-registered from measurement uncertainty plus controller sensitivity, as in the Omnicopter ledger.

## 2. Propulsion model (L1). This is the core of "add motors and propellers"

Per rotor i:

```
ESC + motor:   ω̇_i = (ω_cmd,i − ω_i) / τ_m                     (first-order, identified τ_m)
          or   L di/dt = V − R i − K_e ω_i,   J_r ω̇_i = K_t i − Q_i − b ω_i   (DC-motor model)
Propeller:     T_i = k_f ω_i |ω_i| ,   Q_i = k_m ω_i |ω_i|      (signed; Omnicopter uses k_f± per direction)
Wrench:        F = Σ T_i d_i ,   τ = Σ [ p_i × T_i d_i  +  s_i Q_i d_i ]  +  gyroscopic (J_r ω_i d_i) × Ω
```

The model follows Mahony, Kumar and Corke (IEEE RAM 19(3):20–32, 2012) and standard rotor momentum
theory; the inflow correction is added at L3.

### MuJoCo implementation (verified against the installed MuJoCo 3.12.0)

- **Actuator dynamics.** The installed version exposes `mjDYN_{NONE, INTEGRATOR, FILTER, FILTEREXACT, MUSCLE, USER, DCMOTOR, PID}`,
  gains `mjGAIN_{FIXED, AFFINE, MUSCLE, USER, DCMOTOR, PID, SO3}`, biases `mjBIAS_{NONE, AFFINE, MUSCLE, USER, DCMOTOR, SO3}`,
  and the callbacks `set_mjcb_act_dyn / act_gain / act_bias / control / passive / sensor`.
- **Option A: kinematic rotor state (fast, recommended first).** Each rotor gets a `general` actuator with
  `dyntype="filterexact"` and `dynprm="τ_m"`. The actuator activation is then the rotor-speed state. A
  `mjcb_act_gain` (or a control-loop update) applies `T = k_f act|act|` along the existing thrust site, and a
  second site/gear term applies `Q`. This needs no new bodies, keeps the timestep, and matches identified
  first-order data.
- **Option B: dynamic propellers (full gyroscopics, real animation).** Each propeller is a child body on a `hinge`
  joint along the shaft, with measured rotor inertia and collision disabled (`contype=conaffinity=0`), driven by a
  `dcmotor` actuator (`motorconst`, `resistance`, `inductance`, `damping`, `armature`). Thrust and drag torque come
  from the joint velocity in `mjcb_passive` (or as site forces each step). Reaction torque and gyroscopic coupling
  then follow from the joint dynamics.
  - *Cost.* Stiffer dynamics (ω about 2–3×10³ rad/s for CF2), so the timestep must stay ≤ 0.5 ms (implicit
    integration helps). Benchmark before adopting.
- **Bidirectional Omnicopter rotors.** Use separate forward and reverse maps, with deadband and hysteresis from
  the load-cell sweep.

### Parameter sources

| Quantity | CF2 | X2 | Omnicopter |
|---|---|---|---|
| Mass, inertia | Menagerie + Förster 2015 (ETH BSc thesis, inertia and motor maps) | Menagerie geometry; manufacturer data not published | Mesh-inferred; the ledger requires scale, CAD or pendulum |
| k_f, k_m, command→ω map | Förster 2015; Bitcraze PWM-to-thrust tables | **Bench test required** (no manufacturer propulsion data) | **Load-cell sweep, both directions** (ledger: `measurement_required`) |
| τ_m | Bitcraze RPM step, about 180 ms full command (reported, not an identified τ) | Bench step test | Bench step test |
| Rotor inertia J_r | Propeller mass and geometry (scale) | Measure | Measure |

X2 and Omnicopter L1 variants stay **parameter templates** until bench data exist. CF2 can reach L1 from published sources, clearly labelled "literature-sourced, not our hardware".

## 3. Electrical (L2)

`V_bus = V_oc(SOC) − R_int Σ i`, with SOC integrated from the current. Motor speed limits and gains scale with
V_bus. Implement it in the control loop (Option A) or feed the `dcmotor` input (Option B). Parameters come
from discharge tests at constant hover.

## 4. Aerodynamics (L3)

- **Rotor drag / H-force.** `F_drag = −R D Rᵀ v` with D diagonal, linear in rotor-plane velocity (Faessler,
  Franchi, Scaramuzza, IEEE RA-L 3(2):620–626, 2018). Cheap, identifiable from flight data, and it matters for
  6-DOF tracking.
- **Body drag.** MuJoCo's native fluid model: `<option density="1.2" viscosity="1.8e-5" wind="…"/>` plus per-geom
  `fluidshape="ellipsoid"` / `fluidcoef`. It is quadratic in velocity. Coefficients must be identified; it is
  reduced-order, not CFD.
- **Ground effect.** A thrust multiplier as a function of rotor height (the classical Cheeseman–Bennett
  form), applied only below about 2 rotor diameters. It needs a takeoff/landing validation.
- **Omnicopter cage interference.** Data-driven per-rotor thrust-efficiency factors versus attitude and rotor
  pair, identified in flight. There is no physical MuJoCo model for it.

## 5. Sensing and computation (L4)

- **Sensors.** MuJoCo `gyro` / `accelerometer` sensors already exist on the Omnicopter `imu_site`; add them to CF2 and X2.
  In Python, add Gaussian noise (density from Allan variance), bias random walk, a first-order bandwidth, and a
  ring-buffer delay.
- **Estimation.** A complementary or EKF attitude estimator in the loop replaces the direct `qpos`/`qvel` feedback
  used today. This matters for CMG–PES, whose learning target uses measured error.

## 6. Animation

- **Spinning propellers.**
  - With Option B, the rotation is physical.
  - With Option A, a kinematic hinge advanced by ∫ω dt gives a **visual-only** spin. It must be excluded from
    physical claims (as the Omnicopter doc already states).
- **Overlays.** `mujoco.viewer.launch_passive` with per-frame user geoms (thrust arrows scaled by T_i, reference
  frame, trajectory trail) through `viewer.user_scn`.
- **Video.** Offscreen `mujoco.Renderer` → frames → MP4 (imageio-ffmpeg). The camera tracks the body; side-by-side
  PID vs dual, synchronized with the error plots.
- **Deliverable.** `tools/animate.py --run <trace dir>` replays any logged campaign trace. Replay is deterministic
  and needs no re-simulation.

## 7. Implementation plan

| Step | Work | Output | Effort |
|---|---|---|---|
| 1 | Shared `hifi/propulsion.py` (Option A), `hifi/sensors.py`, `hifi/aero.py` with unit tests; the ideal model is recovered exactly when the effects are off | Library + tests | 3–4 days |
| 2 | CF2 L1–L2 variant from literature parameters; step-response and hover tests | `models/hifi/cf2/` | 2 days |
| 3 | Replay/animation tool; propeller spin (visual) + thrust arrows | MP4s of ACC 2027 runs | 2 days |
| 4 | X2 and Omnicopter L1 templates (null parameters) plus a bench-test card; shared log schema (reuse the Omnicopter `COMMON_LOG_SCHEMA.md`) | Templates + test cards | 2 days |
| 5 | Option B prototype on CF2: dcmotor + hinge propellers; timestep and cost benchmark | Decision memo A vs B | 2–3 days |
| 6 | L3 rotor drag and fluid body drag, identification scripts; held-out validation once data exist | Identified variants | Data-dependent |
| 7 | Rerun P5 Phase 2–3 campaigns on L1+ variants (H3: does learning help more under realistic propulsion?) | Campaign reports | 1 week |

## 8. Risks

- **Parameter illusion.** A detailed model with unidentified parameters is less trustworthy than the ideal one.
  Keep the null-until-measured rule.
- **Stiffness.** Option B rotor speeds can force smaller steps. Benchmark first; use Option A for campaigns.
- **Scope creep into CFD.** Cage interference and wakes stay data-driven corrections.
- **Controller confound.** Retune nothing silently when fidelity changes. Report the ideal and high-fidelity
  results side by side.
