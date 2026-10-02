"""Translate Spanish LaTeX prose while preserving LaTeX structure.

The immutable source is read from source_es and translated files are written
to source_en.  pylatexenc identifies prose nodes; equations, comments, labels,
citations, paths, and bibliography keys are never sent to the translation
model.  A persistent JSON cache makes the process resumable.

This is a first-pass technical translation.  The generated source must still
pass equation/label parity, scientific editing, compilation, and visual QA.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch
from pylatexenc.latexwalker import (
    LatexCharsNode,
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
    LatexSpecialsNode,
    LatexWalker,
)
from transformers import MarianMTModel, MarianTokenizer


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ES = ROOT / "source_es"
SOURCE_EN = ROOT / "source_en"
CACHE_PATH = ROOT / "tmp" / "translation_cache_es_en.json"
REPORT_PATH = ROOT / "tmp" / "translation_report_es_en.json"
MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"

DEFAULT_FILES = [
    "Agradecimientos/Agradecimientos.tex",
    "Agradecimientos/Dedicatoria.tex",
    "Declaracion/Declaracion.tex",
    "Capitulo1/introduccion.tex",
    "Capitulo2/marco_teorico.tex",
    "Capitulo3/diseno_experimento.tex",
    "Capitulo4/resultados_y_analisis.tex",
    "Capitulo5/conclusiones.tex",
    "Apéndice/Apendice1.tex",
]

PROTECTED_MACROS = {
    "bibliography",
    "bibliographystyle",
    "cite",
    "citealp",
    "citeauthor",
    "citep",
    "citet",
    "documentclass",
    "eqref",
    "include",
    "includegraphics",
    "input",
    "label",
    "pageref",
    "ref",
    "url",
    "usepackage",
}

MATH_ENVIRONMENTS = {
    "align",
    "align*",
    "array",
    "cases",
    "displaymath",
    "equation",
    "equation*",
    "gather",
    "gather*",
    "math",
    "multline",
    "multline*",
    "split",
}

SPANISH_MARKERS = {
    "a", "además", "al", "analisis", "análisis", "ante", "aquí", "así",
    "aeronave", "aerodinámico", "aunque", "bajo", "cada", "capítulo", "como",
    "con", "controlador", "cual", "cuando", "de", "del", "desde", "diseño",
    "donde", "dónde", "durante", "el", "ella", "en", "entre", "es", "esta",
    "este", "estos", "fue", "han", "hacia", "hasta", "la", "las", "lo", "los",
    "mediante", "modelo", "mientras", "muy", "no", "para", "pero", "por", "porque",
    "presenta", "que", "realiza", "respecto", "se", "según", "ser", "sistema",
    "sobre", "son", "su", "sus", "también", "tanto", "tiene", "una", "uno", "un",
    "utiliza", "y", "ya",
}


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    text: str


def load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def save_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def probably_spanish(text: str) -> bool:
    if not re.search(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", text):
        return False
    words = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text.lower())
    if not words:
        return False
    if re.search(r"[áéíóúüñ¿¡]", text.lower()):
        return True
    marker_count = sum(word in SPANISH_MARKERS for word in words)
    return marker_count >= 1 or (len(words) >= 8 and marker_count / len(words) >= 0.04)


def child_nodes(node: object) -> Iterable[object]:
    if isinstance(node, LatexMacroNode):
        if node.nodeargd is not None:
            for arg in node.nodeargd.argnlist:
                if arg is not None:
                    yield arg
        return
    if isinstance(node, LatexEnvironmentNode):
        if node.nodeargd is not None:
            for arg in node.nodeargd.argnlist:
                if arg is not None:
                    yield arg
        if node.nodelist is not None:
            yield from node.nodelist
        return
    if isinstance(node, LatexGroupNode):
        if node.nodelist is not None:
            yield from node.nodelist
        return
    nodelist = getattr(node, "nodelist", None)
    if nodelist is not None:
        yield from nodelist


def collect_translatable_spans(source: str) -> list[Span]:
    nodes, _, _ = LatexWalker(source, tolerant_parsing=True).get_latex_nodes()
    spans: list[Span] = []

    def walk(node: object, protected: bool = False) -> None:
        if isinstance(node, (LatexMathNode, LatexCommentNode)):
            return
        if isinstance(node, LatexEnvironmentNode) and node.environmentname in MATH_ENVIRONMENTS:
            return
        if isinstance(node, LatexMacroNode):
            macro_protected = protected or node.macroname in PROTECTED_MACROS
            if node.nodeargd is not None:
                for index, arg in enumerate(node.nodeargd.argnlist):
                    if arg is None:
                        continue
                    arg_protected = macro_protected or (node.macroname == "href" and index == 0)
                    walk(arg, arg_protected)
            return
        if isinstance(node, LatexCharsNode):
            if not protected and probably_spanish(node.chars):
                spans.append(Span(node.pos, node.pos + node.len, node.chars))
            return
        for child in child_nodes(node):
            walk(child, protected)

    for top in nodes:
        walk(top)

    # Defensive invariant: replacement spans must never overlap.
    spans.sort(key=lambda span: span.start)
    for left, right in zip(spans, spans[1:]):
        if left.end > right.start:
            raise RuntimeError(f"Overlapping prose spans at {left.start}:{left.end} and {right.start}:{right.end}")
    return spans


def split_for_model(text: str, max_chars: int = 900) -> list[tuple[str, bool]]:
    """Return (piece, translate) items while retaining whitespace separators."""
    items: list[tuple[str, bool]] = []
    for block in re.split(r"(\n\s*\n)", text):
        if not block:
            continue
        if re.fullmatch(r"\n\s*\n", block):
            items.append((block, False))
            continue
        leading = re.match(r"^\s*", block).group(0)
        trailing = re.search(r"\s*$", block).group(0)
        core_end = len(block) - len(trailing) if trailing else len(block)
        core = block[len(leading):core_end]
        if leading:
            items.append((leading, False))
        if core:
            sentences = re.split(r"(?<=[.!?;:])\s+", core)
            current = ""
            for sentence in sentences:
                if not sentence:
                    continue
                candidate = sentence if not current else current + " " + sentence
                if current and len(candidate) > max_chars:
                    items.append((current, True))
                    current = sentence
                else:
                    current = candidate
            if current:
                if len(current) <= max_chars:
                    items.append((current, True))
                else:
                    for start in range(0, len(current), max_chars):
                        items.append((current[start:start + max_chars], True))
        if trailing:
            items.append((trailing, False))
    return items


class Translator:
    def __init__(self, batch_size: int = 8) -> None:
        self.batch_size = batch_size
        self.cache = load_cache()
        self.tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
        self.model = MarianMTModel.from_pretrained(MODEL_NAME)
        self.model.eval()

    def translate_many(self, texts: list[str]) -> list[str]:
        outputs: list[str | None] = [None] * len(texts)
        pending_indices: list[int] = []
        pending_texts: list[str] = []
        for index, text in enumerate(texts):
            key = cache_key(text)
            if key in self.cache:
                outputs[index] = self.cache[key]
            else:
                pending_indices.append(index)
                pending_texts.append(text)

        for offset in range(0, len(pending_texts), self.batch_size):
            batch = pending_texts[offset:offset + self.batch_size]
            encoded = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            with torch.inference_mode():
                generated = self.model.generate(**encoded, max_new_tokens=512, num_beams=4)
            translated = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
            for local_index, value in enumerate(translated):
                global_pending = offset + local_index
                source_index = pending_indices[global_pending]
                original = pending_texts[global_pending]
                outputs[source_index] = value
                self.cache[cache_key(original)] = value
            save_json_atomic(CACHE_PATH, self.cache)

        return [value if value is not None else texts[index] for index, value in enumerate(outputs)]

    def translate_span(self, text: str) -> str:
        pieces = split_for_model(text)
        translatable = [piece for piece, do_translate in pieces if do_translate]
        translated = iter(self.translate_many(translatable))
        rebuilt: list[str] = []
        for piece, do_translate in pieces:
            rebuilt.append(next(translated) if do_translate else piece)
        return "".join(rebuilt)


def translate_file(relative: str, translator: Translator) -> dict[str, object]:
    source_path = SOURCE_ES / relative
    target_path = SOURCE_EN / relative
    source = source_path.read_text(encoding="utf-8")
    spans = collect_translatable_spans(source)
    replacements: list[tuple[Span, str]] = []
    for span in spans:
        replacements.append((span, translator.translate_span(span.text)))

    translated_source = source
    for span, replacement in reversed(replacements):
        translated_source = translated_source[:span.start] + replacement + translated_source[span.end:]

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(translated_source, encoding="utf-8", newline="\n")

    return {
        "file": relative,
        "source_chars": len(source),
        "translated_spans": len(spans),
        "translated_chars": sum(len(span.text) for span in spans),
        "source_labels": len(re.findall(r"\\label\{", source)),
        "target_labels": len(re.findall(r"\\label\{", translated_source)),
        "source_equation_envs": len(re.findall(r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}", source)),
        "target_equation_envs": len(re.findall(r"\\begin\{(?:equation\*?|align\*?|gather\*?|multline\*?)\}", translated_source)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", default=DEFAULT_FILES)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()

    if args.inventory_only:
        report = []
        for relative in args.files:
            source = (SOURCE_ES / relative).read_text(encoding="utf-8")
            spans = collect_translatable_spans(source)
            report.append({
                "file": relative,
                "spans": len(spans),
                "chars": sum(len(span.text) for span in spans),
            })
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    translator = Translator(batch_size=args.batch_size)
    report: list[dict[str, object]] = []
    for relative in args.files:
        item = translate_file(relative, translator)
        report.append(item)
        save_json_atomic(REPORT_PATH, report)
        print(json.dumps(item, ensure_ascii=False), flush=True)

    print(json.dumps({"report": str(REPORT_PATH), "files": len(report)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
