# Aero2 Residual — Launchers & Runners

Every launcher used for the Aero2 HyperLIF residual-augmentation work, reconstructed from the
scripts and the **75 run CSVs / 31 conditions** in `results/residual/` (controller `smc/yawboost`,
backend `hil`). Pitch channel, neuron `adaptive_hyperlif` (defaults) throughout.

---

## 0. Environment / how runs were launched

All hardware runs go through the PowerShell wrapper, which selects the Quanser venv and puts this
project + `aero2_clean` + the Quanser libs on `PYTHONPATH`:

```powershell
# scripts/run_residual.ps1  — passes ALL args through to runners/run_aero2_residual.py
.\scripts\run_residual.ps1 <args...>
```
It is equivalent to:
```powershell
$env:PYTHONPATH = "C:\00_Research_\Neuromorphic_Embodied_AI\04_Aero2_SNNs;C:\02_Research\01_Robotics_Quanser\01_Aero2\aero2_clean;C:\Quanser\0_libraries\python"
$env:AERO2_CLEAN = "C:\02_Research\01_Robotics_Quanser\01_Aero2\aero2_clean"
& "C:\02_Research\01_Robotics_Quanser\.quanser_env\Scripts\python.exe" -u .\runners\run_aero2_residual.py <args...>
```
Output CSVs → `results/residual/{prefix}_{backend}_{timestamp}.csv`
(`prefix` = `--residual-log-prefix`).

---

## 1. Main residual runner — `runners/run_aero2_residual.py`

Classical controller is the stability anchor; a bounded HyperLIF gate-state residual is optionally
added at the virtual pitch/yaw level. Key flags:

| Flag | Used values | Meaning |
|---|---|---|
| `--controller` | `smc` | also `backstepping`, `nmpc` |
| `--variant` | `yawboost` | chosen baseline (robust, low overrun) |
| `--backend` | `hil` | also `pal` |
| `--mission` | `tracking`, `equilibrium` | square-wave vs. hold |
| `--residual-mode` | `none, shadow_gate, gate, always_on, shuffled_gate` | ablation conditions |
| `--residual-channel` | `pitch` | also `yaw, pitch_yaw, motor_pair` |
| `--residual-max-voltage` | `0.5`, `1.0` | hard cap on \|applied residual\| (the `cap05`/`cap10` tokens) |
| `--residual-demand-threshold` | `0.20` (default), `0.30` | gate-open demand (the `dthr030` token) |
| `--residual-neuron` | `adaptive_hyperlif` (default) | also `hyperlif` |
| `--perturbation-profile` | `pitch_pulse_train` | scripted reference pulses (the `pitchpulse` token) |
| `--residual-log-prefix` | descriptive | sets the output filename stem |

Defaults worth noting: `--run-time 30`, `--frequency 500`, `--filter-dt-mode actual`,
perturbation `amp 0.08 rad / width 3 s / times 10,20,30,40 / alternating sign`.

---

## 2. The residual-ablation campaign (exactly what was run, HIL)

Common flags for every run below:
`--controller smc --variant yawboost --backend hil --residual-channel pitch`
(`_rep` conditions = the **same command re-run**; each run writes a new timestamped CSV.)

### Mission 1 — tracking (square-wave pitch ±20° @0.05 Hz, yaw ±45° @0.04 Hz)
```powershell
cd "C:\00_Research_\Neuromorphic_Embodied_AI\04_Aero2_SNNs"
# baseline (residual off)
.\scripts\run_residual.ps1 --mission tracking --residual-mode none        --residual-log-prefix aero2_smc_baseline_tracking
# shadow (candidate computed, applied = 0)
.\scripts\run_residual.ps1 --mission tracking --residual-mode shadow_gate  --residual-log-prefix aero2_smc_shadow_tracking
# gate, cap 0.5 V  /  cap 1.0 V
.\scripts\run_residual.ps1 --mission tracking --residual-mode gate --residual-max-voltage 0.5 --residual-log-prefix aero2_smc_gate_cap05_tracking
.\scripts\run_residual.ps1 --mission tracking --residual-mode gate --residual-max-voltage 1.0 --residual-log-prefix aero2_smc_gate_cap10_tracking
# controls: always_on / shuffled_gate at cap 0.5 V
.\scripts\run_residual.ps1 --mission tracking --residual-mode always_on     --residual-max-voltage 0.5 --residual-log-prefix aero2_smc_alwayson_cap05_tracking
.\scripts\run_residual.ps1 --mission tracking --residual-mode shuffled_gate  --residual-max-voltage 0.5 --residual-log-prefix aero2_smc_shuffled_cap05_tracking
```
(`*_tracking_rep` = the six commands above repeated, prefix suffix `_tracking_rep`.)

