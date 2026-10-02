# Online PES-Adapted Neuromorphic Membrane–Gate Residual Control for Actuator-Constrained UAV Quaternion Attitude Tracking

## Draft abstract

This paper presents online-adaptive coupled membrane–gate (CMG) residual augmentation for
quaternion attitude control. A classical quaternion proportional-derivative
controller supplies a stabilizing baseline, while positive/negative pairs of
continuous CMG gate states encode normalized control demand. A bounded
decoder generates an additive residual torque, and a projected online PES rule
adapts the decoder during operation. Unlike a replacement controller, the
proposed architecture retains the baseline command and applies the learned term
through the physical actuator allocation. In MuJoCo Hard45 tracking on the
Skydio X2 four-rotor model, online PES reduces mean quaternion error from 0.2941
to 0.1380 (53.1%) and the composite score by 52.0%, with zero rotor saturation.
On a 27 g Crazyflie rotor-authority design model with a 1.98 thrust-to-weight
ratio, the method reduces mean error from 0.2854 to 0.1323 (53.6%) and score by
53.2%, also without rotor saturation. Fixed- and adaptive-conductance CMG
variants are numerically indistinguishable under the present amplified-gate
regime, showing that the performance improvement arises from online decoder
adaptation rather than conductance adaptation. Stock Crazyflie virtual-moment
limits are separately evaluated and shown to be insufficient for the aggressive
mission. The results establish a transparent controller--actuator co-design
framework and motivate hardware validation on a Qube pendulum, 3DOF Hover, and
QCar lane-control platform.

The abstract is paper-ready only after the robustness/hold-out matrix confirms
the numbers. Keep “design model” attached to every enhanced-CF2 claim.

## Core equations

Quaternion error and baseline:

\[
q_e=q_{\rm ref}\otimes q^{-1},\qquad
e_q=\operatorname{sgn}(q_{e,0})\operatorname{vec}(q_e),
\]

\[
\tau_0=\operatorname{sat}_{\tau_{\lim}}
\left(-K_qe_q-K_\omega\omega\right).
\]

Pair encoding:

\[
\bar\tau=\tau_0\oslash\tau_{\lim},\quad
I^+=b+\eta\max(\bar\tau,0),\quad
I^-=b+\eta\max(-\bar\tau,0).
\]

Coupled membrane–gate dynamics:

\[
\dot r=\frac{\sigma(\alpha[v-(v_{\rm th}-\gamma r)])-r}{\tau_r},
\]

\[
\dot v=-\frac{v-v_{\rm rest}}{\tau}+\frac{I}{\tau}
-g(I)r^2(v-v_{\rm reset}),
\]

where \(g(I)=g_0\) for fixed conductance and
\(g(I)=g_0+g_1|I|\) for adaptive conductance.

Gate activity, learned decoder, and additive residual:

\[
a=\operatorname{clip}(G r,0,1),\qquad
s_k=\operatorname{clip}(W_ka_k,-1,1),
\]

\[
\Delta\tau_k=s_k\odot\tau_{\lim},\qquad
\boxed{\tau_k=\operatorname{sat}_{\tau_{\lim}}
(\tau_{0,k}+\beta\Delta\tau_k)}.
\]

Projected PES update:

\[
y_k^*=\operatorname{clip}(-k_e e_{q,k}-k_\omega^*\omega_k,-1,1),
\]

\[
W_{k+1}=\Pi_{[-6,6]}
\left(W_k+\eta(y_k^*-s_k)a_k^\top-\lambda W_k\right).
\]

Rotor allocation:

\[
\begin{bmatrix}T&\tau_x&\tau_y&\tau_z\end{bmatrix}^{\!\top}
=B u,\qquad
u=\operatorname{clip}(B^{-1}[T,\tau^\top]^\top,u_{\min},u_{\max}).
\]

## Contributions

1. A baseline-preserving additive CMG residual architecture with bounded
   commands and explicit rotor allocation.
2. A clean separation between fixed/adaptive neuronal conductance and online
   decoder adaptation.
