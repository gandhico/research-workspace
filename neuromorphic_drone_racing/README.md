# Neuromorphic heterogeneous drone racing in MuJoCo, stage 1

Stage 1 started 2026-09-24. It is inspired by the UZH Robotics and Perception Group drone-racing line of work,
especially Swift (Kaufmann et al., *Nature* 2023). Two things are new here:

- **Heterogeneous fleet:** four very different airframes fly the same track. They are the Skydio X2, the Crazyflie 2 (rotor-level model), the Omnicopter and the coaxial Y6.
- **Neuromorphic sensing:** every drone carries an emulated event camera (DVS).

Stage 1 is the environment, the fleet, the control baseline and the event sensors. Neuromorphic *control* and *perception* from events are stage 2 (see "Next").

| Layer | File | What it does |
| --- | --- | --- |
| Track | `track.py` | 7 square gates (1.5 m opening) in a 30×30×8 m volume with a Split-S. C² quintic-Hermite racing line that crosses every gate through its centre with zero curvature. Per-vehicle standing-start speed profile |
| World | `build_scene.py` | MjSpec composes the gates and the four unmodified vehicle MJCFs under name prefixes. Ghost collision bits: vehicles hit gates and the ground, not each other. Adds `fpv` and `dvs` cameras to every vehicle |
| Control | `controller.py` | One controller for all vehicles. Geometric SO(3) control for X2, CF2 and Y6; full 6-DOF wrench control for the Omnicopter. Allocation matrix built from each MJCF's actuator sites and gears; bounded least squares on saturation |
| Race | `race.py` | Time-trial with all four vehicles at once. Detects gate passes (order, clearance) and collisions |
| Event camera | `event_camera.py` | DVS emulator (ESIM/v2e recipe): log intensity, per-pixel thresholds with mismatch, interpolated sub-ms timestamps, refractory period, background noise. DAVIS346 geometry |
| Events | `render_events.py` | Replays a race and renders each vehicle's `dvs` camera at 500 Hz. Writes events plus an [RGB \| events] video |
| Media | `make_media.py` | 2×2 event video, overview video, figures, `results/summary.json` |

## The fleet and the gate size

Mass, rotor count and thrust-to-weight come from each MJCF. Thrust-to-weight is a linear program over the vehicle's own allocation.

| Vehicle | Source model | Mass | Rotors | T/W | Frontal size |
| --- | --- | --- | --- | --- | --- |
| Skydio X2 | MuJoCo Menagerie (Apache-2.0) | 1.325 kg | 4 | 4.00 | 0.56 × 0.64 m |
| Crazyflie 2 | ACC 2027 rotor-level design model | 0.027 kg | 4 | 2.25\* | 0.15 × 0.15 m |
| Omnicopter | `C:\Research\omnicopter` (8 reversible rotors) | 2.5 kg | 8 | 1.87 | 0.87 × 0.96 m (1.47 m bounding sphere) |
| Coaxial Y6 | `C:\Research\y6_hexa` (validated vs Nengo plant, 0.48 mm) | 1.412 kg | 6 | 2.40 | ≈0.71 m prop span |

\* The CF2 per-rotor ceiling is scaled by ×1.7 (`CF2_AUTHORITY`). This is a **declared design assumption**, not identification data: with the stock 0.35 N total (T/W 1.32) the CF2 can hover but cannot race with any control reserve. See `models/vehicles/cf2_rotor/README.md`.

**Gate opening: 1.5 m square.** The Omnicopter is the binding vehicle: its frontal area is 0.87 × 0.96 m in its upright pose, which it can hold because it is fully actuated. That leaves at least 0.27 m clearance per side. The real Swift gate dimensions and poses are in `racing_data.zip/…/params/track.yaml` (Zenodo 10.5281/zenodo.7955278, 445.9 MB) and have not been downloaded yet. The current layout is our own Swift-*format* approximation (7 gates, 30×30×8 m, Split-S). Our lap is 101 m; the paper's is 75 m.

## Run (hyperlif env: mujoco 3.11, nengo 4.1)

```
set PY=C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe
%PY% race.py                      # 4-vehicle race (~10 min); results/race_fleet.{npz,json}
%PY% race.py --viewer --only y6   # watch one vehicle live
%PY% render_events.py --veh y6    # DVS events + video for one vehicle (~5-10 min each)
%PY% make_media.py                # grid video, overview video, figures, summary.json
```

## How the baseline was made to work (what failed first)

These are kept as notes for the paper's methods section:

1. **Periodic speed profile.** The reference started at race speed while the drone was at rest, so the X2 hit G1. Fix: an unrolled standing-start profile.
2. **Bang-bang acceleration profile.** The desired tilt jumped about 60° at launch. Fix: a moving-minimum then moving-average jerk filter, which never exceeds the speed bounds.
3. **Cubic spline through pre/centre/post points.** Curvature spikes caused lateral jerk and gate strikes. Fix: a C² quintic-Hermite line through gate centres, with κ = 0 at each gate and a roomier Split-S loop.
4. **Finite-difference ω_d of a feedback-laden R_d.** This destabilised the loop and was reverted. The kept version is a **differential-flatness ω_d from the reference jerk only**.
5. **Same attitude gains for every airframe.** Gains now come from each vehicle's tilt authority (LP at hover), and the planner's jerk bound is matched to that bandwidth.
6. **X2 needs a conservative plan** (T/W margin 0.35; others 0.6). Its yaw authority at hover is only 4.3 rad/s² (Y6: 19.7). Evidence: `results/sweep_x2.json`.

## Honest limitations of stage 1

- The controllers are classical. They are not neuromorphic yet, and not time-optimal or RL (Swift uses RL). Lap times are **not** comparable to Swift.
- Controllers use perfect state feedback; there is no VIO or gate-detection loop. The cameras are not yet in the control loop.
- Ghost race: no drone–drone contact, downwash or wake. No rotor dynamics or aerodynamics beyond rigid-body thrust and torque.
- The DVS is emulated from rendered frames at 500 Hz. It has no motion blur, uses linear-in-time log intensity between frames, and has no latency jitter. Cast shadows are off in DVS renders for speed (19 → 241 fps), so shadow edges produce no events.
- Every number is from single runs; no seed statistics yet.

## Next (stage 2, proposed)

An exploratory stage-2 full-vehicle CMG reinforcement-learning pilot now
lives in [`rl_cmg_2026_09_30/README.md`](rl_cmg_2026_09_30/README.md).
It compares continuous-gate and genuine-event CMG readouts in the same
MuJoCo racing world. Its first direct-policy pilot is negative and does not
alter the stage-1 classical results or the ACC paper.

- Event-based gate detection with spiking networks: events drive a Nengo/Lava network, which feeds gate-corner or centroid estimates to the planner.
- Neuromorphic control: port the Y6 NEF controller (validated in `y6_hexa`) and the ACC CMG-PES residual to the fleet.
- Download the real Swift `track.yaml` (needs approval: 445.9 MB zip) and replace `track.GATES`.
- Time-optimal or RL baselines for a fair comparison with the UZH results.
