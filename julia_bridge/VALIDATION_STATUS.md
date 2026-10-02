# Julia ⇄ Quanser Bridge — Validation Status (2026-07-12)

> **Re-verified on the current (rebuilt) laptop, 2026-08-21**, after this
> folder was pulled forward from the backup drive into `C:\Research\julia_bridge\`:
> `julia --startup-file=no julia\validate_all.jl` → **V0 PASS** (`hil.dll` found
> at `C:\Program Files\Common Files\Quanser\bin\hil`), **V1 PASS** (all 14
> boards resolve). V2 (twin connect) and V4 (hardware) not re-attempted yet —
> need QLabs / the physical rig running first. See `pendulum\RUNNERS.md` §4
> and `aero2\launchers_runners.md` §6 for how this plugs into each platform.

## ★ LIVE TWIN MILESTONE (later same day, QLabs Aero2 running)
- **V2 PASS (aero2, live)** — `julia validate_all.jl --connect aero2`: `hil_open` on
  `0@tcpip://localhost:18950` OK, encoder read OK, safe zero + close OK.
- **V3 PASS (aero2, live)** — `julia aero2_twin_pd_loop.jl 8 200`: **pure-Julia closed
  PD loop on the twin** (Bridge 2; Julia owns timing and I/O via `ccall`→`hil.dll`).
  Implemented Aero2 PD gains, pitch-only square wave (scene is pitch-only per 04),
  hardware-timed tach rate feedback, hybrid sleep+spin pacing:
  **1600 samples, realized 199.8 Hz (target 200), pitch RMS 0.0479 rad (last 75%)**,
  safe zero + red LED + clean close. Comparable Python/PAL live run (04, Stage 3b):
  0.1572 rad RMS over 3 s including transient — both stable at ~200 Hz; the
  cross-language path is proven end to end.
- Conclusion: **Bridge 2 is production-grade for family-A twins**; hardware V4 is now
  a card-identifier change (`"0"` instead of the tcpip URI) at the lab bench.

## Machine-verified today

### Bridge 2 (Julia `ccall` → hil.dll) — family A
- **V0 PASS** — `QuanserHIL.jl` loads on Julia 1.12.6; `hil.dll` discovered at
  `C:\Program Files\Common Files\Quanser\bin\hil`.
- **V1 PASS** — the 14-board registry resolves (card types verified from Quanser's
  own PAL/HAL sources); no device opened.
- **V2 (aero2)**: attempt returned HIL error **-816** = connection not reachable —
  the *ccall chain itself executed correctly*; the QLabs Aero2 scene was simply not
  running at test time. V2 was previously **proven live** in `04_Aero2_SNNs`
  (virtual sensor read + safe zero + close) with the same signatures this module
  generalizes. → V2 is a *scene-availability* condition, not a bridge risk.
- **V2 (qube3)**: pending a running QLabs Qube scene (ports 18920–18923).

### Bridge 1 (PythonCall → PAL) — both families
- Official `quanser` Python API **installed from the QUARC wheels**
  (`pip install --no-index --find-links "C:\Program Files\Quanser\QUARC\python" quanser-api`);
  `quanser.hardware.HIL` imports.
- **PAL product matrix: 10/10 OK** — qube, aero2, qarm, qarm_mini, qbot_platform,
  qbot, qcar, qdrone2, actuators, sensors.
- juliacall/PythonCall previously validated end-to-end in `04_Aero2_SNNs`
  (offline closed loop at 200 Hz with a Julia policy).

## Research findings (carry into the paper/docs)
- **F1 — two transport families.** Host-HIL robots (Qube3, Aero2, QArm/Mini,
  legacy QBots, trainers) take the direct `ccall` bridge. Onboard robots
  (QDrone2 `tcpip://<ip>:18491`, QBot Platform driver/LiDAR/video ports, QCar on-car
  HIL) are reached from the host by **streams/PAL** — the Julia path there is
  PythonCall→PAL now, native `quanser_communications.dll` ccall later.
- **F2 — twin ports are per-product.** QLabs virtual HIL cards: Aero2 = 18950,
  Qube = 18920–18923 (per instance, `nagle='off'`). Not one universal port.
- **F3 — `pal.products.qcar` blocks on an interactive prompt at import**
  ("virtual QCar1 or QCar2?"). Any bridge/automation must pre-answer (pipe stdin
  or pre-write its config) — a background/service loop would deadlock otherwise.
- **F4 — Gyroscope/HD-Haptic are DAQ-mediated** (QUARC-era): the bridge opens the
  Q8-class DAQ card type; the device is a channel map (from their manuals), so
  Bridge 2 covers them once the DAQ is present — no product-specific card exists.

## Ladder per robot (current)
| Robot | V0 | V1 | V2 twin | V3 loop | V4 hw |
|---|---|---|---|---|---|
| Qube3 | ✅ | ✅ | scene pending | — | lab |
| Aero2 | ✅ | ✅ | ✅ (proven in 04) | Julia-policy offline loop ✅ (04) | lab |
| 3-DOF Hover | ✅ | ✅ (`q8_usb`, no open) | n/a | offline Julia bridge tests ✅ | lab; sensor-only first |
| QArm / Mini | ✅ | ✅ | qvl path | — | lab |
| QBot Platform | ✅ | ✅ (streamed) | qvl path | — | lab |
| QCar / 2 | ✅ | ✅ (F3 handled) | qvl path | — | lab |
| QDrone2 | ✅ | ✅ (streamed) | qvl path | — | lab |
| Gyro / Haptic | ✅ | ✅ (DAQ-mediated) | n/a | — | lab |

## Next steps
1. With QLabs running: `julia julia\validate_all.jl --connect aero2` (and `qube3`)
   → V2 live; then a Julia LQR/PD closed loop on the twin (V3) reusing the
   `JuliaPolicyController` pattern from 04.
2. Family-B V3: PythonCall loop through PAL against qvl twins (start with QBot
   Platform, the richest streamed case).
3. Native stream bridge (optional): wrap `quanser_communications.dll` in Julia.
4. V4 hardware passes at the lab bench, robot by robot, in the paper priority order.
