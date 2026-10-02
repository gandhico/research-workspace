# Omnidrone Virtual Twin and Controller Validation Methodology

**Public technical document**  
**Version:** Draft 0.1 — 2026-09-23  
**Scope:** MuJoCo virtual twin, geometric PD control, Nengo-PD execution,
software validation, physical identification, ROS 2 integration and HIL roadmap

## 1. Purpose and claim boundary

This document defines a traceable methodology for developing and validating a
MuJoCo virtual twin of a fully actuated eight-rotor omnicopter. It connects the
mathematical model to the executable controller, simulation tests, physical
identification campaign and future hardware-in-the-loop (HIL) operation.

The present model is a **controller-development twin**. Its rotor geometry and
software-control path are well defined and regression tested, but several physical
parameters remain inferred or configured rather than measured. It must not yet be
described as a fully predictive hardware twin.

Only the public controller baseline is described here:

1. direct geometric proportional-derivative control with analytic feedforward; and
2. the same mathematical law executed through a Nengo computational graph.

The current Nengo implementation uses an exact `nengo.Node` computation. It is a
backend-conformance implementation, not a neural approximation and not evidence of a
performance advantage from neuromorphic computation. Unreleased research controllers
and private experimental results are outside the scope of the public repository.

## 2. Reproducibility principles

The project follows six principles:

1. **Geometry before tuning:** verify rotor positions, axes, signs and numbering before
   changing controller gains.
2. **Measured parameters before added fidelity:** unknown physical values remain
   explicitly unknown rather than being replaced by generic drone constants.
3. **One mathematical core:** direct, Nengo, simulation and hardware interfaces use the
   same frames, state definitions, references, gains, actuator map and limits.
4. **Identification and validation are disjoint:** data used to fit parameters are not
   reused to claim predictive validity.
5. **Evidence is versioned:** model, mesh, controller, parameter and mission hashes are
   recorded with each released experiment.
6. **Claims follow demonstrated fidelity:** software agreement is not physical
   validation, and visual similarity is not parameter identification.

## 3. Frames, state and notation

The following frames are used:

- \(\mathcal{W}\): MuJoCo world frame;
- \(\mathcal{B}\): vehicle body frame at the MuJoCo body origin;
- \(\mathcal{C}\): centre-of-mass frame, parallel to \(\mathcal{B}\);
- \(\mathcal{S}_i\): local frame of rotor site \(i\);
- \(\mathcal{I}\): physical IMU frame; and
- \(\mathcal{M}\): external motion-capture frame.

The rigid-body state is

\[
x = \left(p^\mathcal{W}_{B},\;q^\mathcal{W}_{B},\;v^\mathcal{W}_{B},\;
\omega^\mathcal{B}\right),
\]

where \(p\in\mathbb{R}^3\), the unit quaternion is stored scalar-first as
\(q=[q_w,q_x,q_y,q_z]\), and \(\omega\) is expressed in body coordinates. The
rotation matrix \(R(q)\in SO(3)\) maps body vectors into world coordinates.

The body origin and centre of mass are not assumed to coincide. If
\(r^\mathcal{B}_{BC}\) is the body-frame centre-of-mass offset, then

\[
p^\mathcal{W}_{C}=p^\mathcal{W}_{B}+R(q)r^\mathcal{B}_{BC},
\qquad
v^\mathcal{W}_{C}=v^\mathcal{W}_{B}
+R(q)\left(\omega^\mathcal{B}\times r^\mathcal{B}_{BC}\right).
\]

Every physical sensor transform must be calibrated into this tree. Axis swaps or sign
changes may not be selected retrospectively by observing which choice produces the
best trajectory agreement.

## 4. MuJoCo virtual-twin construction

### 4.1 STL registration

The source STL uses millimetres. The MJCF mesh scale is

```xml
scale="0.001 0.001 0.001"
```

and the mesh is translated by

\[
t^\mathcal{B}_{mesh}=(0.1936,-0.2036,0.1786)\ \mathrm{m}
\]

