"""Generate a verifiable index of the CMG-PES research session, 2026-09-01.

Two things, both read-only, no simulation/hardware touched:
1. SHA256 of every canonical/architecture file, so a later session can
   detect whether any of the math/control-law files changed since this
   report was written (compare against research_index.json's "canonical"
   section).
2. A flat table of every experiment result directory found under the
   known result roots, with its config (read from summary.json where
   present) and headline error/improvement numbers -- one row per run,
   so every number in RESEARCH_SESSION_FINAL_REPORT_2026-09-01.md can be
   traced back to the exact file it came from.

Usage:
    python generate_research_index.py [--out research_index.json] [--csv research_index.csv]

Re-run any time to get a fresh, current snapshot; diff two runs to see
what changed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

CANONICAL_FILES = [
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\gate.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\math3d.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\src\gra_control\platforms\drone.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\nengo_cmg.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29\nengo_neuron_family.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\run_6dof_wrench.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\run_6dof_cascade.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\run_6dof_cascade_nengo.py",
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\nengo_neuron_family_6dof.py",
    r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\hover_nengo_hil_gui.py",
    r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\launch_hover_nengo_gui.py",
    r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\run_hover_direct_nengo.py",
    r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\run_hover_headless.py",
]

# Each root is searched for summary.json (MuJoCo/Nengo campaigns) or
# nested run_dir/summary.json (Hover hardware, one level deeper).
RESULT_ROOTS = [
    r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\six_dof_expansion_2026-08-31\results",
    r"C:\Research\hover3dof\nengo_gui_hil_2026-08-29\results",
]


def sha256_of(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def index_canonical() -> list[dict]:
    rows = []
    for p in CANONICAL_FILES:
        path = Path(p)
        rows.append({
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_of(path),
            "size_bytes": path.stat().st_size if path.exists() else None,
        })
    return rows


def index_results() -> list[dict]:
    rows = []
    for root_str in RESULT_ROOTS:
        root = Path(root_str)
        if not root.exists():
            continue
        for summary_path in root.rglob("summary.json"):
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            config = data.get("config", {})
            row = {
                "summary_path": str(summary_path),
                "run_dir": str(summary_path.parent),
                "platform": data.get("platform"),
                "controller": data.get("controller") or config.get("controller"),
                "mission": data.get("mission") or config.get("mission"),
                "hardware": data.get("hardware"),
                "run_completed": data.get("run_completed"),
                "abort_reason": data.get("abort_reason"),
                "angle_err_mean_deg": data.get("angle_err_mean_deg"),
                "angle_err_max_deg": data.get("angle_err_max_deg"),
                "pos_err_mean_m": data.get("pos_err_mean_m"),
                "qerr_mean_rad": data.get("qerr_mean_rad"),
                "reference_scale": config.get("reference_scale"),
                "duration": data.get("duration") or config.get("duration"),
                "beta": config.get("beta"),
                "armed": config.get("armed"),
                "io_mode": config.get("io_mode"),
            }
            rows.append(row)
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("research_index.json"))
    p.add_argument("--csv", type=Path, default=Path("research_index.csv"))
    a = p.parse_args()

    canonical = index_canonical()
    results = index_results()

    manifest = {
        "generated_by": "generate_research_index.py",
        "canonical_files": canonical,
        "n_result_runs_found": len(results),
        "result_runs": results,
    }
    a.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {a.out}  ({len(canonical)} canonical files, {len(results)} result runs)")

    missing = [c["path"] for c in canonical if not c["exists"]]
    if missing:
        print("WARNING -- canonical files not found:")
        for m in missing:
            print(f"  {m}")

    if results:
        fieldnames = list(results[0].keys())
        with a.csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"wrote {a.csv}  ({len(results)} rows, open in Excel/grep freely)")


if __name__ == "__main__":
    main()
