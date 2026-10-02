# 11 — Connecting Julia to Quanser (digital twin + hardware)

Short answer: **not hard — but there is no native Julia binding, so you bridge.**
Quanser ships official APIs for **Python** (the `quanser` HIL SDK), **C** (the
underlying HIL library), and **MATLAB/Simulink** (QUARC). There is **no Julia API**.
So "use Julia with Quanser" always means one of two bridges: Julia↔Python interop,
or Julia↔C `ccall` into the HIL library. Both are mature and low-risk.

## Targets
- **Digital twin (QLabs / Quanser Interactive Labs)** — Python `qvl` library. **No
  real-time constraint** (it's a sim). Bridging is *easy*.
- **Hardware (HIL/PAL on the Aero2)** — the Quanser **HIL SDK**: a C library
  (`hil_open`, `hil_read_*`, `hil_write_*`, `hil_close`, …) with an official Python
  wrapper (`quanser.hardware`). Soft real-time loop (~300–400 Hz best-effort, the
  same regime this project already hits in Python).

## Three bridge options (easiest → most native)
1. **Julia ↔ Python interop (PythonCall.jl / juliacall).** Mature, ~zero-friction.
   Either direction works:
   - *Python drives* (recommended first): keep this repo's Python runner +
     `Backend` (QLabs/HIL), and call the **Julia HyperLIF policy from Python** via
     `juliacall`. A `JuliaHyperLIFController(Controller)` loads the Julia module and
     calls it in `compute()`. Drops into `run_control --execution_mode hardware`
     once Phase-6 backends exist. **Lowest effort; reuses all existing I/O.**
   - *Julia drives*: a Julia loop calls the Python `quanser`/`qvl` API via PythonCall.
   - Overhead: a PythonCall round-trip is sub-millisecond; at a 2–5 ms loop period it
     is negligible. This is the same best-effort timing regime as the current Python.
2. **Julia ↔ C HIL via `ccall`.** Julia's `ccall` calls the HIL C DLL with **zero
   overhead** — the most "native", fastest, no-Python path. Effort: wrap ~10–15 C
   functions (open board, read encoders/other channels, write analog, close). Cleanest
   if you want a pure-Julia real-time stack. (QLabs has no C API, so the twin still
   goes through Python.)
3. **Process bridge (decoupled).** Run I/O in one process and the controller in the
   other, communicating over UDP/ZMQ/shared memory. Most moving parts; use only if you
   need hard process isolation or to pin the I/O loop to a real-time thread.

## How it maps onto this repo's architecture
The `Backend`/`Controller` contract makes this clean:
- The **I/O stays Python** (`HardwareBackend`/`VirtualTwinBackend`, Phase 6) — reuse
  `DirectHilAero2IO` and the QLabs backend already in the original project.
- The **Julia HyperLIF policy** is the `Controller` (option 1a): a thin Python
  `JuliaHyperLIFController` calls into Julia. So the *exact* runners/applications/metrics
  we built score the Julia controller with no changes — the whole point of the contract.
- Alternatively, keep everything Python (we already replicated the e-prop in Python,
  `eprop.py`) and skip Julia entirely for deployment; use Julia only for heavy offline
  training (APEX V11/CUDA) and export weights to the Python `EpropSNN`.

## The real prerequisite (current blocker)
Neither bridge works until the **Quanser HIL SDK is installed** on the lab machine
(it is **not** installed here — `quanser` Python package missing, so `hil.dll` is
also absent). Step 0 for *any* path (Python, Julia, or MATLAB): install the Quanser
SDK + device drivers and connect the Aero2. After that:
- Python bridge needs the `quanser` package (comes with the SDK).
- `ccall` bridge needs `hil.dll` on the load path (comes with the SDK).

## Recommendation
1. **Now:** train/deploy in **Python** (`EpropSNN` here) — no Julia needed; lowest risk.
2. **If you want Julia in the loop:** **PythonCall, Python-drives** (option 1a) — wrap
   the Julia policy as a `Controller`; reuse our Python QLabs/HIL backends. Hours of work.
3. **If you want a pure-Julia real-time stack:** **`ccall` to the HIL C library** —
   a day or two to wrap the handful of HIL calls; QLabs still via PythonCall.
4. Use **Julia/APEX (CUDA)** for heavy offline SNN training; **export weights** to the
   Python runtime for deployment. Best of both: Julia's training, Python's Quanser I/O.

## Stage J0 - parity smoke

The first implemented Julia bridge check is deliberately small:

```powershell
python .\runners\run_julia_policy_smoke.py
```

It calls `julia\aero2_policy_smoke.jl`, evaluates the same PD policy equation as
the Python `PD2DOF` controller on a fixed state/reference, and fails if the
outputs differ. This proves the cross-language policy path and local Julia
availability without putting a Julia subprocess inside the live 200 Hz control
loop. The next stage is a PythonCall/juliacall `Controller` wrapper or exported
Julia-trained weights loaded by the existing Python runtime.

## Bridge 1 - Python drives, Julia supplies policy

Implemented scaffold:

- Python wrapper: `aero2/control/julia_bridge.py`
- Optional controller class: `JuliaPolicyController`
- Optional dependency group: `pip install -e .[julia]`

Current machine status:

- Julia executable: available.
- Python `juliacall`: installed through `pip install -e .[julia]`.
- PythonCall.jl: installed in the active Julia 1.12 environment.
- App/runners: unchanged by default; the bridge is not registered as an app
  controller until the explicit app-facing controller selection is approved.

Validation now:

- `tests/test_julia_bridge.py` verifies the controller contract with an injected
  policy callable.
- The missing-`juliacall` path raises a clear `JuliaBridgeUnavailable` error
  instead of breaking normal Aero2 operation.
- Direct `juliacall` load of `julia/aero2_policy_smoke.jl` returned the expected
  command `[9.630224495367466, 11.89963407672024]`.
- `runners/run_julia_bridge_smoke.py` runs an offline closed loop with Python
  owning timing/I/O and `JuliaPolicyController` supplying the policy.

Bridge-1 commands:

```powershell
python .\runners\run_julia_bridge_smoke.py --duration 0.5 --hz 200 --dt 0.005
```

Latest local smoke:

- samples: 100
- realized rate: 200.0 Hz
- pitch RMS: 0.3250 rad
- yaw RMS: 0.0587 rad

Next bridge-1 step:

1. Add an explicit app/runner controller option only after review.
2. Replace the PD smoke policy with exported Julia-trained HyperLIF weights or
   the real Julia HyperLIF policy.
3. Validate offline first, then pitch-only QLabs, then hardware.

## Bridge 2 - Julia ccall to Quanser HIL

Implemented scaffold:

- Julia module: `julia/Aero2HilCBridge.jl`
- Guarded runner: `julia/aero2_hil_sensor_check.jl`
- Discovers `hil.dll` via `Libdl.find_library`.
- Wraps core immediate HIL functions:
  `hil_open`, `hil_close`, `hil_read`, `hil_write_analog`,
  `hil_write_digital`, and `hil_write_other`.
- Adds Aero2 helpers for motor voltage, LED color, immediate sensor read, and
  safe zero/red shutdown.
- Adds sensor conversion helpers matching the validated direct-HIL mapping:
  pitch encoder channel 2, yaw encoder channel 3, pitch-rate other channel
  14002, yaw-rate other channel 14003.

Current machine status:

- `hil.dll` is discoverable at `C:\Program Files\Common Files\Quanser\bin\hil.dll`.
- The module loads and discovers the HIL library.
- The sensor runner defaults to no-connect mode and reports the virtual card
  identifier `0@tcpip://localhost:18950` without opening QLabs or hardware.
- The virtual Aero2 sensor-only `--connect` path opens, reads, zeros/red-shuts
  down, and closes cleanly.
- No physical hardware-opening call is run by tests; opening hardware remains an
  explicit lab action with `--target hardware --connect`.

Validation now:

- `tests/test_julia_hil_c_bridge.py` loads the Julia module and confirms HIL
  library discovery without opening hardware.
- The same test validates the sensor conversion helpers and confirms
  `aero2_hil_sensor_check.jl` exits with `status=not_connected` by default.
- Manual virtual sensor-only validation:
  `julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --target virtual --connect --duration 0.5 --hz 20`
  exited with `status=connected_sensor_only`.

Bridge-2 commands:

```powershell
julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --duration 0.01
```

Later, when QLabs or hardware is intentionally ready:

```powershell
julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --target virtual --connect --duration 2 --hz 20
julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --target hardware --connect --duration 2 --hz 20
```

Next bridge-2 step:

1. Run the sensor-only physical hardware `--connect` check.
2. Add green LED only for future active-command loops; sensor-only remains
   zero-voltage/red because no command is being sent.
3. Only after sensor-only validation, add open-loop voltage diagnostics matching
   the Python `run_virtual_twin_io_diagnostic.py` runner.