3. More than 50% Hard45 improvement on the X2 rotor-actuator model.
4. A transparent CF2 actuator-authority study separating the inadequate stock
   virtual-moment model from an explicit four-rotor design model.
5. A shared implementation contract for drones, Qube, 3DOF Hover, and QCar,
   with the canonical controller exercised through the QLabs/PAL QUBE interface.

## Current validated Hard45 results

| Platform | Classical | Fixed residual | Online PES residual | Improvement | Saturation |
|---|---:|---:|---:|---:|---:|
| Skydio X2 rotor model | 0.294082 | 0.263890 | 0.138007 | 53.07% | 0% |
| CF2 stock virtual moments | 2.458662 | 2.516808 | not defensible | — | 99.88% |
| CF2 four-rotor design, 1.5× | 0.285449 | 0.266050 | 0.132319 | 53.65% | 0% |

## QLabs QUBE pendulum transfer result

The same `CMGResidualAugmentor` implementation was connected to the Quanser QUBE
Servo 3 QLabs virtual twin through PAL at 500 Hz. The classical LQR was retained
and the additive neural voltage was bounded to 0.35 V within a 5 V command limit.
Three trials per controller accumulated exactly 20 s of upright balance. All 15
trials remained balanced in the final 5 s with zero reported amplifier faults or
stalls.

| Controller | final-5-s alpha RMS (deg) | Relative to LQR |
|---|---:|---:|
| LQR | 1.0581 +/- 0.0012 | reference |
| fixed residual | 1.0590 +/- 0.0020 | -0.08% |
| adaptive-conductance residual | 1.1170 +/- 0.1003 | -5.57% |
| online-PES fixed conductance | 1.0566 +/- 0.0011 | +0.15% |
| online-PES adaptive conductance | 1.0570 +/- 0.0015 | +0.10% |

This is a cross-backend feasibility and bounded-safety result, not an accuracy
improvement. QLabs exhibits encoder-quantized equilibrium branches near 1.06 and
1.23 degrees RMS. A fixed-wall-time comparison initially suggested approximately
14% improvement, but that effect disappeared after matching actual balance
exposure. The invalidated comparison is preserved in the audit and must not be
cited as a result.

## Claims that are permitted

- Online decoder adaptation produces the large performance gain.
- The X2 result uses explicit rotor actuators and allocation.
- A 50% increase in assumed CF2 per-rotor maximum thrust removes saturation in
  the design model and permits the online residual benefit.
- Fixed and adaptive conductance are null-equivalent in the current regime.
- Archived LIF and Izhikevich pipelines performed worse than PD, but those runs
  motivate rather than prove an intrinsic CMG advantage.

## Claims that are not permitted yet

- Stock Crazyflie hardware achieves the enhanced-model result.
- The method generalizes zero-shot; it learns on each evaluation trajectory.
- Adaptive conductance causes the 50% improvement.
- The CF2 rotor coefficients are identified physical parameters.
- QCar SNN or 3DOF Hover hardware experiments are completed.
- The matched QLabs pendulum nominal experiment improves LQR accuracy.
- CMG is inherently superior to LIF, ALIF, or Izhikevich; a matched feature and
  decoder ablation has not yet been completed.

## Required remaining experiments

1. Hard45, full3, roll, and hardstep on X2 and CF2 rotor design.
2. Five-seed measurement-noise and disturbance matrix.
3. Held-out frequency/amplitude trajectories after freezing learned weights.
4. Beta, learning-rate, gate-gain, and actuator-authority sensitivity.
5. Disturbance-onset recovery and settling-time analysis.
6. If the QUBE is retained as more than a transfer/safety result, run a matched
   arm-recentered disturbance protocol; do not repeat nominal tuning.
7. Run the preregistered neuron-family comparison with identical six-channel
   pair encoding, feature normalization, decoder/PES settings, actuator path,
   tuning budget, missions, and seeds. Include CMG `r`, `v`, and `[v,r]` readouts,
   `gamma=0`, no gate-conductance, and a bandwidth-matched low-pass control.
8. Recover or rerun ALIF; no saved ALIF result artifact is currently available
   on the active `C:` research drive.
