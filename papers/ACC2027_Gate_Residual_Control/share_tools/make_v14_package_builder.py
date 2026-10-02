"""One-off: derive build_advisor_package_v14.py from build_advisor_package_2026-09-21.py (paper v14, amendment A3 material).

The earlier package (share/advisor_2026-09-21) is left untouched.  Exact-one-match assertions on every replaced passage.
"""
from pathlib import Path

D = Path(__file__).resolve().parent
src = (D / "build_advisor_package_2026-09-21.py").read_text(encoding="utf-8")
s = src


def sub(old, new, tag):
    global s
    assert s.count(old) == 1, f"{tag}: {s.count(old)}"
    s = s.replace(old, new)
    print("ok", tag)


sub('"""Build the advisor package (2026-09-21):', '"""Build the advisor package v14 (2026-09-21, paper v14 + amendment A3 Izhikevich material):', "docstring")
sub('OUT = ROOT / "share" / "advisor_2026-09-21"', 'OUT = ROOT / "share" / "advisor_2026-09-21_v14"', "OUT")
sub('STAMP = "2026-09-21"', 'STAMP = "2026-09-21_v14"', "STAMP")
sub('PAPER = "paper/v13_2026-09-20_robustness"', 'PAPER = "paper/v14_2026-09-21_izhikevich"', "PAPER")
sub("# keep ACC2027.log: audit_v13.py reads it", "# keep ACC2027.log: audit_v14.py reads it", "log comment")
sub("share_tools, paper/v13_2026-09-20_robustness", "share_tools, paper/v14_2026-09-21_izhikevich", "rules comment")

old_tr = '''    # Izhikevich supplement + the archived CMG runs the adapter is validated against'''
new_tr = '''    # amendment A3: Izhikevich under the CMG protocol -- the traces behind figures_out/izh_a3 (both airframes)
    *[f"{G}/results/izh_a3/nominal/x2/{m}/izh_pes_gated_b0p5/load_1/seed_001/trace.csv" for m in ("hard45", "hardstep", "roll")],
    f"{G}/results/izh_a3/nominal/x2/hardstep/izh_pes_ungated_b0p5/nominal/seed_001/trace.csv",
    *[f"{G}/results/izh_a3/nominal/cf2-rotor/{m}/izh_pes_gated_b0p2/load_1/seed_001/trace.csv" for m in ("hard45", "hardstep", "roll")],
    f"{G}/results/izh_a3/nominal/cf2-rotor/hardstep/izh_pes_ungated_b0p2/nominal/seed_001/trace.csv",
    *[f"{G}/results/confirmatory/nominal/cf2-rotor/{m}/{a}/nominal/seed_001/trace.csv" for m in ("hard45", "roll") for a in ("pdff_rho3", "cmg_pes_table")],
    *[f"{G}/results/confirmatory_a2/a2_nominal/cf2-rotor/{m}/cmg_pes_gated_b02/load_1/seed_001/trace.csv" for m in ("hard45", "hardstep", "roll")],
    # earlier exploratory Izhikevich supplement + the archived CMG runs the adapter is validated against'''
sub(old_tr, new_tr, "traces")
sub("then run make_paper_figures.py / make_izh_figures.py / make_noise_figure.py.",
    "then run make_paper_figures.py / make_v14_figures.py / make_izh_figures.py / make_izh_a3_figures.py / make_noise_figure.py.", "traces readme")
(D / "build_advisor_package_v14.py").write_text(s, encoding="utf-8")
print("written build_advisor_package_v14.py")
