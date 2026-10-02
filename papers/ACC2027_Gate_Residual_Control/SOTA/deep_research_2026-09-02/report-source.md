# State of the Art and Contribution Audit for ACC 2027

**Working paper:** Online PES-Adapted Neuromorphic Membrane–Gate Residual Control for Actuator-Constrained UAV Quaternion Attitude Tracking  
**Audience:** authors and advisers preparing an ACC 2027 submission  
**Research date:** 2026-09-02  
**Coverage:** English-language primary literature and official documentation available through 2026-09-02; local paper corpus; ACC proceedings and ACC 2027 author guidance  
**Canonical project evidence:** C:\Research\papers\ACC2027_Gate_Residual_Control\docs\FULL_PROJECT_AUDIT_2026-09-02.md

## Direct answer

The project has a credible and timely ACC contribution, but the novelty must be stated precisely.

The two papers in the local SOTA folder are related:

1. **L1Quad is the strongest control-theoretic comparator.** It already establishes classical-baseline plus online adaptive augmentation for quadrotors, with computable transient/ultimate bounds and unusually broad free-flight validation. It prevents us from claiming that baseline-preserving adaptive augmentation, fast online quadrotor adaptation, or actuator-fault/disturbance compensation is new by itself.
2. **HPA-PPO is the closest residual-attitude-learning comparator.** It adds a learned residual to PID for roll, pitch, and yaw and reports large numerical, SITL, and Pixhawk/Gazebo HITL improvements. It prevents us from claiming that additive learned residual attitude control over PID is new. Its policy is trained through PPO, its state includes history and preview, and its HITL plant remains in Gazebo; it does not implement local online PES, a continuous membrane–gate state basis, shortest-path quaternion error, or an explicit rotor-level residual allocation study.

A still closer neuromorphic precedent was found outside the supplied folder: **Olivares et al. (2026)** implement a Nengo spiking PID controller with online PES-based gain adaptation and validate it on a free-flying DJI Tello. Therefore, the manuscript must not claim the first Nengo/PES adaptive UAV controller, the first PES neuromorphic UAV controller, or the first online neuromorphic flight controller.

The defensible contribution is the **combination and the mechanism**:

- a fixed classical quaternion-PD backbone;
- paired directional current encoding;
- a continuous, non-spiking coupled membrane–gate dynamical basis;
- online PES adaptation of a low-dimensional decoder rather than PID gains or a deep policy;
- bounded additive residual authority;
- explicit command-to-actuator allocation and saturation telemetry;
- controlled separation of conductance adaptation from decoder adaptation;
- matched comparison against LIF, ALIF, Izhikevich, and rate units;
- numerical equivalence inside and outside Nengo;
- actuator-faithful MuJoCo evidence plus a limited but honest physical 3DOF Hover result.

This is a strong **architecture/mechanism and reproducibility contribution**, a moderate **UAV performance contribution**, and currently a weak **theory, free-flight, and neuromorphic-energy contribution**. The paper can be competitive at ACC if it avoids broad priority claims, leads with the transparent mechanism and actuator semantics, and reports negative and boundary results honestly.

## 1. Research questions and method

The review addressed five questions:

1. Which prior works already combine classical and learned/adaptive control?
2. Which works use Nengo, the Neural Engineering Framework (NEF), PES, spiking or non-spiking dynamics in robot/UAV control?
3. Which works address quaternion/geometric attitude tracking and actuator constraints?
4. What has ACC already published in neighboring areas, and how does ACC 2027 define scope?
5. Which claims are supported by the present project evidence, and which experiments are still required?

The search emphasized primary sources: publisher pages, proceedings, author manuscripts, official repositories, and official ACC guidance. The local PDFs were text-extracted and representative architecture/result pages were visually inspected. Search terms covered adaptive augmentation, residual control, quadrotor attitude tracking, quaternion control, actuator allocation, Nengo, NEF, PES, spiking and non-spiking control, MuJoCo, hardware-in-the-loop, and ACC.

This is a targeted state-of-the-art review, not a registered systematic review. Consequently, “first” claims remain inappropriate unless a separate database-level systematic search is completed.

## 2. The two supplied papers

### 2.1 L1Quad

