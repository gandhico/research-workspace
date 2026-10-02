# Environments — Python / Julia / MATLAB / C++

Which tool to use for what, and how to activate it. Written 2026-08-18 so setup doesn't
need rediscovering on the next rented-laptop rebuild (see `SETUP.md`).

## Python — one environment for everything research-related

**`hyperlif` conda env (Python 3.11)** is the only Python environment you need to activate
for HyperLIF research work — PyTorch (P1), Nengo (P2), MuJoCo (P3), and now Quanser hardware
access (aero2) all live here together, so there's no environment-juggling mid-experiment.

```powershell
# conda.exe isn't on PATH (silent install used /RegisterPython=0) — call it directly, or:
& C:\Users\gandhico\AppData\Local\miniconda3\Scripts\conda.exe activate hyperlif
```

Contents: numpy, scipy, matplotlib, jupyter, `nengo==4.1.*`, `mujoco==3.11.*`,
`torch==2.5.1+cu121` (**GPU/CUDA confirmed working** — RTX A500 Laptop), and as of tonight
`quanser`/`quanser-api` (installed from the local QUARC SDK wheel — this package is **not**
on public PyPI; if reinstalling on a future rebuild, use
`pip install --find-links "C:\Program Files\Quanser\QUARC\python" "C:\Program Files\Quanser\QUARC\python\quanser_api-<version>-py2.py3-none-any.whl"`,
not a plain `pip install quanser`, which will fail with no matching distribution).

`qvl` (Quanser Interactive Labs bindings) isn't pip-installed — it comes from
`Documents\Quanser\0_libraries\python` via `PYTHONPATH`:
```powershell
$env:PYTHONPATH += ";C:\Users\gandhico\Documents\Quanser\0_libraries\python"
```

**Standalone Python 3.13** (separate install) exists only for Quanser's own
`configure_python.bat`/install-time scripts. Don't use it for research work — everything
research-related goes in `hyperlif`.

## Julia — shared project at `C:\Research\julia_env`

One shared environment for all research Julia work, rather than a project-less ad hoc
`.julia` install:

```powershell
julia --project=C:\Research\julia_env
# or, inside a script/session:
# import Pkg; Pkg.activate("C:\\Research\\julia_env")
```

Currently no external packages — every Julia script in the tree (`aero2\julia\*.jl`,
`C:\Research\julia_bridge\julia\*.jl`,
`papers\P3_Gate_Residual\quaternion_quad\paper_ode_replication.jl`) only uses stdlib
(`LinearAlgebra`, `Printf`, `Statistics`, `Libdl`) via direct `ccall` into `hil.dll`. Add
packages with `Pkg.activate("C:\\Research\\julia_env"); Pkg.add("PackageName")` as needed —
they'll be tracked in this project's `Project.toml`/`Manifest.toml`, not scattered per-script.

**`C:\Research\julia_bridge\`** (pulled forward from the backup drive 2026-08-21) is the
real cross-platform Julia⇄Quanser bridge — a generic 14-board `ccall` registry
(`QuanserHIL.jl`) plus platform scripts for **Aero2** (`aero2_twin_pd_loop.jl`, V3-proven
closed loop) and **Pendulum** (`qube3_twin_equilibrium.jl`, `qube3_twin_swingup_balance.jl`,
`calib_qube.jl`, `diag_qube_start.jl` — the only Julia-Pendulum code that exists anywhere).
This was the single biggest concrete gap flagged in the 2026-08-18 setup session; see
`pendulum\RUNNERS.md` §4 and `aero2\launchers_runners.md` §6 for exact commands per
platform. QCar has no Julia path.

## MATLAB — R2025a + QUARC

Standard system install, no project-specific setup needed. Aero2's MATLAB↔twin bridge:
```powershell
matlab -sd C:\Research\aero2\matlab -batch "aero2_twin_pd(15,100)"
```

## C/C++ — MinGW-w64 (WinLibs POSIX/UCRT build)

Installed tonight via `winget install BrechtSanders.WinLibs.POSIX.UCRT`. `gcc`/`g++`/`gdb`/
`make` are directly on PATH, no prefix needed:
```powershell
gcc --version   # MinGW-W64 x86_64-ucrt-posix-seh, gcc 16.1.0
```

**This is separate from `C:\GW`** — that's a different MinGW/GCC toolchain bundled with
Quartus Prime Lite specifically for Nios-II embedded targets (TA/VHDL work), not on PATH,
and shouldn't be mixed with general-purpose C/C++ work.

**Known limitation, decide later if it comes up**: PyTorch C++/CUDA extensions on Windows
expect **MSVC**, not MinGW — if you ever write a custom CUDA kernel or C++ extension for
HyperLIF (P1's PyTorch side), MinGW won't work for that specific case and you'd need MSVC
Build Tools (~6-8GB) installed alongside this, not instead of it.

## LaTeX — MiKTeX

Also installed tonight (this machine had **no LaTeX distribution at all** before — none of
P1/P2/P3's `main.tex` files had ever actually been compiled on this machine; only pre-built
PDFs existed). Standard build sequence:
```powershell
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```
MiKTeX installs missing packages on-demand on first use of each one — the very first build
of a new paper may be slower while it fetches packages.
