# CMG/PES alignment to the 3DOF Hover

> Implementation status, 2026-08-28: the gaps documented below describe the
> original LQR hardware runner. The isolated runner now implements the proposed
> three-axis torque-space design with six units, quaternion error, body rate,
> and ten 0.5 ms neural substeps. The remaining voltage allocation and safety
> projection differences are enumerated in `MUJOCO_HOVER_CONFORMANCE.md`.

## Current signal path

The current hardware runner implements

\[
x\rightarrow e\rightarrow K_{LQR}\rightarrow
u_{0,raw}\rightarrow\operatorname{clip}_{[0,24]}\rightarrow u_0,
\]

then

\[
u_0\rightarrow\text{scaled gate drive}\rightarrow(v,r,a),
\]

and independently

\[
(e_q,-\omega)\rightarrow\text{unit motor mixer}\rightarrow y^*,
\]

followed by

\[
W^+=W+\eta(y^*-Wa)a^T-\lambda W,
\qquad
\Delta u_v=\beta\,\ell\odot\operatorname{clip}(Wa,-1,1),
\]

\[
u=\operatorname{clip}_{[0,24]}(u_0+\Delta u_v).
\]

The continuous membrane–gate unit is

\[
\dot r=\frac{\sigma\{\alpha[v-(v_{th}-\gamma r)]\}-r}{\tau_r},
\]

\[
\dot v=-\frac{v-v_{rest}}{\tau}+\frac{I}{\tau}
-\big(g_0+g_1|I|\big)r^2(v-v_{reset}),
\]

and activity is `a = clip(1e5 r, 0, 1)`.

## Where it differs from MuJoCo

| Item | MuJoCo drones | Current 3DOF Hover |
|---|---|---|
| Learned/output channels | 3 body torques | 4 motor voltages |
| CMG units | 6 (± per torque axis) | 8 (± per motor) |
| Baseline gate drive | signed pre-allocation torque | clipped, biased motor command rescaled after saturation |
| Residual insertion | before rotor allocation | after baseline motor allocation/clipping |
| Saturation geometry | torque limit, then actuator mixer | per-motor residual bound, then positive-voltage clip |
| Error geometry | quaternion vector + body rate | Euler angle + filtered joint rate |
| Neural timestep | typically 1 ms | 5 ms at 200 Hz |

These are legitimate platform adaptations, but they are not the same
architecture with only a different plant.

## High-priority gaps

### 1. Learn in generalized torque space

Use three CMG channels `[yaw, pitch, roll]`, drive them with the signed
pre-allocation PD torque, learn a three-axis target, then allocate
`tau_PD + delta_tau` to four motors under the positive-voltage constraints.
This removes common-mode motor residuals and gives each learned channel a clear
physical meaning.

### 2. Preserve unsatisfied demand

The current gate drive is derived after the LQR motor command is clipped. When a
motor request goes negative, clipping erases how far outside the feasible set it
was. Feed the gate the signed pre-saturation axis torque (normalized by a reviewed
torque authority) and separately provide allocator saturation/headroom features
if desired.

### 3. Respect neural time constants at 200 Hz

At 200 Hz, `dt = tau_r = 5 ms`; the explicit gate update reduces to essentially
one-sample assignment to its instantaneous sigmoid target. MuJoCo generally uses
`dt = 1 ms`, so it resolves five samples per gate time constant. Either run the
CMG dynamics in stable internal substeps or redesign/discretize the time constants
for 200 Hz. This should be an offline/replay ablation before hardware.

### 4. Fix the claimed slew behavior before relying on it

`SafeGateBridge.step()` slew-limits `out.command`, but the hardware runner adds
`out.residual` directly to the LQR baseline. The returned residual is the
pre-slew augmentor residual, so the configured 4 V/s bridge slew limit is not on
the actually applied residual path. The residual magnitude bound still applies;
the slew guarantee does not.

### 5. Make positive-voltage saturation part of learning

At Set K, the actual maximum residual per motor is
`beta * max_residual_volts = 0.4 * 3 = 1.2 V`, not 3 V. If the baseline is at
0 V, negative residual authority is immediately removed, while positive residual
remains available. PES currently learns a symmetric target for an asymmetric
realized actuator. Use allocator-aware projection and train/update against the
realized torque residual, not merely the requested motor residual.

### 6. Log what proves the mechanism

Add, in a later reviewed runner revision:

- raw and clipped baseline motor commands;
- requested and realized axis torque;
- raw, projected, and applied residuals;
- per-channel lower/upper saturation flags and allocator headroom;
- measured loop period and deadline misses;
- all decoder weights `W(t)` or at least periodic snapshots;
- per-axis error, gate activity, and membrane/gate states.

## Focused architecture recommendation

The next CMG version should be

\[
\tau_0=K_p e-K_d\omega,
\]

\[
\Delta\tau=\beta\,\tau_{lim}\odot\operatorname{clip}(Wa,-1,1),
\]

\[
u_v=\mathcal A_{[0,24]}(\tau_0+\Delta\tau,V_b),
\]

where `A` is a constrained four-motor allocator. PES should use the difference
between desired correction and the torque correction actually realized after
allocation. Keep the existing motor-space implementation as an ablation, not as
the only hardware realization.
