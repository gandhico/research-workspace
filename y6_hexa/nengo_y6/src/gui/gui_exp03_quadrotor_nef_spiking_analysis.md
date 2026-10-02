# Exp03 full quadrotor — NEF spiking GUI analysis

## 1. Purpose

`gui_exp03_quadrotor_nef_spiking.py` visualizes the complete 12-state trajectory-tracking cascade used in Exp03, including position references, outer feedback, desired tilt, attitude stabilization, total thrust, and the four-component plant command.

## 2. Physical plant equations

The translational dynamics are

$$\ddot x=\frac{u}{m}(\sin\phi\sin\psi+\cos\phi\cos\psi\sin\theta),$$
$$\ddot y=\frac{u}{m}(\cos\phi\sin\theta\sin\psi-\cos\psi\sin\phi),$$
$$\ddot z=\frac{u}{m}\cos\theta\cos\phi-g,$$

and $\ddot\psi=\tau_\psi$, $\ddot\theta=\tau_\theta$, $\ddot\phi=\tau_\phi$. `_QuadPlant` uses the benchmark RK4 update with $m=0.9$ kg.

## 3. State definition

$X=[x,\dot x,y,\dot y,z,\dot z,\psi,\dot\psi,\theta,\dot\theta,\phi,\dot\phi]$.

## 4. Reference signal

$x_d=y_d=\sin(0.1t)$ with analytic derivatives. $z_d$ ramps 0→1 m over 10 s, holds to 20 s, ramps to 0.5 m by 30 s, then holds. $\psi_d=0$. Initial state matches `X0`.

## 5. Controller law

$$u_x=K_{px}(x_d-x)+K_{vx}(\dot x_d-\dot x),\quad \theta_d=\atan2(u_x,g),$$
$$u_y=K_{py}(y_d-y)+K_{vy}(\dot y_d-\dot y),\quad \phi_d=\atan2(-u_y\cos\theta,g),$$
$$u=\frac{mg+K_{pz}(z_d-z)-K_{vz}\dot z}{\cos\theta\cos\phi},$$
$$\tau_a=K_{pa}(a_d-a)-K_{va}\dot a,\qquad a\in\{\psi,\theta,\phi\}.$$

Gains are the benchmark values: z 40/5, x 1.6/2, y 3/2, yaw 7/4, pitch 120/8, and roll 40/8.

## 6. Nengo implementation mapping

Six NEF PD channels each use error, rate, and command ensembles. The file selects LIF spiking neurons. The analytic tilt and thrust inversions remain Nodes, matching `quadrotor_nef.py`.

## 7. Nodes and ensembles

`reference` and `plant` define the closed-loop boundary. Error and feedback blocks expose position/yaw and attitude regulation. `desired_attitude` computes $[\theta_d,\phi_d]`; `thrust_command` applies gravity/tilt compensation; `final_command` is $[u,\tau_\psi,\tau_\theta,\tau_\phi]$. Tracking monitors combine actual/reference position and actual/desired tilt.

## 8. Connections

Signed connections form position, velocity, and attitude errors. Gain transforms implement each PD channel. Outer x/y feedback feeds the nonlinear desired-attitude map; inner feedback plus compensated thrust is assembled and sent directly to the RK4 plant.

## 9. Closed-loop interpretation

The architecture is a time-scale-separated cascade. Near hover, $\theta_d\approx u_x/g$ and $\phi_d\approx-u_y/g$, so horizontal acceleration follows the outer virtual command while fast pitch/roll loops stabilize tilt. The z feed-forward cancels gravity when level.

## 10. CFG visualizations

The layout shows six-trace position tracking, the four final commands, position error, and actual/desired attitude. The spiking layout adds representative error, damping, and pitch-control rasters.

## 11. Expected behavior

The vehicle follows the slow x/y sinusoid and z ramp with small lag. Desired tilt remains modest; total thrust stays near $mg$ in steady level flight and changes during vertical/tilt transients.

## 12. Limitations

Angular inputs are inertia-normalized; motor/rotor allocation, drag, sensor noise, saturation, and rigid-body gyroscopic coupling are omitted. The GUI mirrors the benchmark abstraction rather than a hardware flight stack.
