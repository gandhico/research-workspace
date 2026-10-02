"""Build the `code/` folder of the GitHub release from this repository (copy + filter, never edits a file).

Keeps the repository's relative tree (src/, experiments/<dated study>/, reproduce/, models/, third_party/) so every script
runs unmodified and every file hash still equals the one recorded in the run manifests. Ships code, reports, and the
compact run outputs (summary.json, manifest.json, CSV/JSON/TeX tables); drops per-step traces (*.npz, trace.csv),
logs, caches, smoke runs and recordings. Then runs the claim verifier inside the copy.

    .venv\\Scripts\\python.exe tools\\release\\build_release_code.py <release_root>
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STUDIES = ["nengo_nef_replication_2026-08-29", "theory_certificate_2026-09-12", "baseline_restatement_2026-09-16",
           "final_robustness_gating_2026-09-20", "neuron_basis_decisive_2026-09-24"]   # the studies behind the paper
TOP = ["src", "reproduce", "tools/release", "models/cf2_rotor_design", "third_party/mujoco_menagerie/skydio_x2",
       "third_party/mujoco_menagerie/bitcraze_crazyflie_2"]
KEEP_EXT = {".py", ".md", ".ps1", ".json", ".csv", ".tex", ".txt", ".xml", ".obj", ".stl", ".png", ".cff", ".toml",
            ".yaml", ".yml", ".LICENSE"}
DROP_NAMES = {"trace.csv", "trace_full.csv"}
DROP_PARTS = {"__pycache__", "viewer_runs", "recordings", "_root_smoke_classical", "_root_smoke_nengo_gate", "tmp",
              ".pytest_cache"}
MAX_BYTES = 5_000_000


VERIFIER_TRACES = "experiments/final_robustness_gating_2026-09-20/results_izh_corrected/table2_full_2026-09-29"


def keep(p: Path) -> bool:
    if set(p.parts) & DROP_PARTS:
        return False
    if p.as_posix().startswith(("tools/release/docs", "tools/release/figs")):   # release sources, not release content
        return False
    if p.name in DROP_NAMES:                          # per-step traces live in the data archive (DATA.md)
        return False
    if p.suffix == ".png" and p.parts[0] != "third_party":   # exploratory plots; curated figures live in figures/
        return False
    if p.name == "LICENSE" or p.suffix in KEEP_EXT:
        return p.stat().st_size <= MAX_BYTES
    return False


def main(dst_root: Path):
    code = dst_root / "code"
    if code.exists():
        shutil.rmtree(code)
    files = []
    for rel in TOP + [f"experiments/{s}" for s in STUDIES]:
        base = REPO / rel
        for p in sorted(base.rglob("*")):
            if p.is_file() and keep(p.relative_to(REPO)):
                files.append(p)
    files += [REPO / "pyproject.toml", REPO / "REPRODUCE_ACC2027.md"]
    total = 0
    manifest = {}
    for p in files:
        rel = p.relative_to(REPO)
        q = code / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)
        total += p.stat().st_size
        manifest[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    shutil.copy2(Path(__file__).with_name("docs") / "REPRODUCIBILITY.md", code / "REPRODUCIBILITY.md")
    (code / "RELEASE_MANIFEST.json").write_text(json.dumps({"source_repo_commit_note": "copied from the paper repository",
                                                           "files": manifest}, indent=0))
    print(f"copied {len(files)} files, {total / 1e6:.1f} MB")
    py = sys.executable
    r = subprocess.run([py, str(code / "reproduce" / "verify_acc2027_claims.py")], capture_output=True, text=True,
                       cwd=code)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    print("verifier in the release copy:", *tail, sep="\n  ")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
