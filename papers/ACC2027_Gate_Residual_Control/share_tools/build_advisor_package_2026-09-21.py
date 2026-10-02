"""Build the advisor package (2026-09-21): one main zip (code, paper, docs, summaries, provenance, figures) and one optional
zip with only the raw traces needed to regenerate the figures.

Rules (see PACKAGE_README.md inside the zip for the reader-facing version):
  * always: src, scripts, tests, configs, models, third_party, docs, figures, share_tools, paper/v13_2026-09-20_robustness
  * experiments/*: code, docs, and summary-level data only -- never trace.csv / .npz / .zip / .obj, nothing over a size cap,
    and under any results* folder only json / csv / log / md / txt
  * never: .venv, .git, other paper versions, share/ (older packages), frozen_archives/, SOTA/ (third-party PDFs), tmp/, output/,
    presentation/ (stale), top-level results/ (old raw traces)

usage:  python build_advisor_package_2026-09-21.py [--dry-run]
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "share" / "advisor_2026-09-21"
STAMP = "2026-09-21"
SKIP_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache", "$BuildDir"}
FULL_DIRS = ["src", "scripts", "tests", "configs", "models", "third_party", "docs", "figures", "share_tools"]
TOP_FILES = ["README.md", "pyproject.toml"]
PAPER = "paper/v13_2026-09-20_robustness"
PAPER_SKIP_EXT = {".aux", ".out", ".blg", ".pyc"}   # keep ACC2027.log: audit_v13.py reads it
EXPERIMENTS = ["final_robustness_gating_2026-09-20", "baseline_restatement_2026-09-16", "nengo_nef_replication_2026-08-29",
               "theory_certificate_2026-09-12", "gate_gain_sweep_2026-09-11", "six_dof_expansion_2026-08-31",
               "final_clean_figures_2026-09-20"]
EXP_SKIP_EXT = {".npz", ".zip", ".obj", ".pyc", ".aux", ".out"}
CAPS = {".csv": 3_000_000, ".json": 5_000_000, ".png": 1_500_000, ".pdf": 3_000_000, ".log": 1_000_000}
DEFAULT_CAP = 3_000_000
RESULTS_OK = {".json", ".csv", ".log", ".md", ".txt"}

G = "experiments/final_robustness_gating_2026-09-20"
TRACES = [
    # nominal campaign: the arms every figure script draws
    *[f"{G}/results/confirmatory/nominal/x2/{m}/{a}/{t}/seed_001/trace.csv"
      for m in ("hard45", "hardstep", "roll", "full3") for a, t in (("pdff_rho3", "nominal"), ("cmg_pes_table", "nominal"), ("cmg_pes_gated", "load_1"))],
    *[f"{G}/results/confirmatory/nominal/cf2-rotor/{m}/{a}/{t}/seed_001/trace.csv"
      for m in ("hardstep", "full3") for a, t in (("pdff_rho3", "nominal"), ("cmg_pes_table", "nominal"), ("cmg_pes_gated", "load_1"))],
    # disturbance figures
    f"{G}/results/confirmatory/disturbance/x2/hover/pdff_rho3/dist_x1/seed_001/trace.csv",
    f"{G}/results/confirmatory/disturbance/x2/hover/cmg_pes_gated/dist_x1__load_1/seed_001/trace.csv",
    f"{G}/results/confirmatory/disturbance/cf2-rotor/hover/pdff_rho3/dist_x1/seed_001/trace.csv",
    f"{G}/results/confirmatory_a2/a2_dist/cf2-rotor/hover/cmg_pes_gated_b02/dist_x1__load_1/seed_001/trace.csv",
    # noise figures
    f"{G}/results/confirmatory/noise/x2/hard45/pdff_rho3/noise_realistic/seed_001/trace.csv",
    f"{G}/results/confirmatory/noise/x2/hard45/cmg_pes_gated/noise_realistic__load_1/seed_001/trace.csv",
    f"{G}/results/confirmatory/noise/cf2-rotor/hard45/pdff_rho3/noise_realistic/seed_001/trace.csv",
    f"{G}/results/confirmatory_a2/a2_noise/cf2-rotor/hard45/cmg_pes_gated_b02/noise_realistic__load_1/seed_001/trace.csv",
    # CF2 noisy-Hardstep divergence diagnosis (default seed 2, moderate)
    f"{G}/results/confirmatory/noise/cf2-rotor/hardstep/pdff_rho3/noise_moderate/seed_002/trace.csv",
    f"{G}/results/confirmatory/noise/cf2-rotor/hardstep/cmg_pes_gated/noise_moderate__load_1/seed_002/trace.csv",
    # Izhikevich supplement + the archived CMG runs the adapter is validated against
    *[f"{G}/results/supplementary_izhikevich/x2/{m}/nengo_izhikevich_pes/trace.csv" for m in ("hard45", "hardstep", "roll")],
    *[f"experiments/nengo_nef_replication_2026-08-29/results/baselines_2026-09-10/stretch/pdff/bw3/x2_{m}_nengo_nef_pes/trace.csv"
      for m in ("hard45", "hardstep", "roll")],
]


def walk(rel_root: str):
    base = ROOT / rel_root
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            p = Path(dp) / f
            yield p, p.relative_to(ROOT)


def keep_experiment(rel: Path, size: int) -> bool:
    ext = rel.suffix.lower()
    if rel.name == "trace.csv" or ext in EXP_SKIP_EXT:
        return False
    if any(part.startswith("results") for part in rel.parts) and ext not in RESULTS_OK:
        return False
    return size <= CAPS.get(ext, DEFAULT_CAP)


def collect() -> dict[str, list[tuple[Path, Path]]]:
    groups: dict[str, list[tuple[Path, Path]]] = {}
    for f in TOP_FILES:
        if (ROOT / f).exists():
            groups.setdefault("(root files)", []).append((ROOT / f, Path(f)))
    for d in FULL_DIRS:
        groups[d] = [(p, r) for p, r in walk(d) if p.suffix.lower() != ".pyc"]
    groups[PAPER] = [(p, r) for p, r in walk(PAPER) if p.suffix.lower() not in PAPER_SKIP_EXT]
    for e in EXPERIMENTS:
        groups[f"experiments/{e}"] = [(p, r) for p, r in walk(f"experiments/{e}") if keep_experiment(r, p.stat().st_size)]
    top_md = [(p, p.relative_to(ROOT)) for p in (ROOT / "experiments").glob("*.md")]
    if top_md:
        groups["experiments/(top-level notes)"] = top_md
    return groups


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(dry: bool) -> None:
    groups = collect()
    total = 0
    print(f"{'group':70s}{'files':>7s}{'MB':>9s}")
    for g, items in groups.items():
        sz = sum(p.stat().st_size for p, _ in items)
        total += sz
        print(f"{g:70s}{len(items):7d}{sz / 1e6:9.1f}")
    miss = [t for t in TRACES if not (ROOT / t).exists()]
    tr_sz = sum((ROOT / t).stat().st_size for t in TRACES if (ROOT / t).exists())
    print(f"\nmain zip content: {total / 1e6:.1f} MB uncompressed;  traces: {len(TRACES) - len(miss)} files, {tr_sz / 1e6:.1f} MB; missing traces: {miss}")
    if dry:
        return

    OUT.mkdir(parents=True, exist_ok=True)
    extra = ROOT / "share_tools" / "package_extras"
    main_zip = OUT / f"ACC2027_advisor_package_{STAMP}.zip"
    manifest = []
    with zipfile.ZipFile(main_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for items in groups.values():
            for p, rel in items:
                z.write(p, rel.as_posix())
                manifest.append((sha256(p), rel.as_posix()))
        for name in ("PACKAGE_README.md", "requirements_frozen.txt", "tools/rebase_paths.py"):
            z.write(extra / name, name)
            manifest.append((sha256(extra / name), name))
        z.writestr("MANIFEST_SHA256.txt", "\n".join(f"{h}  {n}" for h, n in sorted(manifest, key=lambda x: x[1])) + "\n")
    trace_zip = OUT / f"ACC2027_advisor_traces_for_figures_{STAMP}.zip"
    with zipfile.ZipFile(trace_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for t in TRACES:
            if (ROOT / t).exists():
                z.write(ROOT / t, t)
        z.writestr("README_TRACES.txt",
                   "Raw 5-ms traces needed to regenerate the figures. Extract INTO the root of the extracted main package "
                   "(same relative paths), then run make_paper_figures.py / make_izh_figures.py / make_noise_figure.py.\n")
    sums = []
    for zp in (main_zip, trace_zip):
        sums.append(f"{sha256(zp)}  {zp.name}")
        print(f"{zp.name}: {zp.stat().st_size / 1e6:.1f} MB")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main("--dry-run" in sys.argv)
