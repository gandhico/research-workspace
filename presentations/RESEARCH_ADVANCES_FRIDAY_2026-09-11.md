# Research advances — Friday, 2026-09-11

## One-sentence thesis

We are building a reproducible path from biologically grounded neuron dynamics
to safe residual control across Quanser robots and spacecraft, while separating
software parity, digital-twin evidence, and physical-hardware evidence.

## Recommended 12-minute narrative

1. **Architecture (2 min):** HyperLIF and Adaptive HyperLIF now have a portable
   Julia reference for dense, recurrent, and temporal-delay networks, with all
   six state readouts and an explicit offline/causal delay distinction.
2. **Robotics workflow (2 min):** the same staged contract is used for
   identification, classical/nonlinear control, and bounded ANN/SNN/RL
   residuals. Hover now joins pendulum and Aero2 in the direct Julia HIL bridge.
3. **DILISIC (2 min):** show the corrected 80 s seven-agent reproduction and
   mathematical audit. State the article's sign conflict and Lyapunov-proof
   assumptions explicitly.
4. **QArm (1 min):** tomorrow is an identification-and-shadow milestone, not an
   unsupported direct actuation claim.
5. **QCar collaboration (3 min):** existing image NMPC and HyperLIF residuals
   become the starting baseline for fused-state bicycle MPC, obstacle safety,
   measured compute/energy, and Grafton's reproducibility role.
6. **Space systems (2 min):** demonstrate the controlled single-satellite
   Basilisk `MJScene`; close with the communication-graph multi-agent plan.

## 1. HyperLIF: model and Julia replication

The reset gate and effective threshold are

\[
\theta_{eff,k}=\theta_v-\gamma r_k,\qquad
r_{\infty,k}=\sigma\left(\alpha(v_k-\theta_{eff,k})\right),
\]

\[
r_{k+1}=\operatorname{clip}_{[0,1]}\left(r_{\infty,k}+
(r_k-r_{\infty,k})e^{-\Delta t/\tau_r}\right).
\]

With \(G_{k+1}=g_kr_{k+1}^2\), freezing current and conductance over one
sample yields the exact scalar substep

\[
v_{k+1}=v_ke^{-\lambda_k\Delta t}+\frac{b_k}{\lambda_k}
\left(1-e^{-\lambda_k\Delta t}\right),
\]

where \(\lambda_k=1/\tau_m+G_{k+1}\) and
\(b_k=v_{rest}/\tau_m+J_k/\tau_m+G_{k+1}v_{reset,eff}\). It is rigorous to call
this an exact frozen-current split step, not an exact solution of the fully
coupled nonlinear neuron.

Julia status: 13 deterministic CPU assertions pass. The existing shared-weight
CUDA fixtures already establish PyTorch/Julia forward parity for dense,
recurrent, and centered-delay models at feature tolerance \(10^{-4}\) and
logit tolerance \(10^{-3}\). Gradient/optimizer parity and a portable
convolutional architecture remain future work.

## 2. Common control workflow

Every platform should expose the same evidence ladder:

\[
\mathcal D=\{t_k,y_k,u_k\}\to
\hat f,\hat g,\Sigma\to
u_{baseline}\to
u_{nonlinear/MPC}\to
u_{safe\ learned}.
\]

Identification must report units, timing, excitation, uncertainty and held-out
error. A learned controller is introduced as a bounded residual

\[
u=\Pi_{\mathcal U_{safe}(x)}(u_b+\alpha(x)\Delta u_\theta),
\]

so the classical controller, authority schedule, saturation, watchdog and
fallback remain independently testable. Compare ANN, SNN and RL policies using
identical observations, action bounds, training data/seeds and test missions.

Hover Julia status: the `q8_usb` bridge now maps AO0–3 to front/back/left/right
motor commands and ENC0–2 to pitch/roll/yaw, preserves the amplifier and
0–24 V constraints, and defaults to zero output unless explicitly armed. Its
103-test smoke suite and the shared 15-board registry validation pass without
opening hardware. A live device test is still required.

## 3. DILISIC mathematical audit

