# Exp04 coaxial Y6 trirotor — classical GUI analysis

## 1. Purpose

`gui_exp04_trirotor_classical.py` is the interactive Exp04 controller/plant model. It retains the full Y6 rigid-body plant, position/yaw cascade, total thrust and body moments, the 6×4 coaxial allocation, and all six rotor-speed commands.

## 2. Physical plant equations

Rotor $i$ produces $F_i=K_F\Omega_i^2$ and drag torque $K_\tau\Omega_i^2$. Total thrust is $F_z=\sum_iF_i$. Body translation uses

$$\dot{\mathbf p}=R_{EB}\mathbf v_b,\quad
\dot u=rv-qw+g\sin\theta,\quad
\dot v=pw-ru-g\sin\phi\cos\theta,$$
$$\dot w=qu-pv-g\cos\phi\cos\theta+F_z/m.$$

Euler rates use $T_{EB}[p,q,r]^T$. Roll/pitch moments come from the triangular arm geometry plus coaxial gyroscopic terms; yaw comes from the odd(top)-minus-even(bottom) drag split. The full $I_{xz}$ form is retained (with benchmark $I_{xz}=0$), and RK4 advances all 12 states.

## 3. State definition

$[X,Y,Z,u,v,w,\phi,\theta,\psi,p,q,r]$: Earth position, body velocity, Euler attitude, and body rates.

## 4. Reference signal

Before 2 s the command is $(0,0,1.5\text{ m},0)$. At 2 s it steps to $(1,-0.5,2\text{ m},20^\circ)$, matching `run_exp04.py`.

## 5. Controller law

$$a_x^*=2(x_d-x)-2.6v_x,\quad a_y^*=2(y_d-y)-2.6v_y,$$
$$\theta^*=\operatorname{clip}((a_x^*\cos\psi+a_y^*\sin\psi)/g),$$
$$\phi^*=\operatorname{clip}((a_x^*\sin\psi-a_y^*\cos\psi)/g),$$
$$T=\operatorname{clip}\left(\frac{mg+9(z_d-z)-5.2v_z}{\max(\cos\phi\cos\theta,0.5)}\right),$$
$$\tau_x=1.3(\phi^*-\phi)-0.28p,\quad \tau_y=1.8(\theta^*-\theta)-0.36q,$$
$$\tau_z=1.0(\psi^*-\psi)-0.32r.$$

## 6. Nengo implementation mapping

Classical labeled Nodes implement the outer and inner feedback equations, followed by the exact allocator.

## 7. Nodes and ensembles

`reference`, `plant`, and `world_velocity` expose the loop boundary and frame conversion. `tracking_error`, feedback blocks, `desired_attitude`, and `total_thrust` implement the cascade. `final_command` is $[T,\tau_x,\tau_y,\tau_z]$; `rotor_forces` and `rotor_command` expose $F_1\ldots F_6$ and $\Omega_1\ldots\Omega_6$.

## 8. Connections

Signed state/reference paths form errors and rate damping. Yaw and horizontal acceleration feed the attitude inversion. Total thrust and body moments enter the allocator. The allocator output is converted through $\Omega_i=\sqrt{\max(F_i,0)/K_F}$, clipped at 900 rad/s, and applied to the plant.

## 9. Closed-loop interpretation

The outer loop requests world-frame acceleration and altitude force; the inner loop stabilizes attitude/yaw. Allocation applies

$$[F_1,\ldots,F_6]^T=A_{mix}[T,\tau_x,\tau_y,\tau_z]^T.$$

For NEF, the command is normalized by $[35,2.5,2.5,1.2]$ in the 4-D population and those scales are folded back into each linear rotor decoder, exactly as in `trirotor_nef.py`.

## 10. CFG visualizations

The layout shows position/yaw tracking, all six rotor speeds, four tracking errors, virtual command, and actual/desired attitude.

## 11. Expected behavior

The vehicle first climbs to 1.5 m, then translates to the waypoint while climbing to 2 m and turning to 20°. Rotor pairs separate transiently to make roll/pitch/yaw moments, then converge toward a hover distribution.

## 12. Limitations

The GUI retains the benchmark rigid-body and allocator equations but omits motor lag, battery dynamics, ground contact, sensor/estimator dynamics, and faults. Negative allocated thrust is clipped during the square-root conversion, so severe commands cannot realize the unconstrained linear mixer exactly.