**Source:** Zhuohuan Wu et al., “L1Quad: L1 Adaptive Augmentation of Geometric Control for Agile Quadrotors With Performance Guarantees,” IEEE Transactions on Control Systems Technology, 33(2), 597–612, 2025, DOI 10.1109/TCST.2024.3521182.

**Architecture.** L1Quad augments a geometric SE(3) baseline with an L1 adaptive element. A state predictor produces a prediction error; a piecewise-constant adaptation law estimates matched and unmatched uncertainties; a low-pass filter separates fast estimation from the applied compensation; and the total input is baseline plus adaptive input.

**Evidence.** It supplies a Lyapunov analysis with tunable uniform and uniform-ultimate tracking bounds. It reports free-flight tests on a custom 0.62 kg quadrotor with one controller setting across eleven uncertainty classes, including injected uncertainty, liquid slosh, tunnel airflow, a propeller with one quarter removed, four mixed propellers, battery-voltage drop, ground effect, downwash, off-center weights, added weights, and slung weights. A chipped-propeller circular flight reports 0.045 m RMSE. Some baseline/PID cells in the appendix are as good as or better than L1Quad at easy conditions, but L1Quad is markedly more consistent as uncertainty severity and speed increase, and avoids crashes in several harsh cases.

**Direct relationship to this project.** Very high at the outer architecture level; moderate at the internal mechanism level.

| Dimension | L1Quad | Present CMG–PES work |
|---|---|---|
| Baseline | geometric SE(3) controller | quaternion PD attitude controller |
| Adaptive object | estimated uncertainty passed through L1 filter | decoder from CMG activity to normalized residual |
| Online update | piecewise-constant uncertainty estimate | projected PES-style decoder update each sample |
| Learned basis | nonparametric uncertainty estimate, no neural basis required | six paired continuous membrane–gate activities |
| Controlled dynamics | translation and rotation | mainly attitude; collective remains classical |
| Guarantees | explicit transient and ultimate bounds | no closed-loop proof yet |
| Actuation evidence | real rotorcraft and harsh physical faults | explicit rotor path in MuJoCo; limited 3DOF rig |
| Neuromorphic claim | none | Nengo/NEF-compatible local learning and neural-state telemetry |

**Consequence for our claims.** L1Quad must be presented as the stronger robustness/theory benchmark. Our distinction is not superior robustness. It is a compact, inspectable neuromorphic residual basis and a mechanism-controlled study that exposes activity, decoder evolution, residual authority, and actuator feasibility.

### 2.2 HPA-PPO

**Source:** Xinxin Li, Bo-Chao Zheng, Weixi Wang, and Weilong Zhang, “HPA-PPO: A history-preview and attention-enhanced PPO for quadrotor attitude tracking,” Applied Mathematics and Computation 532 (2027), article 130236; available online 13 July 2026; DOI 10.1016/j.amc.2026.130236.

**Architecture.** The paper defines

\[
u=u_{\mathrm{PID}}+\Delta u_{\mathrm{RL}},
\]

where a PPO actor with preprocessing, feature/type encoding, history and reference preview, and multi-head self-attention produces bounded residual roll, pitch, and yaw torques. In HITL, the offboard controller instead sends a baseline-plus-residual angular-rate target to the PX4 inner rate loop.

**Evidence.** In SITL, the reported RMSE values for PID/PPO/HPA-PPO are 2.47/1.78/0.53 deg in roll, 2.54/1.81/1.22 deg in pitch, and 4.82/3.49/1.60 deg in yaw. The HPA-PPO yaw RMSE is therefore 66.8% below PID. In Pixhawk/Gazebo HITL, HPA-PPO reports RMSE 0.51, 0.62, and 0.52 deg for roll, pitch, and yaw versus PID values 1.68, 1.91, and 1.98 deg. The actual flight-controller board is in the loop, but the vehicle dynamics and sensor response are computed by Gazebo; the authors explicitly leave real-world flight experiments for future work.

**Direct relationship to this project.** Very high for additive learned residual attitude control; low for learning mechanism and neuron model.

