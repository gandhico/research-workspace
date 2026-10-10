"""Point build_advisor_package.py at the v7 manuscript and the final sweep."""
from __future__ import annotations

import io

P = "../build_advisor_package.py"
s = io.open(P, encoding="utf-8").read()
n = 0


def sub(old: str, new: str, tag: str) -> None:
    global s, n
    if s.count(old) != 1:
        raise SystemExit(f"FAILED [{tag}]: found {s.count(old)}, expected 1")
    s = s.replace(old, new, 1)
    n += 1
    print(f"  ok  {tag}")


# --- the manuscript moved into the research tree and became v7 -------------
sub('PAPER_V5 = Path(r"C:\\Users\\gandhico\\Downloads\\paper_v5")',
    'PAPER_SRC = ACC / "paper" / "v7_2026-09-05"', "paper-src")

sub('put(PAPER_V5 / "ACC2027_v6.pdf", "paper/ACC2027_manuscript.pdf")\n'
    'put(PAPER_V5 / "ACC2027_v6.tex", "paper/ACC2027_manuscript.tex")',
    'put(PAPER_SRC / "ACC2027_v7.pdf", "paper/ACC2027_manuscript.pdf")\n'
    'put(PAPER_SRC / "ACC2027_v7.tex", "paper/ACC2027_manuscript.tex")',
    "manuscript-v7")

s = s.replace("PAPER_V5 /", "PAPER_SRC /")
s = s.replace('PAPER_V5 / "figures/arch"', 'PAPER_SRC / "figures/arch"')

# --- new figures and data from the final sweep -----------------------------
sub("""n = put_glob(RESEARCH / "eprop_anneal_reproduction/plots_5missions", "*.png",
             "figures/06_eprop_anneal")
print(f"    {n:4d} eprop/annealed-trace plots")""",
    '''n = put_glob(RESEARCH / "eprop_anneal_reproduction/plots_5missions", "*.png",
             "figures/06_eprop_anneal")
print(f"    {n:4d} eprop/annealed-trace plots")

# --- disturbance rejection and noise sensitivity (2026-09-05) -------------
NENGO_EXP = ACC / "experiments/nengo_nef_replication_2026-08-29/results"
SWEEP = NENGO_EXP / "final_sweep_2026-09-05/compiled"
HOVER45 = NENGO_EXP / "hover_intermittent_2026-09-05"
n = put_glob(SWEEP, "*.png", "figures/07_disturbance_and_noise")
n += put_glob(SWEEP, "*.pdf", "figures/07_disturbance_and_noise")
n += put_glob(HOVER45, "*.png", "figures/07_disturbance_and_noise")
n += put_glob(HOVER45, "*.pdf", "figures/07_disturbance_and_noise")
print(f"    {n:4d} disturbance / noise-sensitivity plots")

for f, dst in ((SWEEP / "noise_sensitivity.csv", "data/tables/noise_sensitivity.csv"),
               (SWEEP / "table_noise.tex", "data/tables/table_noise.tex"),
               (SWEEP / "retention.json", "data/tables/hover_retention.json"),
               (NENGO_EXP / "final_sweep_2026-09-05/raw_results.json",
                "data/tables/final_sweep_raw.json"),
               (NENGO_EXP / "noise_check_2026-09-05/noise_check_summary.json",
                "data/tables/noise_check_summary.json")):
    put(f, dst)''',
    "new-results")

io.open(P, "w", encoding="utf-8").write(s)
print(f"\nupdated {P} ({n} changes)")
