# Exp02 pitch — classical Node-based GUI analysis

## 1. Purpose

This GUI isolates the benchmark pitch axis and makes its classical Node-based PD computation visible.

## 2. Physical plant equations

The benchmark folds inertia into the command gains, so $\ddot{theta}=\tau_{theta}$ (equivalently $J\ddot{theta}=\tau$ before normalization). `_AttitudePlant` integrates the double integrator with RK4.

## 3. State definition

The state is $[theta,\dot{theta}]$ in radians and radians/second.

## 4. Reference signal

The reference steps from 0 to 0.2 rad at $t=1$ s, matching `ATT_TARGET['pitch']`.

## 5. Controller law

$$e=theta_{ref}-theta,\qquad \tau=K_pe-K_d\dot{theta},$$

with $K_p=36.0$ and $K_d=8.4$.

## 6. Nengo implementation mapping

`reference` and `plant[0]` form the error. `plant[1]` supplies full-state rate feedback. Labeled Nodes expose the subtraction, damping term, and summed torque.

## 7. Nodes and ensembles

- `reference`: commanded pitch angle.
- `plant`: normalized rotational plant.
- `error`: angle error.
- `rate_feedback`: negative angular-rate path.
- `controller_feedback`: PD torque/acceleration command.
- `final_command`: explicit plant input.
- `tracking`: actual and commanded angle.

## 8. Connections

Reference enters with +1 and angle with -1. Gain transforms $K_p$ and $K_d$ converge on the feedback signal. The final command drives the plant; tracking connections are filtered only for display.

## 9. Closed-loop interpretation

For a constant reference, $\ddot e+8.4\dot e+36.0e=0$. Thus $\omega_n=\sqrt{36.0}=6.000$ rad/s and $\zeta=8.4/(2\sqrt{36.0})=0.700$.

## 10. CFG visualizations

The layout shows angle/reference tracking, final torque, error, and controller feedback.

## 11. Expected behavior

The angle remains near zero before 1 s, then reaches 0.2 rad with a well-damped transient; rate and torque return toward zero after settling.

## 12. Limitations

Axes are decoupled, inertia is normalized, and aerodynamic coupling, actuator limits, sensor noise, and Euler-angle cross-coupling are omitted.
