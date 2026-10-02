# Machine Setup Notes — Gandhi Contreras Torres (NMSU)

This file is the master reference for provisioning a Windows laptop for research
(HyperLIF / neuromorphic embodied AI, Quanser robotics) + TA duties (Computer
Organization Lab, VHDL). Written so a future reset/rental-laptop swap takes
minutes to look up, not hours to rediscover.

**Golden rule:** this machine is disposable. `D:\NMSU_backups\` (or wherever the
external drive lands) is the only durable copy of anything. Keep C: minimal —
clean working trees only, no heavy archives, no results dumps.

---

## 1. The pattern behind this layout

You've now done this twice: once on a previous rented laptop (Aug 9–16, 2026,
fully validated through hardware experiments — see `C:\Research\WORKFLOW.md`),
and now on this one (Aug 17, 2026). Both times the same shape emerged:

- **`C:\Research\`** — clean working code only. Heavy results/archives/old
  semester code stay on the backup drive, never copied to C:.
- **`C:\Quanser_Setup\`** — a self-contained installer kit (staged once,
  reused every time): MATLAB, QUARC, QLabs, Python 3.13, licenses, dev tools.
- **`C:\Teaching\`** — TA/course materials, separate from research.
- **Standard tool locations** — MATLAB at `C:\Program Files\MATLAB\R2025a`,
  Quanser Academic Resources at `C:\Users\gandhico\Documents\Quanser`, conda
  at `C:\Users\gandhico\AppData\Local\miniconda3` — because Quanser's own
  scripts and your code hardcode these.
- **`C:\.claude\`** — Claude Code is run with **C:\ as the working directory**,
  not a user folder. Keep `C:\.claude\settings.local.json` backed up.

An earlier, older scheme (`C:\00_Research_`, `C:\02_Research`, `C:\04_programs`,
`C:\Quanser`, `C:\QuanserLicense` — from the Spring 2026 backup) is now
**retired**. It's still archived at `D:\NMSU_backups\Backup\` for reference but
don't resurrect it — the `C:\Research` / `C:\Quanser_Setup` scheme above is the
current, proven one.

---

## 2. What lives where on the backup drive

`D:\NMSU_backups\` (external drive), as of 2026-08-17:

| Path | Contents | Size |
|---|---|---|
| `Backup\00_Research_\` | Old (Spring '26) research portfolio tree | ~102 GB |
| `Backup\02_Research\` | Old code ecosystem (uv-based Python + Julia envs) | ~66 GB |
| `Backup\04_programs\` | Old cached installers (superseded by `Quanser_Setup`) | ~3 GB |
| `Backup\Quanser\` / `Backup\QuanserLicense\` | Old Quanser SDK tree + license files | ~6 GB |
| `Backup\Users\gandhico\` | Profile backup: `.julia` (7.7GB), `.vscode`, `.codex`, `.ssh`, `AppData`, `Downloads` — **not** a full profile | ~12 GB |
| `Backup\_root_dotclaude\` | Old `C:\.claude\settings.local.json` | tiny |
| `VHDL_Lab_Fall_2026.zip` (drive root) | Bundle staged 2026-08-17: TA materials + `Quanser_Setup` kit + `Research` working tree + papers + wiscom creds + `.claude` settings | 8 GB |
| `hyperlif_replication.zip` (drive root) | HyperLIF replication datasets (DVS gesture, N-MNIST, chunked `.h5`) | 0.7 GB |
| `Downloads.zip` (drive root) | General Downloads folder backup | 6 GB |
| `mujoco_chunks\` (drive root) | Split MuJoCo scene/asset archives (`.partNN`) — reassemble before use | ~2 GB |

**Note:** the "old" scheme and the "new" scheme both exist on the backup drive.
When restoring, prefer content staged at the drive root (dated most recently)
over `Backup\00_Research_` / `Backup\02_Research`, which are frozen Spring '26
snapshots.

---

## 3. Quanser install pipeline

Full detail lives in `C:\Quanser_Setup\README.md` (mermaid dependency graph +
Gantt schedule). Summary:

**Critical path:** MATLAB → QUARC → activate license → configure scripts → restart.
**Parallel (off critical path):** QLabs install, Python 3.13 install, Git/VS Code/conda.

1. `C:\Quanser_Setup\01_matlab\matlab_R2025a_Windows.exe` — sign in with
   MathWorks/NMSU campus account. ~40 min, start first.
2. `C:\Quanser_Setup\02_quarc\install_quarc.exe` — **after** MATLAB, needs
   internet (small bootstrapper, fetches components live).
3. Activate with both `.qlic` files in `C:\Quanser_Setup\` (Complete + Essentials,
   NMSU Lab Job#13488).
4. `C:\Quanser_Setup\03_qlabs\Install QLabs.exe` (1.47 GB) — can run in parallel
   with steps 2–3.
   - **Gotcha:** if you later install *full* QUARC (not just QUARC Runtime),
     it reinstalls its own QLabs — uninstall the standalone QLabs first,
     otherwise you get a duplicate/conflicting install.
5. `C:\Quanser_Setup\04_python\python-3.13.11-amd64.exe` — tick **"Add
   python.exe to PATH"** on the first screen. Don't use Microsoft Store Python.
6. Extract `C:\Quanser_Setup\06_resources\Quanser Examples.zip` to
   `C:\Users\gandhico\Documents\Quanser` (exact path — scripts read this as
   `QAL_DIR`).
7. In `Documents\Quanser\1_setup\`, run **in order**:
   `step_1_check_requirements.bat` → `configure_matlab.bat` → `configure_python.bat`.
8. **Restart Windows.**
9. Verify: MATLAB `ver` lists QUARC; QLabs opens a virtual workspace;
   `py -3.13 -c "import quanser; import qvl"` succeeds; `%QAL_DIR%` and
   `%PYTHONPATH%` are set.

**Known gotcha (hit on the previous laptop):** `hardware=1` PAL backend fails
with *"Support for the given board type does not appear to be installed"* if
only QUARC *Runtime* is installed — the physical Aero2's HIL/USB drivers ship
with **full QUARC**, not the runtime-only install. Install full QUARC if you
need the physical hardware tier, not just the twin.

---

## 4. Python environment

**`hyperlif` conda env** (Python 3.11) at
`C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif` — this is the one
actually used for the Aero2/Quanser research (confirmed against hardware).
Contents: `numpy`, `scipy`, `matplotlib`, `jupyter`, `nengo==4.1.*`,
`mujoco==3.11.*`, plus (added **after** step 7 above, once
`Documents\Quanser\0_libraries\python` exists):
- `pip install quanser` (the `quanser` PyPI package, Quanser's Python API —
  confirmed working at version 2025.11.1 against 26.0 HIL drivers)
- `qvl` — not pip-installed; comes from `Documents\Quanser\0_libraries\python`,
  added to `PYTHONPATH` (handled by `configure_python.bat`, or manually:
  `$env:PYTHONPATH += ";C:\Users\gandhico\Documents\Quanser\0_libraries\python"`)

There's also an **older, separate** `uv`-based Python setup under
`D:\NMSU_backups\Backup\02_Research\00_Code_Ecosystem\` (`uv.lock`,
`pyproject.toml`, `.venv`) — this was the Spring '26 code ecosystem for
`adaptive-hyperlif-nengo`, `hyperlif_learning`, `neuromorphic-robotics-control`.
It's superseded by the conda `hyperlif` env for the Aero2 work, but may still
be the right env for those specific older repos if you pull them back in —
check each repo's own `pyproject.toml` before assuming.

**Julia:** referenced in the old scheme
(`00_Research_\Neuromorphic_Embodied_AI\17_Julia_Quanser_Bridge\`) with a
`julia_policy` controller registered in the Aero2 code. Not yet reinstalled
this round — use `juliaup` (the standard installer/version manager), not a
bare Julia installer.

---

## 5. X-Plane

**Not installed on this Windows machine, and never needs to be.** X-Plane 12
runs on a separate Ubuntu lab machine; this machine only edits the Python
integration code (from `Xplane11...` repos under
`D:\NMSU_backups\Backup\00_Research_\_github\Neuromorphic-Embodied-AI\`).
Restore the Python source when needed; skip the simulator entirely.

---

## 6. Dev tools (installed silently, no GUI)

- **Git** — `C:\Quanser_Setup\05_dev_tools\Git-*.exe /VERYSILENT /NORESTART /NOCANCEL /SP- /SUPPRESSMSGBOXES`
- **Miniconda3** — `C:\Quanser_Setup\05_dev_tools\Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /S /D=C:\Users\gandhico\AppData\Local\miniconda3`
  - First `conda create` will fail with a ToS error on `pkgs/main` / `pkgs/r` /
    `pkgs/msys2` — run `conda tos accept --override-channels --channel <url>`
    for each, then retry. One-time per machine.
- **VS Code** — was already present on this machine's image (installed via
  the org's standard build). Check with `Get-Command code` before reinstalling.

---

## 7. Sandbox / tooling gotchas (this session, Claude Code on Windows)

- **`Remove-Item` on a top-level `C:\` folder is blocked** by the coding
  agent's sandbox, even for empty folders you just created yourself. Work
  around it with `Move-Item` (rename/relocate) instead of deleting — or just
  leave empty stray folders and clean them up by hand in Explorer.
- **`Move-Item` with a wildcard source to a not-yet-existing destination
  directory can flatten one level of nesting** (the first matched item's
  *contents* can end up merged into the destination instead of nested one
  level down). Always `New-Item -ItemType Directory` the destination **first**,
  then `Move-Item` into it, and verify the resulting structure before moving on.
- PowerShell commands that take a while (installers, `conda`/`pip`, big
  recursive `Get-ChildItem`) routinely exceed the tool's 120s foreground
  timeout and get moved to a background task — that's normal, not a failure;
  poll the task output instead of re-running the command.
- Writing files directly to a drive root (`C:\foo.md`) is also blocked —
  write inside an existing subfolder instead.
- **Don't run multiple `.exe`/MSI-based installers at the exact same moment.**
  Running QUARC + QLabs + Quartus Lite in parallel caused the Python 3.13
  installer to fail with `0x80070652` (`ERROR_INSTALL_ALREADY_RUNNING` — only
  one Windows Installer transaction can run system-wide at a time). Fix: check
  `Get-Process msiexec` is empty before launching another MSI-based installer,
  or just retry after a failure — it usually succeeds once the mutex frees up.
- **A GUI installer that stays "Responding" for a very long time with no
  install files on disk yet is very likely parked on a dialog** (license
  agreement, component selection, install path) waiting for a click, not
  actually hung or downloading. Quartus Lite 25 sat like this for 2+ hours —
  check the window instead of assuming it's still working.

---

## 8. Sensitive files — handle, don't repeat

- `C:\Research\_misc\wiscom\ID_wiscom.txt` — campus wifi credentials
  (username `gcontreras`). Restored from backup; don't echo its contents
  into logs, chat transcripts, or anywhere that leaves the machine.
- `C:\Quanser_Setup\*.qlic` — QUARC license files tied to NMSU Lab Job#13488.
  Don't redistribute outside the lab per Quanser's license terms.

---

## 9. Status as of 2026-08-18 (end of setup session)

Done:
- [x] MATLAB R2025a, QUARC 2026 (full, not just Runtime), Quanser Interactive Labs
      2.25.5256, Quartus Prime Lite 25.1 — all installed and confirmed working.
- [x] Git, Miniconda3, Julia (juliaup 1.12.7), standalone Python 3.13.11.
- [x] `hyperlif` conda env (Python 3.11): numpy, scipy, matplotlib, jupyter,
      nengo==4.1, mujoco==3.11, **torch==2.5.1+cu121 (CUDA confirmed working —
      RTX A500 Laptop GPU, 4GB)**.
- [x] Academic Resources at `Documents\Quanser` (extracted from
      `Quanser_Setup\06_resources`), plus `configure_matlab.bat` /
      `configure_python.bat` / `step_1_check_requirements.bat` copied in from a
      fresh `git clone` of `quanser/Quanser_Academic_Resources` (dev-windows) —
      the staged zip didn't include these scripts, only example content.
- [x] `C:\Teaching\VHDL\` — clean short paths to all VHDL labs (Lab 0–13 +
      Libraries), copied out from the deeply-nested Spring course export at
      `VHDL_Lab_Fall_2026\old\...`. Lab 0 has a working Quartus project to
      sanity-check the Quartus install.
- [x] `C:\Research\papers\` — HyperLIF paper portfolio organized: see
      `papers\README.md`. P1 frozen, P2 85%, P3 still needs its two-source
      fusion (documented in `papers\_planning\P3_FUSION_PLAN_2026_07_20.md`).

Still open:
- [x] **QUARC license activation** — DONE 2026-08-18. `quanser_license_registration.exe`
      is a GUI/MSI-style tool with an undocumented CLI: `-f <license file> <PRODUCT>`
      (product name required, e.g. `QUARC`, `QLABS`). Ran elevated via a small
      `.bat` wrapper (`C:\Quanser_Setup\register_license.bat`) since `Start-Process
      -Verb RunAs` can't combine with `-RedirectStandardOutput` directly. Used the
      **Complete** `.qlic` (max version 29.x) not Essentials (max version 25.x) —
      QUARC 2026 reports as version 26.0.5256, which only Complete covers.
      Registry confirms: `HKLM:\SOFTWARE\Quanser\Quanser License Manager` →
      `LicenseSourceFile = C:\Quanser_Setup\13488_QUARC_Complete_....qlic`.
      `step_1_check_requirements.bat` now reports QUARC=1/QSDK=1/QLabs=1 (was 0/0).
      Note: the earlier attempt failed only because of a typo —
      `quarc_license_registration.exe` vs. the real name
      `quanser_license_registration.exe`.
- [ ] **Windows restart** — still needed. `configure_matlab.bat`/`configure_python.bat`
      run right after the license fix still report QUARC/QSDK "Not Installed" even
      though `step_1_check_requirements` (a separate check) sees them — the
      `QUARC_DIR`/`QSDK_DIR` env vars written moments ago haven't propagated to
      new processes yet. Restart, then re-run `configure_matlab.bat` →
      `configure_python.bat` in that order.
- [ ] `pip install quanser` + add `Documents\Quanser\0_libraries\python` to
      `PYTHONPATH` inside the `hyperlif` conda env specifically (separate from
      the standalone-Python `configure_python.bat` step above) — this is the
      env the actual Aero2 research runs in, per `WORKFLOW.md`.
- [x] **Julia bridge pulled forward — 2026-08-21.** `17_Julia_Quanser_Bridge`
      copied to `C:\Research\julia_bridge\` (generic 14-board `QuanserHIL.jl`
      registry + Aero2 twin-PD-loop + all four Pendulum Julia scripts — see
      `pendulum\RUNNERS.md` §4, `aero2\launchers_runners.md` §6). No external
      packages needed (stdlib `ccall` only); `julia_env` project still has an
      empty `Manifest.toml` and that's fine.
- [ ] Reassemble/restore `hyperlif_replication.zip` and `mujoco_chunks\*.partNN`
      wherever the current research code expects its datasets.
- [ ] Decide whether to pull any of the older `02_Research\00_Code_Ecosystem`
      (uv-based) repos back in, or treat them as archived.
- [ ] Delete the 5 empty leftover folders from the retired old scheme
      (`00_Research_`, `02_Research`, `04_programs`, `Quanser`, `QuanserLicense`)
      manually in Explorer — the sandbox won't let the agent do it.
