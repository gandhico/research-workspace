# Omnicopter, X2 and CF2: model review before control

> The Omnicopter rotor frames are now hardware-confirmed. The authoritative STL-to-frame construction, physics-fidelity boundary, controller revision, and online-PES integration are documented in [the virtual-twin methodology](../docs/DIGITAL_TWIN_METHODOLOGY.md). This file remains the visual inspection guide.

**Progressive missions:** [Mission campaign](../control/MISSION_CAMPAIGN.md) covers translations, large reorientations, 360-degree turns, curved paths and disturbance recovery with the current PD controller.

**Hover controller added:** see [the stage-1 hover guide](../control/HOVER_GUIDE.md) for the controller launch command, disturbance controls, equations and validation. The review/simulate commands below still run without a controller.

Verified locally with MuJoCo 3.12.0. This guide assumes VS means Visual Studio Code. VS Code edits XML/Python and launches commands; MuJoCo displays the interactive 3D model in its own window.

## 1. Open the shared workspace

In VS Code choose **File > Open Workspace from File** and select:

`C:\Research\omnicopter\twin\UAV-review.code-workspace`

Or run this in PowerShell:

```powershell
code "C:\Research\omnicopter\twin\UAV-review.code-workspace"
```

The Explorer contains Omnicopter, X2, stock CF2, and the CF2 rotor variant. Open `review/README.md`; Ctrl+Shift+V opens its Markdown preview.

The existing Python interpreter is:

`C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe`

It already has MuJoCo and NumPy. The default system Python does **not** have MuJoCo. The workspace tasks explicitly use the working interpreter, so no activation or installation is needed. If you use the Python extension's Run button, choose this interpreter through **Python: Select Interpreter** first.

## 2. Open Omnicopter for design inspection

Choose **Terminal > Run Task > Review: Omnicopter (frozen design)**. A separate MuJoCo window opens with the XML initial pose, rotor labels and site axes. The aircraft stays still; this review mode does not advance physics. The mesh and model parameters on disk are unchanged.

Alternatively, in the VS Code PowerShell terminal:

```powershell
$uavPython = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$uavReview = 'C:\Research\omnicopter\twin\review\review_models.py'
& $uavPython $uavReview omni --view
```

Close the viewer to return to the terminal. Run the same command with `x2`, `cf2`, or `cf2-rotor` instead of `omni`. To compare windows together, launch separate review tasks or use separate terminals.

Mouse controls: left-drag orbits; right-drag pans; scroll zooms. F1 shows help. Site axes are red X, green Y, blue Z. The red/blue translucent rotor disks are separate site colors, not indications of spin direction. In **Visualization**, select site labels/frames or turn them off for an unobstructed view. **Group enable** controls site and geometry visibility; the helper enables all site groups. X2/CF2 visual geoms use group 2 and collision geoms group 3; Omnicopter uses one mesh geom in group 0 for both.

## 3. Open the XML next to the viewer

Open the Omnicopter XML in Explorer:

`C:\Research\omnicopter\twin\omnidrone.xml`

The unusual filename is valid; quote it in commands. Read in this order:

1. **compiler / option:** degree angles, STL scale 0.001, timestep 0.002 s and gravity.
2. **asset:** the STL supplies geometry. It does not define eight physical motor dynamics.
3. **body / freejoint:** one rigid body with six velocity DOFs, initialized at 1 m and rotated +90 degrees around Y. Seven position coordinates mean XYZ plus a four-component quaternion, not seven physical DOFs.
4. **geom / inertial:** the 2.5 kg mass is specified on the mesh. COM and inertia are inferred from geometry because there is no explicit inertial element.
5. **sites:** rotor locations and orientations. Positive actuator force follows each site's local +Z, shown in blue.
6. **actuator:** each input supplies signed site thrust through `gear="0 0 1 0 0 0"`, bounded to -10...10. With the current unit gain these inputs represent newtons, not PWM or RPM.
7. **sensor:** accelerometer, gyro and local velocimeter at the IMU. Sensor values are not automatically world-frame position or attitude. The accelerometer measures specific force; free fall is not a stationary gravity reading. There is no frame-quaternion sensor in this XML; simulator ground-truth orientation is available in qpos.

