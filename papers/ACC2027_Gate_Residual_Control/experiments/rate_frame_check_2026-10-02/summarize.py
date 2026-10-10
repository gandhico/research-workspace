"""Published (omega - omega_d) vs frame-aligned (omega - R(q_e)^T omega_d) baseline, primary cells. Writes SUMMARY.md/json."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = ["roll", "full3", "hard45", "hardstep", "yaw360"]
gm = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
red = lambda b, c: 100 * (1 - c / b)
out, lines = {}, ["| platform | mission | PD+ff published (mrad) | PD+ff frame-aligned | change | reduction published | reduction frame-aligned |",
                  "|---|---|---|---|---|---|---|"]
for p in ("x2", "cf2"):
    r = {(m, a): json.loads((HERE / "results" / f"{p}_{m}_{a}" / "frame_check.json").read_text()) for m in M for a in ("pdff", "cmg")}
    pub = {k: v["published_mean_rad"] for k, v in r.items()}
    new = {k: v["frame_aligned_mean_rad"] for k, v in r.items()}
    for m in M:
        bp, bn, cp, cn = pub[(m, "pdff")], new[(m, "pdff")], pub[(m, "cmg")], new[(m, "cmg")]
        lines.append(f"| {p} | {m} | {1e3*bp:.4f} | {1e3*bn:.4f} | {100*(bn/bp-1):+.2f} % | {red(bp, cp):.1f} % | {red(bn, cn):.1f} % |")
    gb = lambda d, a: gm([d[(m, a)] for m in M])
    out[p] = dict(geo_red_published=red(gb(pub, "pdff"), gb(pub, "cmg")), geo_red_frame_aligned=red(gb(new, "pdff"), gb(new, "cmg")),
                  geo_baseline_change_pct=100 * (gb(new, "pdff") / gb(pub, "pdff") - 1))
    lines.append(f"| **{p}** | **5-mission (geo)** | {1e3*gb(pub,'pdff'):.3f} | {1e3*gb(new,'pdff'):.3f} | {out[p]['geo_baseline_change_pct']:+.2f} % | "
                 f"**{out[p]['geo_red_published']:.1f} %** | **{out[p]['geo_red_frame_aligned']:.1f} %** |")
(HERE / "SUMMARY.json").write_text(json.dumps(out, indent=1))
(HERE / "SUMMARY.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