For \(e=x-x_d\),

\[
s=e^{(n-1)}+\lambda_{n-1}e^{(n-2)}+\cdots+\lambda_1e,
\]

and the implemented inner law is

\[
u_{LISIC}=-\hat h(\hat f+q_a+Ks-u_r),\qquad
u_r=-B_e^TP_es_e/r.
\]

The reference and plant now receive the same filtered DILISIC command; the
experiment integrates exactly to the requested terminal time. The reproduced
80 s contract matches all 11 metrics to relative tolerance \(10^{-6}\), with
final center-of-mass error \(9.5251\times10^{-5}\).

Disclose four limits: Section III and Eq. (30) use opposite tracking-error
signs; the Lyapunov derivative appears to omit the derivative of a
state-dependent \(1/\hat h^*\); positivity of the approximated inverse gain is
not established; and Eq. (25) appears to use the wrong norm in the
\(W_f\)-projection denominator. The code uses the internally consistent sign,
a positive engineering floor, and separate radial projections.

## 4. QArm milestone

The software replication is ready; the plant interface is not. DILISIC assumes
a known-sign highest-derivative input to a fourth-order affine plant, while the
current QArm path exposes an inner position servo. Tomorrow's safe sequence is
bounded one-joint excitation, ARX contract identification, chronological
validation, and non-actuating DILISIC replay. Direct actuation remains false
until the input model, state observer, units, limits, watchdog and fallback are
validated.

## 5. QCar/QDrone/QBot and collaboration

QCar is the integration priority; QDrone is a twin/telemetry research lane;
QBot needs its first runner. The existing QCar predictive controller is a
two-state image model, so call it “image-state beam-search NMPC,” not full
vehicle NMPC. The next baseline is fused-pose kinematic-bicycle MPC with hard
input/slew/obstacle constraints. The current ROS 2 fusion stack needs timestamp
alignment and correlated-measurement treatment because RF2O LiDAR odometry is
called GPS and its heading is effectively reused.

Grafton should own reproducibility: signal dictionaries, log validators,
offline baseline tests, rosbag fusion evaluation, result cards and small
reviewed pull requests. Senior collaborators retain safety gates and claim
approval. Benchmark success, safety, latency and measured energy—not only RMS
tracking error.

## 6. Basilisk–MuJoCo spacecraft twin

The example uses Basilisk 2.11.1 `MJScene` as the dynamics engine, with a free
bus, three orthogonal reaction-wheel joints, point-mass Earth gravity, standard
navigation/guidance/MRP feedback, wheel allocation and torque saturation. The
verified 600 s run reduces MRP error norm from `0.374166` to `0.000641` and
rate-error norm to `5.47e-5 rad/s`; peak wheel torque is the configured
`0.2 N m` limit.

For multiple agents, give every satellite separate truth/navigation/control
messages and define a sampled communication graph \(\mathcal G(t)\) with delay,
loss and neighbor selection. Design first in Hill/Clohessy–Wiltshire relative
coordinates, then validate formation maneuvers against Basilisk nonlinear
gravity and actuator/sensor limits. Separate bodies without decentralized state,
control and communication contracts are multi-spacecraft, not yet multi-agent.

## Demonstration commands

```powershell
# Julia HyperLIF reference
cd C:\Research\papers\P1_HyperLIF_Learning\code\julia\portable
julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'

# Hover bridge, no device opened
cd C:\Research\hover3dof
julia --startup-file=no .\julia\hover_bridge_smoke.jl

# DILISIC exact contract
cd C:\Research\dilisic
.\.venv\Scripts\python.exe verify.py

# Native Basilisk MuJoCo satellite
cd C:\Research\spacecraft_twin
.\.venv\Scripts\python.exe .\single_satellite_mujoco.py
```

## Claim labels for every slide

- **Verified software:** deterministic tests or reproducible saved result.
- **Digital twin:** simulated dynamics with stated fidelity and parameters.
- **Hardware observed:** logged physical run with provenance.
- **Proposed:** architecture or experiment not yet executed.

Never merge these labels. They are the difference between an ambitious program
and an inflated claim.
