# CMG-PES residual architecture: signal and implementation audit

Date: 2026-09-11. Scope: the rotor-actuated X2 and CF2-derived MuJoCo experiments in the current manuscript. The figure represents the canonical additive, online-PES controller. It does not represent the legacy blending mode, an LQR controller, or a four-motor-voltage Hover controller.

No experiment, controller source, gain, result, or hardware configuration is changed by this revision. The old paper and diagrams remain in their previous folders. The new editable drawing is `source/architectures/tikz/arch_residual_io.tex`; the updated manuscript is `source/ACC2027.tex` in this review folder.

## 1. What the architecture does

A fixed quaternion PD controller requests three body torques. Its clipped output also drives six continuous membrane-gate units: one positive-current and one negative-current channel per torque axis. Their gate-derived activities feed a learned 3-by-6 decoder. A bounded decoder output is scaled into torque units, added to the PD request, and clipped again. A fixed height loop supplies collective thrust. The common inverse allocator converts this four-component requested wrench into four rotor forces; per-rotor clipping determines the wrench actually delivered to the MuJoCo rigid body.

The learning branch is different from the encoding branch. Encoding receives the clipped PD torque. The teaching target receives the quaternion error and body rate. PES compares this prescribed normalized target with the clipped decoder output, using the same activity that produced that output. Only the decoder weights are updated by PES. The evolving membrane and gate states are not themselves learned parameters.

## 2. Corrections to the two supplied drawings

| Issue | Resolution in the new figure |
|---|---|
| Mission, quaternion convention, and error formation | A mission-reference input and the exact quaternion error equations are visible in the error/PD block. Plant feedback is labeled with the controller quaternion and body rate. |
| Teacher appeared to receive raw attitude instead of computed error | A separate, labeled output carries `e_q, omega` from the error/PD block into the teaching-target block. |
| Old drawing omitted rotor-force clipping and the collective-thrust path | Both clipping stages and the height-controller branch are explicit. |
| Dimensionless neural output could be mistaken for torque | `s_k`, the torque-valued pre-clipping residual, requested torque, rotor forces, and realized wrench have separate names. |
| `W_(k+1)` seemed to feed the current decoder immediately | A one-step memory block makes the causal update explicit. The current step reads `W_k`; the update is stored for the next step. |
| Activity-to-PES connection was missing or unlabeled | A branch dot and labeled `a_k` connection supply exactly the activity used in decoding. |
| Existing PES block implicitly needed old weights for leak | The memory also supplies `W_k` to the update block. |
| Crowded implementation qualifications along the feedback wire | The wire now contains only the feedback signals. Backend timing details remain in text, not inside the figure. |
| Gate called a decoder | The gate is an internal state; its scaled/clipped activity is a decoder input. `W_k` is the learned linear decoder. |

Gray identifies the fixed classical/plant path. Blue identifies components belonging to the residual branch; it does **not** mean every blue block learns. The dashed boundary groups the residual branch. Dots identify signal branching. The error and PD operations share one frame for space, but their computed error has its own output port.

## 3. Input/output contract at every block

All vector clipping, division, multiplication, and maxima below are componentwise unless a matrix product is shown. The neuron variables and decoder signals are dimensionless; the neural current is not a measured electrical current in amperes, and the membrane state is not a calibrated voltage in volts.

