# 17 — Julia ⇄ Quanser Bridge (independent research track)

**Home of the Julia–Quanser research.** Independent of the math-paper mission, but it
must ultimately validate that Julia can drive **all ten robots** across offline /
digital-twin / hardware. Builds on the Aero2-proven pieces
(`04_Aero2_SNNs/julia/` + `docs/11_julia_quanser_bridge.md`): Stage-J0 policy parity,
Bridge 1 (Python drives, Julia policy via juliacall/PythonCall — offline loop
validated at 200 Hz), Bridge 2 (Julia `ccall` into `hil.dll` — virtual Aero2
sensor-read validated).

## Architecture — the central research finding

Quanser platforms split into **two transport families**, so "the Julia bridge" is
two bridges:

| Family | Robots | Host talks via | Julia path |
|---|---|---|---|
| **A. Host-HIL** (device is a USB DAQ/amp; HIL runs on the host) | Qube-Servo 3, Aero 2, 3-DOF Hover, QArm, QArm Mini, QBot 2e/3 (legacy), trainers; legacy DAQ-mediated devices (3-DOF Gyroscope, HD Haptic via Q8-class DAQ) | `hil.dll` (`hil_open/read/write`) | **Bridge 2: direct `ccall`** (zero overhead) — `julia/QuanserHIL.jl` |
| **B. Onboard/streamed** (HIL runs on the robot's own computer) | QDrone 2 (`tcpip://<ip>:18491`), QBot Platform (driver port, LiDAR/video local ports), QCar 2 | `quanser.communications` streams / PAL wrappers | **Bridge 1: PythonCall→PAL** now; later native `ccall` into `quanser_communications.dll` |

Digital twins (QLabs) present family-A devices as **virtual HIL cards** at
`id@tcpip://localhost:PORT` — so Bridge 2 works unchanged against twins:
- Aero 2: port **18950** (validated), Qube: ports **18920–18923** (per instance, `nagle='off'`),
- family-B twins go through `qvl`/PAL as on hardware.

## Verified card/URI registry (source: Quanser's own PAL/HAL code)

| Robot | Card type | Physical id | Virtual id |
|---|---|---|---|
| Qube-Servo 3 | `qube_servo3_usb` | `0` | `0@tcpip://localhost:18920..3?nagle='off'` |
| Aero 2 | `quanser_aero2_usb` | `0` | `0@tcpip://localhost:18950` |
| 3-DOF Hover | `q8_usb` | `0` or rig-verified Q8 identifier | — |
| QArm | `qarm_usb` | `0` | — (qvl twin) |
| QArm Mini | `qarm_mini` | `0` | — |
| QBot 2e / 3 | `qbot2e` / `qbot3` | onboard | — |
| QCar / QCar 2 | `qcar` / `qcar2` | onboard | qvl twin |
| QDrone 2 | *(stream, not host-HIL)* | `tcpip://<ip>:18491` | qvl twin |
| QBot Platform | *(streams)* | driver port / `18889` | qvl twin |
| Trainers | `mech_actuators_trainer_usb`, `mech_sensors_trainer_usb` | `0` | — |
| 3-DOF Gyro / HD Haptic | via Q8-class DAQ card type | per DAQ | — (QUARC-era) |

## Validation ladder (what "works" means, per robot)
- **V0** — Julia module loads; `hil.dll` discovered.
- **V1** — no-connect: card type + identifier resolve; safe (never opens hardware).
- **V2** — twin connect: `hil_open` against the QLabs virtual card (or qvl for family B); read sensors; safe zero; close.
- **V3** — closed loop on twin: Julia policy in the loop (either bridge), parity vs Python controller.
- **V4** — hardware (explicit lab action only; `--target hardware --connect`).

Current status: see `VALIDATION_STATUS.md`.

## Layout
```
julia\QuanserHIL.jl      generic ccall bridge + board registry (family A + twins)
julia\validate_all.jl    V0/V1 sweep over the registry; --connect virtual <robot> for V2
python\check_pal_matrix.py   PAL availability matrix (family B path / Bridge 1)
VALIDATION_STATUS.md     machine-verified results log
```

## Environment facts (this machine)
Julia 1.12.6; PythonCall/juliacall installed; QUARC + QLabs installed;
`hil.dll` at `C:\Program Files\Common Files\Quanser\bin`; the official
`quanser` Python API ships as wheels in `C:\Program Files\Quanser\QUARC\python\`
(install with `pip install --no-index --find-links <that dir> quanser-api`).