to register the physical cage with the selected body frame. This translation is a
mesh-registration transform; it is not a rotor position or centre-of-mass correction.

### 4.2 Rotor positions and local frames

The eight configured rotor sites occupy all sign combinations of

\[
p_i^\mathcal{B}=(\pm0.0973,\pm0.0973,\pm0.0973)\ \mathrm{m}.
\]

For every site, local X follows the outward beam direction:

\[
\hat{x}_i=\frac{p_i^\mathcal{B}}{\lVert p_i^\mathcal{B}\rVert}.
\]

The local Z direction \(\hat{z}_i\) is the normal of the hardware-selected right face
of the square beam. The remaining axis is

\[
\hat{y}_i=\hat{z}_i\times\hat{x}_i.
\]

The acceptance conditions for each compiled site rotation \(R^\mathcal{B}_{S_i}\) are

\[
R^T R=I,\qquad \det(R)=+1,
\]

with the first and third columns equal to the approved \(\hat{x}_i\) and
\(\hat{z}_i\). The same local Z direction defines both the displayed motor cylinder
axis and the applied thrust direction. Rotor-frame orientation therefore changes the
physics and is not a cosmetic viewer setting.

### 4.3 Current parameter set

| Parameter | Current value | Status |
|---|---:|---|
| Simulation timestep | `0.002 s` | Configured |
| Gravity | `(0,0,-9.81) m/s²` | Configured |
| Mass | `2.5 kg` | Configured, unverified |
| CoM in body | `(0.00326881, 0.00071909, 0.00103101) m` | Mesh inferred, unverified |
| Inertia \(J_B\) | Full tensor shown below | Uniform-density mesh inferred |
| Rotor-site coordinate magnitude | `0.0973 m` | Configured, final survey pending |
| Per-rotor command bound | `[-10,10] N` | Configured, unverified |
| Actuator dynamics | Memoryless unit-gain force | Ideal assumption |
| Fluid density and viscosity | Zero | Aerodynamics disabled |
| Wind | `(0,0,0) m/s` | Configured zero |
| IMU pose | Body origin, identity rotation | Configured, unverified |

The current body-frame inertia tensor is

\[
J_B=\begin{bmatrix}
0.0862437890 & 0.0000215936 & -0.0000369610\\
0.0000215936 & 0.0862749670 & 0.0000039037\\
-0.0000369610 & 0.0000039037 & 0.0861079624
\end{bmatrix}\ \mathrm{kg\,m^2}.
\]

These mass properties are provisional. The STL determines external shape, but a
uniform-density mesh does not represent the real distribution of motors, battery,
electronics, fasteners and payload.

## 5. Rigid-body and actuator mathematics

Ignoring contact for the airborne case, the six-degree-of-freedom dynamics are

\[
m\dot{v}_C^\mathcal{W}=m g^\mathcal{W}+R(q)F^\mathcal{B}
+f_{ext}^\mathcal{W},
\]

\[
J_B\dot{\omega}^\mathcal{B}
+\omega^\mathcal{B}\times J_B\omega^\mathcal{B}
=\tau^\mathcal{B}+\tau_{ext}^\mathcal{B},
\]

and quaternion kinematics are

\[
\dot q=\frac{1}{2}q\otimes[0,\omega^\mathcal{B}].
\]

For signed rotor thrust \(u_i\), body-frame direction \(d_i=\hat z_i\), rotor
position \(p_i\), centre of mass \(p_C\), and reaction torque per unit thrust
\(k_{\tau i}\), the actuator column is

\[
B_i=\begin{bmatrix}
d_i\\
(p_i-p_C)\times d_i+k_{\tau i}
\end{bmatrix}.
\]

At present, \(k_{\tau i}=0\) because reaction torque has not been measured. The full
allocation matrix is

\[
B=[B_1\ B_2\ \cdots\ B_8]\in\mathbb{R}^{6\times8},
\qquad w=Bu,
\]

