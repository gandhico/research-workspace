"""Build the portable SHA-256 manifest for key EHEKATL transfer artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "UBUNTU_TRANSFER_SHA256SUMS.txt"

EXACT = (
    "UBUNTU_AGENT_START_HERE.md",
    "EHEKATL_RESEARCH_ROADMAP_2026.md",
    "EHEKATL_SOTA_IJCOPI_HYPERLIF_SENSORS_2026.md",
    "dissertation/TRANSLATION_STATUS.md",
    "dissertation/output/pdf/EHEKATL_English_Dissertation_2026.pdf",
    "dissertation/tmp/translation_audit.json",
    "project/AGENTS.md",
    "project/docs/CONTROL_DEVELOPMENT_PROCESS.md",
    "project/docs/LAST_SESSION_HANDOFF.md",
    "project/paper/CLAIMS_MATRIX.md",
    "project/paper/DATASET_REGISTRY.csv",
    "project/paper/ijcopi/IJCOPI_MANUSCRIPT.md",
    "project/paper/ijcopi/IJCOPI_EXPERIMENT_GATES.md",
    "project/paper/ijcopi/IJCOPI_SUBMISSION_READINESS.md",
    "project/paper/ijcopi/build_ijcopi_2027_docx.py",
    "project/paper/ijcopi/2027-IJCOPI_template_simple_British_English.docx",
    "project/paper/ijcopi/EHEKATL_LQR_DeePC_IJCOPI_Double_Blind.docx",
    "project/paper/ijcopi/qa_render_final/EHEKATL_LQR_DeePC_IJCOPI_Double_Blind.pdf",
    "project/paper/ijcopi/EHEKATL_LQR_DeePC_IJCOPI_2027_Double_Blind.docx",
    "project/paper/ijcopi/qa_render_2027_verified/EHEKATL_LQR_DeePC_IJCOPI_2027_Double_Blind.pdf",
    "project/elevon_allocation/README.md",
    "project/elevon_allocation/MISSION_COMPARISON_REPORT.md",
)

GLOBS = (
    "project/elevon_allocation/*.py",
    "project/elevon_allocation/results/*.csv",
    "project/elevon_allocation/results/*.json",
    "project/elevon_allocation/results/*.png",
    "project/elevon_allocation/results/*.pdf",
    "project/elevon_allocation/results/mission_comparison/*",
    "project/paper/generated/*",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> None:
    selected = {ROOT / name for name in EXACT}
    for pattern in GLOBS:
        selected.update(path for path in ROOT.glob(pattern) if path.is_file())
    selected.discard(OUTPUT)
    missing = sorted(path for path in selected if not path.is_file())
    if missing:
        raise SystemExit("Missing manifest inputs: " + ", ".join(str(path) for path in missing))
    lines = []
    for path in sorted(selected, key=lambda item: item.relative_to(ROOT).as_posix().lower()):
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"{digest(path)}  {relative}")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {len(lines)} hashes to {OUTPUT}")


if __name__ == "__main__":
    main()
