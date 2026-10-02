# QCar / QCar2 — Runners & Launchers Index

Single place to find "how do I run X" for the QCar platform. Companion docs:
`README.md` (quickstart + tomorrow's hardware plan), `runners\Qcar_Hardware_runners.md`
(raw tuned-gain command log, kept verbatim as a tuning reference),
`01_Code\hardware\qcar\RUNNERS_1.md` (ROS2 node stack, separate lineage — see §3).
This file is the authoritative, exhaustive index — updated 2026-08-21.

**No Julia, no MATLAB for QCar** — Python only. The hardware controller runs
**on the car's onboard NVIDIA Jetson**, not this Windows machine.

---

## 1. Python — offline (this Windows machine, no car needed)

| Script | Command | Purpose |
|---|---|---|
| `runners\run_offline_benchmark.py` | `python .\runners\run_offline_benchmark.py --duration 20` | Baseline vs. HyperLIF-residual benchmark, shared-campaign code, software-only. Output → `results\offline\qcar_<timestamp>\`. |
| `runners\plot_results.py` | `python .\runners\plot_results.py` | Re-plot latest offline results. |

## 2. Python — physical hardware (on the car, via SSH)

```bash
ssh nvidia@192.168.1.129
cd ~/Documents/Quanser/examples/sdcs/qcar2/hardware/applications/GHYN/lane_following_research
```

**Tomorrow's start-up order** (from `README.md` — do not skip the perception-only
step): confirm camera, lane sign, steering sign, and log writing with
perception mode *before* adding `--armed`:

```bash
python3 qcar2_unified_lane_control_hardware_v1.py --mode perception --duration 30 --no-display
```

**Main entry point:** `qcar2_unified_lane_control_hardware_v1.py`
— `--mode {perception, lane}` × `--controller {pid, smc, nmpc_image,
adaptive_hyperlif_gate, pid_gated_adaptive_hyperlif_residual,
smc_gated_adaptive_hyperlif_residual, nmpc_gated_adaptive_hyperlif_residual}`.
`--armed` is required for nonzero throttle in `lane` mode.

Every tuned command actually validated on hardware (PID/SMC/NMPC baselines,
the adaptive-HyperLIF gate controller alone, and three gated
PID/SMC/NMPC + adaptive-HyperLIF-residual combinations) is preserved verbatim,
with the exact working gains, in **`runners\Qcar_Hardware_runners.md`** — copy
commands from there rather than re-deriving flags. Quick reference to what's there:

| Controller | What it is |
|---|---|
| `pid` | Classical baseline (two gain sets logged: gentle first-run, and a stronger baseline). |
| `smc` | Sliding-mode baseline, stronger. |
| `nmpc_image` | Nonlinear MPC in image space, stronger baseline. |
| `adaptive_hyperlif_gate` | Full HyperLIF-family gated controller, standalone (not a residual). |
| `pid_gated_adaptive_hyperlif_residual` | PID + gated adaptive-HyperLIF residual. |
| `smc_gated_adaptive_hyperlif_residual` | SMC + gated adaptive-HyperLIF residual. |
| `nmpc_gated_adaptive_hyperlif_residual` | NMPC + gated adaptive-HyperLIF residual — strongest experimental run logged. |

Shut down the car when done: `sudo shutdown now`.

**Predecessor script:** `Qcar2\qcar2_unified_lane_control_base_v6.py` and
`01_Code\hardware\qcar2_unified_lane_control_base_v6.py` are **byte-identical**
(confirmed by hash 2026-08-21) — `hardware_v1.py` above supersedes both; the
`base_v6.py` copies are kept for reference only, not a live runner.

## 3. ROS2 stack — `01_Code\hardware\qcar\` (separate control lineage, ROS2-native)

Not the same code path as `qcar2_unified_lane_control_hardware_v1.py` above —
this is a ROS2 node graph (`QCarControlNode`, `quanser_state_estimator`,
`qcar2_interfaces`, `qcar2_nodes`) built/deployed on the Jetson via `colcon`.
Full build/deploy/verify sequence: `01_Code\hardware\qcar\RUNNERS_1.md`. Summary:

```bash
# Autonomous (controller drives; use this)
ros2 launch quanser_state_estimator quanser_state_Estimator_autonomous.launch.py

# Manual / joystick (deadman button 5)
ros2 launch quanser_state_estimator quanser_state_Estimator.launch.py

# Controller node alone (if estimator+hardware already up)
ros2 run QCarControlNode node --ros-args -p controller:=CONTROLLER_1   # SMC, tested
ros2 run QCarControlNode node --ros-args -p controller:=CONTROLLER_2   # NMPC, sign-fixed but not hardware-verified
```
As of the doc's last update (2026-06-12): `CONTROLLER_1` (SMC) is the verified
path; `CONTROLLER_2` (NMPC) is not yet verified on hardware. Do not run the
autonomous launch and the manual/joystick launch together.

## 4. Other content in `qcar\` (not runners — reference only)

- `SNN-Controller-for-Qcar2-with-SLAM\` — external third-party repo (own
  `.git`), separate lineage from the code above. Don't merge into it.
- `01_Code\hardware\artgmap_vcs\` — vendored C++ mapping GUI tool (own `.git`),
  not part of the control pipeline.
- `01_Code\hardware\Readme.md`, `Qcar2\Readme.md` — unfilled template stubs
  (identical `TODO`-only boilerplate); not authoritative, superseded by this
  file and `README.md`.

---

## Known gaps / flags

- `qcar2_unified_lane_control_base_v6.py` duplicated in two places (§2) — safe
  to delete one copy by hand later; left alone here since nothing currently
  depends on either path being removed.
- No Julia or MATLAB path exists for QCar and none is planned — Python (host
  offline benchmark + on-car hardware runner) and ROS2 (on-car) are the only
  two lanes.
