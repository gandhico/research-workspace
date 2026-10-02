"""Audit Spanish residue and LaTeX-structure parity in the English variant."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import translate_latex_es_en as translator  # noqa: E402


ROOT = HERE.parent
SOURCE = ROOT / "source_es"
TARGET = ROOT / "source_en"
OUTPUT = ROOT / "tmp" / "translation_audit.json"


PATTERNS = {
    "labels": r"\\label\{",
    "refs": r"\\(?:ref|eqref|pageref)\{",
    "citations": r"\\cite[a-zA-Z]*\{",
    "graphics": r"\\includegraphics",
    "equation_environments": r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}",
}


def main() -> None:
    report = []
    residue_examples = []
    for relative in translator.DEFAULT_FILES:
        source_text = (SOURCE / relative).read_text(encoding="utf-8")
        target_text = (TARGET / relative).read_text(encoding="utf-8")
        counts = {}
        parity = True
        for name, pattern in PATTERNS.items():
            source_count = len(re.findall(pattern, source_text))
            target_count = len(re.findall(pattern, target_text))
            counts[name] = {"source": source_count, "target": target_count}
            parity &= source_count == target_count
        spans = translator.collect_translatable_spans(target_text)
        for span in spans[:8]:
            residue_examples.append({
                "file": relative,
                "position": span.start,
                "text": re.sub(r"\s+", " ", span.text.strip())[:240],
            })
        report.append({
            "file": relative,
            "structure_parity": parity,
            "counts": counts,
            "probable_spanish_spans": len(spans),
            "probable_spanish_characters": sum(len(span.text) for span in spans),
        })
    payload = {
        "all_structure_parity": all(item["structure_parity"] for item in report),
        "probable_spanish_spans": sum(item["probable_spanish_spans"] for item in report),
        "probable_spanish_characters": sum(item["probable_spanish_characters"] for item in report),
        "files": report,
        "residue_examples": residue_examples,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
