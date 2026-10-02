# Physics model status

The canonical XML is a validated rigid-body and ideal-thrust control model, not yet a fully identified hardware twin. The authoritative parameter ledger is [omnicopter_parameters.json](omnicopter_parameters.json). It deliberately uses `null` for unknown hardware quantities rather than inserting plausible-looking constants.

What is active today:

- MuJoCo six-degree-of-freedom rigid-body dynamics, gravity, contact with the ground plane, mesh-derived centre of mass and inertia, and eight signed site forces.
- The final hardware-confirmed rotor positions and frames. Each actuator applies force along that site's local +Z; each moment arm is therefore included automatically.
- Ideal, instantaneous, reversible thrust in the configured range -10 to +10 N.

What is not identified or active:

- measured mass, COM and full inertia tensor;
- ESC command-to-RPM-to-thrust maps in both directions, motor/propeller time constants, reaction torque and rotor gyroscopic inertia;
- body drag coefficients, rotor inflow, wake interaction, ground effect and wind;
- battery, sensor, estimator, computation and communication effects.

Do not enable one of these effects using a guessed value in the canonical model. Measure it, record the raw data and identification method, update the ledger, then add a model variant and rerun the same regression and mission campaigns. This preserves a clean distinction between geometric fidelity, numerical stability and physical predictive validity.

## Identification order

1. Weigh the complete vehicle and locate COM using at least three suspension/support configurations.
2. Obtain inertia from component CAD with verified masses or a pendulum experiment.
3. On a six-axis load cell, sweep each propulsion unit through positive and negative commands at several battery voltages. Fit thrust, reaction torque, deadband, hysteresis and time response.
4. Measure IMU pose, axis convention, noise density, bias instability, bandwidth and total estimator/control delay.
5. Identify body drag using wind-tunnel, free-decay or instrumented flight data. Treat MuJoCo's native fluid model as a reduced-order approximation and validate it against held-out data.
6. Add rotor inflow, ground effect and rotor-rotor interference only through a validated custom force model or co-simulation when those phenomena matter to the mission envelope.

Every parameter set should include units, hardware revision, measurement date, test conditions, uncertainty and source-data hash.