where \(w=[F_B^T,\tau_B^T]^T\). The compiled matrix has rank six, so it provides
instantaneous authority over all six wrench components within actuator bounds.

Rank six is necessary but not sufficient for a mission: the requested wrench must also
lie inside the bounded attainable set generated by the eight columns.

## 6. Conventional geometric PD controller

### 6.1 Translational control

With desired centre-of-mass position, velocity and acceleration
\((p_d,v_d,a_d)\), define

\[
e_p=p_d-p_C,\qquad e_v=v_d-v_C.
\]

The requested world-frame force is

\[
F_d^\mathcal{W}=m\left(a_d+K_p e_p+K_d e_v-g^\mathcal{W}\right),
\]

and the body-frame force passed to the allocator is

\[
F_d^\mathcal{B}=R(q)^T F_d^\mathcal{W}.
\]

Current scalar gains are

\[
K_p=4.0,\qquad K_d=3.6.
\]

### 6.2 Quaternion attitude error

Let the quaternion error mapping current attitude to desired attitude be

\[
q_e=q^{-1}\otimes q_d=[\eta_e,\epsilon_e].
\]

Because \(q\) and \(-q\) represent the same physical attitude, the implementation
changes the sign of \(q_e\) when \(\eta_e<0\). The body-frame shortest rotation vector
is

\[
e_R=
\begin{cases}
2\epsilon_e, & \lVert\epsilon_e\rVert\approx0,\\
2\dfrac{\operatorname{atan2}(\lVert\epsilon_e\rVert,\eta_e)}
{\lVert\epsilon_e\rVert}\epsilon_e, & \text{otherwise}.
\end{cases}
\]

This formulation avoids Euler-angle singularities and produces zero error for the
equivalent pair \(q\) and \(-q\).

### 6.3 Rotational control

For desired body angular velocity \(\omega_d\) and angular acceleration \(\alpha_d\),

\[
\tau_d^\mathcal{B}=J_B\left(\alpha_d+K_R e_R
+K_\omega(\omega_d-\omega)\right)
+\omega\times J_B\omega.
\]

Current scalar gains are

\[
K_R=16.0,\qquad K_\omega=7.2.
\]

The gyroscopic term \(\omega\times J_B\omega\) compensates the known rigid-body
coupling represented by the present inertia model.

### 6.4 Bounded allocation

The desired wrench is

\[
w_d=\begin{bmatrix}F_d^\mathcal{B}\\\tau_d^\mathcal{B}\end{bmatrix}.
\]

Rotor commands solve the weighted bounded least-squares problem

\[
u^*=\arg\min_{u_{min}\le u\le u_{max}}
\left\lVert W(Bu-w_d)\right\rVert_2^2.
\]

The weighting matrix balances force and torque units using a characteristic moment-arm
length. If the unconstrained minimum-norm solution is feasible, it is used directly.
Otherwise, an active-set solver fixes violated commands at their bounds and
redistributes the remaining demand. Merely clipping an unconstrained mixer would not
solve the constrained allocation problem.

The implementation records

\[
r_w=Bu^*-w_d
\]

as separate force and torque residuals and marks every saturated timestep.

## 7. Trajectory generation and complete rotations

References use a quintic time-scaling polynomial

\[
h(s)=10s^3-15s^4+6s^5,\qquad s\in[0,1],
\]

whose first two derivatives vanish at both endpoints. Position, velocity and
acceleration are generated analytically rather than numerically differentiated.

A complete rotation cannot be specified by final attitude alone because a 360-degree
turn returns to the same physical orientation. For fixed world axis \(a\), the
reference is advanced continuously through

\[
\theta(t)=\theta_{total}h(s),
\]

\[
q_a(\theta)=\left[\cos\frac{\theta}{2},\;
a\sin\frac{\theta}{2}\right],
\qquad q_d=q_a(\theta)\otimes q_0.
\]

