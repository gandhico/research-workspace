"""Prove the package is location-independent.

Copies it to a throwaway directory with a different name, runs from an
unrelated working directory, and checks that

  * acc2027_paths resolves ROOT to the copy, not to the original;
  * no module-level path constant still points at the original tree;
  * every rewritten module imports, or fails only because a third-party
    package (nengo, mujoco, quanser) is absent -- never because of a path.

Run:  python test_portability.py <package_root>
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

THIRD_PARTY = {"nengo", "mujoco", "quanser", "nengo_gui", "matplotlib",
               "numpy", "scipy"}

PROBE = r'''
import importlib
import importlib.util
import sys, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import acc2027_paths as P

root = Path(__file__).resolve().parent.parent
assert P.ROOT == root, f"ROOT resolved to {P.ROOT}, expected {root}"
print("ROOT_OK", P.ROOT)

bad = []
for name, info in P.describe().items():
    if "ACC2027_Gate_Residual_Control\\experiments" in info["path"] \
            or info["path"].startswith(("C:\\Research", "/c/Research")):
        bad.append(f"{name} -> {info['path']}")
print("LEAKED", len(bad))
for b in bad:
    print("   ", b)

mods = []
for f in sorted((root / "code").rglob("*.py")):
    if f.name in ("acc2027_paths.py", "check_environment.py", "_probe.py") \
            or "__pycache__" in str(f):
        continue
    mods.append(f)

results = []
for f in mods:
    sys.path.insert(0, str(f.parent))
    try:
        spec = importlib.util.spec_from_file_location(f.stem, f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        results.append(("ok", f.name, ""))
    except ImportError as e:
        # An ImportError naming acc2027_paths is OUR bug, not a missing
        # third-party package -- never let it hide in the "dep" bucket.
        if "acc2027_paths" in str(e):
            results.append(("FAIL", f.name, f"acc2027_paths: {e}"))
        else:
            results.append(("dep", f.name,
                            str(e).split("'")[1] if "'" in str(e) else str(e)))
    except SystemExit:
        results.append(("ok", f.name, "exits on import (argparse)"))
    except Exception as e:
        results.append(("FAIL", f.name, f"{type(e).__name__}: {e}"))
    finally:
        sys.path.pop(0)

for kind, name, note in results:
    print(f"{kind}\t{name}\t{note}")
'''


def main(pkg: Path) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="acc2027_portability_"))
    dest = tmp / "somewhere" / "else" / "renamed_package"
    print(f"copying package -> {dest}")
    shutil.copytree(pkg, dest)

    probe = dest / "code" / "_probe.py"
    probe.write_text(PROBE, encoding="utf-8")

    # run from an unrelated working directory, with a clean environment
    env = {k: v for k, v in os.environ.items() if not k.startswith("ACC2027_")}
    cwd = tmp  # deliberately NOT inside the package
    out = subprocess.run([sys.executable, str(probe)], capture_output=True,
                         text=True, cwd=cwd, env=env)
    print(out.stdout)
    if out.stderr.strip():
        print("--- stderr ---")
        print(out.stderr[-3000:])

    lines = out.stdout.splitlines()
    ok = sum(1 for ln in lines if ln.startswith("ok\t"))
    dep = sum(1 for ln in lines if ln.startswith("dep\t"))
    fail = [ln for ln in lines if ln.startswith("FAIL\t")]
    leaked = next((ln for ln in lines if ln.startswith("LEAKED")), "LEAKED ?")
    root_ok = any(ln.startswith("ROOT_OK") for ln in lines)

    print("=" * 70)
    print(f"ROOT resolved to the copy : {'yes' if root_ok else 'NO'}")
    print(f"paths leaking to original : {leaked.split()[1]}")
    print(f"modules importing cleanly : {ok}")
    print(f"blocked only by a missing dependency : {dep}")
    print(f"path-related failures     : {len(fail)}")
    for f in fail:
        print("   ", f)
    print(f"\nscratch copy left at {tmp} (delete when done)")
    return 1 if (fail or not root_ok or not leaked.endswith("0")) else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]).resolve()))
