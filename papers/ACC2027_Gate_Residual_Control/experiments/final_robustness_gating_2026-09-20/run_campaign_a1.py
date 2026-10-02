"""Amendment A1 (PREREGISTRATION.md section 8): X2-only exploratory extension of the load threshold.

Imports the sealed driver unchanged.  Output goes to results/development_only/hardstep_variant_screen_a1.
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import run_campaign as rc

THRESHOLDS = (0.75, 0.5, 0.25, 0.0)


def cases():
    return [
        rc.Case(protocol="development_only", campaign="hardstep_variant_screen_a1", platform="x2",
                mission="hardstep", label="cmg_pes_gate", controller="nengo-nef-pes", beta=rc.BETA_CANONICAL,
                output_gate=rc.GATE_OUTPUT, gate_load_threshold=t)
        for t in THRESHOLDS
    ]


if __name__ == "__main__":
    root = rc.DEFAULT_RESULTS
    cs = cases()
    rows = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(rc.run_case, c, root, 45.0, 5e-4, False): c for c in cs}
        for f in as_completed(futs):
            c = futs[f]
            r = f.result()
            print(r["status"], c.case_id, flush=True)
            rows.append(rc.flatten(c, r))
    rc.write_csv(root / "results_hardstep-development-a1.csv", rows)
    sys.exit(0)