The terminal quaternion of a positive full turn is \(-q_0\), which is physically
equivalent to \(q_0\). Therefore the validation code also integrates signed incremental
quaternion motion and projects it on the commanded world axis. This prevents a vehicle
that never rotated from passing only because its final attitude is equivalent.

## 8. Nengo implementation and neuromorphic boundary

### 8.1 Present public Nengo controller

The public `NengoPDController` constructs a Nengo graph with:

- a 33-value input node containing rotation, measured rates, COM velocity, tracking
  errors and reference accelerations;
- a deterministic function implementing the same force and torque equations derived
  above;
- a six-value body-wrench output node; and
- the same bounded 6×8 allocator used by direct PD.

Connections have no synaptic filtering, the simulation timestep is the same `0.002 s`,
and the Nengo network uses a fixed seed. The expected invariant is

\[
w_{Nengo}(x,x_d)=w_{direct}(x,x_d)
\]

to numerical precision for the same state and reference.

### 8.2 What may be called neuromorphic

Nengo is a framework capable of representing neural and neuromorphic computations,
but using a `Node` to execute an ordinary equation does not make that equation a neural
controller. The current public implementation establishes:

- a stable Nengo-compatible state and wrench interface;
- deterministic stepping at the control timestep;
- a reference backend for future neural implementations; and
- direct numerical comparison with the conventional controller.

It does **not** presently establish:

- representation by neuron populations;
- spiking or event-based execution;
- learned decoder performance;
- robustness improvement caused by neural computation; or
- deployment on neuromorphic hardware.

Any future public neural controller must declare its neuron model, encoders, decoders,
synapses, learning rule, training/evaluation separation, random seeds, computational
budget and fallback behavior. It must be compared with direct PD on identical data and
through the same actuator allocator.

## 9. Code architecture required for the public repository

The intended public implementation separates mathematics from transport:

```text
omnidrone_control/
  geometry.py          # quaternion and frame operations
  allocator.py         # bounded 6x8 weighted least squares
  geometric_pd.py      # ROS-independent controller core
  references.py        # analytic mission trajectories
  nengo_pd.py          # exact Nengo execution of public PD
  controller_node.py   # ROS 2 wrapper only
```

The core controller accepts typed numerical state/reference structures and returns a
desired wrench plus eight bounded rotor commands. It must not import ROS 2 message
types. The ROS node performs message conversion, timestamp checks, parameter loading,
publication and diagnostics.

Representative public-safe pseudocode is:

```python
def command(state, reference, parameters):
    ep = reference.com_position - state.com_position
    ev = reference.com_velocity - state.com_velocity
    er = shortest_quaternion_rotation(state.attitude, reference.attitude)
    ew = reference.body_rate - state.body_rate

    force_world = parameters.mass * (
        reference.com_acceleration
        + parameters.kp_position * ep
        + parameters.kd_position * ev
        - parameters.gravity_world
    )
    torque_body = parameters.inertia_body @ (
        reference.body_acceleration
        + parameters.kp_attitude * er
        + parameters.kd_attitude * ew
    ) + cross(state.body_rate, parameters.inertia_body @ state.body_rate)

    wrench_body = concatenate((state.R_world_body.T @ force_world, torque_body))
    rotor_thrust = allocator.solve(wrench_body)
    return wrench_body, rotor_thrust
```

## 10. Validation hierarchy

Validation is progressive. Passing a higher-numbered software layer does not replace
the physical layers below it.

### V0 — Static model and schema validation

- MJCF and STL load without warnings.
- Exactly one free body and eight expected actuators exist.
- Units, names, actuator bounds and timestep match the parameter ledger.
- Parameters marked unknown remain unknown rather than silently defaulted.

### V1 — Geometry and actuation validation

- Rotor positions match the approved drawing/survey.
- Every site frame is orthonormal with determinant +1.
- Rotor X axes match beam directions and Z axes match approved thrust directions.
- Actuator-to-site numbering is one-to-one.
- Each analytically constructed wrench column matches MuJoCo generalized actuator
  force for a unit command.
- \(\operatorname{rank}(B)=6\).

