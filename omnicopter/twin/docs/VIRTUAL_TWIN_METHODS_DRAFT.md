# Methods draft: traceable MuJoCo virtual twin of a fully actuated omnicopter

## Scope

We constructed a MuJoCo virtual twin from the platform STL, hardware-verified
motor mounting frames, measured rigid-body and propulsion parameters, and a
shared six-degree-of-freedom control interface. The methodology distinguishes
geometric registration, parameter identification, software-controller
conformance, and held-out predictive validation. At the present checkpoint,
rotor geometry and software conformance are verified; mass, inertia, propulsion,
sensing and aerodynamic values still require physical identification.

## Geometry and actuation

The STL is converted from millimetres to metres and registered to the body frame
by a fixed translation. Each rotor site lies at a measured body-frame position
`p_i`. Site local X is parallel to its square beam, and site local Z is the
normal of the hardware-selected right beam face. Local Y is computed as
`Z_i × X_i`, producing a right-handed orthonormal frame. The same local Z defines
the motor-cylinder axis and signed thrust direction, eliminating visual/physical
frame disagreement.

For signed thrust `u_i`, direction `d_i`, centre of mass `p_c` and identified
reaction-torque vector `tau_i`, the actuator column is

```text
B_i = [ d_i ; (p_i-p_c) × d_i + tau_i/u_i ].
```

The compiled `B` has rank six. Eight commands are obtained from weighted bounded
least squares; force is applied only through the eight MuJoCo actuator controls.

## Rigid-body and propulsion identification

Mass is measured with a calibrated scale, COM by multi-orientation suspension,
and inertia by bifilar/trifilar tests or component-CAD reconciliation. Every
motor/propeller/ESC channel is tested in both directions to identify static
thrust, reaction torque, deadband, dispersion, first-order dynamics and delay.
Parameter values carry units, standard uncertainty, hardware revision,
conditions and source-data hashes. Identification and validation trajectories
are disjoint.

## Controllers

Four executable variants share the same state, references, gains, actuator map,
limits and 500 Hz update:

1. direct geometric PD plus analytic feedforward;
2. direct PD augmented by a bounded six-channel, 12-cell CMG residual with
   online PES adaptation;
3. the exact PD law executed as a Nengo Node;
4. Nengo-PD plus a custom continuous CMG `NeuronType` and Nengo's native PES
   rule.

Direct/Nengo pairs establish implementation conformance. PD/CMG-PES pairs test
the control hypothesis. Nengo-PD is intentionally exact and is not described as
a neural approximation.

At the current software checkpoint, all four implementations passed the 25
nominal missions without actuator saturation. Direct PD and Nengo-PD had equal
mean position/attitude RMSE (`0.001029 m`, `0.0260 deg`); direct CMG-PES and
Nengo-CMG-PES also matched (`0.011579 m`, `0.0629 deg`). A separate 1000-step
same-state conformance test produced zero stored-precision PD discrepancy and a
maximum direct/Nengo CMG motor-command discrepancy of `1.1437e-7 N`. These are
software results and must not be presented as hardware validation.

The final 25-mission four-way comparison used matching model, mesh, controller,
mission-source, gain and gate hashes. Across complete missions, the maximum
direct/Nengo CMG differences were `9.762e-9 m` in position RMSE,
`3.653e-7 deg` in attitude RMSE and `2.047e-8 N` in peak motor command.

## Physical--virtual synchronization and validation

The physical estimator state, references, eight commands and MuJoCo state are
recorded with acquisition timestamps. Hardware world/body frames are calibrated
to MuJoCo frames before testing. A clock-synchronization protocol determines the
time offset independently of trajectory agreement. Shadow-mode replay feeds the
real initial state and commands to MuJoCo without allowing MuJoCo to command the
aircraft.

Parameter agreement is evaluated against measurement uncertainty and
controller-sensitivity-derived tolerances. Predictive validity is evaluated on
held-out trajectories using position, quaternion geodesic attitude, angular
rate, actuator response, saturation, energy and time-to-recovery metrics.
Confirmatory gates and exclusions are frozen before results are viewed.

## Fidelity boundary

MuJoCo provides rigid-body/contact mechanics, flexible actuator dynamics,
sensors and reduced-order stateless fluid forces. It is not CFD and does not
natively resolve propeller wakes, rotor--rotor interaction, vortex-ring state or
ground effect. Those effects require identified custom wrenches/plugins or
external aerodynamic co-simulation. Claims are limited to phenomena supported
by measured parameters and held-out prediction.

## Reproducibility

Each result bundle records the XML/STL/controller hashes, MuJoCo and Nengo
versions, hardware revision, parameter-set hash, controller settings, mission,
raw and converted logs, time/frame calibration, metrics, gates and deviations.
The ideal-model suite remains a deterministic regression layer and is not
replaced by hardware-calibrated experiments.

## Primary software references

- MuJoCo actuator, sensor, sampling and delay definitions:
  https://mujoco.readthedocs.io/en/stable/XMLreference.html
- MuJoCo reduced-order fluid forces and their non-CFD scope:
  https://mujoco.readthedocs.io/en/stable/computation/fluid.html
- Nengo objects, simulator and ecosystem:
  https://www.nengo.ai/documentation/
- Nengo PES learning rule API:
  https://www.nengo.ai/nengo/frontend-api.html#nengo.PES
- MAVLink time synchronization when MAVLink is the selected transport:
  https://mavlink.io/en/services/timesync.html
