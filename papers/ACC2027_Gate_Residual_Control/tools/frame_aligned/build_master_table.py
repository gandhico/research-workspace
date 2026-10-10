"""Sandbox master_table.csv for the frame-aligned re-run (same formulas as build_restatement.build_master).

PD, PID 0.05, CMG|PD, PD+ff rho = 1 and CMG|PD+ff rho = 1 come from the sandbox rate_ff_summary.csv (run_ff_cmg.py).
The PDff_3x columns of the original table came from the superseded 2026-09-10 rho = 3 sweep (baselines_2026-09-10),
which no paper check reads (the paper's rho = 3 rows are final_nominal.csv); they are left blank here, not re-run.
    .venv/Scripts/python.exe tools/frame_aligned/build_master_table.py
"""
import csv

from build_sandbox import SB

A = SB / "experiments" / "nengo_nef_replication_2026-08-29" / "results" / "pid_baseline_2026-09-10" / "rate_ff_summary.csv"
OUT = SB / "experiments" / "baseline_restatement_2026-09-16" / "master_table.csv"
FIELDS = ["platform", "mission", "PD", "PID_005", "CMG_on_PD", "PDff_1x", "CMG_on_PDff_1x", "PDff_3x", "CMG_on_PDff_3x", "beta_sel",
          "sat_PD", "sat_PDff_1x", "sat_CMG_on_PDff_3x", "residual_CMG_on_PD", "residual_CMG_on_PDff_1x", "residual_CMG_on_PDff_3x",
          "ff1x_vs_PD_pct", "tuned_vs_PD_pct", "CMGonPD_vs_PD_pct", "CMGonff1x_vs_ff1x_pct", "CMGonff3x_vs_ff3x_pct", "tuned_over_CMGonPD"]

out = []
for ra in csv.DictReader(A.open(encoding="utf-8")):
    rec = dict.fromkeys(FIELDS, "")
    rec.update(platform=ra["platform"], mission=ra["mission"], PD=float(ra["PD"]), PID_005=float(ra["PID_0.05"]),
               CMG_on_PD=float(ra["CMG_on_PD"]), PDff_1x=float(ra["PD_ff"]), CMG_on_PDff_1x=float(ra["CMG_on_PD_ff"]),
               sat_PD=float(ra["sat_PD"]), sat_PDff_1x=float(ra["sat_PD_ff"]), residual_CMG_on_PD=float(ra["residual_CMG_on_PD"]),
               residual_CMG_on_PDff_1x=float(ra["residual_CMG_on_PD_ff"]))
    rec["ff1x_vs_PD_pct"] = 100 * (1 - rec["PDff_1x"] / rec["PD"])
    rec["CMGonPD_vs_PD_pct"] = 100 * (1 - rec["CMG_on_PD"] / rec["PD"])
    rec["CMGonff1x_vs_ff1x_pct"] = 100 * (1 - rec["CMG_on_PDff_1x"] / rec["PDff_1x"])
    out.append(rec)
assert len(out) == 10, len(out)
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(out)
print("wrote", OUT)
