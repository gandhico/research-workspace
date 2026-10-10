"""Published vs frame-aligned: every paper number the verifier checks, plus the primary per-mission cells.

Reads reproduce/claims_check.csv of the published tree and of the sandbox (each written by its own copy of
verify_acc2027_claims.py) and the two final_nominal.csv files. Writes FRAME_ALIGNED_COMPARISON.{md,csv} in the sandbox.
    .venv/Scripts/python.exe tools/frame_aligned/compare_claims.py
"""
import csv
import math

from build_sandbox import REPO, SB

rd = lambda p: list(csv.DictReader(p.open(encoding="utf-8")))
pub = {(r["section"], r["claim"]): r for r in rd(REPO / "reproduce" / "claims_check.csv")}
new = {(r["section"], r["claim"]): r for r in rd(SB / "reproduce" / "claims_check.csv")}
assert pub.keys() == new.keys(), set(pub) ^ set(new)

rows, same = [], 0
for k, p in pub.items():
    n = new[k]
    changed = p["recomputed"] != n["recomputed"]
    same += not changed
    rows.append(dict(section=k[0], claim=k[1], paper=p["paper"], published_code=p["recomputed"], frame_aligned=n["recomputed"],
                     changed="yes" if changed else "", frame_aligned_matches_paper="yes" if n["recomputed"] == p["paper"] else "NO"))
with (SB / "FRAME_ALIGNED_COMPARISON.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

M = ("roll", "full3", "hard45", "hardstep", "yaw360")
nom = lambda root: {(r["platform"], r["mission"], r["label"]): float(r["qerr_true_mean_rad"])
                    for r in rd(root / "experiments" / "final_robustness_gating_2026-09-20" / "results" / "final_nominal.csv")}
a, b = nom(REPO), nom(SB)
red = lambda x, y: 100 * (1 - y / x)
gm = lambda v: math.exp(sum(map(math.log, v)) / len(v))
L = ["# Frame-aligned re-run vs published code", "",
     "Change: every rate-tracking error omega - omega_d -> omega_e = omega - R(q_e)^T omega_d (P-(8)); see",
     "`tools/frame_aligned/build_sandbox.py` and `patch_ladder.py` (search FRAME-ALIGNED). Runs without a desired-rate term",
     "are copied unchanged (`COPIED_UNAFFECTED.md`).", "",
     f"**{len(rows) - same} of {len(rows)} verifier rows change; {sum(r['frame_aligned_matches_paper'] == 'yes' for r in rows)} "
     f"of {len(rows)} still equal the paper's printed value.**", "",
     "## Primary result, per mission (1e-3 rad; reduction = 1 - CMG/PD+ff)", "",
     "| platform | mission | PD+ff published | PD+ff frame-aligned | change | reduction published | reduction frame-aligned |",
     "|---|---|---|---|---|---|---|"]
for p in ("x2", "cf2-rotor"):
    for m in M:
        bp, bn = a[(p, m, "pdff_rho3")], b[(p, m, "pdff_rho3")]
        cp, cn = a[(p, m, "cmg_pes_gated")], b[(p, m, "cmg_pes_gated")]
        L.append(f"| {p} | {m} | {1e3 * bp:.4f} | {1e3 * bn:.4f} | {100 * (bn / bp - 1):+.2f}% | {red(bp, cp):.1f}% | {red(bn, cn):.1f}% |")
    g = lambda d, lab: gm([d[(p, m, lab)] for m in M])
    L.append(f"| **{p}** | **geo** | {1e3 * g(a, 'pdff_rho3'):.3f} | {1e3 * g(b, 'pdff_rho3'):.3f} | "
             f"{100 * (g(b, 'pdff_rho3') / g(a, 'pdff_rho3') - 1):+.2f}% | **{red(g(a, 'pdff_rho3'), g(a, 'cmg_pes_gated')):.1f}%** | "
             f"**{red(g(b, 'pdff_rho3'), g(b, 'cmg_pes_gated')):.1f}%** |")
L += ["", "## Every verifier row", "", "| section | claim | paper | published code | frame-aligned | |", "|---|---|---|---|---|---|"]
for r in rows:
    flag = "" if not r["changed"] else ("changed, still rounds to paper" if r["frame_aligned_matches_paper"] == "yes" else "**changed**")
    L.append(f"| {r['section']} | {r['claim']} | {r['paper']} | {r['published_code']} | {r['frame_aligned']} | {flag} |")
(SB / "FRAME_ALIGNED_COMPARISON.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[:30]))
print(f"\n{len(rows) - same} changed of {len(rows)}; written {SB / 'FRAME_ALIGNED_COMPARISON.md'}")
