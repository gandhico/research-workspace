# 13 - Paper Result Manifest

This manifest points paper-facing claims to concrete Aero2 artifacts. It is a
guardrail: only validated artifacts belong in results tables, captions, and
status claims.

## Validated Artifacts

| Claim | Artifact | Use |
|---|---|---|
| App-compatible offline runner works | `tests/test_runner_cli.py` | Methods/reproducibility statement. |
| All app-listed controllers run offline on `helicopter_2dof` | `tests/test_runner_cli.py` | Controller availability table. |
| All app-listed models run offline with PD | `tests/test_runner_cli.py` | Model availability table. |
| Offline benchmark CSV/JSON export works | `results/benchmark_helicopter_2dof_offline_20260711_234326.json` | Example paper-table source; regenerate for final figures. |
| QLabs/PAL backend is connected and pitch-valid | `results/helicopter_2dof_virtual_twin_pd_pitch_reference_tracking_20260712_005742.json` | Digital-twin pitch-only validation evidence. |
| Current QLabs scene keeps yaw locked | `results/virtual_twin_io_all_20260712_011105.json` | Limitation statement; do not report as failed controller performance. |
| LED convention is implemented and tested | `tests/test_virtual_twin_backend.py` | Safety/status note. |
| Julia Stage J0 parity smoke | `runners/run_julia_policy_smoke.py`, `julia/aero2_policy_smoke.jl` | Cross-language readiness note, not a live-control result. |
| Julia bridge 1 offline smoke | `aero2/control/julia_bridge.py`, `runners/run_julia_bridge_smoke.py`, `tests/test_julia_bridge.py` | Python-drives/Julia-policy bridge readiness; offline only, not a live-control result. |
| Julia bridge 2 virtual sensor runner | `julia/Aero2HilCBridge.jl`, `julia/aero2_hil_sensor_check.jl`, `tests/test_julia_hil_c_bridge.py` | C HIL bridge discovery, no-connect guard, and virtual sensor-only connect; not a hardware result. |

## Current Paper-Safe Statements

- The Aero2 app has a validated offline execution path.
- The Aero2 app has a validated QLabs/PAL pitch-only digital-twin path.
- The current QLabs Aero2 scene is not valid for yaw or coupled 2-DOF claims
  because yaw angle, yaw rate, and encoder channel 3 stayed fixed under open-loop
  yaw/direct motor pulses.
- HyperLIF on Aero2 is currently an offline experimental controller, not a live
  Aero2 hardware/digital-twin superiority result.
- Julia bridge 1 is validated for offline closed-loop smoke: Python owns the
  loop/backend and the controller calls a Julia policy through `juliacall`.
- Julia bridge 1 is not yet an app-exposed or live QLabs/hardware controller.
- Julia bridge 2 discovers `hil.dll`, has a no-connect sensor runner guard, and
  has opened the virtual Aero2 in sensor-only mode from Julia.
- Julia bridge 2 has not opened physical Aero2 hardware from Julia.

## Claims Not Yet Allowed

- Do not claim full 2-DOF Aero2 QLabs control until yaw encoder channel 3 moves
  in the open-loop diagnostic and a closed-loop yaw/coupled run is validated.
- Do not claim Aero2 hardware results from the new backend contract until the
  hardware backend is reconnected and staged safety checks pass.
- Do not claim Julia live QLabs/hardware/app control until the Julia controller
  is exposed intentionally in those paths and validated there.
- Do not claim native Julia/HIL hardware control until the ccall bridge passes a
  physical hardware sensor-only connection check and zero-voltage shutdown check.

## Regeneration Commands

```powershell
python .\runners\run_benchmark.py --model helicopter_2dof --duration 30 --dt 0.005 --save
python .\runners\run_control.py --model helicopter_2dof --mode virtual_twin --controller pd --application pitch_reference_tracking --duration 5 --hz 200 --save
python .\runners\run_virtual_twin_io_diagnostic.py --test all --duration 3.5 --hz 200 --voltage 3 --read-mode 1 --save
python .\runners\run_julia_policy_smoke.py
python .\runners\run_julia_bridge_smoke.py --duration 0.5 --hz 200 --dt 0.005
julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --duration 0.01
julia --startup-file=no -e 'include("julia/Aero2HilCBridge.jl"); using .Aero2HilCBridge; println(Aero2HilCBridge.find_hil_library())'
```
