# CF2 four-rotor design-study model

This is not the stock MuJoCo Menagerie CF2 model and is not presented as an
identified Crazyflie 2.1 motor model. It preserves the Menagerie mass, inertia,
geometry, sensors, and total base thrust ceiling, but replaces the abstract body
moments with four explicitly located thrust actuators.

Assumptions:

- Motor-to-motor diagonal: 92 mm, giving projected X-arm coordinates of 32.5 mm.
- Base maximum thrust: 0.0875 N per rotor, preserving the stock XML's 0.35 N total.
- Reaction-torque coefficient: 0.005 m, with alternating rotor signs.
- `--actuator-scale` multiplies the per-rotor maximum for a declared authority study.

This model answers a design question: what rotor authority is required for the
controller to realize the inertia-derived torque commands? It must not be described
as stock Crazyflie hardware validation until thrust and reaction-torque coefficients
are identified experimentally.

