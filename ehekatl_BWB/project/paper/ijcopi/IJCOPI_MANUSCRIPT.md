# From Offline Optimality to Real-Time Simulation Flight: Delay-Aware LQR and Constrained DeePC for an EHEKATL Blended-Wing-Body Aircraft

**Double-blind manuscript**

**Spanish title:** De la optimalidad fuera de línea al vuelo simulado en tiempo real: LQR consciente del retardo y DeePC restringido para una aeronave EHEKATL de ala integrada

## Abstract

Nominal optimal-control performance can deteriorate when a flight controller is
transferred through delayed actuator routing, hidden augmentation and hard
constraints. This study compares delay-aware linear-quadratic regulation (LQR)
and constrained data-enabled predictive control (DeePC) for local roll-rate
regulation of an EHEKATL blended-wing-body aircraft in X-Plane 12. Stabilised
multisine tests identified the realised 35 Hz command-to-surface-to-rate path,
while a recovery-capable backstepping controller provided permanent fallback.
LQR reduced the matched integral error by 11.1%, below the predeclared 30%
target. DeePC passed 243 of 243 model-uncertainty cases. Both controllers then
executed safely at 35 Hz under common command and slew limits; DeePC's maximum
solve time was 7.90 ms within a 28.57 ms period. Power analysis found that a
superiority claim requires 48 pulses per controller under separate reloads or
24 validated paired pulses. The evidence supports real-time feasibility, but
not DeePC superiority.

**Keywords:** blended-wing body; LQR; DeePC; data-driven control; real-time
optimisation; flight simulation

## Spanish metadata

**Resumen:** El desempeño nominal de un controlador óptimo puede deteriorarse
cuando se transfiere a una ruta de actuación con retardo, aumentación oculta y
restricciones duras. Este estudio compara regulación lineal cuadrática (LQR)
consciente del retardo y control predictivo habilitado por datos (DeePC)
restringido para regular localmente la velocidad de alabeo de una aeronave
EHEKATL de ala integrada en X-Plane 12. Ensayos multisinusoidales estabilizados
identificaron la ruta realizada a 35 Hz. LQR redujo el error integral 11.1 %,
por debajo de la meta predeclarada de 30 %, mientras DeePC superó 243 de 243
casos de incertidumbre. Ambos controladores operaron de forma segura a 35 Hz;
el tiempo máximo de solución de DeePC fue 7.90 ms. La evidencia demuestra
viabilidad en tiempo real, pero no superioridad de DeePC.

**Palabras clave:** ala integrada; LQR; DeePC; control basado en datos;
optimización en tiempo real; simulación de vuelo

## 1. Introduction

Linear-quadratic control is attractive for aircraft regulation because it
provides a transparent state-feedback law and an explicit state-versus-control
trade-off (Kalman, 1960). Its conclusions nevertheless depend on the fidelity of the model,
state definition, actuator representation, delay model, and operating point.
Data-enabled predictive control offers a complementary approach: rather than
first reducing measured behaviour to a low-order parametric plant, DeePC uses
input-output trajectories to predict and optimise future behaviour subject to
constraints (Coulson et al., 2019, 2022). Whether this advantage survives real-time implementation is an
experimental question.

The EHEKATL aircraft is a scale blended-wing-body model represented in X-Plane
12. Initial thesis-derived LTI studies produced stable LQR behaviour offline,
but direct transfer to X-Plane was unsuccessful. Historical fixed-gain flights
reached 53.0 deg absolute pitch and 111.9 deg absolute roll in one run, while a
second run repeatedly activated divergence guards. These failures motivated a
stage-gated redevelopment process based on measured actuator realization,
independent training and validation data, immutable performance thresholds, and
a recovery-capable backstepping baseline.

This paper makes five bounded contributions. First, it documents the
implementation gap between nominal LQR analysis and the realised X-Plane
control path. Second, it presents a stabilised identification procedure and a
directly discrete 35-Hz roll cascade. Third, it implements constrained LQR and
DeePC controllers behind a common safety, fallback, and actuator-restoration
contract. Fourth, it measures online optimisation time against the control
deadline. Fifth, it reports both successful real-time integration and failed
performance and power gates without retrospectively weakening the criteria. The
experiments are real-time closed-loop simulation flights; they are not
physical-aircraft flight tests.

## 2. State of the art and research gap