| Dimension | HPA-PPO | Present CMG–PES work |
|---|---|---|
| Attitude variables | Euler-angle errors and rates | shortest-path quaternion vector error and body rate |
| Baseline | PID | quaternion PD |
| Learned component | deep PPO policy with attention/history/preview | linear decoder over six stateful CMG activities |
| Learning time | episodic policy training before evaluation | local decoder adaptation during evaluation |
| Residual location | torque in numerical model; desired angular rate before PX4 rate loop in HITL | body torque before explicit rotor allocation in canonical MuJoCo |
| Constraint mechanism | tanh-bounded action | normalized decoder, residual gain, torque saturation, rotor clipping |
| Validation | numerical, SITL, Pixhawk/Gazebo HITL | MuJoCo, Nengo equivalence, physical 3DOF rig |
| Interpretability | attention/policy-level | paired currents, membrane, gate, activity, decoder rows, motor commands |

**Consequence for our claims.** We may contrast local online learning with offline episodic PPO and emphasize the actuator interface difference. We should not compare percentages as if the tasks were identical.

## 3. Closest literature by field

### 3.1 Neuromorphic and NEF/PES adaptive control

This is the field with the closest conceptual overlap.

- Olivares et al. (2026) use Nengo, a spiking neural PID architecture, and PES to estimate a derivative needed for online gain updates. Their free-flight DJI Tello experiments show ITSE reductions of 7.53–15.28% on a step trajectory and 26.51–38.27% on a Rhodonea trajectory, plus lower control-signal energy in several channels. This is the paper that most directly limits broad novelty language.
- DeWolf et al. (2016) established a spiking adaptive arm controller with a mathematical stability argument for adaptation. DeWolf, Jaworski, and Eliasmith (2020) then showed a standard PD operational-space controller augmented by a PES-trained neural correction on a physical 6DOF Jaco2 arm and demonstrated deployment across CPU, GPU, and Loihi. That paper explicitly describes Nengo as a callable adaptive subfunction of a conventional controller.
- Nengo’s implementation defines PES as an online rule that changes decoders to minimize an externally supplied error. For decoded PES,

\[
\Delta d_i=-\frac{\kappa}{n}E\,a_i,
\]

with filtered presynaptic activity \(a_i\). This supports describing our learning as PES-style decoder adaptation, but not calling it reinforcement learning.
- Non-spiking neural control is also established. Szczecinski et al. use continuous non-spiking Hodgkin–Huxley-like compartments for legged control; mixed spiking/non-spiking pathways and subthreshold neurons are also documented. Therefore, “continuous non-spiking neural dynamics” is not itself novel.

**Our real gap in this field:** a membrane state coupled to a graded gate is used as a compact directional residual basis for constrained quaternion attitude control, with PES acting on the decoder and with explicit ablations separating intrinsic conductance changes from synaptic/decoder adaptation. The literature search did not reveal this exact combination. This should be phrased as “we study” or “we introduce in this control architecture,” not “the first.”

### 3.2 Adaptive and learning-based quadrotor control

The bar is high:

- Bisheban and Lee (2021) adjust multilayer neural-network weights online in a geometric SE(3) controller, prove uniform ultimate boundedness, and provide aggressive indoor flight experiments under wind.
- Neural-Fly (O’Connell et al., 2022) learns a shared representation offline and adapts low-dimensional coefficients online; it provides exponential-stability guarantees and physical flight in winds up to 12.1 m/s.
- DATT (Huang et al., 2023) combines a simulation-trained feedforward/feedback policy with online L1 disturbance estimation and reports real Crazyflie tracking of feasible and infeasible trajectories, with less than 3.2 ms inference.
- Neural Lander (Shi et al., 2019) combines a learned residual-dynamics model with feedback control and stability analysis.
- L1Quad (Wu et al., 2025) provides the broadest single-platform uncertainty campaign among the sources reviewed.

**Our position:** the project is not yet stronger on theory, disturbance breadth, or free-flight validation. It is stronger in transparent neuron-level mechanism isolation, compact local online adaptation, explicit Nengo/non-Nengo correspondence, and reporting the actuator-authority boundary rather than hiding it.

### 3.3 Residual learning

Johannink et al. (2019) formalized residual reinforcement learning as the superposition of a conventional controller and a learned correction. Residual policies have since been used in manipulation, locomotion, UAV planning, dynamics learning, and attitude tracking. Sparse-GP residual dynamics have also been inserted into online NMPC for real multirotor tracking.

