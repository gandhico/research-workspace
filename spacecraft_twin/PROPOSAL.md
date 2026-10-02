# Proposal: neuromorphic spacecraft perception and control

## Research question

Can event-driven estimation and bounded neuromorphic residual control reduce
compute/energy cost while preserving the safety and pointing performance of a
classical spacecraft GNC stack?

## Architecture

1. **Truth dynamics:** Basilisk `MJScene` with bus, reaction wheels, flexible
   appendages, sensors, disturbances, and actuator saturation.
2. **Baseline GNC:** classical navigation, inertial/nadir guidance, MRP or
   quaternion feedback, reaction-wheel allocation, and momentum management.
3. **MuJoCo role:** articulated multibody/contact dynamics inside Basilisk,
   especially wheels, gimbals, deployables, docking, and robotic appendages.
4. **Neuromorphic role:** SNN perception or a bounded residual on top of the
   classical torque request. The baseline remains independently stabilizing.
5. **Evaluation:** pointing error, settling time, wheel momentum, saturation,
   robustness to sensor faults/disturbance, wall time, CPU/GPU utilization, and
   energy proxy per inference/update.

## Experimental ladder

- E0: reproduce the included single-satellite MRP baseline.
- E1: inject sensor noise, gyro bias, and external torque; establish Monte Carlo
  baseline statistics.
- E2: train ANN and SNN estimators on identical observations and labels.
- E3: add a bounded residual torque with authority scheduling and fallback.
- E4: add a second spacecraft with relative-navigation messages and a fixed
  communication graph.
- E5: formation reconfiguration, delay/loss robustness, and decentralized RL;
  preserve a control-barrier or MPC safety filter around every learned action.

## Claim discipline

MuJoCo support in Basilisk 2.11.1 is native but still described upstream as a
developing multibody capability. Validate conservation laws, frame conventions,
and message timing for each new model. Energy claims require measured platform
power or a calibrated hardware energy model; operation counts alone are not
energy measurements.