Blended-wing-body (BWB) control research has progressed from local linear
regulators towards integrated robust control, nonlinear inversion and
allocation over many redundant surfaces. NASA and Boeing's X-48B programme is
the main open flight-research reference. It combined envelope expansion,
system-identification manoeuvres and a nonlinear dynamic-inversion architecture
with pseudo-daisy-chain allocation across a highly redundant surface set
(Glaab et al., 2009; Jordan et al., 2008). The programme also showed that
instrumentation, surface realisation and an explicit envelope-expansion process
are part of the controller experiment rather than peripheral implementation
details.

Model-based work has extended LQR and LQG with mixed H2/H-infinity, structured
H-infinity and linear-parameter-varying formulations. Denieul et al. (2017),
for example, jointly considered BWB surface geometry, allocation and robust
control-law design. These approaches retain interpretable robustness
objectives, but their guarantees remain tied to the selected model,
linearisation, scheduling variables and actuator representation. The broad
2025 BWB review by Ali et al. and the tailless-aircraft review by Hu et al.
(2024) identify stability, control coupling and redundant effectors as
persistent configuration-level problems.

Control allocation is therefore central to tailless aircraft. Weighted
pseudoinverse, direct allocation, redistributed pseudoinverse, quadratic
programming and nonlinear or incremental allocation can distribute requested
moments while respecting position and rate limits. Wind-tunnel BWB experiments
show, however, that linear effectiveness matrices can lose material accuracy at
large deflections and high incidence. Waters et al. (2013) reported typical
moment losses of 10-30%, with some allocation cases delivering only about half
the requested moment. That evidence motivates separate covariance-aware
elevon-allocation work for EHEKATL, but the present paper keeps a single realised
roll channel so that LQR and DeePC use exactly the same input and output.

Nonlinear and fault-tolerant BWB studies use backstepping, sliding-mode control,
incremental methods and disturbance observers. Liu and Whidborne (2021)
combined incremental backstepping, sliding-mode ideas and an RBF observer for
fault tolerance. The present work uses backstepping in a different role: it is
the recovery-capable baseline and permanent safety fallback, not a third
optimiser in the performance contest.

DeePC follows the behavioural result that a persistently exciting trajectory
can parametrise the finite trajectories of a controllable linear system
(Willems et al., 2005). The original formulation and its distributionally
robust extension established the optimisation framework (Coulson et al., 2019,
2022). Experimental aerial evidence includes quadrotors (Elokda et al., 2021),
whereas open BWB studies remain dominated by model-based robust and nonlinear
control. Hybrid DeePC now incorporates partial model knowledge to improve data
efficiency and conditioning (Watson, 2025). Public evidence nevertheless
remains sparse for DeePC acting through the delayed, augmented and
surface-realisation path of a BWB simulator.

Recent IJCOPI aerospace-control studies have reported experimental robust
discrete control for a hexacopter (Ordaz Oliver et al., 2024) and identification
with adaptive control for a tail-sitter UAV (Álvarez González et al., 2026).
These studies establish the relevance of reproducible discrete control and
aircraft identification to the journal, but neither examines behavioural
predictive optimisation through a measured BWB command-to-realised-actuator
path.

The defensible gap is therefore narrower than claiming a first use of DeePC in
aircraft. Published DeePC flight-control evidence is concentrated in
multirotors, while open BWB control work concentrates on model-based nonlinear,
robust and allocation methods. A reproducible LQR-DeePC comparison through a
measured BWB command-to-realised-actuator path, with common constraints,
fallback logic, prospective power analysis and publication of failed gates, is
underrepresented.

## 3. Aircraft, simulator, and operating condition

The test article was the EHEKATL BWB G33 scale aircraft in X-Plane 12.4.3-r2,
interfaced through the NASA XPlaneConnect architecture (NASA Ames Research
Center, n.d.).
The frozen local operating condition, denoted R3, was approximately 1700 m
altitude, 39 kt indicated airspeed, 240 Pa dynamic pressure, cockpit throttle
0.02353, 1.3 deg pitch, near-zero roll, and low body rates. Manual/Clear weather,
no declared failures, enabled X-Plane artificial stability, disabled
autopilot/autothrottle, live simulation speed, and replay off were required.