**Our position:** additive residual control is established. Novelty must lie in the residual generator, update rule, bounded allocation path, and experimental decomposition. The manuscript should call the architecture “baseline-preserving” because

\[
u=\operatorname{sat}_{\ell}(u_0+\beta u_{\mathrm{neu}})
\]

retains \(u_0\) before final saturation. The historical convex blend

\[
u=(1-\beta)u_0+\beta u_{\mathrm{neu}}
\]

does not preserve the baseline and must remain excluded from canonical claims.

### 3.4 Quaternion/geometric attitude control

Quaternion and manifold controllers are mature. Lee, Leok, and McClamroch (2010) provide almost-global geometric tracking on SE(3). Fresk and Nikolakopoulos (2013) give a full-quaternion quadrotor controller. The literature also treats unwinding, hybrid global attitude tracking, adaptive quaternion control, and aggressive geometric maneuvers.

**Our position:** quaternion PD is the classical backbone and not a novelty claim. Its role is important because it supplies singularity-free attitude error and a clean three-channel contract to the residual learner:

\[
q_e=q_d\otimes q^{-1},\qquad
e_q=\operatorname{sgn}(q_{e,0})\operatorname{vec}(q_e),
\]

\[
\tau_0=\operatorname{sat}_{\tau_{\max}}
(-K_q e_q-K_\omega\omega).
\]

The novelty is the neuromorphic residual placed around this backbone, not the quaternion law.

### 3.5 Actuator constraints and control allocation

Actuator-aware quadrotor control is a distinct mature field. ACC 2016 published weighted-least-squares, direct, and partial control allocation strategies for avoiding quadrotor output saturation. Later work couples constrained allocation with yaw-prioritized controllers and formal aggressive-maneuver designs.

**Our position:** the explicit \(4\times4\) mixer and nonnegative rotor clipping are necessary for honesty, but not independently novel. The valuable result is the **controller–actuator co-design audit**:

- Skydio X2 commands four named rotor-thrust actuators and shows zero saturation in canonical nominal runs.
- The stock Crazyflie XML exposes abstract moment actuators whose authority is not sufficient for the historical torque request.
- The CF2 1.5-times rotor model is explicitly a propulsion-design study with thrust-to-weight ratio approximately 1.98, not a stock-hardware validation.

This boundary result is publishable because it prevents a false performance claim and makes the residual authority physically interpretable.

### 3.6 Simulation, Nengo, and cyber-physical execution

MuJoCo supplies generalized-coordinate rigid-body dynamics, forward and inverse dynamics, contacts, constraints, and actuator models. It does not automatically make a model a digital twin: fidelity comes from identified mass, inertia, geometry, motor maps, delays, sensors, and saturation. Nengo supplies a front end for neural models, probes, online learning, and multiple execution back ends. Execution in Nengo on a CPU is not evidence of low-power neuromorphic hardware.

The project’s strongest software claim is implementation equivalence: isolated Nengo and direct updates agree to about \(1.05\times10^{-7}\) relative command error, and closed-loop metrics agree to three or four significant figures. This is evidence that Nengo is an alternate realization of the same controller, not the source of the control benefit.

## 4. Exact present architecture

For each bounded residual channel \(i\), the baseline is normalized and split into positive and negative currents:

\[
\bar u=u_0\oslash\ell,\quad
I^+=I_b{\bf 1}+I_g\max(\bar u,0),\quad
I^-=I_b{\bf 1}+I_g\max(-\bar u,0).
\]

Each of the \(2m\) units has coupled gate and membrane dynamics:

\[
\dot r_j=
\frac{\sigma\{\alpha[v_j-(v_{\rm th}-\gamma r_j)]\}-r_j}{\tau_r},
\]

\[
\dot v_j=
-\frac{v_j-v_{\rm rest}}{\tau}
+\frac{I_j}{\tau}
-c_j(v_j-v_{\rm reset}),
\]

\[
c_j=(g_0+\mathbf 1_{\rm cond}g_1|I_j|)r_j^2.
\]

The activity supplied to the decoder is

\[
a_j=\operatorname{clip}(G r_j,0,1).
\]

Thus the decoder reads the gate, but the gate is not independent: \(v\) drives the gate target, while \(r\) shifts the effective threshold and modulates the membrane conductance. Both state equations matter. The current amplification \(G=10^5\) places much of the activity near clipping, explaining why the tested fixed- and input-dependent-conductance variants are numerically indistinguishable.

