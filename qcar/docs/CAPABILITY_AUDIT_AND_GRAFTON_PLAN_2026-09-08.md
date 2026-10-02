# QCar/QDrone/QBot capability audit and Grafton collaboration plan

## Executive decision

Use QCar as the primary integration platform. It is the only one of the three
with an armed hardware lane-control runner, an image-space predictive
controller, gated HyperLIF residual modes, and a separate ROS 2 estimation
stack. QDrone is suitable for offline and kinematic-mirror experiments but is
telemetry-only on hardware. QBot presently has mathematical documentation only.

| Platform | Reproducible now | Important boundary | Next evidence gate |
|---|---|---|---|
| QCar/QCar2 | offline residual campaign; low-speed hardware runner; PID, SMC, image-state beam-search NMPC, gated Adaptive HyperLIF residuals; ROS 2 EKF lineage | the offline plant is an image-error abstraction; the ROS 2 NMPC path is sign-fixed but not hardware-verified; no complete destination/obstacle stack | fixed-route repeated hardware benchmark with synchronized perception, state, command, compute and power logs |
| QDrone/QDrone2 | offline campaign; ACC2027 controller in a Python dynamics + QLabs kinematic mirror; telemetry logger | mirror is not QLabs-native physics; no armed controller in this repository | vendor baseline flight plus recorded-log replay, then independently reviewed low-authority residual |
| QBot | dynamics/control paper | no runner, hardware adapter, or result | identify exact QBot generation, build offline differential-drive baseline, then twin |

The latest preserved 20 s QCar software-only campaign reports RMS error
`0.03261 -> 0.03151` (3.37% reduction) with mean command
`0.01228 -> 0.01250` (1.82% increase). This is a wiring result, not vehicle
evidence. The current image NMPC is also not a bicycle-model NMPC: it searches
a finite steering tree using two image states.

## Existing image-state predictive controller

The present controller propagates lane error \(e\) and image slope \(m\):

\[
e_{k+1}=e_k+\Delta t(a_m m_k+a_\delta\delta_k),\qquad
m_{k+1}=m_k+\Delta t(b_\delta\delta_k-b_m m_k),
\]

and minimizes over a beam of steering sequences

\[
J=\sum_{j=0}^{N-1}\left(q_e e_j^2+q_m m_j^2+r_\delta
\delta_j^2+r_{\Delta\delta}(\delta_j-\delta_{j-1})^2\right),
\]

subject to steering magnitude and slew limits. This is a useful low-cost
baseline. It does not predict vehicle pose, obstacle clearance, tire effects,
or actuator dynamics.

## Required autonomous-system baseline

The next MPC should use the fused state \(z=[X,Y,\psi,v]^T\), with the
kinematic bicycle discretization

\[
\begin{aligned}
X_{k+1}&=X_k+\Delta t\,v_k\cos\psi_k,\\
Y_{k+1}&=Y_k+\Delta t\,v_k\sin\psi_k,\\
\psi_{k+1}&=\psi_k+\Delta t\,v_k\tan\delta_k/L,\\
v_{k+1}&=v_k+\Delta t\,a_k.
\end{aligned}
\]

Minimize cross-track, heading, speed, input, and input-rate penalties over the
horizon, with hard bounds on \((v,a,\delta,\Delta a,\Delta\delta)\). Obstacle
avoidance must be a geometric constraint or safety-filter constraint, not an
unverified reward term. Progress to a dynamic bicycle model only when lateral
acceleration and tire-slip residuals show the kinematic model is inadequate.

For a learned policy \(u_L\), retain a stabilizing baseline and enforce

\[
u_{cmd}=\Pi_{\mathcal U_{safe}(x)}
\big(u_{MPC}+\alpha(x)\,\Delta u_{ANN/SNN/RL}\big),\quad 0\leq\alpha\leq1,
\]

where the projection is a small quadratic program enforcing actuator and
collision constraints. “Model-free” describes how \(\Delta u\) is learned; it
does not remove the need for a model or reachable-set approximation in the
safety layer.

## Sensor-fusion audit

The ROS 2 lineage implements a bicycle-model EKF for \([X,Y,\psi]\), a gyro
bias filter, wheel speed, IMU yaw rate, and RF2O LiDAR odometry. Its predict and
correct equations are recognizable EKF equations:

\[
\hat x^-_k=f(\hat x^+_{k-1},u_k),\quad
P^-_k=F_kP^+_{k-1}F_k^T+Q_k,
\]

\[
K_k=P^-_kH_k^T(H_kP^-_kH_k^T+R_k)^{-1},\quad
\hat x^+_k=\hat x^-_k+K_k(y_k-H_k\hat x^-_k).
\]

Before presenting it as validated fusion, correct or test these points:

1. `_odom_rf2o` is named “GPS” in code but is LiDAR odometry; provenance must
   remain explicit in plots and covariance selection.
2. RF2O heading corrects the gyro filter, then that filtered heading is fused
   with RF2O position as if independent. The shared measurement creates
   cross-correlation that the current diagonal \(R\) omits.
3. Sensor callbacks use arrival time without measurement-time synchronization,
   interpolation, or out-of-sequence rejection.
4. Steering command is used as steering state; actuator delay, deadband and
   calibration uncertainty are not modeled.
5. Process covariance is fixed rather than derived/scaled with \(\Delta t\),
   and the covariance update should use the Joseph form
   \((I-KH)P(I-KH)^T+KRK^T\) for numerical robustness.
6. Validate with innovations/NIS, held-out ground truth, dropout tests, and
   covariance consistency—not trajectory appearance alone.

## Benchmark matrix

Hold the route, perception version, safety limits and randomization protocol
fixed. Run at least five repeated trials per cell before claiming ranking.

| Factor | Levels |
|---|---|
| estimator | odometry-only; current EKF; corrected synchronized EKF |
| controller | PID; SMC; image NMPC; pose/bicycle MPC |
| learned augmentation | none; ANN residual; SNN residual; RL residual |
| condition | nominal; lane degradation; static obstacle; sensor dropout |
| speed | low qualification; medium; highest safety-approved |

Primary safety metrics are collisions, interventions, lane departures, minimum
time-to-collision, constraint violations and mission completion. Performance
metrics are cross-track/heading RMS, route time, progress and control variation.
Compute metrics are deadline misses, p50/p95/p99 latency, memory, CPU/GPU load
and model size. Measure energy as \(E=\int P(t)dt\) using synchronized Jetson
rail telemetry or an external meter and report joules per completed route and
Wh/km. FLOPs or spike counts are explanatory proxies, not energy measurements.

## Grafton's junior-research-assistant role

Give Grafton ownership of reproducibility and evidence, with small reviewed
changes; retain safety authority and controller-signoff with the senior team.

- Week 1: reproduce perception-only logging, write the signal dictionary, and
  produce a timestamp/units audit. No motion.
- Week 2: reproduce PID and image-NMPC offline baselines; add unit tests for
  dynamics, signs, clamping and slew limits.
- Week 3: build a rosbag/offline fusion evaluator with trajectory, innovation,
  NIS and dropout plots; do not tune on the final evaluation route.
- Week 4: run the approved low-speed matrix with an E-stop operator; produce a
  one-page result card per run and a provenance manifest.

Each task should be one issue and one small pull request with: hypothesis,
changed files, exact command, result artifact, failure modes, and reviewer.
Use a twice-weekly 20-minute review: Monday sets one measurable question;
Thursday checks evidence and decides repeat/advance/stop. This gives a junior
researcher meaningful ownership without making him the sole judge of safety or
scientific claims.