For X2 and CF2, open `scene.xml` to view the environment and follow its include into `x2.xml`, `cf2.xml`, or `cf2_rotor.xml` for vehicle dynamics.

## 4. Compare the actual models

These are compiled simulation parameters, not independently verified hardware specifications.

| Property | Omnicopter | X2 | CF2 stock | CF2 rotor variant |
|---|---|---|---|---|
| Mass | 2.5 kg | 1.325 kg | 0.027 kg | 0.027 kg |
| Free-body velocity DOFs | 6 | 6 | 6 | 6 |
| Inputs | 8 signed rotor thrusts | 4 rotor thrusts | Collective thrust + 3 torque commands | 4 rotor thrusts |
| Control bounds | -10...10 N each | 0...13 N each | 0...0.35 N collective; torque commands -1...1 scaled by -1e-5 N m | 0...0.0875 N each |
| Force-direction rank | 3 | 1 | 1 | 1 |
| Force/torque map rank | 6 | 4 | 4 | 4 |
| XML timestep | 2 ms | 10 ms | 2 ms | 2 ms |
| Integrator | Euler | Euler | RK4 | RK4 |
| Rotor reaction torque | Omitted | Alternating +/-0.0201 m times thrust | Direct body moments | Alternating +/-0.005 m times thrust; assumed |

X2 and the CF2 rotor variant must tilt to accelerate horizontally with rotor thrust. Omnicopter's tilted thrust directions permit independent local force and torque commands around feasible operating points. Rank six does not imply unlimited force at every attitude: individual thrust bounds still constrain the achievable wrench.

Stock CF2 looks like a quadrotor, but its four controls are not four motors. Use `cf2-rotor` for a rotor-allocation comparison. Its rotor geometry and reaction-torque coefficients are a local design study, not identified motor data.

## 5. Current Omnicopter findings

- **Rotor locations need confirmation.** The comment says a 407.20 mm cube with corners at +/-0.2036 m. Actual sites are at +/-0.0973 m, making a 194.6 mm site cube. The transformed STL bounds are approximately 408 x 417 x 407 mm. The rendered sites sit inside the outer frame. That may be intentional, but the comment and coordinates cannot both describe the same cube. Check actual motor centers in CAD before changing either.
- **The mass properties are provisional.** Compiled COM is approximately (3.269, 0.719, 1.031) mm relative to the body origin. Principal inertias are (0.086287, 0.086241, 0.086098) kg m². These are principal-frame values; use the inertial-frame rotation when constructing a body-frame inertia tensor. A single STL with inferred mass distribution may not represent motor, battery and frame masses correctly.
- **Signed thrust is a hardware assumption.** The XML permits negative thrust. Confirm reversible motors/propellers and whether reverse thrust really has the same limits as forward thrust.
- **Propeller reaction torque and motor lag are absent.** The existing model generates moments through lever arms, but no explicit aerodynamic reaction moment. There is also no motor-speed state, battery model or thrust-response delay.
- **Collision geometry is coarse.** One mesh is used for visual appearance and collision. Standard mesh collision uses a convex hull, so the open frame should not be assumed to have open collision gaps. Inspect the hull before designing contact experiments; separate collision primitives or decomposed meshes may be needed.
- **Initial attitude matters.** The +90-degree Y rotation means body Z is not world-up. A quadrotor's equal-input hover recipe does not carry over.
- **Aerodynamics differ.** Omnicopter has zero configured fluid density/viscosity; X2 and CF2 configure 1.225 kg/m³ and 1.8e-5 Pa s. This is another difference to record for future comparisons.

At the current initial attitude, a COM-aware minimum-norm hover allocation is approximately:

```text
thrust_1 ... thrust_8 [N]:
 7.320402, -1.954269,  1.908957, -7.275089,
-7.231655,  1.978050, -1.932737,  7.186342
```

All eight are within the modeled limits. The audit verified near-zero MuJoCo acceleration at an airborne pose with this constant allocation. This is an equilibrium calculation, not a stabilizing controller or hardware validation. The review viewer does not apply these commands automatically.

## 6. Try native simulation after the visual review

Close the frozen viewer, then use **Simulate: Omnicopter (no controller)**, or:

```powershell
& $uavPython $uavReview omni --simulate

& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\twin\review\review_models.py' omni --simulate
```

In this native simulation mode, **Space** toggles play/pause, **Backspace** resets, and **Right arrow** steps while paused. Zero controls mean the vehicle falls under gravity. It is not expected to hover automatically. Pause and reset before using the Control panel to inspect individual inputs. A rotor slider represents force, so the response includes both translation and rotation. Manual input is only for qualitative inspection.

For the standard XML loader, which supports reloading edits, use:

```powershell
& $uavPython -m mujoco.viewer --mjcf='C:\Research\omnicopter\twin\omnidrone.xml'
```

Use **Ctrl+L** to reload after saving XML in VS Code. Close and reopen the custom frozen viewer to reload it. Avoid changing the original model merely to hold it still; use frozen design mode for that.

## 7. Relate this to the existing controllers

The recent `C:\Research\eprop_anneal_reproduction\reproduce_5missions.py` uses the P3 learned benchmark and applies world force/body-rotated torque through `data.xfrc_applied`. That bypasses the XML rotor mixer and actuator limits. Its reset zeros native actuator controls. Those experiments are useful attitude-control evidence, but do not establish motor-level feasibility on Omnicopter.

The X2 and stock CF2 vehicle XMLs in that legacy project have identical SHA-256 hashes to the ACC2027 copies used in this workspace. The newer `src/gra_control/platforms/drone.py` in ACC2027 explicitly separates stock CF2's virtual-wrench interface from X2/CF2-rotor's rotor interface. Its four-rotor mixer assumes parallel body-Z thrust axes and cannot be copied unchanged for Omnicopter. Experiment code also overrides XML timestep, initial pose and sometimes actuator bounds, so always distinguish raw model settings from run settings.

For Omnicopter, construct each allocation column about the true COM:

```text
B_i = [d_i ; (r_i - r_COM) x d_i + k_i*d_i]
w_body = B*u
```

Here d_i is the thrust axis expressed in the body frame, r_i is the rotor position, and k_i is a signed reaction-torque coefficient (currently zero). B is 6x8. Future control should calculate a desired six-axis wrench, allocate it with bounds, and report saturation and residual allocation error. Reuse quaternion-error logic and evaluation procedures only after checking frame conventions; retune gains for the new inertia and actuator authority.

Suggested next sequence: confirm geometry/mass properties and thrust assumptions; verify each actuator's sign and moment; implement bounded allocation and baseline pose control; validate hover and separate translation/rotation maneuvers; then add the learned residual methods and matched disturbance tests. Use one deliberate simulation/control timestep and record all overrides for comparison across vehicles.

## 8. Reproduce this review

```powershell
& $uavPython $uavReview all
& $uavPython $uavReview all --render
```

The first command compiles all four models and saves `review/output/model_audit.json`, including matrices, sensor names, inertial frames, limits and hover checks. The second saves labeled model images. Images are framed separately for readability and are not at a common visual scale.

Verified: all four model loads, four full wrench maps, feasible initial-attitude hover allocations and near-zero airborne equilibrium accelerations, and rendered design views. No source XML or existing controller was changed.

References: [MuJoCo Python viewer](https://mujoco.readthedocs.io/en/stable/python.html#interactive-viewer), [viewer controls](https://mujoco.readthedocs.io/en/stable/programming/samples.html#simulate), [MJCF specification](https://mujoco.readthedocs.io/en/stable/XMLreference.html).