| Block | Inputs | Outputs | Dimensions and units | Stored state / parameters |
|---|---|---|---|---|
| Mission reference | Mission definition, time `t_k` | `q_d,k` | Unit quaternion: 4 components, 3 independent rotational DOFs | Fixed reference schedule |
| Quaternion error and PD | `q_d,k`, `q_k`, `omega_k` | `u_0,k`; separate `e_q,k, omega_k` to teacher | Error: 3 dimensionless components; rate: 3 rad/s; baseline: 3 N m | Fixed `K_q, K_omega, ell`; no PD gain adaptation |
| Normalization and paired currents | `u_0,k` | `I_k = col(I_k^+, I_k^-)` | 3 normalized inputs -> 6 dimensionless currents | Fixed `ell, I_b, I_g` |
| Six CMG units | `I_k`; previous `v_k,r_k` | `a_k` | 6 currents -> 6 activities in `[0,1]`; 12 internal scalar states | Six membranes and six gates; fixed intrinsic parameters |
| Decoder and output bound | `a_k`, stored `W_k` | `s_k` | `W_k`: 3-by-6; `s_k`: 3 components in `[-1,1]` | Reads the current 18 decoder weights |
| Teaching target | `e_q,k, omega_k` | `y_k^*` | 3 dimensionless components in `[-1,1]` | Fixed `k_e, k_omega^*`; not the PD torque gains |
| PES, leak, projection | `y_k^*, s_k, a_k, W_k` | `W_(k+1)` | Error: 3; outer product: 3-by-6 | Per-step `eta, lambda_W`; weight box |
| Decoder memory | `W_(k+1)` | `W_k` on the next sample | 18 scalar weights | Initial `W_0 = [I_3,-I_3]` |
| Bounded torque addition | `u_0,k, s_k` | `u_k` | 3 N m; internal `tilde_delta_k = beta ell .* s_k` | Fixed authority `beta ell` and torque bounds |
| Fixed height controller | `z_k, z_dot,k, R(Q_k)_(33)` | `T_k` | m, m/s, dimensionless -> N | Fixed `z_d=1 m` and height gains |
| Rotor allocation and limits | `T_k, u_k` | `f_act,k` | 4-component requested wrench -> 4 rotor forces in N | Model-specific fixed `B` and rotor-force limits |
| MuJoCo plant | `f_act,k` | Next sampled attitude/rate/height signals | 6-DOF rigid-body state; attitude subtask has 3 DOFs | Rigid-body state and fixed model properties |

There are **three neural torque outputs, six CMG units, eighteen decoder weights, four rotor forces, and six free-body mechanical DOFs**. These counts are not interchangeable. Height control supplies the collective component, not a fourth CMG output. Paired units refer to torque-axis signs, not individual motors.

## 4. Exact equations and within-step order

### 4.1 Error and baseline

The plant quaternion is scalar-first, body-to-inertial `Q`; the controller uses `q=Q^{-1}`. The desired quaternion uses that same passive convention:

\[
q_{e,k}=q_{d,k}\otimes q_k^{-1},\qquad
e_{q,k}=\operatorname{sgn}_{+}(q_{e,0,k})q_{e,v,k},\qquad \operatorname{sgn}_{+}(0)=1.
\]

\[
u_{0,k}=\operatorname{sat}_{\ell}(-K_q e_{q,k}-K_\omega\omega_k).
\]

The derivative term is measured body angular rate, **not** reference-rate error. No desired-rate feedforward or gyroscopic cancellation is added in this diagram. `K_q=diag(k_q)` and `K_omega=diag(k_omega)` reproduce the elementwise products in the code.

### 4.2 Encoding is driven by the baseline, not the teacher

\[
\bar u_k=u_{0,k}\oslash\ell,\qquad
I_k^\pm=I_b\mathbf1+I_g\max(\pm\bar u_k,0),\qquad
I_k=\operatorname{col}(I_k^+,I_k^-).
\]

The order is `(+x,+y,+z,-x,-y,-z)`. Since `u_0` is already clipped, each normalized component lies in `[-1,1]`; the canonical currents lie in `[0.75,2]`. Both sign branches have the positive bias, including at zero command. The encoder never receives `u_k` or realized rotor torque, avoiding an instantaneous self-feedback loop through the residual.

### 4.3 Both membrane and gate participate

For each unit `j`, the continuous dynamics are

\[
\dot r_j=\frac{\sigma(\alpha_h(v_j-v_{\rm th}+\gamma r_j))-r_j}{\tau_r},\quad
\dot v_j=-\frac{v_j-v_{\rm rest}}{\tau}+\frac{I_j}{\tau}-c_j(v_j-v_{\rm reset}),
\quad c_j=(g_0+\chi g_1|I_j|)r_j^2.
\]

The gate affects its own threshold through `gamma r` and affects the membrane through `c`. The membrane affects the gate target. `chi` selects input-dependent conductance; it is a fixed experiment setting, not a PES-trained quantity. Setting `chi=0` removes only `g_1 |I|`, not the `g_0 r^2` shunt or either state equation. There are no threshold-triggered spikes or reset events. `v_reset` is the reversal level of the continuous shunt.