### V2 — Controller unit validation

- Quaternion sign invariance: \(e_R(q,-q)=0\).
- Static equilibrium produces finite bounded thrust.
- Force and torque equations are tested independently.
- The allocator satisfies bounds and Karush-Kuhn-Tucker optimality conditions.
- The constrained solution is no worse than direct clipping under the weighted cost.

### V3 — Direct/Nengo conformance

For a deterministic state/reference sequence, record

\[
\Delta_w=\max_k\lVert w_{direct,k}-w_{Nengo,k}\rVert_\infty,
\]

\[
\Delta_u=\max_k\lVert u_{direct,k}-u_{Nengo,k}\rVert_\infty.
\]

The conformance tolerance must be selected before inspecting a release run. Different
random seeds or hidden filtering are not permitted in an exact-backend test.

### V4 — Deterministic mission regression

The 25-mission suite progresses through:

1. hover and quaternion-sign invariance;
2. independent X/Y/Z translations;
3. small 15-degree rotations;
4. 45-, 90- and 180-degree reorientations;
5. complete X/Y/Z-axis rotations;
6. circle, figure eight, helix and simultaneous circle/yaw;
7. repeatable injected velocity disturbances; and
8. progressively faster complete yaw rotations.

Each mission records tracking error, signed rotation progress, rotor thrust,
saturation, allocation error, contact and abort state.

### V5 — Parameter sensitivity and robustness

Perturb mass, centre of mass, inertia, actuator gain and delay within declared ranges.
This layer identifies parameters to which the controller is most sensitive; it does not
replace physical measurements.

### V6 — Physical parameter identification

Identify parameters from dedicated experiments with uncertainty and immutable raw
data. Update the parameter ledger and create a new model version.

### V7 — Shadow prediction

Initialize MuJoCo from a physical state and drive it with the measured reference and
actuator commands while the real vehicle retains all authority. For a predictive test,
do not continuously reset simulated pose to motion-capture pose.

### V8 — Bench HIL

The physical flight computer receives simulated sensor messages and sends commands to
the MuJoCo plant. Motors remain disabled or otherwise physically safe. Verify rates,
deadlines, packet loss, watchdogs, command bounds and fallback behavior.

### V9 — Tethered and held-out flight validation

Progress from low-authority restrained tests to tethered flight only after frame,
timing, actuator and E-stop checks pass. Confirmatory missions and acceptance gates are
frozen before the held-out data are inspected.

## 11. Present public software evidence

At the current checkpoint:

- direct PD and Nengo-PD each completed all 25 nominal missions;
- neither reported actuator saturation in that campaign;
- both produced aggregate mean position RMSE `0.001029 m`;
- both produced aggregate mean attitude RMSE `0.0260 deg`; and
- the same-state PD conformance test showed zero discrepancy at stored precision.

For the direct-PD `spin_x_360` mission:

| Metric | Result |
|---|---:|
| Planned/actual rotation | `360 deg / 360 deg` |
| Mission duration | `58 s` |
| Position RMSE | `1.55e-8 m` |
| Attitude RMSE | `2.65e-4 deg` |
| Peak rotor command | `9.121 N` |
| Saturated steps | `0` |
| Contacts | `0` |

These very small errors are expected from a deterministic exact-model simulation. They
are regression evidence, not estimates of future hardware accuracy.

## 12. Physical identification plan

### 12.1 Mass and centre of mass

- Measure complete flight mass using a calibrated scale.
- Determine CoM using at least three independent suspension or support orientations.
- Fit the body-frame CoM and covariance from the intersecting gravity lines/planes.
- Repeat after any battery, payload or structural revision.

### 12.2 Inertia

Use one of:

- component CAD reconciled with measured component masses; or
- bifilar/trifilar pendulum experiments about multiple axes.

Identify the full symmetric positive-definite tensor, not only three diagonal values.
Report uncertainty and the transform between experimental and body axes.

### 12.3 Propulsion