The common manipulated variable was trim-relative yoke-roll perturbation. Body
roll rate P was the primary regulated output. Roll angle, total roll-control
ratio, distributed aileron deflection, moments, simulator state, override
ownership, and timing were retained as audit channels. Both optimized
controllers ran at 35 Hz with command magnitude limited to 0.0002 normalised
units and slew limited to 0.00005 per sample. The original backstepping law was
updated at its validated 10-Hz rate and held between updates when used as the
fallback.

## 4. Control-path diagnosis and identification

Early experiments showed that a transmitted XPlaneConnect CTRL packet did not
necessarily equal the realised actuator input. When the simulator was paused
or in replay, writable yoke values could change without advancing surfaces or
aircraft dynamics. Even in live simulation, physical joystick input could
overwrite nonpersistent commands between controller updates. Persistent
per-axis ownership and direct yoke writes were therefore required.

Taking ownership exposed an additional trim problem. The original controller
implicitly relied on a physical pitch input near 0.149 normalised units. A
first owned-axis handoff removed this contribution and produced a pitch-rate
transient of approximately -13.85 deg/s. Subsequent tests captured the realised
trim before ownership and applied controller outputs as trim-relative
perturbations. Artificial stability remained active and altered the mapping
between yoke command and total control; consequently, measured total control,
not sent command alone, was used for plant identification.

Stabilized multisine experiments were superimposed on backstepping rather than
replacing it. Two training and two held-out validation runs were collected for
each of roll and pitch. All eight datasets passed completeness, realization,
spectral-richness, safety, and restoration gates. A 10-Hz local angle/rate model
identified a three-sample input delay but retained colored residuals. Higher-rate
testing subsequently isolated the measured cascade

\[
u_{y,k} \rightarrow u_{t,k} \rightarrow \delta_{a,k} \rightarrow P_k,
\]

where commanded yoke perturbation maps dynamically to total roll control,
total control maps almost statically to distributed aileron motion, and surface
motion maps dynamically to roll rate. Temporal held-out validation supported a
directly discrete 35-Hz cascade, while continuous-time pole interpretations
were rejected because fitted time constants were at or below the sampling
interval.

## 5. Delay-aware LQR

The frozen roll-rate LQR state was

\[
x_k = [\Delta P_k,\;\Delta u_{t,k},\;\Delta u_{y,k-1}]^T,
\]

with the identified dynamics

\[
x_{k+1}=Ax_k+Bu_k.
\]

The discrete matrices were

\[
A=\begin{bmatrix}
0.40856&3.55738&37.94551\\
0&0.05609&0.59835\\
0&0&0
\end{bmatrix},\qquad
B=\begin{bmatrix}23.90120\\0.37689\\1\end{bmatrix}.
\]

The input minimized the infinite-horizon quadratic cost

\[
J=\sum_{k=0}^{\infty}(x_k^TQx_k+u_k^TRu_k),
\]

subject at runtime to the common command and slew limits. The resulting gain
was

\[
K=[0.0002944,\;0.0027424,\;0.0292528].
\]

The nominal closed-loop spectral radius was 0.3684. Across 243 coefficient
combinations, the worst spectral radius was 0.4936 with no unstable cases.
These results establish robustness of the frozen measured-cascade model, not
global stability of the X-Plane aircraft.

## 6. Regularised constrained DeePC

The selected DeePC used one input (trim-relative yoke-roll perturbation) and one
output (roll-rate perturbation). Attempts to predict P, roll angle, and total
roll control jointly failed the reconstruction gate; the final claim is
therefore explicitly P-only. With Hankel matrices constructed from the frozen
design trajectory following the behavioural trajectory parameterisation
(Coulson et al., 2019; Willems et al., 2005), each control update solved a
regularised finite-horizon problem of the form

\[
\min_g \; \|y_f\|_{Q_y}^2+\|u_f\|_{R_u}^2+
\|\Delta u_f\|_{R_{\Delta u}}^2+\lambda_g\|g\|_2^2,
\]

subject to past input/output consistency, future behavioural constraints, and
hard command/slew bounds. Candidate output sets, five past/prediction-window
pairs, and six regularisation values from 0.0001 to 1000 were evaluated using a
training-only temporal split. The P-only, five-past/five-future configuration
gave the lowest accepted normalised reconstruction error (0.2926) with full
constraint-row rank. A subsequent 3 by 4 grid over input and slew penalties was
screened against convergence and frozen worst-case gates. The selected
configuration used lambda_g = 10, Q_y = 1, R_u = 0.01, and R_delta_u = 0.02.
Selection preferred the least aggressive penalty pair within 2% of the best
passing worst-case integral ratio; confirmation responses remained unopened.

