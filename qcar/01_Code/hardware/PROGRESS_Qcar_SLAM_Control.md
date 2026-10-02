# QCarControlNode — Progress & Runner Reference

_Last updated: 2026-06-12_

ROS 2 control node for the Quanser QCar2. Receives EKF pose and A\* waypoints,
runs a selectable steering controller, and publishes motor commands.

---

## Status

| Piece | State | Notes |
|---|---|---|
| `controllers.py` | **Done** | Self-contained: imports, `LaneState`, `ControlOutput`, controllers, `build_default_args()`. |
| `node.py` | **Done** | Wired to controllers; pose+waypoint → lane errors; speed policy; safe-stop; ROS params. |
| Controller selection | **Done** | Launch-time ROS parameter with validation + fallback. |
| Tunable limits | **Done** | `cruise_speed`, `max_speed`, `max_steering`, `goal_radius` as ROS params. |
| `setup.py` entry point | **Verify** | Confirm the `console_scripts` name before `ros2 run`. |
| `MotorCommands` fields | **Verify on HW** | Assumes scalar `.speed` / `.steering`; some builds use arrays. |
| Speed units | **Verify on HW** | Unknown whether `.speed` is m/s or normalized throttle. |
| Steering sign | **Verify on HW** | Confirm wheels turn *toward* target (wheels-up test). |
| Controller gains | **Untuned** | Placeholders in `build_default_args()`; stable-ish, need tuning. |
| Hardware drive test | **Not started** | Do wheels-up checks first. |

---

## Architecture

```
/qcar_pose_ekf  (PoseStamped) ─┐
                               ├─► QCarControlNode ─► /qcar2_motor_speed_cmd (MotorCommands)
/a_star_waypoint (Pose2D) ─────┘        │
                                        └─ builds LaneState (lane_error, slope_xy, ...)
                                           and calls the selected controller
```

- **lane_error** = lateral offset of the target in the vehicle frame (left positive).
- **slope_xy** = heading error to the target (rad).
- Controllers output steering only; the node adds the speed policy.

---

## Controller slots

| Selector | Controller | Source |
|---|---|---|
| `CONTROLLER_1` | Sliding-Mode Control (SMC) | `SMCLaneController` |
| `CONTROLLER_2` | Beam-search NMPC | `ImageNMPCController` |
| `CONTROLLER_3` | Simple proportional (placeholder) | inline in `node.py` |
| `CONTROLLER_4` | Simple proportional (placeholder) | inline in `node.py` |

Invalid selector → warning logged, falls back to `CONTROLLER_1`.

---

## Runners

> Replace `node` with the actual `console_scripts` name from `setup.py`.

**Default (CONTROLLER_1 / SMC):**
```bash
ros2 run QCarControlNode node
```

**Switch to NMPC:**
```bash
ros2 run QCarControlNode node --ros-args -p controller:=CONTROLLER_2
```

**Slow first drive (low speed, tighter goal):**
```bash
ros2 run QCarControlNode node --ros-args \
  -p controller:=CONTROLLER_2 -p cruise_speed:=0.15 -p goal_radius:=0.15
```

**Override several limits at once:**
```bash
ros2 run QCarControlNode node --ros-args \
  -p controller:=CONTROLLER_1 \
  -p cruise_speed:=0.25 \
  -p max_speed:=0.40 \
  -p max_steering:=0.50 \
  -p goal_radius:=0.20
```

### Available ROS parameters

| Parameter | Default | Meaning |
|---|---|---|
| `controller` | `CONTROLLER_1` | Active controller slot. |
| `cruise_speed` | `0.30` | Base speed command (units **unverified**). |
| `max_speed` | `0.50` | Hard clamp on commanded speed. |
| `max_steering` | `0.50` | Steering clamp (rad); kept in sync with controllers. |
| `goal_radius` | `0.25` | Stop within this distance of the waypoint (m). |

---

## Build & deploy

**Push files from the PC (run in PowerShell, not inside SSH):**
```powershell
scp node.py controllers.py nvidia@192.168.1.128:~/ros2/src/QCarControlNode/QCarControlNode/
```

**Build on the Jetson (from `~/ros2`):**
```bash
colcon build --packages-select QCarControlNode
source install/setup.bash
```

---

## Pre-drive verification (wheels OFF the ground)

Do all four before the car touches the floor.

1. **Publishing works** — `ros2 topic echo /qcar2_motor_speed_cmd`.
   Field errors → check `ros2 interface show qcar2_interfaces/msg/MotorCommands`
   and fix the two marked lines in `publish_commands`.
2. **Inputs arriving** — `ros2 topic hz /qcar_pose_ekf` and
   `ros2 topic hz /a_star_waypoint`. No pose → no commands (by design).
3. **Steering sign** — publish a waypoint to one side; wheels should turn
   *toward* it. If not, flip the sign: `lane_error = -float(y_v)` in
   `_build_lane_state`.
4. **Speed units/magnitude** — confirm `.speed` units; keep `cruise_speed` low
   to start.

Then: clear space, e-stop in reach, lowest `cruise_speed`, single nearby
waypoint. Expect sloppy tracking until gains are tuned.

---

## Useful debug commands

```bash
ros2 node list
ros2 topic list
ros2 topic hz /qcar_pose_ekf
ros2 topic echo /qcar2_motor_speed_cmd
ros2 param list /qcar_control_node
ros2 param get /qcar_control_node controller
ros2 interface show qcar2_interfaces/msg/MotorCommands
```

---

## Open items / next steps

- [ ] Confirm `setup.py` entry-point name for `ros2 run`.
- [ ] Verify `MotorCommands` field layout on hardware.
- [ ] Verify speed units and steering sign (wheels-up).
- [ ] Tune SMC and NMPC gains.
- [ ] Consider lookahead / waypoint smoothing for tight A\* paths.
- [ ] Fill `CONTROLLER_3` and `CONTROLLER_4` if more algorithms are planned.