For each numbered motor/propeller/ESC channel and several battery voltages, measure:

- signed command, RPM and axial thrust;
- reaction torque;
- deadband, hysteresis and channel dispersion;
- current and voltage;
- step response, delay and first-order or higher-order dynamics; and
- repeatability in both thrust directions.

The identified model replaces the current direct-newton assumption. Rotor spinning for
visualization alone does not generate aerodynamic thrust in MuJoCo.

### 12.4 Sensors and timing

Calibrate IMU scale, axis orientation, translation, bias, noise density, bandwidth and
latency. For the ceiling-camera system, store pose covariance, marker quality,
occlusions and acquisition—not reception—timestamps.

The transforms

\[
T^\mathcal{W}_{\mathcal{M}},\qquad T^\mathcal{B}_{\mathcal{I}},\qquad
T^\mathcal{B}_{marker}
\]

are estimated in dedicated calibration trials and frozen before validation missions.

### 12.5 Aerodynamics

Begin with identifiable low-order effects such as translational and rotational drag.
Use free-decay, fan, wind-tunnel or instrumented-flight data covering the intended
operating envelope. Add ground effect, rotor inflow or rotor interaction only when the
data demonstrate that simpler models are inadequate.

MuJoCo provides reduced-order fluid forces but is not a computational-fluid-dynamics
solver. Higher-order rotor-flow effects require validated custom wrenches, plugins or
external co-simulation.

## 13. ROS 2 connection architecture

```text
ceiling cameras ---> motion-capture driver ---+
                                                |
onboard IMU ------> IMU driver ----------------+--> estimator --> stamped state
                                                |                    |
other sensors ----> sensor drivers ------------+                    v
mission manager -------------------------------------------> controller core
                                                                     |
                                                          desired body wrench
                                                                     |
                                                          bounded 6x8 allocator
                                                                     |
                                                       eight thrust commands
                                                          /                 \
                                                MuJoCo plant          hardware bridge
                                                   |                       |
                                            simulated sensors          ESC/autopilot
```

Minimum public interfaces are:

- stamped synchronized state;
- stamped mission reference;
- baseline body wrench;
- eight signed thrust commands with units;
- actuator status, voltage/current and saturation;
- safety/fallback status;
- `tf2` frame transforms; and
- simulation `/clock` only in simulation mode.

The 500 Hz safety-critical control loop must not depend on unmeasured network latency.
ROS 2 may provide orchestration, configuration, observation and data transport, while
the final execution location is chosen from measured deadline and jitter evidence.

## 14. Physical/virtual comparison metrics

After fixed frame and clock conversion, compare paired physical and virtual logs using:

### Position

\[
e_p(t)=\lVert p_h(t)-p_m(t)\rVert_2,
\qquad
RMSE_p=\sqrt{\frac1N\sum_k e_p(k)^2}.
\]

### Quaternion-geodesic attitude

\[
e_R(t)=2\cos^{-1}\left(\left|q_h(t)^Tq_m(t)\right|\right).
\]

The absolute inner product makes the metric invariant to quaternion sign.

### Angular rate and actuators

\[
RMSE_\omega=\sqrt{\frac1N\sum_k
\lVert\omega_h(k)-\omega_m(k)\rVert_2^2},
\]

with analogous per-channel metrics for RPM, thrust estimate, current and command.

Also report peak error, settling/recovery time, saturation fraction, energy, packet
loss, timestamp age, aborts and missing data. Do not optimize the physical/virtual time
shift against trajectory agreement; obtain it from the clock-synchronization system.

## 15. Experimental design

- Separate development, identification, pilot and confirmatory datasets.
- Pre-register hypotheses, missions, metrics, exclusions and gates.
- Use paired blocks with the same battery state, payload and environmental condition.
- Randomize controller order where operationally safe.
- Report every repetition, not only averages or successful trials.
- Carry parameter and measurement uncertainty into predictive intervals.
- Record all deviations and aborted runs.
- Never use the held-out validation trials to tune the model they evaluate.