The ten-second, 35-Hz library window was normalised before constructing the
trajectory maps. Constant matrices were condensed offline, and the online
five-step input sequence was solved with a deterministic projected-gradient
method. Its fixed step was 0.95 divided by the largest eigenvalue of the
condensed Hessian. Iteration stopped when the maximum component-wise change in
the input sequence was no greater than 1e-7, or after 300 iterations. Every
update enforced the 0.0002 command and 0.00005-per-sample slew limits.
Precomputation reduced runtime without changing commands;
packaged-versus-design command error was exactly zero.

The controller contained a permanent fallback latch. Nonfinite inputs,
optimiser nonconvergence, deadline violation, simulator-state violation, or
safety-envelope violation permanently transferred selection to bounded
backstepping for the remainder of the run. Automatic DeePC re-engagement was
not permitted.

## 7. Experimental protocol and metrics

Every engaged run first evaluated altitude, airspeed, pitch, roll, body rates,
artificial-stability state, override ownership, pause, simulation speed, and
replay mode. A failed start gate sent no control. After a passing gate, roll and
pitch axes were owned explicitly. Pitch remained stabilised by the original
backstepping law, while the tested controller supplied the roll perturbation.
Captured yoke values were restored in a `finally` path and verified after the
run.

The primary performance measure was time-integrated absolute roll-rate
deviation. Secondary measures included peak and final-window roll-rate
deviation, control energy, command and slew utilization, computation time,
deadline misses, fallback events, and restoration error. Performance thresholds
and dataset roles were frozen before confirmation data were opened. A safe run
was treated as integration evidence, not automatically as a performance pass.

## 8. Results

### 8.1 LQR matched-performance result

The measured-cascade LQR passed its integration and safety prerequisites. In
the frozen matched backstepping/LQR flight pair, the final integral ratio was
0.888807, or an 11.1% reduction relative to backstepping. The predeclared gate
required a ratio no greater than 0.70. The LQR performance claim therefore
failed. The ratio worsened as the quiet tail was accumulated, indicating that
reload-specific background motion dominated the small disturbance response.

### 8.2 DeePC offline robustness and integration

The final DeePC candidate converged in all 243 frozen-model uncertainty cases.
The worst and median DeePC/LQR integral ratios were 0.895344 and 0.788056, and
the worst peak ratio was 0.928154. Maximum command and base slew were
4.39e-5 and 9.97e-6, respectively, within the common constraints. A guarded
design pilot passed all integration gates and was excluded from confirmation.

### 8.3 Direct demonstrations

Table 1 reports the two user-requested direct demonstrations. Each began after
a fresh R3 reload; consequently, the values are descriptive and are not a
matched comparison.

**Table 1. Direct controller demonstrations under the common runtime contract**

| Metric | DeePC | LQR |
|---|---:|---:|
| Samples | 1050 | 1050 |
| Effective frequency [Hz] | 35.0014 | 35.0040 |
| Maximum gap [ms] | 50.09 | 42.23 |
| Integral absolute delta-P [deg] | 0.01972 | 0.02025 |
| RMS delta-P [deg/s] | 0.000796 | 0.000863 |
| Peak absolute delta-P [deg/s] | 0.004163 | 0.005622 |
| Final-5-s maximum absolute delta-P [deg/s] | 0.001311 | 0.001496 |
| Peak command | 4.609e-5 | 4.670e-5 |
| Maximum slew | 2.126e-5 | 2.171e-5 |
| Fallback/safety event | none | none |
| Verified restoration | pass | pass |

DeePC median, 95th-percentile, and maximum optimisation times were 4.02, 5.36,
and 7.90 ms, respectively, below the 28.57-ms sample period. Both controller
runtimes reproduced their frozen offline behaviour exactly. The slightly smaller
DeePC response metrics cannot be interpreted causally because the initial
reloads and background trajectories were not matched.

![Direct controller demonstrations](generated/direct_controller_demonstrations.png)

### 8.4 Prospective power

