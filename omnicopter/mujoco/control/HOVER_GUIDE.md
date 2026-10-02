# Omnicopter: first-stage hover controller

**Progressive maneuverability testing:** [Mission campaign](MISSION_CAMPAIGN.md) adds analytic moving-reference kinematics, complete rotations, staged pass/fail gates, and an optional online-PES residual while preserving the verified PD gains.

This is a simulation baseline for the current Omnicopter XML. It holds the body origin at (0, 0, 1) metres and maintains the original +90-degree rotation about Y. It does not take off from the floor, communicate with PX4, or command hardware.

## Launch

In the existing VS Code workspace, choose **Terminal > Run Task > Hover: Omnicopter stage 1**.

Alternatively paste this complete command into any PowerShell terminal. It does not depend on previously defined variables:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\hover.py'
```

The default demonstration begins at (0.10, -0.08, 0.85) metres with a small attitude offset. Watch it return to the 1 m hover target. For an undisturbed start, append `--start-at-target`.

- **Space:** pause/resume the controller simulation.
- **Enter:** apply a repeatable simulated velocity impulse and watch recovery. Each press adds world linear velocity (0.30, -0.20, 0.15) m/s and body angular velocity (0.35, -0.25, 0.20) rad/s.
- **Backspace:** restart the demonstration.
- **Close the window:** finish the run and write its summary.
- Orbit, pan, zoom and visualization controls work as before. The controller overwrites the thrust sliders each step.

This is a separate controller viewer. Launching `review_models.py omni --simulate` still runs without a controller.

## Controller design

All forces pass through the eight native site actuators via `data.ctrl`; the controller does not apply an external body wrench or reset the aircraft state to fake hover. The Enter disturbance changes velocity solely as a deliberate simulated impulse.

The controller regulates COM position, with its target chosen so the body origin settles at (0, 0, 1). This accounts for the model's small nonzero COM offset.

```text
F_world = mass * [a_COM_ref + 4*(p_COM_ref - p_COM)
                  + 3.6*(v_COM_ref - v_COM) - gravity]

e_rotation = shortest quaternion rotation vector from current to target,
             expressed in the current body frame

torque_body = J_body * [alpha_body_ref + 16*e_rotation
                        + 7.2*(omega_body_ref - omega_body)]
              + omega_body x (J_body*omega_body)

w_body = [R_world_from_body.T * F_world; torque_body]
```

The inertia tensor is reconstructed from MuJoCo's principal inertias and inertial-frame orientation, rather than treating the principal values as body-axis diagonals.

For each rotor, the wrench matrix includes its actual thrust axis and moment arm about the COM. It also includes any reaction-torque gear terms (zero in the supplied Omnicopter XML):

```text
B_i = [d_i; (r_i - r_COM) x d_i + rotor reaction torque per unit input]
```

Allocation solves a bounded least-squares problem:

```text
minimize ||W*(B*u - w_body)||^2
subject to XML actuator bounds: -10 <= u_i <= 10 N
```

Force rows have unit weight; torque rows are divided by the mean rotor-to-COM distance to put the residuals on comparable scales. Feasible commands use the minimum-norm pseudoinverse solution. When bounds activate, an active-set solver redistributes the request and checks the optimality conditions. This is not a hard attitude-priority allocator.

Position gains correspond to a nominal 2 rad/s natural frequency and 0.9 damping ratio; attitude gains use 4 rad/s and 0.9. The controller and physics both run at the unchanged XML timestep of 0.002 s (500 Hz). There is no integral term; persistent unmodeled forces or mass errors can leave a position offset.

## Logs and repeatable validation

Each viewer/headless run creates a unique directory below `control/output/`, with:

- `config.json`: model/mesh hashes, version, gains, inertia, bounds, target and initial pose.
- `trace.csv`: 100 Hz samples of pose errors, position, eight thrust commands, saturation and allocation residuals. Episode numbers distinguish resets.
- `summary.json`: final sampled errors, contact count and peak input across the run.

Headless demonstration:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\hover.py' --headless --duration 15
```

Validation suite:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\validate_hover.py'
```

The suite covers equilibrium, the default demonstration, a velocity impulse at 2 s, combined 0.47 m / 26.9-degree initial error, +/-15-degree errors around each body axis, and the demonstration at a halved timestep. Each case runs for 10 simulated seconds. Acceptance requires position error below 5 mm and attitude error below 0.2 degrees throughout the final two seconds, no contacts, and all inputs within bounds.

It additionally checks 150 randomly generated allocation requests against bounded-optimality conditions, compares their cost with simple clipping, and checks all eight wrench columns against MuJoCo's actual actuator forces at five orientations. Quaternion sign equivalence is checked as well.

Results are in `control/output/validation/validation.json` and per-case CSV files. These are ideal-model tests, not hardware accuracy claims.

Re-verified on 2026-09-09 with MuJoCo 3.12.0 after the final rotor-frame update and controller refactor: all 11 cases passed. No case touched the floor or saturated. The largest input was 8.834 N in the combined 0.47 m / 26.9-degree displacement case. These very small residuals reflect an ideal, matching simulation model.

The graphical viewer was also exercised for three seconds with the default disturbance: its final sampled position error was 0.189 mm. Use the acceptance bounds above, not numerical precision, when assessing future model changes.

![Hover validation](output/validation/hover_validation.png)

## Scope before hardware transfer

This baseline uses exact MuJoCo state, configured mesh-derived mass/inertia, instantaneous thrust, and the reversible thrust limits already in the XML. It has no estimator, motor lag, battery model, communication delay or sensor noise. Rotor frames are hardware-confirmed; rotor locations, propulsion data and hardware mass properties still require metrology. The tests do not establish robustness to those missing effects or guarantee recovery from arbitrary attitudes/disturbances.

Use this as the classical baseline. The full geometry, physics-fidelity boundary, identification plan, and PES integration are documented in [the virtual-twin methodology](../DIGITAL_TWIN_METHODOLOGY.md).

MuJoCo references: [Python viewer](https://mujoco.readthedocs.io/en/stable/python.html#interactive-viewer), [simulation functions](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#main-simulation).
