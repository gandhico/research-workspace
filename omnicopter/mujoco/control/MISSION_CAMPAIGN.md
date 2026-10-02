# Omnicopter maneuverability campaign

The campaign uses the final hardware-confirmed rotor frames, unchanged PD gains, a 500 Hz control rate, and the configured +/-10 N bounds. References include analytic position, velocity and acceleration at the COM and fixed-world-axis attitude, angular-rate and angular-acceleration commands. The optional `cmg-pes` mode adds the repository's canonical online-PES residual at the six-axis body-wrench level before the same bounded eight-rotor allocator.

This is a simulation campaign to establish a baseline operating envelope for this controller/model pair. Its gates are engineering screening criteria selected before the runs, not hardware qualification criteria.

**Historical pose-only baseline, 2026-09-04:** 23 missions passed, the 12 s yaw failed tracking-quality gates, and the 6 s yaw was skipped. See the [historical measured results](output/campaign_initial_20260904/REPORT.md).

**Final feedforward PD campaign, 2026-09-09:** all 25 missions pass without changing the gains or gates. The 12 s and 6 s yaw trials peak at approximately 0.01 and 0.03 degrees attitude error. The old failure was a moving-reference formulation limitation, not rotor saturation or loss of rank.

The mission viewer was also exercised through a complete 14 s hover run. All 25 reference definitions were checked for finite positions, normalized quaternion endpoints and the expected final pose.

## Launch commands

For a named PowerShell runner for each of the 25 missions, plus baseline and full-campaign runners, open [the complete runner guide](runners/README.md). Each runner finds the Python environment automatically; no shell variables need to be defined first.

Run all stages headlessly, automatically stopping escalation at the first failed mission:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\missions.py'
```

Run the matched online-PES campaign:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\missions.py' --controller cmg-pes
```

Run the exact Nengo-PD and Nengo-CMG-PES implementations:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\missions.py' --controller nengo-pd
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\missions.py' --controller nengo-cmg-pes
```

`nengo-pd` is the exact geometric law evaluated by a Nengo graph; it is not a neural approximation. `nengo-cmg-pes` adds the custom continuous CMG `NeuronType` and Nengo's built-in PES operator. Run [verify_nengo_equivalence.py](verify_nengo_equivalence.py) before every released campaign to distinguish backend conformance from controller performance.

Watch a slow complete revolution about world Z:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\missions.py' --mission yaw_360 --view
```

