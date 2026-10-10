"""Every noise number quoted in the manuscript, from final_noise.csv (true-attitude error, paired seeds)."""
import csv
import math
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader((HERE / "results" / "final_noise.csv").open()))
nom = {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"])
       for r in csv.DictReader((HERE / "results" / "final_nominal.csv").open())}
idx = {(r["noise_level"], r["platform"], r["mission"], int(r["seed"]), r["label"]): r for r in rows}
M = ("roll", "full3", "hard45", "hardstep", "yaw360")


def gm(xs):
    return math.exp(sum(math.log(x) for x in xs) / len(xs))


red = lambda b, c: 100 * (1 - c / b)
for level in ("moderate", "realistic"):
    seeds = sorted({int(r["seed"]) for r in rows if r["noise_level"] == level})
    print(f"\n=== {level}: {len(seeds)} seeds")
    for p in ("x2", "cf2-rotor"):
        print(f"  {p}")
        seedmean = {}
        for m in M:
            base = [float(idx[(level, p, m, s, "pdff_rho3")]["qerr_true_mean_rad"]) for s in seeds]
            for arm in ("cmg_pes_gated", "cmg_pes_table"):
                c = [float(idx[(level, p, m, s, arm)]["qerr_true_mean_rad"]) for s in seeds]
                r = [red(b, x) for b, x in zip(base, c)]
                seedmean[(m, arm)] = st.mean(c)
                if arm == "cmg_pes_gated":
                    print(f"    {m:9s} PD+ff {st.mean(base)*1e3:8.3f} (noise-free {nom[(p, m, 'pdff_rho3')]*1e3:8.3f}) mrad | gated: mean {st.mean(r):8.2f}%  sd {st.stdev(r):5.2f}  min {min(r):8.2f}  positive {sum(x > 0 for x in r)}/{len(r)}"
                          f" | table-beta: mean {st.mean([red(b, x) for b, x in zip(base, [float(idx[(level, p, m, s, 'cmg_pes_table')]['qerr_true_mean_rad']) for s in seeds])]):7.2f}%")
            seedmean[(m, "base")] = st.mean(base)
        for arm in ("cmg_pes_gated", "cmg_pes_table"):
            b5 = gm([seedmean[(m, "base")] for m in M]); c5 = gm([seedmean[(m, arm)] for m in M])
            M4 = [m for m in M if m != "hardstep"]
            b4 = gm([seedmean[(m, "base")] for m in M4]); c4 = gm([seedmean[(m, arm)] for m in M4])
            print(f"    geo(5 missions) {arm:14s}: {red(b5, c5):8.2f}%   geo(4, no Hardstep): {red(b4, c4):7.2f}%")
sys.exit(0)