The initialized signed decoder and online target are

\[
W_0=[I_m\;-I_m],\qquad
s_k=\operatorname{clip}(W_ka_k,-1,1),
\]

\[
y_k^*=\operatorname{clip}(-k_e e_{q,k}-k_\omega^*\omega_k,-1,1),
\]

\[
W_{k+1}=\Pi_{[-6,6]}
\left(W_k+\eta(y_k^*-s_k)a_k^\top-\lambda_WW_k\right).
\]

The decoded signal is applied only after scaling and bounding:

\[
u_k=\operatorname{sat}_{\ell}
\left(u_{0,k}+\beta(s_k\odot\ell)\right).
\]

This is online supervised error-driven adaptation, not PPO, actor–critic learning, or reward-based reinforcement learning.

## 5. Field-coverage map

| Field | What this project contributes | Evidence strength now | Main missing evidence |
|---|---|---:|---|
| Learning-enabled control | local online decoder adaptation around a fixed baseline | strong mechanism; moderate performance | held-out frozen-weight tests; repeated random seeds |
| Adaptive control | bounded error-directed correction during operation | moderate | Lyapunov/ISS or projection-bound analysis; persistent-excitation discussion |
| Neuromorphic control | continuous membrane–gate dynamics, Nengo implementation, full state telemetry | strong software/mechanism | deployment on Loihi/SpiNNaker/FPGA; measured power/latency |
| UAV attitude control | quaternion PD plus residual torque | strong deterministic simulation | free-flight quadrotor experiments and disturbances |
| Actuator-constrained control | explicit rotor allocation, saturation logs, CF2 authority audit | strong transparency | identified motor/propeller maps and battery/ESC dynamics |
| Residual learning | baseline-preserving bounded additive architecture | strong implementation, low novelty alone | compare with non-neural adaptive residuals |
| Sim-to-real/HIL | same Nengo concept in MuJoCo and Quanser rig | moderate | calibrated full-airframe digital twin and real free flight |
| Comparative neuron dynamics | CMG/LIF/ALIF/Izhikevich/LIFRate with matched controller path | potentially strong | repeated seeds, matched effective activity/authority, frozen policy |
| Reproducible research | full-rate telemetry, manifests, code graph, explicit exclusions | unusually strong | public archival release and independent reproduction |

## 6. Contribution strength and claim language

### 6.1 Strong, defensible claims

1. **Mechanism separation.** Under the reported amplified-gate parameterization, changing conductance does not explain the gain; adapting the decoder does.
2. **Baseline preservation.** The canonical additive formulation preserves the classical command prior to final saturation, unlike the earlier convex blend.
3. **Actuator transparency.** Every canonical multirotor torque passes through a declared actuator interface, and infeasible stock-CF2 authority is reported rather than reinterpreted as a controller result.
4. **Consistent deterministic simulation improvement.** CMG–PES improves mean quaternion-angle error on all ten X2/CF2-design mission cells by 17.33–60.60% under the fixed canonical protocol.
5. **Nengo equivalence.** The Nengo and direct implementations reproduce the same update and controller behavior to numerical tolerance.
6. **Non-universal neuron conclusion.** Izhikevich–PES can outperform CMG on mean error while using roughly three times the normalized residual RMS; CMG’s advantage is a lower-authority, graded, interpretable operating point, not exclusive learnability.

### 6.2 Claims that require qualification

- “Neuromorphic” is architectural: neuron-inspired state dynamics plus local learning and Nengo realization. It is not yet a hardware-energy claim.
- “Adaptive” must identify the variable. Input-dependent conductance and online PES decoder adaptation are different mechanisms.
- “Hardware validated” applies to the Quanser 3DOF Hover, not to free-flying X2/CF2 vehicles.
- The CF2 1.5-times result is a controller–propulsion design study, not a stock Crazyflie performance claim.
- The physical Hover evidence is mission-dependent. The repeated positive Roll result is the strongest. Full3 and reduced-yaw regressions and full-yaw safety aborts must not be hidden.

### 6.3 Claims to prohibit

