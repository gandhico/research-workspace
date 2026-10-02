# Exp01 altitude — NEF LIF-spiking GUI analysis

## 1. Purpose

`gui_exp01_altitude_nef.py` is the interactive counterpart of Exp01. It closes the benchmark 1-DOF altitude plant around the NEF LIF-spiking PD controller and exposes tracking, error, damping feedback, controller feedback, and final thrust.

## 2. Physical plant equations

The z-up plant is

$$\dot z=v_z,\qquad \dot v_z=\frac{u}{m}-g,$$

with $m=0.9$ kg, $g=9.81$ m/s$^2$, and $0\le u\le2.5mg$. `_AltitudePlant` applies the same zero-order-hold RK4 step and thrust clipping as `src/models/altitude_1dof.py`.

## 3. State definition

`plant` returns $[z,\dot z]$. Position is index 0 and vertical velocity is index 1.

## 4. Reference signal

`reference` is 0 m for $t<1$ s and 1 m afterward, exactly matching `run_exp01.py`.

## 5. Controller law

$$e_z=z_{ref}-z,\qquad u=mg+K_pe_z-K_d\dot z,$$

with $K_p=8$ and $K_d=4$. For a constant reference,

$$\ddot e_z+\frac{K_d}{m}\dot e_z+\frac{K_p}{m}e_z=0.$$

## 6. Nengo implementation mapping

The controller uses LIF spiking ensembles. The reference and negative plant position form `error`; negative velocity forms the damping/rate path; the gain-bearing connections or Nodes form `controller_feedback`; `final_command` adds $mg$ and closes the loop.

## 7. Nodes and ensembles

- `reference`: altitude command.
- `plant`: stateful physical plant.
- error signal: represents $e_z$.
- rate feedback: represents $-\dot z$ (or the already scaled $-K_d\dot z$ in the classical graph).
- controller feedback: represents $K_pe_z-K_d\dot z$.
- `final_command`: total thrust $u$.
- `tracking`: combined $[z,z_{ref}]$ monitor.

## 8. Connections

The positive reference and negative state connections implement subtraction. The proportional and derivative transforms implement the gains. The hover feed-forward and feedback converge at the command, which drives the plant without an extra synapse; monitor connections use 10 ms filtering.

## 9. Closed-loop interpretation

Substituting the controller into the plant cancels gravity. The unsaturated ideal dynamics are a stable second-order system with $\omega_n=\sqrt{8/0.9}\approx2.98$ rad/s and $\zeta=4/(2\sqrt{8(0.9)})\approx0.745$. Neural synapses and decoding add small lag/error but do not change the intended law.

## 10. CFG visualizations

The layout shows tracking, total thrust, error, and PD feedback. Spiking layouts additionally show error, rate, and control rasters; rate/classical layouts omit meaningless spike rasters.

## 11. Expected behavior

Before 1 s the command sits near hover. At the step, thrust rises, altitude approaches 1 m with modest overshoot, and thrust returns to $mg=8.829$ N as error and velocity decay.

## 12. Limitations

This is a vertical point-mass model: attitude, drag, motor dynamics, sensor noise, and ground contact are omitted. Actuator clipping makes the exact linear error equation valid only away from saturation.
