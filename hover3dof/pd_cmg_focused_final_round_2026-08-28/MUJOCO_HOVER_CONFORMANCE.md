# MuJoCo PD/CMG to 3DOF Hover conformance specification

Status: implemented and offline-validated on 2026-08-28. No hardware was
opened, armed, or commanded during this work.

## 1. What "reproduce MuJoCo" means

The first physical comparison uses the controller structure and frozen neural
parameters from `platforms/drone.py`, with only the transformations required by
the Hover coordinate convention and actuator interface. The experiment is
therefore described precisely as:

> MuJoCo-matched quaternion-PD plus three-axis CMG/PES, followed by a declared
> 3DOF-Hover voltage safety projection.

It must not be described as identical actuator authority. MuJoCo accepts a
signed three-axis torque before its rotor allocation; the Hover accepts four
nonnegative motor voltages and needs additional magnitude and slew limits.

## 2. Canonical MuJoCo equations

In `drone.py`, body order is (x,y,z=[roll,pitch,yaw]). With

\[
\omega_n=[4,4,3.5],\qquad \zeta=0.95,
\]

\[
K_q=2J\omega_n^2,\qquad K_\omega=2\zeta J\omega_n,
\]

and the model/inertia torque policy

\[
\tau_{lim}=J\odot[12,12,10],
\]

the quaternion baseline is

\[
q_e=q_d\otimes q^{-1},\qquad q_e\leftarrow
\operatorname{sgn}(q_{e,w})q_e,
\]

\[
\tau_0^{M}=\operatorname{clip}
\left(-K_q\odot q_{e,v}^{M}-K_\omega\odot\omega^{M},
-\tau_{lim},\tau_{lim}\right).
\]

The six coupled membrane-gate units receive the signed normalized baseline
torque (one positive and one negative unit per axis). PES uses

\[
y^{*M}=\operatorname{clip}
\left(-k_e q_{e,v}^{M}-k_\omega\omega^{M},-1,1\right),
\]

with the frozen comparison parameters

\[
\beta=0.5,\quad \eta=8\times10^{-4},\quad k_e=8,\quad
k_\omega=0,\quad \Delta t_n=0.0005\;s.
\]

The decoder produces a bounded three-axis residual torque, and the residual is
inserted before actuator allocation.

## 3. Exact Hover-coordinate form

The Hover signal order is (h=[yaw,pitch,roll]). Its verified physical torque
map has the opposite sign from the MuJoCo controller torque coordinate. Define

\[
P=\begin{bmatrix}0&0&1\\0&1&0\\1&0&0\end{bmatrix},\qquad
z^H=-Pz^M
\]

for physical rate/torque vectors. After applying this declared coordinate map,
the implemented equations are

\[
\tau_0^H=\operatorname{clip}
\left(+K_q^H\odot q_{e,v}^H-K_\omega^H\odot\omega^H,
-\tau_{lim}^H,\tau_{lim}^H\right),
\]

\[
y^{*H}=\operatorname{clip}
\left(+k_e q_{e,v}^H-k_\omega\omega^H,-1,1\right).
\]

These plus/minus signs are a coordinate transform, not a changed feedback law.
A unit test evaluates both coordinate forms on the same synthetic state and
requires their transformed torques and PES targets to be equal.

For the vendor plant values, in Hover yaw/pitch/roll order:

| Quantity | Yaw | Pitch | Roll |
|---|---:|---:|---:|
| inertia (J), kg m2 | 0.110444919 | 0.055222460 | 0.055222460 |
| (K_q) | 2.70590052 | 1.76711871 | 1.76711871 |
| (K_\omega) | 0.73445871 | 0.41969069 | 0.41969069 |
| +/- torque limit, N m | 1.10444919 | 0.66266951 | 0.66266951 |

Encoder Euler rates are converted to ZYX body angular velocity before either
the PD damping term or PES target is evaluated.

