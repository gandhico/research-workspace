"""Amendment A1 results: X2 Hardstep, noise-free, beta = 0.5, output-only gate at lowered load thresholds."""
import csv
import glob
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
b = json.load(open(HERE / "results/confirmatory/nominal/x2/hardstep/pdff_rho3/nominal/seed_001/summary.json"))
bm = b["metrics"]["qerr_true_mean_rad"]
g1 = json.load(open(HERE / "results/confirmatory/nominal/x2/hardstep/cmg_pes_gated/load_1/seed_001/summary.json"))
rows = [("1", g1)]
for f in glob.glob(str(HERE / "results/development_only/hardstep_variant_screen_a1/x2/hardstep/cmg_pes_gate/*/seed_001/summary.json")):
    thr = Path(f).parts[-3].split("_")[1]
    rows.append((thr, json.load(open(f))))
rows.sort(key=lambda r: -float(r[0]))
print(f"PD+ff X2 Hardstep: mean {math.degrees(bm):.3f} deg, settled {math.degrees(b['hardstep']['settled_mean_rad']):.3f}, "
      f"settling {b['hardstep']['settling_time_5deg_s_mean']:.3f} s\n")
print(f"{'load thr':>9s}{'mean [deg]':>12s}{'vs PD+ff':>10s}{'settled':>9s}{'t_settle':>10s}{'gate share':>12s}")
for thr, s in rows:
    m = s["metrics"]["qerr_true_mean_rad"]
    print(f"{thr:>9s}{math.degrees(m):12.3f}{100 * (1 - m / bm):+9.2f}%{math.degrees(s['hardstep']['settled_mean_rad']):9.3f}"
          f"{s['hardstep']['settling_time_5deg_s_mean']:10.3f}{s['output_gate']['blocked_fraction_any_axis']:12.3f}")
sys.exit(0)