The code uses this sequential discrete step, not a simultaneous Euler step:

\[
b_{j,k}=\sigma\!\left(\operatorname{clip}_{[-60,60]}
\{\alpha_h(v_{j,k}-v_{\rm th}+\gamma r_{j,k})\}\right),\qquad
r_{j,k}^{+}=\operatorname{clip}_{[0,1]}\!\left[r_{j,k}+\frac{h}{\tau_r}(b_{j,k}-r_{j,k})\right].
\]

\[
c_{j,k}=(g_0+\chi g_1|I_{j,k}|)(r_{j,k}^{+})^2,\quad
\lambda_{j,k}=\tau^{-1}+c_{j,k},\quad
d_{j,k}=\frac{v_{\rm rest}+I_{j,k}}{\tau}+c_{j,k}v_{\rm reset}.
\]

\[
v_{j,k}^{+}=e^{-\lambda_{j,k}h}v_{j,k}
 +(1-e^{-\lambda_{j,k}h})\frac{d_{j,k}}{\lambda_{j,k}},\quad
a_{j,k}=\operatorname{clip}_{[0,1]}(G r_{j,k}^{+}).
\]

The next stored states are `(v_(k+1),r_(k+1))=(v_k^+,r_k^+)`. In this splitting, `r_k^+` uses the **old** membrane state. The just-computed membrane `v_k^+` influences the next gate update. The diagram's map denotes this complete step; the expanded unit topology remains Figure 3 and the numerical equations remain in Section III.

The decoder reads `a`, not `v`, not raw `r`, and not a spike train. At canonical `G=10^5`, `a=1` already when `r>=10^-5`; an active internal coupling need not produce distinguishable decoded activity. The revised diagram does not claim that conductance is necessary for the reported improvement.

### 4.4 Decoding and learning are distinct operations

\[
s_k=\operatorname{clip}_{[-1,1]}(W_k a_k),\quad W_0=[I_3,-I_3],\qquad
y_k^*=\operatorname{clip}_{[-1,1]}(-k_e e_{q,k}-k_\omega^*\omega_k).
\]

Initially the decoder subtracts each negative-direction activity from its positive-direction partner. Learning may subsequently couple all six activities into each of the three outputs; it is not constrained to three isolated pairs. The teacher gains set a normalized residual target and are not `K_q,K_omega` in different notation. Neither `y^*` nor `s` is a desired angle or rotor-force vector.

\[
\varepsilon_k=y_k^*-s_k,\qquad
W_{k+1}=\Pi_{\mathcal W}\!\left[(1-\lambda_W)W_k+\eta\varepsilon_k a_k^\mathsf T\right],
\qquad \mathcal W=[-6,6]^{3\times6}.
\]

Dimensions: `(3-by-1)(1-by-6)=3-by-6`, matching `W`. Leak uses the old weights. Projection acts entrywise. `eta` and `lambda_W` are per-step coefficients; the implemented direct update does not multiply them by an additional timestep. The current command keeps the already-computed `s_k` even though the code updates stored weights before returning from the function. This is exactly what the one-step memory expresses.

PES is an error-directed decoder update toward a prescribed target. It does not identify an unknown disturbance torque, backpropagate through MuJoCo, or optimize the actual mission metric directly. With clipped readout, it is not the exact gradient of the clipped squared-error loss. The diagram intentionally contains no unsupported plant-gradient or disturbance-observer arrow.

### 4.5 Residual, requested torque, and realized torque

\[
\widetilde\delta_k=\beta\ell\odot s_k,\qquad
u_k=\operatorname{sat}_{\ell}(u_{0,k}+\widetilde\delta_k),\qquad
\delta_k=u_k-u_{0,k}.
\]

`tilde_delta` is the pre-clipping neural torque request; `delta` is the actual change in the requested torque after the controller-side clip. They differ whenever that clip is active. Since `u_0` already lies in the same torque box, `|delta_i| <= beta ell_i`. At `beta=0`, the command is exactly `u_0`; this is a command-level baseline-preservation statement, not a general nonlinear stability certificate.

