"""Aero2 digital-twin controller benchmark campaign (Python, QLabs).

Runs each registered controller closed-loop on the QLabs Aero2 **digital twin**
(reference tracking), saves a standard record per run, and writes a comparison
table (CSV + Markdown) for the ToE paper. Also runs PD at a reduced rate to
rate-match the MATLAB-via-bridge cross-platform point.

PRECONDITION: QLabs Aero2 open on localhost:18950, in the **helicopter 2DOF**
configuration (NOT half-rotor) so the twin matches `model_variant=helicopter_2dof`.

Run:  conda run -n hyperlif python C:\\Research\\aero2\\campaigns\\run_twin_campaign.py
"""
from __future__ import annotations

import csv
import os
import sys
import time
import traceback
from datetime import datetime

REPO = r"C:\Research\aero2"
QPY = r"C:\Users\gandhico\Documents\Quanser\0_libraries\python"
os.environ.setdefault("QUANSER_PYTHON", QPY)
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "runners"))

import numpy as np  # noqa: E402
import run_control as rc  # noqa: E402

OUT = os.path.join(REPO, "results_twin_campaign")
os.makedirs(OUT, exist_ok=True)

DUR = 18.0
# (controller_key, target_hz). julia_policy skipped (needs Julia bridge).
RUNS = [
    ("pd", 200.0), ("lqr", 200.0), ("lqg", 200.0), ("mpc", 200.0),
    ("backstepping", 200.0), ("smc", 200.0), ("nmpc", 200.0), ("hyperlif", 200.0),
    ("pd", 85.0),  # cross-platform rate-match vs MATLAB bridge
]

rows = []
for i, (ctrl, hz) in enumerate(RUNS, 1):
    tag = f"{ctrl}@{int(hz)}Hz"
    print(f"[{i}/{len(RUNS)}] {tag} ...", flush=True)
    cfg = dict(
        execution_mode="virtual_twin", model_variant="helicopter_2dof",
        controller=ctrl, application="reference_tracking",
        duration_s=DUR, hz=hz, estimator="passthrough", out="results_twin_campaign",
    )
    try:
        rec, m = rc.run(cfg)
        t = np.asarray(rec.t, dtype=float)
        realized = (len(t) - 1) / (t[-1] - t[0]) if len(t) > 1 else 0.0
        row = {"controller": ctrl, "target_hz": hz, "realized_hz": round(realized, 1)}
        for k, v in m.items():
            try:
                row[k] = round(float(v), 4)
            except (TypeError, ValueError):
                pass
        rc.save_record(rec, m, cfg)
        rows.append(row)
        print("   ok:", row, flush=True)
    except Exception as e:  # keep the campaign going
        print("   FAIL:", repr(e), flush=True)
        traceback.print_exc()
        rows.append({"controller": ctrl, "target_hz": hz, "error": str(e)})
    time.sleep(0.6)  # brief settle between controllers

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
keys = ["controller", "target_hz", "realized_hz"] + sorted(
    {k for r in rows for k in r} - {"controller", "target_hz", "realized_hz"}
)
csv_path = os.path.join(OUT, f"campaign_summary_{stamp}.csv")
with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)

md_path = os.path.join(OUT, f"campaign_summary_{stamp}.md")
with open(md_path, "w") as f:
    f.write(f"# Aero2 digital-twin controller benchmark ({stamp})\n\n")
    f.write("Config: QLabs Aero2 **helicopter 2DOF**, reference tracking "
            "(theta +/-20 deg @0.05 Hz, psi +/-45 deg @0.04 Hz), 18 s.\n\n")
    f.write("| " + " | ".join(keys) + " |\n")
    f.write("|" + "|".join(["---"] * len(keys)) + "|\n")
    for r in rows:
        f.write("| " + " | ".join(str(r.get(c, "")) for c in keys) + " |\n")

print("SUMMARY CSV:", csv_path)
print("SUMMARY MD :", md_path)
print("CAMPAIGN DONE")