### Mission 2 — equilibrium (refs = 0, hold; `_clean` adds `--residual-demand-threshold 0.30`)
```powershell
cd "C:\00_Research_\Neuromorphic_Embodied_AI\04_Aero2_SNNs"
.\scripts\run_residual.ps1 --mission equilibrium --residual-mode none        --residual-log-prefix aero2_smc_baseline_equil
.\scripts\run_residual.ps1 --mission equilibrium --residual-mode shadow_gate  --residual-log-prefix aero2_smc_shadow_equil
.\scripts\run_residual.ps1 --mission equilibrium --residual-mode gate     --residual-max-voltage 0.5 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_gate_cap05_equil_clean_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --residual-mode gate     --residual-max-voltage 1.0 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_gate_cap10_equil_clean_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --residual-mode always_on --residual-max-voltage 0.5 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_alwayson_cap05_equil_clean_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --residual-mode shuffled_gate --residual-max-voltage 0.5 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_shuffled_cap05_equil_clean_dthr030
```
(`*_equil_rep` = these repeated with the `_equil_rep` prefix; the first equilibrium block used
prefixes without `_clean_dthr030`.)

### Scripted pitch-pulse perturbation (equilibrium + reference pulse train, dthr 0.30)
```powershell
# add to an equilibrium run:  --perturbation-profile pitch_pulse_train --residual-demand-threshold 0.30
.\scripts\run_residual.ps1 --mission equilibrium --perturbation-profile pitch_pulse_train --residual-mode none        --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_baseline_pitchpulse
.\scripts\run_residual.ps1 --mission equilibrium --perturbation-profile pitch_pulse_train --residual-mode shadow_gate  --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_shadow_pitchpulse_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --perturbation-profile pitch_pulse_train --residual-mode gate     --residual-max-voltage 0.5 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_gate_cap05_pitchpulse_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --perturbation-profile pitch_pulse_train --residual-mode gate     --residual-max-voltage 1.0 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_gate_cap10_pitchpulse_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --perturbation-profile pitch_pulse_train --residual-mode always_on --residual-max-voltage 0.5 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_alwayson_cap05_pitchpulse_dthr030
.\scripts\run_residual.ps1 --mission equilibrium --perturbation-profile pitch_pulse_train --residual-mode shuffled_gate --residual-max-voltage 0.5 --residual-demand-threshold 0.30 --residual-log-prefix aero2_smc_shuffled_cap05_pitchpulse_dthr030
```

**Conditions actually present in `results/residual/` (75 CSVs / 31 prefixes):** baseline, shadow,
gate (cap05 & cap10), always_on (cap05), shuffled (cap05) — each across tracking, equilibrium
(plain / `_rep` / `_clean_dthr030`), and pitchpulse.

---

## 3. Analysis of the runs — `tools/analyze_aero2_residual_conditions.py`

After each block, compare conditions (none/shadow/gate/always_on/shuffled):
```powershell
& $python tools\analyze_aero2_residual_conditions.py --log results\residual\<A>.csv --log results\residual\<B>.csv ...
# self-test (no hardware):
& $python tools\analyze_aero2_residual_conditions.py --demo
```
Outputs → `analysis/aero2_residual_comparison_YYYYMMDD_HHMMSS/` (summary, demand-binned metrics,
report, overlays, comparison/activity/error/energy figures). Eight such comparison folders +
bundle zips already exist under `analysis/`.

