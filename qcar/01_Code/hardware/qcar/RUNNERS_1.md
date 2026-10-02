# QCarControlNode — Runner Reference

_Last updated: 2026-06-12_

How to build, run, and verify the QCar2 controller stack in its current state.

---

## Current state

- **Steering**: fixed. Sign corrected (steers toward the target); SMC gains tamed
  so it no longer slams to ±30° on tiny errors.
- **Throttle**: fixed at the system level. The car wasn't moving because
  `joy2qcar2/joy_control_node` was a second publisher on
  `/qcar2_motor_speed_cmd`, streaming `throttle=0` and cancelling the
  controller. The autonomous launch below removes it so the controller is the
  sole publisher.
- **Controllers**: `CONTROLLER_1` (SMC) is the tested path. `CONTROLLER_2`
  (NMPC) inherits the sign fix but is not yet verified on hardware.

---

## Build & deploy

Push from the PC (run in PowerShell, **not** inside SSH):

```powershell
# controller package
scp node.py controllers.py nvidia@192.168.1.128:~/ros2/src/QCarControlNode/QCarControlNode/

# autonomous launch (into the estimator package)
scp quanser_state_Estimator_autonomous.launch.py nvidia@192.168.1.128:~/ros2/src/quanser_state_estimator/launch/
```

Build on the Jetson (from `~/ros2`):

```bash
colcon build --packages-select QCarControlNode quanser_state_estimator
source install/setup.bash
```

---

## Runners

### A) Autonomous (controller drives) — use this

Single publisher on the motor topic; estimator auto-switches to autonomous
fallback. The controller node is started by the launch.

```bash
ros2 launch quanser_state_estimator quanser_state_Estimator_autonomous.launch.py
```

Keep the **e-stop** within reach: this configuration has no joystick deadman.

### B) Manual / joystick (original)

The original launch, with joystick arming. Use for manual driving or as a
manual safety check. Hold the **deadman (button 5)** to arm; RT = throttle,
left stick = steering, A = reverse.

```bash
ros2 launch quanser_state_estimator quanser_state_Estimator.launch.py
```

> Do not run A and B together, and do not run the controller node separately
> while B is running — that recreates the dual-publisher conflict.

### C) Controller node alone

If the estimator + hardware are already up (e.g. via a launch that does **not**
start a joystick publisher) and you want to run/restart just the controller:

```bash
# default: CONTROLLER_1 (SMC)
ros2 run QCarControlNode node

# pick a controller
ros2 run QCarControlNode node --ros-args -p controller:=CONTROLLER_2

# slow first drive
ros2 run QCarControlNode node --ros-args -p controller:=CONTROLLER_1 \
  -p cruise_speed:=0.15 -p goal_radius:=0.20
```

### Controller parameters

| Parameter      | Default        | Meaning                                   |
|----------------|----------------|-------------------------------------------|
| `controller`   | `CONTROLLER_1` | `CONTROLLER_1`=SMC, `2`=NMPC, `3`/`4`=P    |
| `cruise_speed` | `0.30`         | Base speed command (m/s)                  |
| `max_speed`    | `0.50`         | Hard clamp on speed                       |
| `max_steering` | `0.523`        | Steering clamp (rad, ~30°)                |
| `goal_radius`  | `0.25`         | Stop within this distance of waypoint (m) |

---

## Verify (do this every run)

**1. Exactly one publisher on the motor topic** (the whole point of the fix):

```bash
ros2 topic info /qcar2_motor_speed_cmd --verbose
```
Expect a single publisher: `qcar_control_node`. If you see `joystick_publisher`
or `joy_control_node` too, you launched the wrong thing.

**2. Inputs are flowing:**

```bash
ros2 topic hz /qcar_pose_ekf
ros2 topic hz /a_star_waypoint
```

**3. Estimator is in autonomous mode** — its console should print:

```
INPUT MODE: AUTONOMOUS SUBSCRIBER fallback
```

**4. Live command + reason** (from the controller's own logs, ~1 Hz):

```
[DATA OUT] ... Cmd Velocidad: 0.30 m/s | Motivo Velocidad: CRUISE (...)
```
- target left → `Cmd Dirección` positive; target right → negative.
- on the floor, `Error Lateral` in `[DATA IN]` should shrink over time.

**5. Watch the raw motor command if needed:**

```bash
ros2 topic echo /qcar2_motor_speed_cmd
```
`values[1]` (motor_throttle) should hold ~0.30, not flicker to 0.

---

## Handy debug commands

```bash
ros2 node list
ros2 topic list
ros2 param list /qcar_control_node
ros2 param get /qcar_control_node controller
ros2 interface show qcar2_interfaces/msg/MotorCommands
```

---

## Open items / next steps

- [ ] Confirm the car holds speed and converges to waypoints on the floor.
- [ ] Verify `CONTROLLER_2` (NMPC) separately on the stand before trusting it.
- [ ] Investigate `rf2o_laser_odometry` dying (`exit code -2`) — localization input.
- [ ] Tune SMC gains for crisper tracking once basic driving is confirmed.
- [ ] (Robust) Add a command mux so joystick + autonomous coexist with the
      deadman as the arbiter, instead of removing the joystick.
```
