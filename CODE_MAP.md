# Code Map — Runners, Launchers, and HyperLIF Architectures

Single place to find "how do I run X" across the whole `C:\Research\` tree, and
to see at a glance how many HyperLIF-family neuron architectures and
experiments exist and where their code actually lives (vs. only being
described in a paper). Written 2026-08-18. Each project below also has its
own more detailed runner doc — this file is the index, not a replacement.

**`01_Code\` is an empty placeholder folder** — ignore it; nothing was ever
put there. All real code lives under `papers\P*\`, `aero2\`, `pendulum\`, and `qcar\`.

---

## 1. The HyperLIF neuron family (the architecture itself)

The same small family of spiking-neuron models recurs across every project
below, at different levels of loyalty to the reference math:

| Architecture | What it is | Where it's *implemented* (not just described) |
|---|---|---|
| **LIF** | Standard leaky integrate-and-fire, baseline. | P2 `src/neurons/`, P3 fixed_adaptive `src/controllers/neuron_dynamics.py`, aero2 `control/neuromorphic/neuron.py` |
| **HyperLIF (fixed gate)** | Core contribution: adds a gate state to LIF. | Same three locations as above, plus aero2 `control/neuromorphic/gate_residual.py` / `hyperlif_residual.py` |
| **Adaptive HyperLIF** | HyperLIF + adaptation variable `a` on the gate gain. | P3 fixed_adaptive `neuron_dynamics.py` (**proven numerically ≡ HyperLIF in gate mode** — see §4), aero2 `gate_residual.py` (`adaptive_hyperlif`) |
| **Learned-decode HyperLIF** | Adaptive/fixed gate + an online-learned (PES/e-prop) readout instead of a hand-set decode. | P3 `learned/` — **code not present on this machine**, see §3 gap list |
| **Izhikevich** | Reviewer-baseline comparison neuron, not a HyperLIF variant. | P3 fixed_adaptive `neuron_dynamics.py` only |
| **HyperLIF Learning (APEX)** | GPU/PyTorch trainable version used for P1's architecture/learning results. | **Not present on this machine** — P1 folder here has only the paper, not the APEX training code (see §3) |

So: **5 architectures in the HyperLIF family** (LIF baseline, HyperLIF,
Adaptive HyperLIF, learned-decode HyperLIF, plus the APEX learning variant),
**1 non-HyperLIF baseline neuron** (Izhikevich) kept only for comparison.

---

## 2. Runners / launchers by project

### P1 — HyperLIF Learning (`papers\P1_HyperLIF_Learning\`)
No experiment code on this machine — frozen paper only. Rebuild the PDF with:
```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```
(No LaTeX distribution is installed on this machine yet — see SETUP.md.)
The actual APEX training code that produced its results is on the backup
drive / not yet identified in this rebuild — treat P1 as **results-frozen,
code archived elsewhere** until pulled back.

### P2 — HyperLIF in Nengo/NEF (`papers\P2_HyperLIF_Nengo\`)
Full pipeline present and runnable. See `RUNNERS.md` in that folder for the
authoritative version; summary:

| Script | Purpose |
|---|---|
| `scripts\setup_env.ps1` | Create `.venv`, install `requirements.txt` |
| `scripts\run_experiments.ps1` → `experiments\run_all.py` | Runs all 17 numbered experiments (`01_lif_vs_hyperlif.py` … `18_nef_decoder_state_ablation.py`, no `12`) |
| `scripts\make_figures.ps1` | `figures\make_figures.py` — CSV → PNG/PDF |
| `scripts\make_tables.ps1` | `tables\make_tables.py` — CSV → `.tex` tables |
| `scripts\build_paper.ps1` | `pdflatex → bibtex → pdflatex → pdflatex` |
| `scripts\build_all.ps1` | All of the above, in order |

**17 experiment scripts** covering: LIF-vs-HyperLIF parity, adaptive
comparison, current sweeps, depolarization block, gate-state decoding,
numerical-integration accuracy, Python-vs-Nengo parity, NEF app smoke tests,
capability sweeps (core/backend-portability/seed-repeat), PES learning-rate
tuning, and decoder-state ablation. Fully self-contained; nothing missing.

### P3 — Gate-Residual Control, `fixed_adaptive\` (`papers\P3_Gate_Residual\fixed_adaptive\`)
MuJoCo quadrotor sim. Full command reference: `docs\runner_commands.md`
(also copied into this project's own README chain). Two runners:

| Script | Purpose |
|---|---|
| `runners\run_rotor_level.py` | **Main entry point** — single-run controller benchmark. `--controller {classical, direct_lif, direct_hyperlif, direct_adaptive_hyperlif, direct_izhikevich, rotor_residual_hyperlif, rotor_residual_adaptive_hyperlif, nengo_lifrate, nengo_lif, nengo_adaptive_lif}` × `--quad {skydio_x2, bitcraze_crazyflie_2}` |
| `runners\run_benchmark_sweep.py` | Multi-controller sweep + comparison table (`--preset smoke/full/rotor/quick`) |
| `runners\compare_conductance_residual.py` / `_v2.py` | One-off comparison plots, not part of the main pipeline |
| `runners\make_comparison_figures.py` | Figure generation from sweep output |

**10 registered controllers**, 4 of them HyperLIF-family (`direct_hyperlif`,
`direct_adaptive_hyperlif`, `rotor_residual_hyperlif`,
`rotor_residual_adaptive_hyperlif`).

⚠️ **Known content bug, not yet applied:** `paper\main2.tex` still claims
"Adaptive HyperLIF outperforms fixed HyperLIF" (Contribution 3) — this is
disproven (they're numerically identical in gate mode). The fix is already
written in `paper\sec_mujoco_gate_mechanism.tex`; it needs `\input`ing after
`\section{Results}` (main2.tex line 484) **and** the Contribution-3 text
elsewhere in the paper updated to match, per
`docs\2026_07_05_results_params_runners.md`. Left untouched today —
deliberately not sent to advisors in this state (see `_share_2026-08-18\`).

### P3 — Gate-Residual Control, `learned\` (`papers\P3_Gate_Residual\learned\`)
**Paper and results dossier only — the runnable code is not on this
machine.** Its own README points to
`neuromorphic-robotics-control\experiments\controller_benchmarks\learned_gate_experiment.py`,
which doesn't exist under `C:\Research\` yet. Full commands/params are
preserved in `docs\full_results_dossier.md` §8 for when that repo is pulled
back from the backup drive. This is the paper with the headline
**+86.7% (Bitcraze) / ~57% (Skydio)** result.

### Aero2 (`aero2\`) — hardware + digital-twin platform
Not a HyperLIF paper by itself, but the same neuron architectures are ported
here as registered controllers for the physical/twin Aero2. See
`WORKFLOW.md` for the full narrative; runner index:

| Script | Purpose |
|---|---|
| `runners\run_control.py` | Main entry — `--mode {offline, virtual_twin, hardware}` × `--controller {pd, lqr, lqg, mpc, backstepping, smc, nmpc, hyperlif, qpd, julia_policy, gate_residual, adaptive_hyperlif}` |
| `runners\run_identification.py` | System-ID runs (M1/M2/M3 in `data\raw_logs\`) |
| `runners\run_benchmark.py` | Controller benchmark sweep |
| `runners\run_state_estimation.py` | Estimator comparison |
| `runners\run_aero2_residual.py` | Aero2-specific residual controller runs |
| `runners\run_cross_platform_offline_benchmark.py` / `plot_cross_platform_results.py` | Python-vs-MATLAB comparison + plotting |
| `runners\run_julia_bridge_smoke.py` / `run_julia_policy_smoke.py` | Julia integration smoke tests |
| `runners\run_virtual_twin_io_diagnostic.py` | QLabs twin I/O sanity check |
| `campaigns\run_*.py` (not in `runners\`) | Named experiment campaigns — yaw, disturbance, gate-residual, motor-ID, etc. — see `WORKFLOW.md` §5 for the full list and results |

2 HyperLIF-family architectures ported here: `gate_residual` (fixed) and its
`adaptive_hyperlif` variant, both in `control\neuromorphic\gate_residual.py`
(plus a standalone `hyperlif_residual.py` and `eprop.py` for the
learned-decode direction).

### Pendulum (`pendulum\`) — Qube-Servo 3, offline + twin + hardware
Full runner index: **`pendulum\RUNNERS.md`** (authoritative, all tiers/languages).
Summary — Python offline (`run_offline_benchmark.py`), Python twin
(`run_online_qube.py --hardware 0`, plus standalone `twin_diagnostic.py` /
`twin_swingup_balance.py` / `twin_hyperlif_residual.py` / `twin_perturbation_benchmark.py`),
Python hardware (`run_online_qube.py --hardware 1`, `hardware\run_qube_sensor_check.py`),
MATLAB/Simulink (vendor examples only, `run_simulink_balance.py`), and — new as
of 2026-08-21 — **Julia twin** (`C:\Research\julia_bridge\julia\qube3_twin_*.jl`,
`calib_qube.jl`, `diag_qube_start.jl`; this is the *only* Julia-Pendulum code
that exists anywhere, pulled forward from the backup drive). Desktop app
`app\qube_pendulum_app.py` wraps offline/twin/hardware without duplicating
control logic. 1 HyperLIF-family architecture (`hyperlif_residual`, learned
decode — currently blocked on a missing `neuromorphic-robotics-control`
dependency, see `pendulum\RUNNERS.md` §2).

### QCar / QCar2 (`qcar\`) — offline (host) + hardware (on-car)
Full runner index: **`qcar\RUNNERS.md`**. Summary — Python offline benchmark
runs on this Windows machine (`runners\run_offline_benchmark.py`); the real
controller runs **on the car's Jetson via SSH**
(`01_Code\hardware\qcar2_unified_lane_control_hardware_v1.py`, 7 registered
controllers including `adaptive_hyperlif_gate` and three gated
PID/SMC/NMPC + adaptive-HyperLIF-residual combinations — exact tuned commands
in `qcar\runners\Qcar_Hardware_runners.md`); a separate ROS2 node stack
(`QCarControlNode`) is a parallel, ROS2-native control lineage — see
`01_Code\hardware\qcar\RUNNERS_1.md`. No Julia or MATLAB for this platform.
1 HyperLIF-family architecture (`adaptive_hyperlif_gate`, standalone or as a
residual on PID/SMC/NMPC).

### QDrone / QDrone2 (`qdrone\`) — offline (partial pipeline)
Full runner index: **`qdrone\RUNNERS.md`**. Python only. Offline benchmark
works and has a recorded result; hardware tier is telemetry-read-only (no
arming code); **no digital-twin tier yet** (flagged in `docs\future_work.md`
as a to-do). 1 HyperLIF-family architecture (gate-state residual on a
classical cascaded attitude/altitude baseline, same shape as Aero2/QCar/Pendulum).

### Gyroscope, QBot, Haptic, QArm, QArm Mini (`gyro3dof\`, `qbot\`, `haptic_hd\`, `qarm\`, `qarm_mini\`) — theory only
**No code exists for any of these five** — each folder contains only an IEEE
theory paper (`paper_math\*_models_control_ieee.tex`/`.pdf`, Gandhi Contreras)
deriving hardware physics, identification, modelling, and a full
PID/LQR/LQG/backstepping/SMC/NMPC controller suite **on paper**, with no
accompanying runners. Each has its own `RUNNERS.md` stating this explicitly
and pointing at the pattern to follow (`pendulum\`/`qdrone\`) when ready to
implement. Pulled forward from the backup drive 2026-08-21 for reference
alongside the platforms that do have code.

### Shared campaign module (`C:\Research\_shared\quanser_residual_campaign\`)
Pulled forward from the backup drive 2026-08-21 — this fixed **three silently
broken runners** that already expected it at this exact path and had no local
vendor copy: Aero2's `run_cross_platform_offline_benchmark.py`, QCar's
`run_offline_benchmark.py`, and (newly added) QDrone's
`run_offline_benchmark.py`. All three were smoke-tested successfully after
the copy. (Pendulum instead vendors its own local copy at
`pendulum\src\quanser_residual_campaign\` — both patterns coexist in the tree,
no code was changed to make them consistent.)

### Julia — cross-platform bridge (`C:\Research\julia_bridge\`)
Pulled forward from the backup drive 2026-08-21 (previously the single
biggest gap: `pendulum\` had zero Julia code, and Aero2's in-package Julia
scaffold was an older generation). `julia_bridge\julia\QuanserHIL.jl` is a
generic `ccall`→`hil.dll` bridge with a 14-board registry covering every
Quanser platform in the lab, not just these three. See
`pendulum\RUNNERS.md` §4 and `aero2\launchers_runners.md` §6 for per-platform
commands, and `julia_bridge\README.md` / `VALIDATION_STATUS.md` for the
full validation ladder (V0–V4) across all ten robots.

---

## 3. Code gaps on this machine (things a paper references but aren't here yet)

Pull these from `D:\NMSU_backups\` when needed — see `SETUP.md` for the
backup drive map:

- **P1's APEX training code** — not identified/copied yet.
- **`neuromorphic-robotics-control` repo** (P3 `learned\`'s actual sim code) — not copied yet; only the paper + results dossier are here.
- **`code\quaternion_quad\`** — the older from-scratch Julia ODE cross-check (`paper_ode_replication.jl`), independent of MuJoCo — not copied yet (see [[project-hyperlif-papers]] memory for why it's not a MuJoCo binding).

## 4. Experiment counts, at a glance

| Project | Experiment/runner scripts | HyperLIF-family architectures exercised |
|---|---:|---:|
| P1 | 0 on this machine (frozen paper) | 1 (APEX learning variant, code elsewhere) |
| P2 (Nengo) | 17 numbered experiments | 3 (LIF, HyperLIF, Adaptive HyperLIF) |
| P3 fixed_adaptive | 5 runner scripts, 10 registered controllers | 4 (direct + rotor-residual × fixed/adaptive) |
| P3 learned | 1 (code not present) | 1 (learned-decode gate) |
| aero2 | 9 `runners\` + several `campaigns\` scripts | 2 (gate_residual fixed/adaptive) |
| pendulum | 3 `runners\` (offline/vendor) + 4 standalone twin scripts + 1 online-runner (3 modes) + 1 legacy hardware | 1 (hyperlif_residual, learned decode — blocked, missing dependency) |
| qcar | 2 `runners\` (offline) + 1 on-car hardware runner (7 controllers) + ROS2 stack (2 controllers) | 1 (adaptive_hyperlif_gate, standalone or residual) |
| qdrone | 2 `runners\` (offline) + 1 hardware telemetry check (read-only) | 1 (gate-state residual, offline only so far) |
| gyro3dof / qbot / haptic_hd / qarm / qarm_mini | 0 (theory paper only, each) | 0 (planned, not implemented) |
