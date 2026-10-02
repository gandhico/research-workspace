# PD baseline design and exact LQR equivalence

> Update, 2026-08-28: this document proves the optional `lqr-equivalent`
> bridge. The default physical experiment now reproduces the canonical MuJoCo
> quaternion-PD/CMG path. See `MUJOCO_HOVER_CONFORMANCE.md`. The two profiles
> are intentionally not conflated.

## 1. Result

The current vendor LQR is already a PD controller in generalized torque
coordinates. A separately tuned PD baseline is therefore useful as an
architecture/implementation ablation, but it is not a fundamentally different
controller class. The fairest MuJoCo-comparable baseline is to expose the
existing law explicitly as axis-space PD and retain the same bias, motor map,
voltage limits, rate estimate, reference, and sample rate.

## 2. Plant and channel map

Use the verified hardware order

\[
u_v=[V_f,V_b,V_l,V_r]^\top.
\]

For state order

\[
x=[\psi,\theta,\phi,\dot\psi,\dot\theta,\dot\phi]^\top
\]

(yaw, pitch, roll), the vendor linear model gives

\[
\tau=G u_v,
\qquad
G=\begin{bmatrix}
-K_t&-K_t&K_t&K_t\\
LK_f&-LK_f&0&0\\
0&0&-LK_f&LK_f
\end{bmatrix},
\]

where \(\tau=[\tau_y,\tau_p,\tau_r]^\top\). The common bias
\(V_b\mathbf{1}_4\) is in the nullspace of \(G\), so it produces no nominal
generalized torque.

The current Python baseline is

\[
u_v=\operatorname{clip}_{[0,24]}
\left(K_{\rm LQR}\begin{bmatrix}e_q\\-\omega\end{bmatrix}
+V_b\mathbf{1}_4\right),
\]

with \(V_b=2\) motor-equivalent volts and
\(e_q=q_d-q=[e_y,e_p,e_r]^\top\).

## 3. Transforming LQR to PD

Before element-wise voltage clipping,

\[
\tau=G K_{\rm LQR}
\begin{bmatrix}e_q\\-\omega\end{bmatrix}
=K_p e_q-K_d\omega.
\]

Using the exact matrix in the hardware runner,

\[
G K_{\rm LQR}=
\begin{bmatrix}
1.609969&0&0&0.596344&0&0\\
0&6.187297&0&0&1.694384&0\\
0&0&6.187297&0&0&1.694384
\end{bmatrix}.
\]

Therefore

\[
K_p=\operatorname{diag}(1.609969,6.187297,6.187297)\;{\rm N\,m/rad},
\]

\[
K_d=\operatorname{diag}(0.596344,1.694384,1.694384)
\;{\rm N\,m\,s/rad}.
\]

Numerically, the largest off-axis term is less than
\(6\times10^{-17}\), i.e. floating-point zero. This is an exact structural
equivalence, not an approximation.

With the vendor inertias
\(J_y=0.110445\) and \(J_p=J_r=0.0552225\;{\rm kg\,m^2}\), the equivalent
second-order values are

\[
\omega_n=[3.818,10.585,10.585]\;{\rm rad/s},\qquad
\zeta=[0.707,1.449,1.449].
\]

## 4. Two legitimate implementations

### A. Exact baseline reproduction

Compute the existing four motor-voltage commands and clip them exactly as the
vendor law does. This is the correct implementation when the goal is to prove
that the Python result reproduces MATLAB/Simulink, including its saturation
behavior.

### B. MuJoCo-like axis PD plus allocation

Compute \(\tau_{PD}=K_pe_q-K_d\omega\), then solve

\[
\min_{u_v}\|u_v-V_b\mathbf{1}\|_2^2
\quad\text{s.t.}\quad
G u_v=\tau_{PD},\;0\le u_v\le24.
\]

This has a transparent 3-DOF controller/4-actuator separation and is the better
interface for a three-channel CMG residual. It is exactly equal to the LQR in
the unsaturated region. Near an actuator bound it can differ because constrained
allocation preserves requested torque differently from independently clipping
the four LQR voltages. That difference must be declared as an allocator change,
not attributed to PD versus LQR.

## 5. Fair comparison conditions

Hold all of the following fixed between LQR and explicit PD:

- same startup tare and physical initial pose;
- same 200 Hz loop and same measured/filtered rates;
- same reference and duration;
- same 2 V common bias and 0–24 V motor-equivalent bounds;
- same channel order and amplifier conversion;
- same safety aborts and output slew policy;
- same error metric and exclusion/transient policy.

Because A and B are identical away from saturation, a large tracking difference
would indicate an implementation mismatch, saturation/allocation difference, or
data-condition mismatch—not a control-theory advantage.

## 6. Recommended role in the ACC paper

Describe the hardware baseline as “vendor LQR (equivalently, a decentralized
axis PD law for the identified double-integrator model).” Keep LQR as the named
hardware benchmark because that is how the gains were designed and validated by
Quanser. Use the explicit PD form to connect the hardware architecture to the
MuJoCo baseline and to make the residual insertion point unambiguous.
