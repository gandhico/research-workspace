# 12 - Aero2 Status Checklist

This checklist is the current working map for the Aero2 app, runners, validation
state, and next integration stages. It mirrors the pendulum project's
mode-by-mode style while keeping the Aero2 yaw limitation visible.

## Validated Now

| Area | Status | Evidence |
|---|---|---|
| Robot-specific app | Done | `app/aero2_app.py` launches Aero2-only runs through `runners/run_control.py`. |
| Offline simulation | Done | Full app-compatible offline runner path is tested. |
| Offline controllers | Done | All listed controllers run offline on `helicopter_2dof`. |
| Offline models | Done | All listed models run offline with PD. |
| Benchmark export | Done | `runners/run_benchmark.py --save` writes CSV/JSON for paper tables. |
| QLabs/PAL connection | Done | `VirtualTwinBackend` connects through PAL `Aero2(hardware=0)`. |
| Digital twin pitch | Done | User-validated from the app; short live smoke also ran at 200.1 Hz. |
| Digital twin LED convention | Done | Red when connected/idle or shutting down; green while commands are active. |
| Digital twin diagnostics | Done | Open-loop motor probe logs raw encoders, rates, motor voltages, and summary JSON. |
| Julia bridge 1 offline smoke | Done | `runners/run_julia_bridge_smoke.py` runs Python timing/I/O with a Julia policy controller at 200 Hz offline. |
| Julia bridge 2 virtual sensor check | Done | `julia/aero2_hil_sensor_check.jl` discovers `hil.dll`, exits no-connect by default, and `--target virtual --connect` reads/zeros/closes cleanly. |
| Test suite | Done | Full suite passed after Julia bridge changes: 107 passed, 1 skipped. |
| Hardware backend (PD, reference_tracking) | Done | **2026-09-03: first confirmed physical-hardware run.** `run_control.py --model helicopter_2dof --mode hardware --controller pd --application reference_tracking`, staged 3s low-voltage test then full-duration run at standard voltage limit — both clean. `HardwareBackend` is a thin `hardware=1` wrapper over the already-validated `VirtualTwinBackend`, so this closes the "scaffolded only" gap noted below for the PD/reference_tracking combination specifically. |

## Partially Validated

| Area | Current truth | Next action |
|---|---|---|
| Digital twin yaw | Current QLabs scene keeps yaw fixed. `psi_range=0`, `psi_dot_peak=0`, and encoder channel 3 stayed fixed under yaw/direct motor pulses. | Load or spawn a true 2-DOF Aero2 QLabs scene before making yaw/2-DOF digital-twin claims. |
| Full 2-DOF digital twin | Runner connects and logs, but yaw is not physically free in the current scene. | Repeat `run_virtual_twin_io_diagnostic.py --test all` after switching QLabs asset/configuration. |
| HyperLIF on Aero2 | Implemented and tested offline as an experimental residual controller. | Train gates, test harder/noisy regimes, then move to live pitch-only twin and hardware. |
| Julia integration | Stage J0 parity smoke, bridge-1 offline closed-loop smoke, and bridge-2 virtual sensor-only connect are present. | Approve app-facing Julia controller exposure, then run bridge-2 physical hardware `--connect` sensor check before any voltage diagnostics. |
| Paper integration | Benchmark and live-diagnostic artifacts exist. | Maintain `docs/13_paper_result_manifest.md` as the figure/table/status source. |

## Not Yet Validated

| Area | Status | Required before claim |
|---|---|---|
| Hardware backend, other controllers (lqr/lqg/mpc/backstepping/smc/nmpc/hyperlif/julia_policy) | Not yet attempted on hardware — only `pd` confirmed 2026-09-03. | Stage each the same way: short low-voltage test, then full duration/voltage. `hyperlif` especially should stay offline/twin-only until trained gates are validated (see Partially Validated above). |
| Hardware yaw/2-DOF | `reference_tracking` (coupled pitch+yaw square-wave) ran clean on hardware 2026-09-03 — unlike the QLabs twin, physical yaw is NOT scene-locked, so this may already be a stronger 2-DOF result than the twin's. Not yet analyzed/quantified (no benchmark table run against it). | Run `run_benchmark.py`-style analysis on the 2026-09-03 hardware log before citing numbers; still no dedicated sensor-only/staged-arming runner — the 3s-then-full-duration manual staging is the only safety net right now. |
| True 2-DOF QLabs | Blocked by current pitch-only scene behavior. | Use a QLabs 2-DOF Aero2 asset/configuration where yaw encoder channel 3 moves. |
| Julia live control | Bridge 1 is validated offline, but not exposed in the app or live QLabs/hardware loop. Bridge 2 is sensor-only on virtual Aero2. | Approve app-facing controller registration, validate pitch-only QLabs, then hardware. Bridge 2 must pass physical hardware sensor-only check before any voltage commands. |

## Recommended Next Stages

1. **Julia Stage J0 - policy parity smoke.** Validate a Julia PD policy against
   the Python PD controller on fixed states. This is a smoke test, not the live
   controller bridge.
2. **Paper Stage P0 - status manifest.** Keep a figure/table/result map that
   points to offline benchmark JSON, live QLabs pitch smoke JSON, and yaw-locked
   diagnostic JSON.
3. **QLabs Stage Q1 - true 2-DOF asset.** Change the QLabs Aero2 scene/config
   and rerun the open-loop diagnostic.
4. **Hardware Stage H1 - safe backend reconnect.** Add sensor-only and
   zero-command hardware checks before any closed-loop command path.
5. **Julia Bridge J3/J4.** J3: expose bridge 1 as an explicit app/runner
   controller option after approval. J4: run bridge-2 sensor-only physical
   hardware `--connect` before any voltage diagnostics.

## Canonical Commands

```powershell
python .\app\aero2_app.py
python .\runners\run_control.py --model helicopter_2dof --mode offline --controller pd --application reference_tracking --duration 5 --save
python .\runners\run_control.py --model helicopter_2dof --mode virtual_twin --controller pd --application pitch_reference_tracking --duration 5 --hz 200 --save
python .\runners\run_virtual_twin_io_diagnostic.py --test all --duration 3.5 --hz 200 --voltage 3 --read-mode 1 --save
python .\runners\run_benchmark.py --model helicopter_2dof --duration 30 --dt 0.005 --save
python .\runners\run_julia_policy_smoke.py
python .\runners\run_julia_bridge_smoke.py --duration 0.5 --hz 200 --dt 0.005
julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --duration 0.01
julia --startup-file=no -e 'include("julia/Aero2HilCBridge.jl"); using .Aero2HilCBridge; println(Aero2HilCBridge.find_hil_library())'
```
