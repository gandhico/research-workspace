# Pendulum (Qube-Servo 3) — Runners & Launchers Index

Single place to find "how do I run X" for the pendulum platform, across every
language and simulation tier. Companion docs: `README.md` (setup + quick run
order), `docs/execution_modes_and_apps.md` (the desktop app's mode mapping),
`app/README.md`. This file is the authoritative, exhaustive index — updated
2026-08-21.

Activate the environment first (see `C:\Research\ENVIRONMENTS.md`):
```powershell
& C:\Users\gandhico\AppData\Local\miniconda3\Scripts\conda.exe activate hyperlif
```

---

## 1. Python — offline (no hardware, no QLabs)

| Script | Command | Purpose |
|---|---|---|
| `runners\run_offline_benchmark.py` | `python .\runners\run_offline_benchmark.py --duration 20 [--no-plots]` | Baseline vs. HyperLIF-residual benchmark, software-only. |
| `runners\plot_results.py` | `python .\runners\plot_results.py` | Re-plot latest offline results. |
| `runners\run_quanser_provided.py` | `python .\runners\run_quanser_provided.py --list`<br>`python .\runners\run_quanser_provided.py --example balance --i-understand` | Launch **unmodified, vendored** Quanser example scripts (`vendor\quanser_examples\`) — first sanity check that the Quanser stack itself works, independent of this project's own code. |

## 2. Python — digital twin (QLabs, `localhost:18920–18923`)

**Gated online runner** (`src\servo_pendulum_snn\online_runner.py`, invoked via `runners\run_online_qube.py`):

| Mode | Command |
|---|---|
| Sensor check (0 V) | `python .\runners\run_online_qube.py --mode sensor_check --hardware 0 --duration 5` |
| Balance (LQR) | `python .\runners\run_online_qube.py --mode balance --hardware 0 --armed --duration 20` |
| HyperLIF residual balance | `python .\runners\run_online_qube.py --mode hyperlif_residual --hardware 0 --armed --duration 20` |

Other flags: `--version {2,3}` (default 3), `--sample-rate`, `--voltage-limit`,
`--capture-angle-deg`, `--balance-gains <k1 k2 k3 k4>`, `--residual-limit`,
`--residual-blend`, `--gate-gain`, `--no-tachometer`. `--armed` is required for
any nonzero motor voltage; without it the runner logs state while commanding
zero volts.

**Standalone twin scripts** (`runners\`, not routed through the app/online
runner — each is its own experiment, verified against the twin on 2026-07-23,
virtual card `0@tcpip://localhost:18923`):

| Script | Command | Purpose |
|---|---|---|
| `twin_diagnostic.py` | `python .\runners\twin_diagnostic.py [seconds]` | **Safe, 0 V.** Confirms QLabs connection, exercises LEDs, logs every PAL parameter, determines encoder-zero convention. Run this first on a new machine/twin. |
| `twin_swingup_balance.py` | `python .\runners\twin_swingup_balance.py [duration_s] [hz] [mu] [V_sw] [gains: twin\|code] [bal_sign]` | Energy swing-up + LQR balance, pure Python/PAL reference. Its Julia twin is `julia_bridge\julia\qube3_twin_swingup_balance.jl` — both must agree (see §4). |
| `twin_hyperlif_residual.py` | `python .\runners\twin_hyperlif_residual.py [method: baseline\|fixed_gate\|online_pes\|eprop_anneal] [neuron: lif\|hyperlif\|adaptive_hyperlif\|izhikevich] [duration] [blend] [lr] [k_rate]` | HyperLIF gate residual with **learned** decode (PES/e-prop), LED error gauge. ⚠️ Imports `neuron_dynamics.make_direct_neuron` from the `neuromorphic-robotics-control` repo, which **is not present on this machine** (see `CODE_MAP.md` §3) — will fail until that repo is pulled from the backup drive. |
| `twin_perturbation_benchmark.py` | `python .\runners\twin_perturbation_benchmark.py [method] [neuron] [v_pert] [blend]` | Scripted disturbance-rejection benchmark (swingup → center → repeated impulses), LED gauge, same perturbation schedule across controller variants for direct comparison. |
| `twin_acc2027_gate_residual.py` | `python .\runners\twin_acc2027_gate_residual.py --controller <name> --balance-duration 20 --max-duration 90` | **Canonical 2026-08-27 ACC runner.** Imports the exact `gra_control.gate` implementation, auto-discovers current PAL, uses bounded additive voltage, hashes sources, and is hard-coded to QLabs `hardware=0`. |

Matched five-controller matrix and aggregation:

```powershell
.\scripts\run_acc2027_twin_matrix.ps1 -BalanceDuration 20 -MaxDuration 90 -Trials 3 -Label paper_matched20
python .\tools\summarize_acc2027_twin.py --label paper_matched20 --output .\analysis\paper_matched20
```

See `docs\ACC2027_PENDULUM_CLOSURE_2026-08-27.md` before interpreting results.
The older `twin_hyperlif_residual.py` uses a different blend architecture and a
stale external import; it is not the ACC canonical runner.

## 3. Python — physical hardware (all confirmed working 2026-09-03)

Python: `C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif\python.exe`
(`conda` is not on PATH on this machine — call this path directly, don't
`conda activate`). `pal`/`qvl` were copied into this env from `qdrone`'s
isolated `.venv` on 2026-09-03 (see `_shared`/CODE_MAP.md) — previously
missing (`ModuleNotFoundError: No module named 'pal'`).

**Bug fixed 2026-09-03:** `src\servo_pendulum_snn\qube_io.py`'s `read_state()`
was missing the hanging→upright `-pi` shift on `alpha`, so the hardware
balance controller regulated toward hanging-down instead of upright. Fixed by
making the shift a parameter (`alpha_offset_rad`, default `math.pi`) — see
that file's docstring for why callers applying their own offset (like
`simulink_balance_runner.py`) must pass `alpha_offset_rad=0.0` to avoid the
two shifts stacking to `2*pi` and cancelling out (hit and fixed same day).

| Script | Command | Status |
|---|---|---|
| Sensor check | `python .\runners\run_online_qube.py --mode sensor_check --hardware 1 --duration 5` | ✅ Working. Always run first. |
| LED color test | `python .\runners\run_online_qube.py --led-test --hardware 1 [--led-hold-s 1.0]` | ✅ Working (added 2026-09-03). Zero voltage throughout; cycles red→green→blue→yellow→cyan→magenta→white→off. |
| Equilibrium (LQR balance) | `python .\runners\run_online_qube.py --mode balance --hardware 1 --armed --duration 20` | ⚠️ **Do not use for the demo.** Alpha convention is correct, but `QuanserBalanceController` has no latching/hysteresis/engagement-velocity gate — it switches on/off every sample purely on `\|alpha\|<=capture_angle_deg`, so it can catch mid-swing with bad timing and appear to "not keep equilibrium." Confirmed unreliable on hardware 2026-09-03. Was never part of the June-14 hardware validation — use `run_simulink_balance.py` (below) instead. |
| HyperLIF residual balance | `python .\runners\run_online_qube.py --mode hyperlif_residual --hardware 1 --armed --duration 20` | ⚠️ **Do not use for the demo.** Same naive-engagement issue as above (shares `QuanserBalanceController` as its base), reported "working weird" on hardware 2026-09-03. This is a *different, never hardware-validated* residual architecture from the proven one — the June-14 gate-residual results came entirely through `run_simulink_balance.py --residual-mode gate`, not this controller. Use that instead. |
| Swing-up + balance (proper engagement logic) | `python .\runners\run_simulink_balance.py --hardware 1 --armed --duration 20 --voltage-limit 4.0 --require-manual-swing --manual-swing-release-deg 15 --alpha-upright-offset-deg 180 --capture-angle-deg 10 --capture-hysteresis-deg 2 --engage-confirm-samples 3 --max-engage-alpha-dot 3.0 --theta-ref-mode current_on_engage --soft-start-s 0.05` | ✅ Working (fixed + confirmed 2026-09-03). Waits at 0V for a manual swing >15° away from rest, then latches balance once within the capture band. This is the **classical baseline** per `docs\qube_servo3_simulink_python_baseline.md` — prefer it over the plain `--mode balance` above for anything beyond a quick sanity check. |
| Swing-up + gate residual, cap ±0.20V (strongest documented result: 0.775° mean error, 2026-06-14) | Same as above + `--duration 60 --residual-mode gate --residual-scale 1.0 --residual-sign 1.0 --residual-neuron adaptive_hyperlif --residual-max-voltage 0.20 --residual-log-prefix qube3_gate_cap020_60s` | ✅ Previously validated (12 hardware trials, 0 amplifier faults) — architecture unchanged, re-confirm with a short run before presenting. |
| Legacy read-only sensor helper | `python .\hardware\run_qube_sensor_check.py --duration 10`<br>`python .\hardware\run_qube_sensor_check.py --connect --hardware 0 --duration 10` | Kept for reference, superseded by `run_online_qube.py --mode sensor_check`. |

`run_simulink_balance.py` (via `simulink_balance_runner.py`) is the more
complete/proven hardware controller — manual-swing detection, latched
engagement, hysteresis, current-on-engage base reference. `run_online_qube.py
--mode balance` is simpler (naive capture-gated LQR, no manual-swing
requirement or hysteresis) — fine for a quick check, not the primary demo
controller. See `docs\qube_servo3_simulink_python_baseline.md` §11 for the
full comparison.

## 4. Julia — digital twin (pulled forward from backup 2026-08-21)

Previously **zero Julia code existed for the pendulum** on this machine (see
`SETUP.md` — "no Julia project/packages set up"). The real Julia⇄Quanser
bridge lives at `C:\Research\julia_bridge\` (copied from
`D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\17_Julia_Quanser_Bridge\`
— see that folder's own `README.md`/`VALIDATION_STATUS.md` for the full
cross-platform picture). No external Julia packages are required — everything
uses stdlib (`Libdl`, `LinearAlgebra`, `Printf`, `Statistics`) via direct
`ccall` into `hil.dll`; the shared project `C:\Research\julia_env` is still a
fine place to `Pkg.activate` from, it just has nothing to install yet.

| Script | Command | Status |
|---|---|---|
| `julia_bridge\julia\diag_qube_start.jl` | `julia --startup-file=no julia_bridge\julia\diag_qube_start.jl` | Safe diagnostic (V0/V1). |
| `julia_bridge\julia\calib_qube.jl` | `julia --startup-file=no julia_bridge\julia\calib_qube.jl` | Calibration. |
| `julia_bridge\julia\qube3_twin_equilibrium.jl` | `julia --startup-file=no julia_bridge\julia\qube3_twin_equilibrium.jl [dur] [hz] [mu] [V_sw] [gains] [bal_sign]` | Equilibrium hold on the twin. |
| `julia_bridge\julia\qube3_twin_swingup_balance.jl` | `julia --startup-file=no julia_bridge\julia\qube3_twin_swingup_balance.jl [duration_s] [hz] [mu] [V_sw] [gains: twin\|code] [bal_sign]` | Pure-Julia energy swing-up + LQR balance on the twin — the Julia counterpart of `runners\twin_swingup_balance.py` above. **Ran successfully 2026-07-23**; sample output preserved at `julia_bridge\results\twin_swingup_julia_twin_sign1_20260723_025715.{csv,json}`. |

Per `julia_bridge\VALIDATION_STATUS.md` (2026-07-12): Qube3 V0/V1 pass; **V2
(twin connect) was pending a running QLabs Qube scene** at that writing — open
QLabs → Qube-Servo3 first (ports 18920–18923, `nagle='off'`), same as the
Python twin scripts. V4 (physical hardware) is an explicit lab action only —
swap the virtual card id for `"0"`.

**These `.jl` files `include(joinpath(@__DIR__, "QuanserHIL.jl"))`** — keep
them together in `julia_bridge\julia\`, don't move them individually.

## 5. MATLAB / Simulink

`vendor\quanser_examples\` — Quanser's own `.slx` labs (balance, LQR,
state-space digital twin, quick-start). These are **unmodified vendor
reference material**, not custom controllers (unlike Aero2, which has a
hand-written `aero2_twin_pd.m`). `runners\run_simulink_balance.py` wraps
`src\servo_pendulum_snn\simulink_balance_runner.py` to drive a Simulink
balance model from Python — see `docs\qube_servo3_simulink_python_baseline.md`.

## 6. Desktop app (wraps offline / twin / hardware — no separate control logic)

```powershell
python .\app\qube_pendulum_app.py
```
Maps: **Offline Simulation** → `run_offline_benchmark.py`; **Digital Twin** →
`run_online_qube.py --hardware 0`; **Hardware Experiment** →
`run_online_qube.py --hardware 1`. See `docs\execution_modes_and_apps.md`.

---

## Safety rules (apply to every online/hardware mode above)

- Sensor-check / diagnostic commands always zero voltage.
- Closed-loop commands are zeroed by the runner unless `--armed` is passed.
- Hardware mode asks for confirmation before an armed closed-loop run.
- Emergency stop terminates the runner process; `safe_stop_qube` in the
  runner's `finally` block handles zero-voltage shutdown.

## Known gaps

- `twin_hyperlif_residual.py` needs the `neuromorphic-robotics-control` repo
  (not on this machine yet).
- No standalone `hardware\run_*_control.py` (closed-loop hardware runs go
  through `run_online_qube.py --hardware 1` instead).
- Julia hardware tier (V4) not yet attempted — twin only so far.
