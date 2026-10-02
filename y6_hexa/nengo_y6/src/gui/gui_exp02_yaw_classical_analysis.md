# Exp02 yaw — classical Node-based GUI analysis

## 1. Purpose

This GUI isolates the benchmark yaw axis and makes its classical Node-based PD computation visible.

## 2. Physical plant equations

The benchmark folds inertia into the command gains, so $\ddot{psi}=\tau_{psi}$ (equivalently $J\ddot{psi}=\tau$ before normalization). `_AttitudePlant` integrates the double integrator with RK4.

## 3. State definition

The state is $[psi,\dot{psi}]$ in radians and radians/second.

## 4. Reference signal

The reference steps from 0 to 0.5 rad at $t=1$ s, matching `ATT_TARGET['yaw']`.

## 5. Controller law

$$e=psi_{ref}-psi,\qquad \tau=K_pe-K_d\dot{psi},$$

with $K_p=7.0$ and $K_d=3.7$.

## 6. Nengo implementation mapping

`reference` and `plant[0]` form the error. `plant[1]` supplies full-state rate feedback. Labeled Nodes expose the subtraction, damping term, and summed torque.

## 7. Nodes and ensembles

- `reference`: commanded yaw angle.
- `plant`: normalized rotational plant.
- `error`: angle error.
- `rate_feedback`: negative angular-rate path.
- `controller_feedback`: PD torque/acceleration command.
- `final_command`: explicit plant input.
- `tracking`: actual and commanded angle.

## 8. Connections

Reference enters with +1 and angle with -1. Gain transforms $K_p$ and $K_d$ converge on the feedback signal. The final command drives the plant; tracking connections are filtered only for display.

## 9. Closed-loop interpretation

For a constant reference, $\ddot e+3.7\dot e+7.0e=0$. Thus $\omega_n=\sqrt{7.0}=2.646$ rad/s and $\zeta=3.7/(2\sqrt{7.0})=0.699$.

## 10. CFG visualizations

The layout shows angle/reference tracking, final torque, error, and controller feedback.

## 11. Expected behavior

The angle remains near zero before 1 s, then reaches 0.5 rad with a well-damped transient; rate and torque return toward zero after settling.

## 12. Limitations

Axes are decoupled, inertia is normalized, and aerodynamic coupling, actuator limits, sensor noise, and Euler-angle cross-coupling are omitted.
