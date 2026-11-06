# Omnicopter MuJoCo virtual-twin methodology

## Status and fidelity boundary

The project now has a hardware-confirmed rotor-frame geometry, a rank-six actuator map, a geometric PD/feedforward controller, a bounded eight-rotor allocator, and an integrated six-channel online-PES residual controller. The model can therefore be used for internally consistent controller development and regression testing.

It is not yet legitimate to call it a fully predictive physical twin. The STL fixes shape, not mass distribution or propulsion/aerodynamic dynamics. Unknown hardware values are recorded as unknown in [physics/omnicopter_parameters.json](../physics/omnicopter_parameters.json); they are not filled with generic drone constants.

The canonical simulation file is [omnidrone.xml](../omnidrone.xml). The root [mjmodel.xml](../mjmodel.xml) is kept geometrically equivalent for direct viewing. Controllers intentionally load the canonical file.

## 1. STL ingestion and model coordinates

The source mesh is [assets/Omnidrone.stl](../assets/Omnidrone.stl). Its raw bounds are approximately:

| STL axis | minimum | maximum | span |
|---|---:|---:|---:|
| X | -395.38687 mm | 12.353123 mm | 407.739993 mm |
| Y | 0.484257 mm | 417.83426 mm | 417.350003 mm |
| Z | -381.57098 mm | 25.629005 mm | 407.199985 mm |

The XML converts millimetres to metres with `scale="0.001 0.001 0.001"`. The mesh geom is translated by `(0.1936, -0.2036, 0.1786)` m in the body so the physical cage is centred on the chosen body frame. This translation is a mesh-to-body registration; it is not a rotor position and must not be folded into site coordinates.

The body starts at `(0, 0, 1)` m with a +90-degree rotation about world Y. That initial world pose is also separate from the local rotor frames. All rotor sites and controller wrench columns are defined in the drone body frame, then MuJoCo applies the body pose.

The rotor site coordinates are the eight sign combinations of `0.0973` m. Their site-to-site cube span is therefore `0.1946` m. The roughly 0.407–0.417 m STL span is the outer structure and must not be substituted for the motor-site cube.

## 2. Constructing each motor/site frame

For rotor position `p_i`, the beam direction is the normalized body-frame position:

```text
X_i = p_i / ||p_i||
```

This makes the site's red local X axis parallel to and outward along its diagonal square beam. A square beam admits four face normals, all perpendicular to `X_i`; choosing one is a discrete physical mounting decision, not an arbitrary Euler-angle fit.

The candidate face planes were recovered from the planar triangle normals in the STL. The final `Z_i` was selected to match the physical motor surface confirmed in the MuJoCo view. The right-handed companion axis is:

```text
Y_i = Z_i × X_i
```

The XML stores `xyaxes="X_i Y_i"`. MuJoCo orthonormalizes those directions and computes local `Z = X × Y`. Consequently, the cylinder axis and `gear="0 0 1 ..."` actuator direction are both the selected surface normal. Changing the visual site frame therefore changes the physics; it is not a cosmetic edit.

The final compiled body-frame axes are:

| Rotor | X: beam direction | Y | Z: thrust / selected face normal |
|---:|---|---|---|
| 1 | (-0.577350, -0.577350, -0.577350) | (0.577350, -0.788675, 0.211325) | (-0.577350, -0.211325, 0.788675) |
| 2 | (-0.577350, -0.577350, 0.577350) | (-0.577350, -0.211325, -0.788675) | (0.577350, -0.788675, -0.211325) |
| 3 | (-0.577350, 0.577350, -0.577350) | (-0.577350, 0.211325, 0.788675) | (0.577350, 0.788675, 0.211325) |
| 4 | (-0.577350, 0.577350, 0.577350) | (0.577350, 0.788675, -0.211325) | (-0.577350, 0.211325, -0.788675) |
| 5 | (0.577350, -0.577350, -0.577350) | (-0.577350, -0.788675, 0.211325) | (-0.577350, 0.211325, -0.788675) |
| 6 | (0.577350, -0.577350, 0.577350) | (0.577350, -0.211325, -0.788675) | (0.577350, 0.788675, 0.211325) |
| 7 | (0.577350, 0.577350, -0.577350) | (0.577350, 0.211325, 0.788675) | (0.577350, -0.788675, -0.211325) |
| 8 | (0.577350, 0.577350, 0.577350) | (-0.577350, 0.788675, -0.211325) | (-0.577350, -0.211325, 0.788675) |

The regression test [review/verify_rotor_frames.py](../review/verify_rotor_frames.py) checks both XML files for the exact X and Z vectors, orthonormality, determinant +1, actuator/site association, rank-six wrench authority, and a bounded hover solution. This replaces visual trial-and-error with a repeatable geometric acceptance test.

## 3. Motor cylinders and physical actuation