## 16. Automated public checks

The public continuous-integration workflow should perform at least:

```text
1. Parse/compile MJCF.
2. Verify rotor frames, numbering and rank(B)=6.
3. Test quaternion sign invariance.
4. Test allocator bounds and KKT conditions.
5. Run deterministic hover acceptance tests.
6. Compare direct PD and Nengo-PD on identical state sequences.
7. Run a short mission regression subset on every pull request.
8. Run the complete 25-mission suite for release candidates.
9. Confirm that generated reports include model/code/parameter hashes.
10. Scan the public tree for forbidden private-material patterns before merge.
```

A release is invalid if a test is disabled merely to obtain a passing status. Changes
to gates, gains or physics create a new versioned result rather than overwriting the
previous evidence.

## 17. Known limitations at this checkpoint

- Mass, CoM and inertia are not physically measured.
- Rotor positions require final metrology.
- Thrust limits and bidirectional curves are not identified.
- Motor lag, reaction torque, rotor inertia and battery voltage effects are absent.
- Sensor noise, estimator delay and communication delay are absent.
- Body drag, wind, inflow, wake interaction and ground effect are absent.
- The controller receives ideal state feedback in the nominal simulation.
- The Nengo-PD implementation is exact equation execution, not a neuron-population
  approximation.
- Current mission gates are simulation engineering gates, not flight-safety limits.
- No ROS 2 bridge, shadow run, bench HIL or physical predictive-validation result has
  yet been released.

## 18. Release evidence package

Every released experiment should contain:

- Git commit and release tag;
- hardware revision and operator;
- XML/STL and controller hashes;
- complete parameter file with status and uncertainty;
- ROS 2 distribution, RMW, MuJoCo, Nengo and Python versions;
- mission/reference definition and acceptance gates;
- raw immutable rosbag or hardware log;
- frame and time-calibration manifests;
- converted common-schema data;
- plots, metrics, aborts and deviations; and
- a machine-readable manifest linking every artifact by SHA-256.

Large raw data should be stored in an immutable dataset archive or Git LFS according to
the repository policy. The Git repository should retain metadata, hashes and retrieval
instructions even when the raw data are stored externally.

## 19. Publication-ready claims after each milestone

| Milestone | Claim permitted |
|---|---|
| Geometry regression | Rotor frames and software actuator map are internally consistent |
| Direct/Nengo conformance | Both backends implement the same public control equation |
| Nominal mission campaign | Controller/model pair satisfies declared simulation gates |
| Parameter identification | Listed physical parameters were measured with uncertainty |
| Held-out shadow validation | Twin predicts unused physical trajectories within declared limits |
| Bench HIL | Hardware/software loop satisfies timing and failure-handling tests |
| Tethered/flight validation | Controller and twin satisfy the tested physical operating envelope |

No earlier milestone should be described using a later milestone's claim.

## 20. Immediate next actions

1. Create the public GitHub foundation and protected `main` branch.
2. Extract a clean public PD core, allocator and Nengo-PD implementation.
3. Add public unit and conformance tests.
4. Reproduce hover and `spin_x_360` in the Linux/ROS 2 environment.
5. Define stamped ROS 2 interfaces and `tf2` frame names with the integration team.
6. Connect motion capture and IMU in read-only mode and characterize timing.
7. Assign a hardware-revision identifier and populate the physical-measurement ledger.
8. Perform mass/CoM/inertia and bidirectional propulsion identification before adding
   higher-fidelity physics.

## References

- MuJoCo documentation: <https://mujoco.readthedocs.io/>
- MuJoCo computation and fluid-force model:
  <https://mujoco.readthedocs.io/en/stable/computation/fluid.html>
- Nengo documentation: <https://www.nengo.ai/documentation/>
- ROS 2 documentation: <https://docs.ros.org/en/rolling/>
- ROS 2 clock and time design: <https://design.ros2.org/articles/clock_and_time.html>
- GitHub protected branches:
  <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches>
