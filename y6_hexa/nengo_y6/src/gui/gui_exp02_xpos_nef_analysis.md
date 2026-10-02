# Exp02 x-position/theta cascade — NEF LIF-spiking GUI analysis

## 1. Purpose

This GUI exposes both layers of the underactuated x-position cascade: outer position PD, nonlinear desired-theta mapping, and inner attitude PD.

## 2. Physical plant equations

$$\dot p=v,\quad \ddot p=s g\tan\eta,\quad \dot\eta=q,\quad \ddot\eta=\tau,$$

where $p=x$, $\eta=theta$, and $s=+1$. Plant tilt is clipped to $\pm35^\circ$ before `tan`, as in `subsystems.py`.

## 3. State definition

`plant` returns $[x,\dot x,theta,\dot theta]$.

## 4. Reference signal

The x reference steps from 0 to 2 m at $t=1$ s.

## 5. Controller law

$$e_p=p_{ref}-p,\quad u_p=1.6e_p-2.0\dot p,$$
$$\eta_{cmd}=\operatorname{clip}(\operatorname{atan2}(s u_p,g),\pm35^\circ),$$
$$e_\eta=\eta_{cmd}-\eta,\quad \tau=36.0e_\eta-8.4\dot\eta.$$

## 6. Nengo implementation mapping

The outer error/rate/command and inner error/rate/torque are LIF ensembles; only the exact `atan2` inversion remains a Node.

## 7. Nodes and ensembles

- `reference`, `position_error`, and `outer_feedback`: outer loop.
- `desired_attitude`: nonlinear virtual command.
- `attitude_error`, rate/damping signal, and `controller_feedback`: inner loop.
- `final_command`: torque input.
- `tracking` and `attitude_tracking`: paired monitors.

## 8. Connections

Signed reference/state connections build both errors. Gain paths build each PD command. The desired attitude bridges the loops; the inner torque closes the four-state plant.

## 9. Closed-loop interpretation

For small tilt, $\tan\eta\approx\eta$ and the exact inversion makes the outer dynamics approximately $\ddot e_p+2.0\dot e_p+1.6e_p=0$. The inner natural frequency is $\sqrt{36.0}=6$ rad/s, faster than the outer $\sqrt{1.6}=1.26$ rad/s.

## 10. CFG visualizations

Plots show position tracking, actual versus commanded theta, torque, position error, outer feedback, and inner feedback. Rasters show outer error, outer damping, and inner torque activity.

## 11. Expected behavior

After the step, the outer loop requests a bounded tilt, position accelerates, the requested tilt reverses for braking, and both position error and attitude command decay near zero.

## 12. Limitations

This is one horizontal channel with exact `tan` but no coupling to altitude/yaw, no rotor dynamics, and full-state velocity feedback. Tilt clipping introduces a nonlinear limit not present in the small-angle error equation.
