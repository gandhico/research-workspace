# QDrone / QDrone2 — Runners & Launchers Index

Single place to find "how do I run X" for the QDrone platform. Companion docs:
`README.md`, `docs\future_work.md`, `docs\experimental_design.md`,
`docs\math_formulation.md`, `docs\source_inventory.md`,
`hardware\README.md`. Pulled forward from
`D:\NMSU_backups\Backup\00_Research_\Neuromorphic_Embodied_AI\06_QDrone_SNNs\`
on 2026-08-21 (excluding `_from_downloads_20260706\` — two X-Plane
flight-sim connector zips, unrelated to QDrone). Python only, no Julia or
MATLAB material exists for this platform.

**Maturity: partial pipeline.** Offline tier works and has a recorded result
(`results\offline\qdrone_20260610_010231\`). Hardware tier is
telemetry-read-only so far — no arming code exists. **QLabs kinematic-mirror
twin added 2026-08-27** (§1a) — the canonical ACC2027 CMG-PES controller,
visualized live in Quanser Interactive Labs. The QLabs-native physics twin
(real QUARC-simulated dynamics) is still a to-do — see §1a's fidelity note
and `docs\QLABS_TWIN_FIDELITY.md`.

---

## 1. Python — offline (no hardware, no QLabs)

| Script | Command | Purpose |
|---|---|---|
| `runners\run_offline_benchmark.py` | `python .\runners\run_offline_benchmark.py --duration 20` | Baseline vs. HyperLIF-residual benchmark, shared-campaign code. Output → `results\offline\qdrone_<timestamp>\`. **Verified working 2026-08-21** after vendoring the shared dependency (see §3). Note: this uses a separate, simpler linear-error-space `HyperLIFResidualController` from `_shared\quanser_residual_campaign`, not the canonical ACC2027 `gra_control.gate` implementation used in §1a. |
| `runners\plot_results.py` | `python .\runners\plot_results.py` | Re-plot latest offline results. |

## 1a. Python — QLabs kinematic-mirror twin (canonical ACC2027 CMG-PES)

Requires Quanser Interactive Labs running (any scene). Uses its own
`.venv` (`C:\Research\qdrone\.venv`, isolated from system Python — see
§3a) with `qvl`, `pal`, and the ACC2027 repo's `gra_control` installed
editable.

| Script | Command | Purpose |
|---|---|---|
| `runners\twin_acc2027_cmg_residual.py` | `.\.venv\Scripts\python.exe .\runners\twin_acc2027_cmg_residual.py --controller online-pes-adaptive --mission hover --duration 20` | Imports the exact `gra_control.gate.CMGResidualAugmentor` + `gra_control.math3d` from the ACC2027 repo (not reimplemented), integrates 6-DOF rigid-body dynamics in Python (mass/inertia read from the paper's own x2 MuJoCo model), and mirrors the resulting pose live into the QLabs QDrone2 actor. **Kinematic-mirror visualization, not a QLabs-native physics twin** — see `docs\QLABS_TWIN_FIDELITY.md` before citing. Output → `results\qlabs_twin\<controller>_<mission>_<timestamp>\` with the same `trace.csv`/`summary.json`/`manifest.json` provenance discipline as the ACC2027 MuJoCo runs. `--mission hard45` will fly the actor out of the visible scene within seconds (no x/y feedback, by design, matching the paper); use `--mission hover` or `--mission roll` for an in-view demo. `--no-visualize` runs the controller/physics standalone for validation. **Verified working 2026-08-27.** |

## 2. Python — physical hardware (telemetry only, not armed)

| Script | Command | Purpose |
|---|---|---|
| `hardware\run_qdrone2_telemetry_check.py` | `python .\hardware\run_qdrone2_telemetry_check.py --duration 10` | **Dry run** — no connection attempted. |
| | `python .\hardware\run_qdrone2_telemetry_check.py --connect --ip 192.168.2.15 --duration 10` | Connects to the telemetry stream; logs state vectors, motor commands, current, battery status. Read-only. |

Per `hardware\README.md`, do not attempt to arm flight until: telemetry is
stable, battery/failsafe states are visible in logs, baseline hover is
confirmed via Quanser's standard mission server, and residual commands have
been replayed offline against recorded baseline logs first.

## 3. Shared dependency fix (2026-08-21)

Like Aero2's cross-platform runner and QCar's offline runner, this platform's
`run_offline_benchmark.py` imports `quanser_residual_campaign` from
`PROJECT_ROOT / "_shared"` — i.e. it expects `C:\Research\_shared\`. That
folder didn't exist anywhere in `C:\Research\` until today; it's now vendored
at `C:\Research\_shared\quanser_residual_campaign\` (copied verbatim from the
backup drive's `Neuromorphic_Embodied_AI\_shared\`, `__pycache__` excluded —
**no code was edited**, the existing runners already pointed here). This same
copy also fixes Aero2's `run_cross_platform_offline_benchmark.py` and QCar's
`run_offline_benchmark.py`, both of which were silently broken before today.
All three were smoke-tested successfully on 2026-08-21.

## 3a. QLabs Python API install (2026-08-27)

`qvl` and `pal` are installed, but **isolated to `C:\Research\qdrone\.venv`**,
not system Python and not `Documents\Quanser\0_libraries\python\` (which
still only has `pit\` — the official installers were deliberately not run,
to avoid touching machine-wide `PYTHONPATH`/`QAL_DIR` via `setx` on this
rented/rebuilt laptop). Sources:

- `qvl` — `python/qvl/` from `github.com/quanser/Quanser_Interactive_Labs_Resources`
  (the same repo the official `install.py` installer pulls from; installed
  manually here instead of running that installer, since it targets
  `Documents\Quanser` + system env vars).
- `pal` — `0_libraries/python/pal/` from
  `github.com/quanser/Quanser_Academic_Resources` (branch `dev-windows` —
  that's the repo's default branch), the same upstream source
  `Documents\Quanser` was originally partially pulled from on 2026-08-21.

`QAL_DIR` and `RTMODELS_DIR` **are already set as persistent Windows env
vars** (`Documents\Quanser` — from an earlier, separate setup attempt), so
`pal.resources.rtmodels` path resolution works without extra configuration.
`quanser_api` (QUARC's own Python wheels, a `pal`/`qvl` dependency) is
installed the same way, from `C:\Program Files\Quanser\QUARC\python\`.

Re-running `pip install -e "C:\Research\papers\ACC2027_Gate_Residual_Control"`
against this venv installs the canonical `gra_control` package (CMG-PES
controller + math3d) editable, for §1a's twin runner.

## 4. Useful Quanser vendor sources

`C:\Quanser\...` paths in `README.md` are from a previous machine and don't
exist here. On this rebuilt laptop, the equivalent QDrone2 vendor material
lives under `C:\Users\gandhico\Documents\Quanser\5_research\autonomous_vehicles\qdrone2\`:

- `virtual\position_control\` — the vendor's own "virtual position control"
  Simulink source (`virtual_QD2_DroneStack_PID_2024a.slx`,
  `virtual_QD2_MissionCtrl_2024a.slx`) plus `spawn_qdrone2.py`. This is the
  source that has to be built via MATLAB + QUARC into
  `RTMODELS_DIR\QDrone2\QDrone2_Workspace` for the QLabs-native physics twin
  (not built yet on this machine — see `docs\QLABS_TWIN_FIDELITY.md`).
- `python_to_simulink\virtual\` — a second, self-contained tutorial
  (`qlabs_setup.py`, `commander.py`, `waypoint_commands.py`,
  `stream_stack_client_qd2.py`) with its own precompiled `.rt-win64` Mission
  Server models, no MATLAB rebuild needed for *that* part — but it still
  calls `rtmodels.QDRONE2` for the main airframe model, so it hits the same
  missing-`QDrone2_Workspace` gap. Its Python API (`commander.py`, read in
  full 2026-08-27) is arm/takeoff/land + `[x,y,z,yaw]` waypoints only — no
  exposed attitude-torque channel.

---

## Known gaps

- **QLabs-native physics digital twin**: not built yet. `qvl`/`pal` are
  installed and QLabs connectivity is verified (§1a), but the compiled
  airframe model `RTMODELS_DIR\QDrone2\QDrone2_Workspace` doesn't exist —
  it needs a one-time MATLAB R2025a + QUARC win64 build from the vendor
  `.slx` source (§4). Until then, §1a's kinematic-mirror twin is the
  available QLabs option.
- No arming/closed-loop hardware code — telemetry read-only.
