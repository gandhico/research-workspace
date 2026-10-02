"""Write a SHA256 manifest of P5 code, docs and results for a freeze.

Run:  python tools/freeze_manifest.py FREEZE_ID
Writes results/FREEZE_<FREEZE_ID>/MANIFEST_SHA256.txt (sha256  size  relative path) and freeze.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

P5 = Path(__file__).resolve().parents[1]
ACC = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control")
PATTERNS = ("README.md", "docs/*.md", "experiments/**/*.py", "experiments/**/*.md", "experiments/**/*.log",
            "results/**/*.json", "results/**/*.csv", "results/**/*.md", "results/**/*.png", "results/**/*.pdf")
ACC_DEPS = ("src/gra_control/gate.py", "src/gra_control/math3d.py", "src/gra_control/platforms/drone.py",
            "experiments/six_dof_expansion_2026-08-31/run_6dof_cascade_ff.py",
            "experiments/six_dof_expansion_2026-08-31/run_6dof_wrench.py")


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    fid = sys.argv[1]
    out = P5 / "results" / f"FREEZE_{fid}"
    out.mkdir(parents=True, exist_ok=True)
    files = sorted({f for pat in PATTERNS for f in P5.glob(pat) if f.is_file() and out not in f.parents})
    lines = [f"{digest(f)}  {f.stat().st_size:>10}  {f.relative_to(P5).as_posix()}" for f in files]
    lines += [f"{digest(ACC / d)}  {(ACC / d).stat().st_size:>10}  ACC2027/{d}" for d in ACC_DEPS]
    (out / "MANIFEST_SHA256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    man = digest(out / "MANIFEST_SHA256.txt")
    meta = {"freeze_id": fid, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": len(lines), "manifest_sha256": man}
    (out / "freeze.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
