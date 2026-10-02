# Qube Servo/Pendulum HyperLIF Residual Validation

This folder is the self-contained Qube Servo 3 / rotary pendulum branch of the
Quanser validation campaign. It vendors the relevant Quanser examples, keeps a
local copy of the offline residual benchmark package in `src`, and adds online
virtual-twin / hardware runners for a classical balance baseline and a bounded
HyperLIF gate-state residual.

The current machine's working PAL copy is under
`C:\Users\gandhico\Documents\Quanser_Academic_Resources_tmp\0_libraries\python`.
The ACC 2027 runner auto-discovers it or accepts `QUANSER_PAL_PYTHON`/
`--pal-path`; older runners may still contain stale paths from previous machines.

## ACC 2027 canonical QLabs experiment

The 2026-08-27 closure campaign connects the exact controller implementation in
`C:\Research\papers\ACC2027_Gate_Residual_Control` to QLabs through PAL. Start
with `docs\ACC2027_PENDULUM_CLOSURE_2026-08-27.md`; it contains equations,
connection details, source hashes, matched results, invalidated comparisons, and
claim restrictions.

```powershell
cd C:\Research\pendulum
.\scripts\run_acc2027_twin_matrix.ps1 -BalanceDuration 20 -MaxDuration 90 -Trials 3 -Label paper_matched20
& C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe `
  .\tools\summarize_acc2027_twin.py --label paper_matched20 --output .\analysis\paper_matched20
```

Canonical 2026-08-27 matched result: all controllers held the final 5 s with no
faults/stalls; nominal RMS was practically equivalent to LQR. The earlier apparent
14% residual improvement was a fixed-wall-time/QLabs-limit-cycle confound and must
not be cited.

## Setup

```powershell
cd C:\00_Research_\Neuromorphic_Embodied_AI\07_ServoPendulum_SNNs
.\scripts\setup_env.ps1
.\scripts\activate_env.ps1
```

## Run Order

1. List copied Quanser examples:

```powershell
python .\runners\run_quanser_provided.py --list
```

2. Run an official copied Quanser example when ready:

```powershell
python .\runners\run_quanser_provided.py --example balance --i-understand
```

The vendor examples are intentionally unmodified and may use hard-coded hardware
defaults. Use them as the first confirmation that the Quanser stack itself is
working.

3. Run the project sensor check on the virtual twin:

```powershell
python .\runners\run_online_qube.py --mode sensor_check --hardware 0 --duration 5
```

4. Run project closed-loop balance on the virtual twin:

```powershell
python .\runners\run_online_qube.py --mode balance --hardware 0 --armed --duration 20
```

5. Run HyperLIF residual balance on the virtual twin:

```powershell
python .\runners\run_online_qube.py --mode hyperlif_residual --hardware 0 --armed --duration 20
```

6. Run the dependency-light offline benchmark:

```powershell
python .\runners\run_offline_benchmark.py --duration 20
python .\runners\plot_results.py
```

## Desktop App

The pendulum has its own robot-specific control panel:

```powershell
python .\app\qube_pendulum_app.py
```

The app exposes three execution modes without duplicating controller logic:

- `Offline Simulation`: runs `runners\run_offline_benchmark.py`.
- `Digital Twin`: runs `runners\run_online_qube.py --hardware 0`.
- `Hardware Experiment`: runs `runners\run_online_qube.py --hardware 1`.

Closed-loop motor output still requires the app's arm checkbox, which maps to
the runner's `--armed` flag. See `app\README.md` and
`docs\execution_modes_and_apps.md`.

## Layout

- `src\servo_pendulum_snn`: online runner, safety helpers, balance controller, HyperLIF residual wrapper.
- `src\quanser_residual_campaign`: local copy of the cross-platform offline benchmark code.
- `vendor\quanser_examples`: copied Quanser Qube Python and Simulink/digital-twin references.
- `vendor\quanser_reference`: copied PAL Qube product wrapper for reference.
- `results\offline` and `results\online`: generated logs and plots.