Each motor representation is a cylinder site with radius 0.025 m and half-length 0.005 m. A MuJoCo cylinder's symmetry axis is local Z, so the cylinder becomes perpendicular to the selected beam surface automatically when the site frame is correct.

Each `general` actuator transmits through one site using:

```xml
gear="0 0 1 0 0 0"
```

Thus one control unit is currently one newton along site +Z and contributes the body wrench

```text
B_i = [ d_i ]
      [ (p_i - p_COM) × d_i + k_tau_i ]
```

where `d_i = Z_i` and the reaction-torque term `k_tau_i` is currently zero. The complete `B` matrix has rank six. At the initial pose, the minimum-norm gravity-balancing controls are approximately:

```text
[ 5.257152, -5.290759, -5.328877, 5.362485,
  5.257152, -5.290759, -5.328877, 5.362485 ] N
```

Negative thrust is required by this reversible fully actuated design. Hardware experiments must verify that bidirectional propulsion, signs, deadband and the ±10 N bounds are real.

## 4. Classical controller update

[control/hover.py](../control/hover.py) rebuilds `B` from MuJoCo's compiled site frames rather than carrying a hand-written mixer. It requests a body wrench using COM position and geometric quaternion attitude errors:

```text
F_world = m [a_ref + Kp (p_ref - p) + Kd (v_ref - v) - gravity]

tau_body = J [alpha_ref + K_R e_R + K_omega (omega_ref - omega)]
           + omega × (J omega)
```

The controller reconstructs the full body-axis inertia tensor from MuJoCo's inertial quaternion and principal moments. [control/missions.py](../control/missions.py) analytically differentiates the quintic trajectory to produce origin velocity/acceleration and fixed-world-axis angular rate/acceleration. It then transports those quantities to the COM. This preserves the existing PD gains while removing the avoidable moving-reference lag present in the earlier pose-only campaign.

The requested wrench is mapped to the eight signed thrusts by weighted, bounded least squares. Saturated solutions are redistributed with an active-set method; commands are never implemented through `xfrc_applied`.

## 5. Online-PES residual architecture

[control/residual.py](../control/residual.py) imports the canonical `CMGResidualAugmentor` from `ACC2027_Gate_Residual_Control`. It uses six body-wrench channels and twelve paired coupled membrane-gate units:

```text
classical wrench -> CMG online-PES additive residual
                 -> bounded 6×8 allocation -> data.ctrl
```

The PES learning target combines normalized COM position/velocity error in body coordinates with attitude/angular-rate error. Decoder weights update online with the canonical PES rule, leak and clipping. The default integration settings are recorded in every mission artifact (`beta=0.05`, learning rate `8e-4`, leak `1e-6`); they are simulation settings, not yet hardware-qualified gains.

Logs preserve baseline wrench, learned residual, final wrench, learning target, mean gate/activity, decoder norm, actuator saturation and allocation residual. PD and PES therefore remain directly comparable. The residual path cannot create a force outside the rotor allocator merely because its six-channel output is mathematically bounded.

The matched 2026-09-09 release campaigns both passed all 25 missions with zero actuator saturation. The ideal-model PD was substantially more accurate in nominal tracking: mean position RMSE was 0.00103 m for PD versus 0.01158 m for PES, and mean attitude RMSE was 0.0260 degrees versus 0.0629 degrees. PES produced a repeatable 0.0592 m startup transient because the current CMG units are driven by the nonzero gravity-compensating baseline wrench. On the two impulse missions, however, PES reduced attitude RMSE (hover push: 0.3946 to 0.2620 degrees; circular-yaw push: 0.2317 to 0.1550 degrees) and slightly reduced position RMSE. This is evidence of a disturbance-recovery tradeoff, not a general superiority result. The full table and plot are in [control/output/comparison_release_pd_pes_20260909/REPORT.md](../control/output/comparison_release_pd_pes_20260909/REPORT.md).

### Direct and Nengo implementations

[control/nengo_controllers.py](../control/nengo_controllers.py) adds two backend-conformance variants. `nengo-pd` executes the exact geometric PD/feedforward equation as a Nengo Node; it is not a neural approximation. `nengo-cmg-pes` uses that exact Nengo PD graph, a custom continuous `CoupledMembraneGate` Nengo `NeuronType`, and Nengo's native `PES` learning operator. All four variants use the same references, gains, wrench convention, allocator, limits and 500 Hz timestep.

[control/verify_nengo_equivalence.py](../control/verify_nengo_equivalence.py) compares the direct and Nengo paths on the same MuJoCo state. In the 2026-09-10, 1000-step yaw excitation, PD wrench and motor commands agreed exactly at stored precision. The largest direct/Nengo CMG motor-command difference was `1.1437e-7 N`, below the preselected `1e-4 N` conformance threshold. This establishes software equivalence only; it does not validate the vehicle physics or prove a CMG performance advantage.