- first PES-based or first Nengo adaptive UAV controller;
- first neuromorphic PID/UAV controller;
- first residual learning controller for quadrotors;
- first adaptive augmentation of a classical quadrotor controller;
- proven stability or safety of CMG–PES;
- energy efficiency without neuromorphic-hardware measurements;
- stock Crazyflie feasibility of the 1.5-times rotor design;
- universal superiority over LIF, ALIF, or Izhikevich;
- full physical yaw360 validation;
- generalization merely because PES adapts during the tested trajectory.

## 7. Recommended ACC 2027 positioning

ACC 2027 explicitly includes control theory, robotics and autonomy, cyber-physical systems, aerospace systems, learning-enabled control, safety, and resilience, and encourages intersections between control and neuroscience/AI. This project sits directly at that intersection.

The best primary technical classifications are:

1. learning-enabled control;
2. aerospace control and UAVs;
3. adaptive/nonlinear control;
4. robotics and autonomy;
5. actuator allocation and constrained control;
6. neuromorphic/cyber-physical implementation.

The paper should open with a control problem, not a biological metaphor:

> How can an online-learned attitude correction be made small, inspectable, baseline-preserving, and physically realizable at the rotors?

Then present CMG–PES as the answer. The contribution hierarchy should be:

1. bounded architecture and variable contract;
2. membrane–gate/PES mechanism and ablations;
3. actuator-faithful two-platform/five-mission simulation;
4. Nengo equivalence and neuron-family benchmark;
5. limited physical evidence and explicit failure boundaries.

ACC contributed papers are complete finished works. The official ACC 2027 schedule lists **Friday, September 25, 2026** for regular ACC manuscript submission and **Friday, September 11, 2026** for joint ACC+L-CSS submission. Initial regular/invited papers may be eight pages; accepted papers are six pages without charge and up to eight pages at USD 200 per excess page. Therefore, the final paper should keep QUBE/QCar as one sentence of future work unless they directly test the main hypothesis.

## 8. Recommended result order

1. **Architecture sanity and ablation:** fixed decoder versus PES; fixed versus input-dependent conductance. This establishes what causes improvement.
2. **Canonical X2 Hard45 result:** full tracking, error, residual, rotor, gate, membrane, decoder, and saturation plots.
3. **Five-mission matrix on X2:** shows the effect is not a single-trajectory artifact.
4. **CF2 authority audit:** stock infeasibility first, then explicitly labeled 1.5-times rotor design. This is an honest boundary result.
5. **Nengo/direct equivalence:** establishes portability without claiming that Nengo creates the improvement.
6. **Neuron-family benchmark:** show error improvement jointly with normalized residual authority and decoder motion. Do not rank on tracking alone.
7. **Physical 3DOF Hover:** lead with repeated Roll; show the complete matrix including negative Full3/reduced-yaw and safety-aborted full yaw360.

The narrative should end with: simulation establishes the control mechanism and actuator-aware potential; hardware establishes feasibility and identifies the gap to robust general deployment.

## 9. Experiments with the highest marginal value

Before submission, the most valuable additions are:

1. **Repeated X2 trials under stochastic disturbances** with at least 10 seeds and confidence intervals.
2. **Frozen-weight evaluation:** adapt on one trajectory segment or mission, freeze \(W\), then evaluate on unseen phase, amplitude, frequency, disturbance, and initial condition.
3. **Authority-matched neuron comparison:** tune each neuron family to the same residual RMS or impose the same integrated residual budget.
4. **CMG readout ablation:** compare gate \(r\), membrane \(v\), concatenated \([v,r]\), and a simple low-pass/rate basis at equal decoder dimension.
5. **Baseline-strength sweep:** show whether gain persists for a better-tuned PD with feedforward/reference-rate terms.
6. **Perturbation campaign:** constant bias, sinusoidal moment, impulse/gust, rotor effectiveness loss, sensor noise, delay, and inertia mismatch.
7. **Closed-loop boundedness argument:** even an ISS/small-gain result conditioned on bounded residual and baseline robustness would materially improve ACC reception.
8. **Repeated physical Roll and one disturbance-recovery task:** this is higher value than broad but underpowered platform expansion.

## 10. Future-work and application map

### Near-term, high fit