Prospective moving-block bootstrap analyses quantified the cost of an
independent superiority claim. A separate-reload design first exceeded 0.80
power at 48 pulses per controller, requiring at least 149 s per controller. A
paired mean per-pulse IAE design achieved power 0.7967 at 16 pairs, which failed
the unchanged 0.80 gate; it first qualified at 24 pairs and at least 152 s.
That design also required controller switching and history handoffs not yet
validated in flight. The benchmark was therefore rejected before collection.

**Table 2. Frozen evidence gates and observed decisions**

| Gate | Frozen criterion | Observed evidence | Decision |
|---|---|---|---|
| LQR matched improvement | Integral ratio <= 0.70 | 0.888807 | Fail |
| DeePC uncertainty replay | Worst integral ratio <= 0.90; worst peak ratio <= 1.10; all updates converge | 0.895344; 0.928154; 243/243 cases converged | Pass |
| Real-time DeePC | Maximum solve time < 28.57 ms | 7.90 ms | Pass |
| Paired superiority design | Prospective power >= 0.80 before collection | 0.7967 at 16 pairs; first pass at 24 pairs, but switching unvalidated | No flight |

![Offline robustness and prospective power](generated/offline_robustness_and_power.png)

## 9. Discussion

The experiments show why offline optimality and online performance should be
treated separately. The LQR was stable and robust over its identified model,
yet its matched improvement was small in X-Plane. The dominant complications
were not numerical Riccati-solver limitations: they were control ownership,
hidden trim, artificial-stability dynamics, a dynamic commanded-to-realised
input path, local model validity, and reload-specific background motion.

DeePC reduced dependence on an explicit low-order state realization and passed
the frozen offline robustness gate. It also met the real-time computational
budget comfortably. Nevertheless, using measured data does not eliminate
distribution shift. The selected controller predicts only P, its design data
come from a local R3 trajectory, and the effect expected over LQR was too small
relative to observed variability for an economical confirmation campaign.

The negative gates are an engineering result. Relaxing the 30% LQR target after
observing an 11.1% improvement, rounding 0.7967 power to 0.80, or presenting
separate-reload demonstrations as a matched comparison would each overstate the
evidence. Preserving these failures yields a reproducible account of what the
controllers do reliably: bounded local roll-rate regulation with verified
real-time execution, fallback readiness, and restoration.

## 10. Limitations

The conclusions apply only near R3 and do not establish transfer to other
airspeeds, dynamic pressures, mass properties, weather conditions, or failure
states. Artificial stability was enabled and forms part of the tested plant.
The work validates roll-rate behaviour, not a complete attitude loop, combined
longitudinal/lateral operation, or large-disturbance recovery. DeePC is P-only.
The direct demonstrations are single, unmatched runs. Finally, X-Plane is a
high-fidelity simulation environment, not physical flight hardware; network,
sensor, actuator, and aerodynamic effects on a real aircraft may differ.

## 11. Conclusions

A delay-aware measured-cascade LQR and a regularised constrained DeePC were
implemented successfully for the EHEKATL BWB in real-time X-Plane flight. Both
direct demonstrations met timing, command, slew, safety, exact-replay, fallback,
and actuator-restoration requirements. DeePC optimisation remained well within
the 35-Hz deadline. However, LQR failed its predeclared 30% matched-improvement
gate, and a powered DeePC-versus-LQR superiority experiment was impractical
under the available local protocol. The appropriate conclusion is therefore
not that one controller universally outperforms the other, but that safe
implementation is achievable while predicted performance differences can be
overwhelmed by the realised control path and operating variability. Future work
should prioritize multi-regime data, state/augmentation measurements,
gain-scheduled or multi-dataset formulations, and a prospectively powered
common benchmark before extending to attitude control.

## Data availability and reproducibility statement

Every paper-facing dataset is listed with its role and SHA256 hash in
`paper/DATASET_REGISTRY.csv`. Raw logs are retained under `logs/`, frozen
numerical artifacts under `configs/`, and controller/analysis code under
`lqr/`, `deepc/`, and `scripts/`. Paper tables and figures are regenerated by
`paper/generate_paper_results.py`. Design, demonstration, and held-out evidence
are kept distinct. No physical-aircraft data are claimed.

## Generative AI use disclosure

Generative AI tools were used for language editing, literature organisation and
document preparation. The authors verified the calculations, source records,
software, experimental evidence and claim boundaries and retain full
responsibility for the manuscript.

## Conflict of interest statement