All four nominal 25-mission campaigns passed with zero saturation. Direct PD and Nengo-PD both produced mean position/attitude RMSE of `0.001029 m / 0.0260 deg`; direct CMG-PES and Nengo-CMG-PES both produced `0.011579 m / 0.0629 deg`. In the final frozen comparison, all four mission-source hashes match. The maximum mission-level direct/Nengo differences were zero for PD and `9.762e-9 m` position RMSE, `3.653e-7 deg` attitude RMSE and `2.047e-8 N` peak motor command for CMG-PES. The matched report is [control/output/comparison_four_controllers_frozen_20260910/REPORT.md](../control/output/comparison_four_controllers_frozen_20260910/REPORT.md).

## 6. Physics implemented and physics still missing

The canonical model currently includes rigid-body translation/rotation, gravity, mesh-derived mass properties, ground contact, exact site moment arms, and ideal signed thrust. The configured mass is 2.5 kg, but both it and the mesh-derived inertia remain unverified against the current hardware.

MuJoCo provides stateless reduced-order fluid forces. Positive global density/viscosity enables inertia-box or per-geom ellipsoid approximations, and a wind vector changes relative air velocity. These models can represent coarse quadratic/viscous body drag, lift-like ellipsoid terms and rotational fluid resistance. They are not CFD: they do not resolve propeller wakes, rotor inflow states, blade-element aerodynamics, rotor-rotor interference, downwash on the frame, vortex-ring state or ground effect. See the official [MuJoCo fluid-force model](https://mujoco.readthedocs.io/en/stable/computation/fluid.html).

The canonical XML intentionally leaves density and viscosity at zero because no drag identification data was supplied. Enabling standard-atmosphere density against a single mesh-equivalent body would add a phenomenon but would not establish hardware accuracy.

MuJoCo can also represent actuator states. Its native actuator dynamics include no state, integration, first-order filters (including exact integration), and DC-motor dynamics; custom gain/dynamics callbacks can implement an identified ESC/motor/propeller model. See the official [actuator dynamics types](https://mujoco.readthedocs.io/en/stable/APIreference/APItypes.html). The current actuators are memoryless: control directly specifies signed force.

Visible propellers may rotate. A physical implementation uses a child body per propeller, a hinge joint about the measured shaft axis, rotor mass/inertia, collision filtering, and a motor or prescribed joint motion. If the joint is dynamically coupled, gyroscopic and reaction effects follow from the modeled inertia/torque. A visualization-only spinning mesh can instead be kinematic, but it must be excluded from physical claims. Rotation by itself does not generate thrust in MuJoCo; thrust still needs an actuator model or custom aerodynamic force law.

## 7. Reproducible validation

Use the research repository's Python environment:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\twin\review\verify_rotor_frames.py'
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\twin\control\validate_hover.py'
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\twin\control\missions.py' --controller pd
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\twin\control\missions.py' --controller cmg-pes
```

Each campaign directory records hashes of the XML, STL and controller scripts together with mission definitions, gates, settings, traces and summaries. Keep the existing ideal-model suite as a regression layer. Add uncertain-parameter and hardware-data validation as new layers; do not replace the deterministic baseline.

## 8. Path to a predictive twin

The required identification campaign is specified in [physics/README.md](../physics/README.md). In short: measure vehicle mass/COM/inertia; characterize every motor-propeller-ESC channel in both directions on a load cell; identify motor lag and reaction torque; calibrate IMU pose/noise/delay; then identify drag and higher-order rotor-flow effects from held-out data. Every value should carry hardware revision, units, uncertainty, conditions and source-data hash.

Only after those measurements should the canonical model gain motor filters, reaction-torque gear terms, rotor inertias, air density/viscosity, wind, sensor noise or delays. A controller that passes the current campaign is valid for this ideal model; it is not automatically flight-safe.

## 9. Physical--virtual connection and predictive validation

The complete procedure is in [TWIN_HARDWARE_VALIDATION_PROTOCOL.md](TWIN_HARDWARE_VALIDATION_PROTOCOL.md). Physical data and MuJoCo predictions are converted into the contract in [hardware/COMMON_LOG_SCHEMA.md](../validation/COMMON_LOG_SCHEMA.md), with frame registration and clock synchronization fixed before comparing trajectories. The first integration is shadow mode: the real initial state, reference and eight commands drive a parallel MuJoCo simulation, while MuJoCo has no authority over the vehicle.

Parameter identity is not inferred from visual trajectory similarity. Directly measured values are compared using measurement uncertainty and controller-sensitivity-derived tolerances. Coupled or weakly identifiable parameters are accepted only when their prediction intervals cover held-out physical trajectories. [hardware/validate_paired_logs.py](../validation/validate_paired_logs.py) computes synchronized position, quaternion-geodesic attitude, angular-rate and optional motor-command differences without silently optimizing a time shift.