- **Quadrotor fault accommodation:** use rotor-effectiveness estimates or motor telemetry as contextual inputs while retaining bounded rotor allocation.
- **3DOF Hover perturbation rejection:** add repeatable impulse, hanging mass, or controlled motor-voltage loss; quantify peak error, recovery time, and residual energy.
- **Pendulum/QUBE:** use CMG–PES for unknown friction, mass change, or base disturbance. Nominal balance alone is too easy and presently shows equivalence.
- **QCar lane keeping:** use the vehicle’s lane/heading error as the classical-control state and reserve CMG–PES for a bounded steering residual. Event-camera or temporal-contrast perception can later feed a separate state estimator; perception and control claims should remain separated.

### Medium-term

- **Spacecraft and gimbal attitude control:** quaternion state and actuator saturation make the architecture structurally transferable, especially with reaction-wheel momentum or thruster constraints.
- **Underwater and marine vehicles:** paired directional channels and slow online adaptation fit uncertain drag/current compensation.
- **Robot manipulators and exoskeletons:** prior PES/NEF adaptive arm work provides a direct path; CMG can be tested as an alternative compact basis with torque limits.
- **Ground vehicles and mobile robots:** steering/yaw residuals under tire-friction change, payload shift, or actuator dead zones.
- **Power electronics and motor drives:** bounded residual compensation for dead time, load torque, or parameter drift, where fast deterministic implementation matters.

### Long-term

- mixed event-driven perception and graded control;
- neuromorphic hardware execution with measured end-to-end energy and latency;
- safety filters or control-barrier-function projection after the residual;
- meta-learned initial decoders followed by local PES adaptation;
- sparse/context-gated CMG banks for state-dependent disturbance compensation;
- multi-agent or fault-tolerant allocation with one local residual bank per actuator group.

## 11. Limitations and risks

1. The strongest 17–61% gains occur in deterministic nominal MuJoCo missions and may partly correct the phase lag of a deliberately feedforward-free PD baseline.
2. Learning and evaluation happen on the same trajectory. This establishes online improvement, not generalization.
3. The CMG activity amplification saturates much of the gate readout, weakening the current conductance-mechanism claim.
4. The cross-neuron comparison is sensitive to activity calibration, filtering, decoder initialization, and residual authority.
5. Physical evidence is a constrained attitude rig, not free flight, and some missions regress.
6. There is no formal closed-loop stability result for online projected PES under the nonlinear actuator path.
7. Nengo execution on a CPU does not establish event-driven or low-power operation.
8. The current manuscript contains stale physical-Hover statements asserting all missions improved. Those statements conflict with the 2026-09-02 audit and must be reconciled before submission.

## 12. Paper-ready related-work synthesis

Learning-based flight control ranges from offline residual-dynamics models and residual reinforcement-learning policies to online adaptive estimators. Residual policy learning superposes a learned correction on a conventional controller, preserving useful model-based structure while allocating difficult-to-model effects to the learner. Quadrotor instances include learned residual dynamics in predictive control, deep policies with online disturbance estimation, and PID-plus-PPO attitude control. In parallel, geometric and L1 adaptive controllers provide strong stability and transient-performance guarantees under wind, payload, actuator degradation, and other uncertainties. These works establish that neither residual augmentation nor online quadrotor adaptation is new in isolation.

Neuromorphic robot control provides a complementary route to compact, local online adaptation. NEF implementations use neural activity and learned decoders to represent dynamical transformations, while PES supplies an error-driven local decoder update. Prior work has augmented a classical PD arm controller with a PES-trained neural correction, deployed adaptive control on neuromorphic hardware, and recently demonstrated a Nengo spiking PID controller with PES-based online gain adaptation on a free-flying quadrotor. Continuous non-spiking neural controllers and mixed spiking/non-spiking pathways are also established. The unresolved question addressed here is therefore not whether PES or neural dynamics can control a robot, but whether a low-dimensional continuous membrane–gate basis can provide a transparent, bounded residual for actuator-constrained quaternion attitude tracking, and which internal adaptation mechanism actually accounts for the observed improvement.