The conflict-of-interest declaration is supplied separately to the editor to
preserve double-blind review.

## References

Ali, U., Okasha, M., Dief, T. N., ElSayed, M. S. A., & Kamra, M. M. (2025).
Blended wing body designs for aerodynamic, stability, and control optimisation:
A comprehensive review. *Transportation Engineering, 22*, 100397.
https://doi.org/10.1016/j.treng.2025.100397

Álvarez González, J. C., Ramos Velasco, L. E., Vega Navarrete, M. A., Domínguez
Mayorga, C. R., Marroquín Gutiérrez, F., & Argumedo Teuffer, P. J. (2026).
Identification and control of a tail-sitter unmanned aerial vehicle.
*International Journal of Combinatorial Optimization Problems and Informatics,
17*(1), 132-155. https://doi.org/10.61467/2007.1558.2026.v17i1.1230

Coulson, J., Lygeros, J., & Dörfler, F. (2019). Data-enabled predictive control:
In the shallows of the DeePC. In *2019 18th European Control Conference*
(pp. 307-312). IEEE. https://doi.org/10.23919/ECC.2019.8795639

Coulson, J., Lygeros, J., & Dörfler, F. (2022). Distributionally robust chance
constrained data-enabled predictive control. *IEEE Transactions on Automatic
Control, 67*(7), 3289-3304. https://doi.org/10.1109/TAC.2021.3097706

Denieul, Y., Bordeneuve-Guibé, J., Alazard, D., Toussaint, C., & Taquin, G.
(2017). Integrated design of flight control surfaces and laws for new aircraft
configurations. *IFAC-PapersOnLine, 50*(1), 14180-14187.
https://doi.org/10.1016/j.ifacol.2017.08.2085

Elokda, E., Coulson, J., Beuchat, P. N., Lygeros, J., & Dörfler, F. (2021).
Data-enabled predictive control for quadcopters. *International Journal of
Robust and Nonlinear Control, 31*(18), 8916-8936.
https://doi.org/10.1002/rnc.5686

Hu, Y., Song, J., & Wu, M. (2024). A review of control methods for tailless
aircraft. *Guidance, Navigation and Control, 4*(4).
https://doi.org/10.1142/S2737480724300026

Kalman, R. E. (1960). Contributions to the theory of optimal control. *Boletín
de la Sociedad Matemática Mexicana, 5*, 102-119.

Liu, S. Q., & Whidborne, J. F. (2021). Observer-based incremental backstepping
sliding-mode fault-tolerant control for blended-wing-body aircrafts.
*Neurocomputing, 464*, 546-561. https://doi.org/10.1016/j.neucom.2021.08.069

NASA Ames Research Center. (n.d.). *X-Plane Communication Toolbox XPC*
(Software reference ARC-17185-1). NASA Software Catalog.

Ordaz Oliver, M. O., Santos Sánchez, O. J., Ordaz Oliver, J. P., Romero Trejo,
H., & García Pérez, O. (2024). Robust linear discrete control for a hexacopter:
Experimental results. *International Journal of Combinatorial Optimization
Problems and Informatics, 15*(3), 183-204.
https://doi.org/10.61467/2007.1558.2024.v15i3.423

Regan, C. D. (2008). *In-flight stability analysis of the X-48B aircraft*.
NASA Technical Reports Server, 20080034515.

Risch, T. K., Cosentino, G. B., Regan, C. D., Kisska, M., & Princen, N. (2009).
*X-48B flight test progress overview*. NASA Technical Reports Server,
20090005939.

Waters, S. M., Voskuijl, M., Veldhuis, L. L. M., & Geuskens, F. J. J. M. M.
(2013). Control allocation performance for blended wing body aircraft and its
impact on control surface design. *Aerospace Science and Technology, 29*(1),
18-27. https://doi.org/10.1016/j.ast.2013.01.004

Watson, J. D. (2025). Hybrid data-enabled predictive control: Incorporating
model knowledge into the DeePC. *IEEE Open Journal of Control Systems, 4*,
549-561. https://doi.org/10.1109/OJCSYS.2025.3625364

Willems, J. C., Rapisarda, P., Markovsky, I., & De Moor, B. L. M. (2005). A
note on persistency of excitation. *Systems & Control Letters, 54*(4), 325-329.
https://doi.org/10.1016/j.sysconle.2004.09.003
