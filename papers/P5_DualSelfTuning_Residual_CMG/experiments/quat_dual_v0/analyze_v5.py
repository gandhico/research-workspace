"""v5 analysis: does self-tuning S generalize beyond PID (E1), and does dual (S+R) beat R alone (E2)?
Reads results/v5_2026-09-25/{family}/{platform}/{mission}/{arm}/summary.json.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent / "results" / "v5_2026-09-25"
FAMILIES = ["lqr", "backstepping", "mpc", "nmpc"]
FULL_MISSIONS = ["roll", "full3", "hard45", "hardstep", "yaw360"]
PILOT_MISSIONS = ["hard45", "roll"]
PLATFORMS = ["x2", "cf2-rotor"]
ARMS = ["base", "res", "st", "dual"]


def qerr(fam, plat, mission, arm):
    p = ROOT / fam / plat / mission / arm / "summary.json"
    return json.loads(p.read_text(encoding="utf-8"))["qerr_mean_rad"]


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


md = ["# v5 results: self-tuning S generalized beyond PID (2026-09-25)\n",
      "Allocation apa throughout (P5's own v3-selected allocation) -- these *_base numbers are a fresh apa "
      "reference, not a re-read of A5's clip-allocation numbers (different allocation scheme; see "
      "dual_controller_v5.py). NMPC: X2-only, Hard45+Roll pilot (cost-driven scope cut, disclosed in the prior "
      "turn); LQR/backstepping/MPC: full 2-platform x 5-mission grid.\n"]

print(f"{'family':14s}{'platform':10s}{'geo base':>10s}{'geo res':>10s}{'geo st':>10s}{'geo dual':>10s}"
      f"{'st/base':>9s}{'dual/res':>10s}{'dual/base':>11s}")

all_rows = {}
for fam in FAMILIES:
    missions = PILOT_MISSIONS if fam == "nmpc" else FULL_MISSIONS
    plats = ["x2"] if fam == "nmpc" else PLATFORMS
    md.append(f"\n## {fam}\n")
    md.append("| platform | mission | base | res (R only) | st (S only) | dual (S+R) | st/base | dual/res | dual/base |")
    md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for plat in plats:
        vals = {a: [] for a in ARMS}
        for m in missions:
            row = {a: qerr(fam, plat, m, a) for a in ARMS}
            for a in ARMS:
                vals[a].append(row[a])
            md.append(f"| {plat} | {m} | {row['base']*1e3:.3f} | {row['res']*1e3:.3f} | {row['st']*1e3:.3f} | "
                      f"{row['dual']*1e3:.3f} | {100*(1-row['st']/row['base']):+.1f}% | "
                      f"{100*(1-row['dual']/row['res']):+.1f}% | {100*(1-row['dual']/row['base']):+.1f}% |")
        g = {a: gm(vals[a]) for a in ARMS}
        st_base = 100 * (1 - g['st'] / g['base'])
        dual_res = 100 * (1 - g['dual'] / g['res'])
        dual_base = 100 * (1 - g['dual'] / g['base'])
        md.append(f"| **{plat}** | **geo** | **{g['base']*1e3:.3f}** | **{g['res']*1e3:.3f}** | "
                  f"**{g['st']*1e3:.3f}** | **{g['dual']*1e3:.3f}** | **{st_base:+.1f}%** | "
                  f"**{dual_res:+.1f}%** | **{dual_base:+.1f}%** |")
        print(f"{fam:14s}{plat:10s}{g['base']*1e3:10.3f}{g['res']*1e3:10.3f}{g['st']*1e3:10.3f}"
              f"{g['dual']*1e3:10.3f}{st_base:9.1f}{dual_res:10.1f}{dual_base:11.1f}")
        all_rows[(fam, plat)] = {"geo_base_mrad": g['base']*1e3, "geo_res_mrad": g['res']*1e3,
                                   "geo_st_mrad": g['st']*1e3, "geo_dual_mrad": g['dual']*1e3,
                                   "st_vs_base_pct": st_base, "dual_vs_res_pct": dual_res,
                                   "dual_vs_base_pct": dual_base}

(ROOT / "V5_RESULTS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
(ROOT / "v5_numbers.json").write_text(json.dumps({f"{f}/{p}": v for (f, p), v in all_rows.items()}, indent=2),
                                        encoding="utf-8")
print(f"\nwrote {ROOT / 'V5_RESULTS.md'}")
