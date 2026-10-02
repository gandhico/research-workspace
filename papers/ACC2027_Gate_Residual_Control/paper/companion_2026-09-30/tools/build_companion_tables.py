"""Generate the data-driven parts of the companion document (read-only over the repository).

  code_hashes.tex   SHA-256 of every cited source/model file, compared with the hashes recorded in the
                    manifests of the published runs (proves the quoted code is the code that ran)
  claims_table.tex  the 59 paper numbers recomputed by reproduce/verify_acc2027_claims.py
  audit_facts.tex   macros for audit numbers quoted in the text

Run after reproduce/verify_acc2027_claims.py:
    .venv\\Scripts\\python.exe paper\\companion_2026-09-30\\tools\\build_companion_tables.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
E = ROOT / "experiments"
FR = E / "final_robustness_gating_2026-09-20"

CITED = [
    "src/gra_control/math3d.py",
    "src/gra_control/gate.py",
    "src/gra_control/platforms/drone.py",
    "experiments/nengo_nef_replication_2026-08-29/nengo_cmg.py",
    "experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef_baselines.py",
    "experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef.py",
    "experiments/nengo_nef_replication_2026-08-29/nengo_neuron_family.py",
    "experiments/nengo_nef_replication_2026-08-29/verify_archived_equivalence.py",
    "experiments/final_robustness_gating_2026-09-20/run_final_robustness.py",
    "experiments/final_robustness_gating_2026-09-20/run_a2_robustness.py",
    "experiments/final_robustness_gating_2026-09-20/run_controllers_gated.py",
    "experiments/final_robustness_gating_2026-09-20/run_izh_corrected.py",
    "experiments/final_robustness_gating_2026-09-20/izh_adapter_corrected.py",
    "experiments/final_robustness_gating_2026-09-20/build_final_csv.py",
    "experiments/final_robustness_gating_2026-09-20/make_ladder_figure.py",
    "experiments/neuron_basis_decisive_2026-09-24/run_neuron_basis.py",
    "experiments/neuron_basis_decisive_2026-09-24/family_basis_adapter.py",
    "experiments/theory_certificate_2026-09-12/compute_local_certificate.py",
    "reproduce/verify_acc2027_claims.py",
    "reproduce/check_rate_frame.py",
    "third_party/mujoco_menagerie/skydio_x2/scene.xml",
    "models/cf2_rotor_design/scene.xml",
]
MANIFESTS = {  # published primary runs: X2 (sealed runner) and CF2 beta=.2 (A2 runner copy)
    "X2": FR / "results/confirmatory/nominal/x2/hard45/cmg_pes_gated/load_1/seed_001/manifest.json",
    "CF2": FR / "results/confirmatory_a2/a2_nominal/cf2-rotor/hard45/cmg_pes_gated_b02/load_1/seed_001/manifest.json",
}
KEY_TO_FILE = {
    ("X2", "runner"): "experiments/final_robustness_gating_2026-09-20/run_final_robustness.py",
    ("CF2", "runner"): "experiments/final_robustness_gating_2026-09-20/run_a2_robustness.py",
    ("X2", "mujoco_model"): "third_party/mujoco_menagerie/skydio_x2/scene.xml",
    ("CF2", "mujoco_model"): "models/cf2_rotor_design/scene.xml",
}
SHARED = {
    "baseline_runner": "experiments/nengo_nef_replication_2026-08-29/run_mujoco_nef_baselines.py",
    "nengo_cmg": "experiments/nengo_nef_replication_2026-08-29/nengo_cmg.py",
    "gate_model": "src/gra_control/gate.py",
    "quaternion_and_reference": "src/gra_control/math3d.py",
    "platform_interface": "src/gra_control/platforms/drone.py",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tex(s: str) -> str:
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
           "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
           "<": r"\textless{}", ">": r"\textgreater{}"}
    return "".join(rep.get(c, c) for c in s)


# ---- 1. hashes vs manifests
recorded: dict[str, list[tuple[str, str]]] = {}
env = {}
for plat, mpath in MANIFESTS.items():
    m = json.loads(mpath.read_text(encoding="utf-8"))
    env[plat] = (m["python"], m["numpy"], m["mujoco"], m["git_commit"], m["created_utc"][:10])
    for key, h in m["source_sha256"].items():
        f = KEY_TO_FILE.get((plat, key)) or SHARED.get(key)
        if f:
            recorded.setdefault(f, []).append((plat, h))

lines, n_match, n_checked = [], 0, 0
for f in CITED:
    h = sha(ROOT / f)
    rec = recorded.get(f, [])
    if rec:
        ok = all(r == h for _, r in rec)
        n_checked += 1
        n_match += ok
        status = ("matches " if ok else "DIFFERS from ") + "/".join(p for p, _ in rec) + " run manifest"
    else:
        status = "not recorded by the primary runs"
    lines.append(rf"\path{{{f}}} & {{\scriptsize\texttt{{{h[:32]}}}\newline\texttt{{{h[32:]}}}}} & {status}\\")
(HERE / "code_hashes.tex").write_text(
    "\\begin{longtable}{@{}p{0.38\\linewidth}p{0.34\\linewidth}p{0.22\\linewidth}@{}}\n\\toprule\nFile & SHA-256 & Provenance check\\\\\\midrule\n\\endhead\n"
    + "\n".join(lines) + "\n\\bottomrule\n\\end{longtable}\n", encoding="utf-8")

# ---- 2. native vs reconstructed command (runner-internal consistency), all primary CMG runs
worst = 0.0
n_runs = 0
for s in list((FR / "results/confirmatory/nominal").glob("*/*/cmg_pes_gated/load_1/seed_001/summary.json")) + \
        list((FR / "results/confirmatory_a2/a2_nominal").glob("*/*/cmg_pes_gated_b02/load_1/seed_001/summary.json")):
    v = json.loads(s.read_text(encoding="utf-8"))["cmg_pes"]["max_native_vs_reconstructed_command_error_Nm"]
    worst, n_runs = max(worst, v), n_runs + 1

# ---- 3. claims table
rows = list(csv.DictReader((ROOT / "reproduce/claims_check.csv").open(encoding="utf-8")))
n_ok = sum(r["status"] == "OK" for r in rows)
brk = lambda s: tex(s).replace(",", r",\allowbreak ").replace("/", r"/\allowbreak ")
body = [rf"{i} & {tex(r['section'])} & {tex(r['claim'])} & {brk(r['paper'])} & {brk(r['recomputed'])} & {r['status']}\\"
        for i, r in enumerate(rows, 1)]
(HERE / "claims_table.tex").write_text(
    "{\\scriptsize\\begin{longtable}{@{}r>{\\raggedright\\arraybackslash}p{0.16\\linewidth}>{\\raggedright\\arraybackslash}p{0.28\\linewidth}>{\\raggedright\\arraybackslash}p{0.19\\linewidth}>{\\raggedright\\arraybackslash}p{0.19\\linewidth}l@{}}\n\\toprule\n"
    "\\# & Paper location & Claim & Paper value & Recomputed & Status\\\\\\midrule\n\\endhead\n"
    + "\n".join(body) + "\n\\bottomrule\n\\end{longtable}}\n", encoding="utf-8")

# ---- 4. macros
py, npv, mj, commit, date = env["X2"]
facts = {
    "auditClaimsOK": str(n_ok), "auditClaimsN": str(len(rows)),
    "auditHashMatch": str(n_match), "auditHashChecked": str(n_checked),
    "auditReconWorst": f"{worst:.1e}".replace("e-", r"\times10^{-").replace("e+", r"\times10^{") + "}" if worst > 0 else "0",
    "auditReconRuns": str(n_runs),
    "envPython": py, "envNumpy": npv, "envMujoco": mj, "envCommit": commit[:12], "envRunDate": date,
}
(HERE / "audit_facts.tex").write_text("".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in facts.items()), encoding="utf-8")
print(json.dumps(facts, indent=1))