\[
T_k=\operatorname{clip}_{[0,2.5Mg]}\left(
\frac{M[g+6(z_d-z_k)-4\dot z_k]}{\max(R(Q_k)_{33},0.35)}\right),\qquad z_d=1\ {\rm m},
\]

\[
f_{{\rm req},k}=B^{-1}\begin{bmatrix}T_k\\u_k\end{bmatrix},\quad
f_{{\rm act},k}=\operatorname{clip}_{[0,f_{\max}]}(f_{{\rm req},k}),\quad
\begin{bmatrix}T_{{\rm act},k}\\\tau_{{\rm act},k}\end{bmatrix}=B f_{{\rm act},k}.
\]

For parallel positive-body-z thrust axes, column `i` of `B` is `[1,p_(i,y),-p_(i,x),kappa_i]^T`. Its first row sums forces; the remaining rows include lever arms and reaction-torque coefficients. Therefore the rows do not all have the same physical units. The actual wrench equals the requested wrench only when the requested rotor forces lie within their bounds. This is clipped inverse allocation, not a constrained optimal allocator.

`f_act` is the model's algebraic rotor-force input in newtons. It is not a PWM, voltage, or RPM command. The current model interface has no motor-lag state. The separate CMG torque output has no direct collective component, although attitude changes affect height and allocation. In the code the collective upper bound is `2.5*M*max(g,1)`; for the Earth-gravity models in the paper this equals the displayed `2.5*M*g`.

### 4.6 Chronological execution at sample k

1. Read plant state at `t_k`; convert `Q_k` into controller quaternion `q_k`; evaluate `q_d,k`.
2. Compute `e_q,k`, fixed clipped `u_0,k`, and the independent teaching target `y_k^*`.
3. Normalize `u_0,k`; form the six paired currents.
4. Advance gate first, then membrane; form gate-derived activity `a_k`.
5. Read current `W_k`; compute and clip `s_k`.
6. Calculate the PES/leak/projected `W_(k+1)` and store it. Do not decode the current activity again with these new weights.
7. Use the saved `s_k` to form the bounded torque command `u_k`.
8. Calculate collective `T_k` from the same sampled height/tilt state; allocate and clip four rotor forces.
9. Write the actuator forces and advance MuJoCo. The new plant state is sampled on the next controller iteration.

The feedback loop passes through the dynamic plant: it is not a zero-delay algebraic state equation. In the canonical experiments the controller/neural/MuJoCo step is `h=0.0005 s` (2 kHz); logging may be decimated and is not a different control period.

### 4.7 Canonical settings (not new tuning)

| Group | Values in the canonical UAV experiment |
|---|---|
| Time | `h=0.0005 s`, `tau=0.05 s`, `tau_r=0.005 s` |
| Membrane/gate | `v_rest=v_reset=0`, `v_th=1`, `alpha_h=50`, `gamma=2` |
| Conductance | `g_0=120`, `g_1=30`, `chi=1`; rates are in inverse seconds for dimensionless current |
| Encoding/readout | `I_b=0.75`, `I_g=1.25`, `G=100000` |
| Teacher | `k_e=8`, `k_omega^*=0` |
| Decoder | `eta=0.0008`, `lambda_W=0.000001`, `W_max=6` |
| Torque authority | `beta=0.5`; axiswise torque limits depend on the vehicle |
| Initial neural state | `v_0=0`, `r_0=0`, `W_0=[I_3,-I_3]` |
| PD tuning | `omega_n=(4,4,3.5) rad/s`, `zeta=0.95`; `k_q=2 j_tune .* omega_n^2`, `k_omega=2 zeta j_tune .* omega_n` |
| Torque limits | `ell_i=max(j_tune,i nu_i, 10^-6 N m)`, `nu=(12,12,10) rad/s^2` |

The principal-moment ordering used for `j_tune` is the runner's gain-scheduling convention; it is not silently replaced with the body-frame diagonal of the physical inertia tensor. Model-specific physical properties and rotor-force limits remain those in the paper's model table. Sweep cases deliberately change selected parameters and are not new canonical settings.

## 5. Code-to-block references

Paths below are relative to `C:\Research\papers\ACC2027_Gate_Residual_Control`. Line anchors refer to the audited files as they existed on this date; their full SHA-256 values are saved in `ARCHITECTURE_VALIDATION.json` beside this document.