Watch simultaneous translation and rotation:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\missions.py' --mission circle_yaw_360 --view
```

Use `--list` for mission names. Use `--max-stage 3` to run only stages 0 through 3. Use `--mission NAME` to run one mission independently; that mode does not enforce previous-stage prerequisites. All viewer runs save new measurements, not a replay of an earlier trace.

In the mission viewer, **Space** pauses/resumes, and closing the window stops the run. A cyan marker shows the requested body-origin position. The mission runs once and then closes. Use MuJoCo's body-frame visualization to make rotations easier to see on the nearly symmetric cage. Thrust sliders are overwritten by the controller.

## Stage progression

Every mission starts from the original hover pose at (0, 0, 1) m. The first two seconds hold that pose. The specified maneuver then runs, followed by eight seconds holding its final reference. Translation/attitude out-and-back missions also hold the displaced pose before returning. The helix ends at 1.3 m rather than returning to 1 m.

| Stage | Missions | Reference maneuver | What it tests |
|---|---|---|---|
| 0 | `hover`, `quaternion_sign` | Fixed hover; replace q with -q while preserving physical orientation | Baseline and quaternion representation invariance |
| 1 | `translate_x`, `translate_y`, `translate_z` | X/Y: +0.25 m; Z: +0.20 m; six seconds each way | Translation while holding attitude |
| 2 | `attitude_x_15`, `attitude_y_15`, `attitude_z_15` | +15 degrees and back; four seconds each way | Small attitude changes while holding position |
| 3 | `attitude_x_45`, `attitude_y_45`, `attitude_y_90`, `attitude_x_180` | 45 degrees in 8 s, 90 in 12 s, 180 in 20 s; hold and return | Large reorientation, without commanding an ambiguous 180-degree step |
| 4 | `yaw_360`, `yaw_minus_360`, `spin_x_360`, `spin_y_360` | World Z: +/-360 degrees in 36 s; world X/Y: +360 in 48 s | Full-turn tracking, direction, thrust reversals and position/orientation independence |
| 5 | `circle`, `figure_eight`, `helix`, `circle_yaw_360` | Circle: radius 0.20 m in 32 s; figure eight: X amplitude 0.20 m/Y 0.15 m in 48 s; helix: radius 0.15 m/+0.30 m climb in 40 s; circle plus 360-degree yaw in 48 s | Curved/3D motion and simultaneous translation/rotation |
| 6 | `hover_push`, `circle_yaw_push` | The existing velocity impulse, during hover and during circle/yaw | Disturbance recovery during a mission |
| 7 | `yaw_360_24s`, `yaw_360_12s`, `yaw_360_6s` | Shorten the world-Z revolution to 24, 12, then 6 s | Find the first tracking-quality limit with unchanged PD |

Circle paths start at the current hover point; their circle center is offset by minus the radius in world X. The figure eight uses x = 0.20 sin(theta), y = 0.15 sin(2 theta). These paths are intentionally modest relative to the aircraft's dimensions so this first campaign emphasizes control rather than large-area navigation.

All rotation axes in this table are **fixed world axes**. The model starts rotated 90 degrees about Y, so world-X rotation is not generally a conventional body-roll command. Mission names and plots use the explicit world-axis convention.

## Correctly commanding 360 degrees

A final orientation alone cannot specify a complete revolution: q and -q represent the same physical orientation. A shortest-path interpolation between the initial and final equivalent orientations would not make the vehicle turn.

Instead the reference advances through an explicit angle trajectory:

```text
s = clamp((time - start_time) / maneuver_duration, 0, 1)
h(s) = 10*s^3 - 15*s^4 + 6*s^5
theta = total_angle * h(s)

