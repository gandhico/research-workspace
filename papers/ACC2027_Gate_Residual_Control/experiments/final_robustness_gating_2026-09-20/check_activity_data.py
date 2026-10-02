import csv
from pathlib import Path

BASE = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\final_robustness_gating_2026-09-20\results\a5_controllers\backstepping\x2")

for m in ("roll", "hard45", "hardstep"):
    with open(BASE / m / "nengo-nef-pes" / "trace.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    acols = [f"activity_{i}" for i in range(6)]
    vals = {c: [float(r[c]) for r in rows] for c in acols}
    print(f"\n{m}:")
    for c in acols:
        v = vals[c]
        print(f"  {c}: min={min(v):.4f} max={max(v):.4f} mean={sum(v)/len(v):.4f}")
    print("  ref_roll range:", min(float(r["ref_roll"]) for r in rows), max(float(r["ref_roll"]) for r in rows))