| Figure operation | Source | Line anchor / exact implementation |
|---|---|---|
| Quaternion conversion, reference, error, PD, teacher | `experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef.py` | 218 onward; `quat_conj`, `quat_error`, clipped `tau0`, clipped `target` |
| Direct encoder | `src/gra_control/gate.py` | 104-115, `CMGResidualAugmentor.step` |
| Gate then membrane update | `src/gra_control/gate.py` | 41-55, `CoupledMembraneGateBank.step` |
| Activity, clipped readout, PES, weight box | `src/gra_control/gate.py` | 116-123 |
| Torque addition and final command clip | `src/gra_control/gate.py` | 125-134; use `online_pes`, not `blend` |
| Fixed collective-height law | `experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef.py` | 289-295 |
| Four-force allocation and write | Same runner | 309-314, `spec.interface == "rotor4"` |
| Plant integration | Same runner | 426, `mujoco.mj_step(model,data)` |
| Native Nengo CMG neuron state step | `experiments/nengo_nef_replication_2026-08-29/nengo_cmg.py` | 71 onward, custom `NeuronType.step` |
| Native Nengo population and learned decoder | Same Nengo module | 150 onward, direct current injection and unfiltered neuron output |
| Nengo output capture, leak, and projection | Same Nengo module | 313-359, `NengoCMGPESAugmentor.step` |

Python output field `command` is paper `u_k`; `baseline` is `u_0,k`; `residual` is `delta_k`, **not** `tilde_delta_k`; `activity` is `a_k`; `gate` is `r_k^+`. The direct object's `W` after the call is `W_(k+1)`, not the weights that produced the returned command. Trace analysis must respect that alignment.

## 6. Direct and Nengo: shared architecture, separately stated timing

The drawing specifies the canonical recurrence in Section III. In Nengo the same six CMG units are a custom neuron type, with current injected into `ensemble.neurons`. It does not add an NEF encoder/gain-fitting layer between the paired-current encoder and these units. The native learned connection maps six unit activities to three residual channels.

Nengo's PES operator uses the opposite error sign, `s-y*`, and a built-in timestep/population-size factor. For unfiltered CMG activity the configured native rate is `eta_N = eta * 6/h`; at `eta=0.0008` and `h=0.0005`, this is `9.6`. That scaling is not a 12,000-fold physical increase in the per-step learning increment. Leak is subtracted using a saved copy of the pre-step weights; weight projection follows the Nengo simulator step.

The native teaching graph has the one-step latency already disclosed in the manuscript. The decoder-memory block in the main diagram explains the causal current/next-weight distinction; it does **not** claim that the native Nengo teaching graph produces the identical direct weight sequence. The backend paragraph remains the place to state that implementation timing and the empirically tested agreement. No identical-trajectory or formal-backend-equivalence claim is introduced here.

## 7. Verification and scope

`validate_architecture.py` independently reconstructs the displayed direct update and compares it with the unmodified controller over 6,144 offline arithmetic steps. It covers `chi=0/1`, gate gains `1/10^5`, residual authorities `0/0.5/1`, canonical initialization, and states near the weight-projection boundary. It checks the old/new-state order, pre-update decoding, leak/projection, output dimensions, exact beta-zero recovery, and the componentwise residual bound. Its machine-readable report contains maximum discrepancies, source hashes, and the number of steps that actually exercise projection.

This is equation-to-implementation verification, not a new mission experiment, hardware test, or stability proof. The current mechanism-audit findings are preserved: substantial tracking gains do not establish a CMG-specific advantage over simpler adaptive residual bases. The architecture accurately documents a tested continuous neuromorphic realization of bounded error-directed residual control.

## 8. Local build and reuse

Compile the paper from this folder's `source` directory: `pdflatex ACC2027.tex`, `bibtex ACC2027`, then `pdflatex ACC2027.tex` twice. The source ZIP is an Overleaf-ready manuscript package, not the postponed full controller/data distribution.

Compile the standalone diagram from this review folder with `pdflatex architecture_standalone.tex`. The same TikZ source is used for the standalone drawing and Figure 1, so they cannot silently diverge. Keep the prior `arch_review.tex` as an archived comparison, not the active Figure 1.
