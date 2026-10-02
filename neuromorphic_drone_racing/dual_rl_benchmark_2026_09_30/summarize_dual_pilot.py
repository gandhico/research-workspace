"""Apply PREREGISTRATION.md's decision rule to the dual pilot and write results/pilot_analysis/{comparison.csv,.md}."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
OUT = R / "pilot_analysis"
OUT.mkdir(parents=True, exist_ok=True)

base = {s: json.loads((R / "baseline_x2" / f"eval_{s}.json").read_text()) for s in ("gust", "nominal")}
rows = [dict(arm="baseline", feature="-", **{f"{s}_{k}": base[s][k] for s in base
                                             for k in ("mean_position_error_m", "max_position_error_m", "gates",
                                                       "collisions", "mean_saturation")},
             gust_change_pct=0.0, nominal_change_pct=0.0, action_rms_gust=0.0, gain_range_gust="1.00-1.00",
             candidate="-")]
for arm in ("self", "residual", "dual"):
    for feat in ("mlp", "graded"):
        f = R / f"pilot_x2_{arm}_{feat}_seed1" / "summary.json"
        if not f.exists():
            continue
        ev = json.loads(f.read_text())["evaluation"]
        ch = {s: 100 * (ev[s]["mean_position_error_m"] / base[s]["mean_position_error_m"] - 1) for s in ev}
        ok = (ch["gust"] <= -5 and ev["gust"]["gates"] >= base["gust"]["gates"] and ev["gust"]["collisions"] == 0
              and ch["nominal"] <= 5)
        rows.append(dict(arm=arm, feature=feat,
                         **{f"{s}_{k}": ev[s][k] for s in ev for k in ("mean_position_error_m", "max_position_error_m",
                                                                       "gates", "collisions", "mean_saturation")},
                         gust_change_pct=ch["gust"], nominal_change_pct=ch["nominal"],
                         action_rms_gust=ev["gust"]["action_rms"],
                         gain_range_gust=f"{ev['gust']['gain_min']:.2f}-{ev['gust']['gain_max']:.2f}",
                         candidate="yes" if ok else "no"))
with (OUT / "comparison.csv").open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
md = ["| Arm | Feature | Gust mean err (m) | Gust change | Gust gates / coll. | Nominal mean err (m) | Nominal change | "
      "Action RMS | Gain range | Candidate |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
for r in rows:
    md.append(f"| {r['arm']} | {r['feature']} | {r['gust_mean_position_error_m']:.4f} | {r['gust_change_pct']:+.1f}% | "
              f"{r['gust_gates']} / {r['gust_collisions']} | {r['nominal_mean_position_error_m']:.4f} | "
              f"{r['nominal_change_pct']:+.1f}% | {r['action_rms_gust']:.3f} | {r['gain_range_gust']} | {r['candidate']} |")
(OUT / "comparison.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
