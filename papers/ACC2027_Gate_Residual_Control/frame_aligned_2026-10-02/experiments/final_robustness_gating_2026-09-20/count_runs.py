"""Count completed runs by protocol/campaign from the summary.json files on disk."""
import glob
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
c = Counter()
bad = 0
for f in glob.glob(str(HERE / "results" / "*" / "*" / "*" / "*" / "*" / "*" / "seed_*" / "summary.json")):
    p = Path(f).parts
    protocol, campaign = p[-8], p[-7]
    try:
        json.load(open(f))
        c[(protocol, campaign)] += 1
    except Exception:
        bad += 1
val = len(glob.glob(str(HERE / "results_validation" / "*" / "*" / "*" / "*" / "*" / "*" / "seed_*" / "summary.json")))
tot_conf = sum(v for (p, _), v in c.items() if p.startswith("confirmatory"))
tot_dev = sum(v for (p, _), v in c.items() if p.startswith("development"))
for k, v in sorted(c.items()):
    print(f"{k[0]:20s}{k[1]:28s}{v:5d}")
print(f"\nvalidation runs: {val}")
print(f"confirmatory: {tot_conf}   exploratory: {tot_dev}   total incl. validation: {tot_conf + tot_dev + val}   unreadable: {bad}")
sys.exit(0)
