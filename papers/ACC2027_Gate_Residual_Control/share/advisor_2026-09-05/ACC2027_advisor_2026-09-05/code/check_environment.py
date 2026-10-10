"""Run this first. It tells you what will and will not work on this machine.

    python code/check_environment.py

Nothing here touches hardware or writes to the package.
"""
from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import acc2027_paths as P  # noqa: E402

OK, NO, WARN = "  ok  ", " MISS ", " warn "

REQUIRED = [("numpy", "arrays"), ("matplotlib", "figures")]
OPTIONAL = [
    ("nengo", "the Nengo/NEF realization and the neuron-family benchmark"),
    ("mujoco", "re-running the simulation missions"),
    ("quanser", "the physical 3DOF Hover rig (lab machine only)"),
]


def line(mark: str, name: str, note: str = "") -> None:
    print(f"[{mark}] {name:<34} {note}")


def main() -> int:
    print("=" * 74)
    print("ACC 2027 package -- environment check")
    print("=" * 74)
    print(f"python   {sys.version.split()[0]}  ({platform.python_implementation()})")
    print(f"platform {platform.system()} {platform.release()}  {platform.machine()}")
    print(f"package  {P.ROOT}")
    print()

    fatal = 0

    print("-- python packages ------------------------------------------------")
    for mod, why in REQUIRED:
        try:
            m = importlib.import_module(mod)
            line(OK, mod, getattr(m, "__version__", ""))
        except ImportError:
            line(NO, mod, f"REQUIRED for {why}  ->  pip install {mod}")
            fatal += 1
    for mod, why in OPTIONAL:
        try:
            m = importlib.import_module(mod)
            line(OK, mod, getattr(m, "__version__", ""))
        except ImportError:
            line(WARN, mod, f"optional; needed for {why}")
    print()

    print("-- shipped content ------------------------------------------------")
    shipped = ["CODE", "DATA", "FIGURES", "PAPER", "TABLES", "TRACES_MUJOCO",
               "TRACES_HOVER", "RUN_SUMMARIES", "LEGACY_P3"]
    for name in shipped:
        p = getattr(P, name)
        n = len(list(p.rglob("*"))) if p.is_dir() else 0
        if p.exists():
            line(OK, name, f"{n} entries")
        else:
            line(NO, name, str(p))
            fatal += 1
    print()

    print("-- optional external trees (set the env var to enable) ------------")
    for name, env in [("HOVER_RESULTS", "ACC2027_HOVER_RESULTS"),
                      ("MUJOCO_RESULTS", "ACC2027_MUJOCO_RESULTS"),
                      ("LAB_ROOT", "ACC2027_LAB_ROOT")]:
        p = getattr(P, name)
        line(OK if p.exists() else WARN, name,
             str(p) if p.exists() else f"not present; set {env} to use it")
    print()

    print("-- output ---------------------------------------------------------")
    line(OK, "OUTPUT", f"{P.OUTPUT}  (created on demand)")
    print()

    print("-- what runs here -------------------------------------------------")
    have_np = all(importlib.util.find_spec(m) for m, _ in REQUIRED)
    have_mj = importlib.util.find_spec("mujoco") is not None
    have_ng = importlib.util.find_spec("nengo") is not None
    rows = [
        ("read the shipped tables and 50 Hz traces", have_np),
        ("re-plot from the shipped traces", have_np),
        ("reproduce the annealed-trace study", have_np and have_mj),
        ("re-run the MuJoCo five-mission matrix", have_np and have_mj),
        ("re-run the Nengo neuron-family benchmark", have_np and have_mj and have_ng),
        ("campaign-wide hardware audits", P.HOVER_RESULTS.exists()),
        ("drive the physical 3DOF Hover rig",
         importlib.util.find_spec("quanser") is not None),
    ]
    for what, ready in rows:
        line(OK if ready else WARN, what, "" if ready else "not available here")

    print()
    if fatal:
        print(f"{fatal} blocking problem(s). Install the required packages, or "
              "check that the package was extracted intact.")
    else:
        print("No blocking problems.")
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main())