## 4. Signal architecture implemented

```text
encoder angles -> quaternion -> shortest-path quaternion error q_e,v
encoder rates  -> ZYX body rate omega
                         |                    |
                         +--> quaternion PD --+--> tau_0 (3 axes, clipped)
                         |                         |
                         |                         +--> signed CMG gate drive
                         +--> PES target y* ----------> online decoder update
                                                       |
tau_0 + requested delta_tau <--------------------------+
              |
              v
3x4 minimum-norm torque-to-motor map
              |
per-motor residual cap -> residual slew limit -> positive 0..24 V projection
              |
              v
Q8 outputs [Front, Back, Left, Right]
```

There are six CMG units: positive and negative units for yaw, pitch, and roll.
The CMG/PES state is advanced ten times at 0.5 ms inside each 5 ms hardware
control interval. This preserves the MuJoCo neural integration step while the
Q8 loop remains at 200 Hz.

## 5. Declared hardware-only adaptations

| Adaptation | Reason | Frozen first-comparison choice |
|---|---|---|
| Euler encoders converted to quaternion/body rate | Hover has joint encoders, not a MuJoCo quaternion sensor | deterministic ZYX conversion |
| Four-motor voltage allocation | Q8 commands voltage, not abstract body torque | verified F/B/L/R motor map |
| Positive voltage box | hardware command range is 0 to 24 V | final command clipping |
| Per-motor residual cap | prevent the learned path from receiving full model torque authority | staged 0.3, 0.6, then 1.2 V; comparison cap 1.2 V |
| Residual slew limit | bound rapid online changes | 4 V/s |
| 200 Hz signal logging | matches the rest of the hardware trace | one post-substep neural state per control sample |
| Optional stability-priority allocation | keep all propellers active and preserve pitch/roll before yaw when voltage demand is infeasible | separately labeled Hover recovery generation; 2 V motor floor |

The LQR-equivalent Euler-PD profile is retained only as a software bridge and
ablation. It is not used as the default MuJoCo-reproduction baseline and is
rejected when `pd-cmg` is selected.

## 6. Complete neuron and decoder record

Every `trace.csv` row includes, at the same 200 Hz timestamps as angles,
torques, and voltages:

- `neuron_v_0..5`: membrane state;
- `neuron_r_0..5`: gate state;
- `neuron_activity_0..5`: decoder input activity;
- `neuron_current_0..5`: signed CMG input current;
- `decoder_w_0..17`: flattened 3 by 6 online PES decoder;
- quaternion error, body rate, PES target, requested/realized residual torque,
  motor residual, and all saturation flags.

These are post-integration states after the ten 0.5 ms substeps in that control
interval. This is deliberately synchronized with the other measured signals,
so later plots and causal comparisons need no resampling.

## 7. Important authority finding

Frozen-trace replay satisfies every command, residual, and slew bound, but the
requested MuJoCo-space residual is much larger than the residual the Hover can
realize after the safety projection:

| Mission | Requested residual RMS | Realized residual RMS | Mean gate |
|---|---:|---:|---:|
| hard45 | 0.232920 N m | 0.010485 N m | 0.9600 |
| full3 | 0.231420 N m | 0.011247 N m | 0.8217 |
| yaw360 | 0.146264 N m | 0.008979 N m | 0.0991 |

This is not hidden or retuned away. Requested and realized torque are both
logged. Any paper result must report that the neuron/controller architecture is
matched, while safe physical authority is projected by the Hover allocator.

## 8. Traceability

- Canonical source: `C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\platforms\drone.py`
- Hover runner: `runners\hover3dof_hil_pd_cmg_control.py`
- Shared tested equations: `src\pd_baseline.py`
- Offline replay: `tools\replay_pd_cmg_on_trace.py`
- Unit tests: `tests\test_pd_baseline.py`
- Hardware protocol: `PD_HARDWARE_RUNBOOK.md`
