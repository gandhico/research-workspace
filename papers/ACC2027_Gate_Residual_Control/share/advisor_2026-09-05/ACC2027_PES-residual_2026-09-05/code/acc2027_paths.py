"""Portable path resolution for the ACC 2027 package.

Nothing in this package should contain an absolute path. Every script asks
this module instead, and this module works out where things are from the
location of this file -- so the package runs from any directory, on any
machine, on Windows, macOS or Linux.

Import it like this (the two-line bootstrap works regardless of the
current working directory)::

    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from acc2027_paths import DATA, FIGURES, OUTPUT

Overriding
----------
Every root can be overridden with an environment variable, which is how you
point the analysis scripts at data that is too large to ship:

===========================  =========================================
``ACC2027_ROOT``             the package root (auto-detected otherwise)
``ACC2027_OUT``              where regenerated output is written
``ACC2027_HOVER_PROJECT``    full 3DOF Hover project tree
``ACC2027_HOVER_RESULTS``    its ``results/`` directory (derived if unset)
``ACC2027_MUJOCO_RESULTS``   full MuJoCo results tree
``ACC2027_LAB_ROOT``         the lab machine's research root, for the
                             hardware entry points that are not shipped
===========================  =========================================

Example::

    # Windows
    set ACC2027_HOVER_RESULTS=D:\\archive\\hover3dof\\results
    # macOS / Linux
    export ACC2027_HOVER_RESULTS=/mnt/archive/hover3dof/results
"""
from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "ROOT", "CODE", "DATA", "FIGURES", "PAPER", "OUTPUT",
    "SIX_DOF", "NENGO_NEF", "HOVER_HW", "EPROP", "GRA_CONTROL", "LEGACY_P3",
    "TABLES", "TRACES", "TRACES_MUJOCO", "TRACES_HOVER", "RUN_SUMMARIES",
    "FIG_MISSIONS", "FIG_NEURAL", "FIG_BENCHMARK", "FIG_HOVER",
    "FIG_SIXDOF", "FIG_EPROP",
    "HOVER_PROJECT", "HOVER_RESULTS", "HOVER_FINAL", "MUJOCO_RESULTS",
    "LAB_ROOT",
    "require", "describe", "out_dir",
]

_MARKERS = ("MANIFEST.csv", "README.md")


def _env_path(name: str) -> Path | None:
    """Read an environment variable as a path, treating empty as unset."""
    raw = os.environ.get(name, "").strip()
    return Path(raw).expanduser().resolve() if raw else None


def _find_root(start: Path) -> Path:
    """Walk up from this file until the package root is recognisable."""
    for cand in (start, *start.parents):
        if all((cand / m).is_file() for m in _MARKERS) and (cand / "code").is_dir():
            return cand
    # Fall back to the parent of the directory holding this file (``code/``),
    # which is correct for the shipped layout even without the markers.
    return start.parent if start.name == "code" else start


# --- roots ------------------------------------------------------------------
ROOT: Path = _env_path("ACC2027_ROOT") or _find_root(Path(__file__).resolve().parent)

CODE: Path = ROOT / "code"
DATA: Path = ROOT / "data"
FIGURES: Path = ROOT / "figures"
PAPER: Path = ROOT / "paper"

#: Regenerated output goes here, so the shipped figures are never overwritten.
OUTPUT: Path = _env_path("ACC2027_OUT") or (ROOT / "outputs")

# --- code trees -------------------------------------------------------------
SIX_DOF: Path = CODE / "six_dof_cascade"
NENGO_NEF: Path = CODE / "nengo_nef_replication"
HOVER_HW: Path = CODE / "hover3dof_hardware"
EPROP: Path = CODE / "eprop_anneal"
GRA_CONTROL: Path = CODE / "gra_control"
LEGACY_P3: Path = CODE / "legacy_p3_learned"

# --- shipped data -----------------------------------------------------------
TABLES: Path = DATA / "tables"
TRACES: Path = DATA / "traces_50hz"
TRACES_MUJOCO: Path = TRACES / "mujoco"
TRACES_HOVER: Path = TRACES / "hover3dof"
RUN_SUMMARIES: Path = DATA / "run_summaries"

# --- shipped figures --------------------------------------------------------
FIG_MISSIONS: Path = FIGURES / "01_mujoco_missions"
FIG_NEURAL: Path = FIGURES / "02_neural_activity"
FIG_BENCHMARK: Path = FIGURES / "03_nengo_neuron_benchmark"
FIG_HOVER: Path = FIGURES / "04_hover3dof_hardware"
FIG_SIXDOF: Path = FIGURES / "05_six_dof_cascade"
FIG_EPROP: Path = FIGURES / "06_eprop_anneal"

# --- large trees that are NOT shipped ---------------------------------------
# These default to the shipped data so scripts import cleanly. Point the
# environment variable at the full archive to run the campaign-wide scripts.
#: The ``nengo_gui_hil_2026-08-29`` project tree from the lab machine.
HOVER_PROJECT: Path = (_env_path("ACC2027_HOVER_PROJECT")
                       or (DATA / "_hover_project_not_shipped"))
HOVER_RESULTS: Path = _env_path("ACC2027_HOVER_RESULTS") or (HOVER_PROJECT / "results")
HOVER_FINAL: Path = HOVER_RESULTS / "DIRECT_NENGO_FINAL_2026-09-01"
MUJOCO_RESULTS: Path = (_env_path("ACC2027_MUJOCO_RESULTS")
                        or (DATA / "_mujoco_results_not_shipped"))

#: The lab machine's research root. Only the hardware entry points need it,
#: and they degrade to ``exists: False`` rather than failing when it is unset.
LAB_ROOT: Path = _env_path("ACC2027_LAB_ROOT") or (ROOT / "_not_present")


# --- helpers ----------------------------------------------------------------
def require(path: Path, what: str, env_var: str | None = None) -> Path:
    """Return ``path``, or raise with an instruction the reader can act on."""
    if path.exists():
        return path
    msg = f"{what} not found at:\n    {path}"
    if env_var:
        msg += (f"\n\nThis tree is too large to ship. Point {env_var} at your "
                f"copy, for example:\n"
                f"    Windows      set {env_var}=D:\\archive\\...\n"
                f"    macOS/Linux  export {env_var}=/mnt/archive/...")
    raise FileNotFoundError(msg)


def out_dir(*parts: str) -> Path:
    """Create and return a subdirectory of OUTPUT."""
    d = OUTPUT.joinpath(*parts)
    d.mkdir(parents=True, exist_ok=True)
    return d


def describe() -> dict[str, dict[str, object]]:
    """Every root, where it resolved, and whether it exists."""
    here = globals()
    names = [n for n in __all__ if isinstance(here.get(n), Path)]
    return {n: {"path": str(here[n]), "exists": here[n].exists()} for n in names}


if __name__ == "__main__":
    width = max(len(k) for k in describe())
    for name, info in describe().items():
        mark = "ok " if info["exists"] else "-- "
        print(f"{mark} {name:<{width}}  {info['path']}")