q_axis(theta) = [cos(theta/2), axis*sin(theta/2)]
q_reference = q_axis(theta) * q_initial
```

The quintic profile has zero reference velocity and acceleration at the start and end. For a full positive turn, the reference quaternion evolves continuously from q_initial to -q_initial. The controller still uses its shortest *instantaneous error*, which stays small when tracking is successful.

The campaign independently accumulates actual small quaternion increments, rotates those increments into world coordinates, and projects them onto the commanded fixed axis. It checks signed progress as well as orientation error. For these fixed-axis missions, this prevents an unchanged final orientation from being mistaken for a completed revolution. This progress measure is not a general Euler-angle unwrapping method for arbitrary tumbling trajectories.

Maximum reference angular speed is 1.875 times the average angle/duration:

| 360-degree maneuver duration | Mean rate | Peak reference rate |
|---|---|---|
| 48 s | 7.5 deg/s | 14.06 deg/s |
| 36 s | 10 deg/s | 18.75 deg/s |
| 24 s | 15 deg/s | 28.125 deg/s |
| 12 s | 30 deg/s | 56.25 deg/s |
| 6 s | 60 deg/s | 112.5 deg/s |

## Gates and measurements

Each mission records position and quaternion references, actual states, eight rotor thrusts, force/torque allocation residuals, and signed rotation progress at 100 Hz. Metrics and abort checks run at 500 Hz. The final two seconds of the eight-second terminal hold provide settling measurements.

Pass requires all of the following:

- Peak position error <= 0.12 m and peak attitude error <= 15 degrees over the whole mission.
- Final-hold position error <= 0.01 m and attitude error <= 0.5 degrees.
- Rotor commands stay inside the original +/-10 N bounds; saturation occupies <= 2% of sampled control instants.
- No ground contact, invalid numerical state or simulation-envelope abort.
- For full rotations: final accumulated signed-angle error <= 5 degrees, and peak accumulated-progress error <= 20 degrees.

A preflight check samples 401 desired attitudes, verifies quaternion normalization/full-turn coverage, and checks whether gravity can be balanced within the actuator limits. It checks quasistatic feasibility only; it does not prove dynamic tracking feasibility.

The simulation aborts on contact, body-origin height below 0.40 m, displacement greater than 2 m from the start, attitude error above 100 degrees, or nonfinite state/control. These are limits for this numerical test setup, not flight failsafes. A quality-gate failure, such as 18 degrees of tracking lag, is recorded after finishing the mission unless an abort limit is reached.

In the default sequential campaign, a failed mission stops further escalation and all later missions are marked skipped. A failed stage-7 speed trial is an operating-envelope finding, not permission to increase the limits or retune gains until it passes.

## Why the controller revision removes the old tracking lag

The historical pose-only controller damped absolute velocity and angular rate toward zero. It therefore required a persistent error to keep moving:

```text
approximately, during slow nearly constant motion:
position lag ~= (kd_position / kp_position) * velocity = 0.9 * velocity
attitude lag ~= (kd_attitude / kp_attitude) * angular_rate = 0.45 * angular_rate
```

The updated implementation tracks desired COM velocity and body angular rate and adds analytic acceleration feedforward. It was evaluated as a separate, hash-recorded controller revision against the same missions and gates. This is why the fast-yaw error collapses without a gain increase.

## Online-PES mode

`--controller cmg-pes` uses six learned body-wrench channels (`Fx`, `Fy`, `Fz`, `Mx`, `My`, `Mz`) with twelve paired CMG units, adaptive conductance, additive residual output, and online PES decoder updates. Every learned wrench is passed through the native rotor allocator and `data.ctrl`; no external-body-force bypass is used.

The default simulation settings are `--beta 0.05 --learning-rate 0.0008 --leak 0.000001`. They can be overridden explicitly and are recorded in `manifest.json` and each `mission.json`. Traces include the classical wrench, PES residual/final wrench, learning target, gate/activity statistics and decoder norm.

Treat the matched PD run as the scientific baseline. A learned controller passing the gates does not by itself show improvement; compare RMSE, peaks, saturation and recovery on identical missions. The complete architecture and fidelity caveats are in [the virtual-twin methodology](../DIGITAL_TWIN_METHODOLOGY.md).

The final matched release campaigns each passed 25/25 missions with no saturation. Across all missions, PD had lower mean position and attitude RMSE. PES did reduce attitude RMSE and slightly reduce position RMSE in both injected-impulse missions, but introduced a 0.0592 m startup transient in otherwise nominal missions. See the [side-by-side report and plot](output/comparison_release_pd_pes_20260909/REPORT.md). The proper next experiment is training/evaluation under identified model mismatch, wind and propulsion dynamics—not retuning against the same exact plant until the comparison becomes favorable.

## Result files and follow-up campaigns

Every invocation creates a timestamped `control/output/campaign_*` folder. `manifest.json` preserves model, mesh and controller/script hashes, mission specifications and gates. `campaign.json` gives pass/fail/skipped results. Each mission contains `mission.json`, `trace.csv` and `summary.json` when a completed/aborted run has samples. The report generator adds a readable table and plots:

```powershell
& 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe' 'C:\Research\omnicopter\mujoco\control\campaign_report.py' 'PATH_TO_CAMPAIGN_FOLDER'
```

This campaign does not yet test motor lag, sensor noise, uncertain mass/inertia, wind, packet loss, battery depletion, motor failures or physical thrust-reversal dynamics. Those belong in subsequent robustness campaigns after a measured hardware model is available. The parameter ledger is [physics/omnicopter_parameters.json](../physics/omnicopter_parameters.json).

For X2/CF2 comparisons, reuse the translation paths, moderate attitude tests, yaw turns and common metrics with matched limits and an appropriate controller. Holding position through arbitrary world-X/Y full rotations is a distinctive fully actuated Omnicopter task; ordinary quadrotors cannot generally maintain hover throughout those maneuvers with fixed-direction thrust.