We retain a fixed quaternion-PD law as the nominal feedback backbone and learn only an additive correction. Positive and negative normalized torque demands excite paired coupled membrane–gate units; a projected PES rule updates a linear decoder online; and the result is bounded before explicit control allocation. This structure differs from gain-adaptive neuromorphic PID, deep residual policies, and L1 uncertainty estimation. Our experiments explicitly separate input-dependent membrane conductance from decoder adaptation, compare continuous CMG activity against common spiking/rate models, and expose rotor saturation and required authority. Consequently, the claimed contribution is a mechanism-controlled neuromorphic residual architecture and actuator-aware validation, not a new quaternion controller, a universal neuron advantage, or a replacement for adaptive-control guarantees.

## 13. Claim-to-source ledger

| Claim | Primary source(s) | Confidence |
|---|---|---:|
| L1Quad provides baseline augmentation, transient bounds, and eleven physical uncertainty classes | Wu et al. 2025; local PDF; DOI 10.1109/TCST.2024.3521182 | high |
| HPA-PPO uses PID plus PPO residual and reports 66.8% yaw RMSE reduction in SITL | Li et al. 2027; local PDF; DOI 10.1016/j.amc.2026.130236 | high |
| HPA-PPO HITL uses actual PX4 electronics but Gazebo vehicle dynamics | Li et al. 2027, Sec. 4.5 and Fig. 10 | high |
| PES/Nengo adaptive UAV control predates this project | Olivares et al. 2026, DOI 10.1007/s00521-026-11941-3 | high |
| PES can adapt decoders online from an external error | official Nengo documentation; Bekolay et al. 2013 | high |
| A classical PD robot controller has been augmented by PES neural correction and run on Loihi | DeWolf et al. 2020, DOI 10.3389/fnbot.2020.568359 | high |
| Residual learning as classical plus learned correction predates this work | Johannink et al. 2019, DOI 10.1109/ICRA.2019.8794127 | high |
| Geometric/quaternion tracking and actuator-aware allocation are mature fields | Lee et al. 2010; Fresk and Nikolakopoulos 2013; ACC 2016 allocation paper | high |
| ACC 2027 explicitly welcomes aerospace, learning-enabled, safety/resilience, and neuroscience intersections | official ACC 2027 author information | high |
| No identical CMG–PES quaternion residual architecture was found | targeted search reported here | medium; absence claims are inherently limited |
| Current project gains and limitations | FULL_PROJECT_AUDIT_2026-09-02.md and frozen manifests | high within the audited files |

## 14. Sources and links

### Local supplied sources

- C:\Research\papers\ACC2027_Gate_Residual_Control\SOTA\Adaptive_augmentation_Geo_control.pdf
- C:\Research\papers\ACC2027_Gate_Residual_Control\SOTA\PPO quadrotor attitude tracking.pdf

### Primary online sources

- L1Quad: https://doi.org/10.1109/TCST.2024.3521182
- HPA-PPO: https://doi.org/10.1016/j.amc.2026.130236
- PES-adaptive UAS controller: https://doi.org/10.1007/s00521-026-11941-3
- Nengo neurorobotics: https://doi.org/10.3389/fnbot.2020.568359
- Spiking adaptive arm control: https://doi.org/10.1098/rspb.2016.2134
- Nengo PES documentation: https://www.nengo.ai/nengo/frontend-api.html
- Residual reinforcement learning: https://doi.org/10.1109/ICRA.2019.8794127
- DATT: https://proceedings.mlr.press/v229/huang23a.html
- Neural-Fly: https://doi.org/10.1126/scirobotics.abm6597
- Neural Lander: https://doi.org/10.1109/ICRA.2019.8794351
- Geometric neural adaptive control: https://doi.org/10.1109/TCST.2020.3006184
- Geometric quadrotor control: https://doi.org/10.1109/CDC.2010.5717652
- Full-quaternion control: https://doi.org/10.23919/ECC.2013.6669617
- ACC actuator allocation: https://doi.org/10.1109/ACC.2016.7524963
- MuJoCo: https://doi.org/10.1109/IROS.2012.6386109
- ACC 2027 author information: https://acc2027.a2c2.org/author-information/
- ACC 2027 important dates: https://acc2027.a2c2.org/important-dates/

## 15. Recommended one-sentence contribution

> We introduce and audit a baseline-preserving, actuator-bounded quaternion attitude residual in which paired continuous membrane–gate dynamics provide the stateful basis and online PES adapts only the decoder, enabling a transparent separation of intrinsic neural dynamics, synaptic adaptation, residual authority, and rotor feasibility across direct and Nengo implementations.