---

## 4. Cross-platform offline benchmark (baseline vs HyperLIF residual)

Uses the shared campaign module `_shared/quanser_residual_campaign`:
```powershell
& $python runners\run_cross_platform_offline_benchmark.py --duration 20      # [--no-plots]
& $python runners\plot_cross_platform_results.py                              # re-plot latest
```
Output → `results/cross_platform_offline/aero2_<timestamp>/`.

---

## 5. Other repo runners (classical pipeline — not residual, listed for completeness)

```powershell
& $python runners\run_control.py        --controller pd --model helicopter_2dof --mode offline --estimator aero2 --duration 40 --hz 200 [--save]
& $python runners\run_control.py        --controller pd --model helicopter_2dof --mode virtual_twin --application pitch_reference_tracking --duration 10 --hz 200 # live-smoke validated pitch path
& $python runners\run_control.py        --controller pd --model helicopter_2dof --mode virtual_twin --application yaw_reference_tracking --duration 5 --hz 200   # connects, but current QLabs scene keeps yaw fixed
& $python runners\run_virtual_twin_io_diagnostic.py --test all --duration 3.5 --hz 200 --voltage 3 --read-mode 1 --save # open-loop QLabs I/O probe; current scene behaves pitch-only
& $python runners\run_benchmark.py      --model helicopter_2dof --duration 30 --dt 0.005 --save # offline Table-IV-style ranking + CSV/JSON
& $python runners\run_identification.py                                                      # ARX/DARX → Table II
& $python runners\run_state_estimation.py                                                    # gyro-vs-encoder pitch-rate estimator
```

`run_control.py` and `run_benchmark.py` are direct-script safe from the repo
root; they do not require an editable install first. `run_benchmark.py --save`
writes paper-table-ready controller comparison summaries to `results/`.

> Note: `pytest` (from the repo root) runs the **unit tests** (config/interface/contract/direct-runner smoke tests) —
> that's the test runner, separate from the experiment launchers above.

---

## 6. Julia — two bridges now live for this platform

**In-package scaffold** (`julia\Aero2HilCBridge.jl`, `julia\aero2_hil_sensor_check.jl`,
`julia\aero2_policy_smoke.jl` + `control\julia_bridge.py`) — Bridge 1
(PythonCall drives, Julia supplies policy) and Bridge 2 (Julia `ccall`→`hil.dll`),
integrated with this repo's `Controller`/`Backend` contract and its own tests
(`tests\test_julia_bridge.py`, `tests\test_julia_hil_c_bridge.py`). Full detail:
`docs\11_julia_quanser_bridge.md`. Commands:
```powershell
python .\runners\run_julia_policy_smoke.py                          # Stage J0 parity smoke
python .\runners\run_julia_bridge_smoke.py --duration 0.5 --hz 200 --dt 0.005  # Bridge 1
julia --startup-file=no .\julia\aero2_hil_sensor_check.jl --duration 0.01      # Bridge 2, no-connect
```

**Standalone generic bridge** — `C:\Research\julia_bridge\` (pulled forward
from the backup drive 2026-08-21; same `17_Julia_Quanser_Bridge` lineage this
in-package scaffold was built from, but with a generalized 14-board
`QuanserHIL.jl` registry and a **V3-proven pure-Julia closed PD loop**
(`julia_bridge\julia\aero2_twin_pd_loop.jl` — 199.8 Hz realized, pitch RMS
0.0479 rad on the twin, per `julia_bridge\VALIDATION_STATUS.md`). Not wired
into this repo's `Controller` contract — a separate, self-contained script:
```powershell
julia --startup-file=no C:\Research\julia_bridge\julia\aero2_twin_pd_loop.jl 8 200
```
Also the only place with **Julia-Pendulum** code — see `..\pendulum\RUNNERS.md` §4.
