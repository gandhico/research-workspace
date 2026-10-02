"""Build the double-blind IJCOPI manuscript from its auditable Markdown source."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "IJCOPI_MANUSCRIPT.md"
OUTPUT = HERE / "EHEKATL_LQR_DeePC_IJCOPI_Double_Blind.docx"


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_border(cell, colour: str = "D9D9D9") -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), colour)


def repeat_table_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    properties.append(marker)


def set_keep_with_next(paragraph, value: bool = True) -> None:
    paragraph.paragraph_format.keep_with_next = value


def style_run(run, *, bold: bool = False, italic: bool = False, size: float | None = None) -> None:
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:ascii"), "Times New Roman")
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), "Times New Roman")
    if size:
        run.font.size = Pt(size)


def add_inline_markdown(paragraph, text: str, size: float = 10.5) -> None:
    # Inline code is rendered as ordinary text because the manuscript uses it
    # only for reproducibility paths. Bold and italic retain semantic emphasis.
    token = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
    position = 0
    for match in token.finditer(text):
        if match.start() > position:
            style_run(paragraph.add_run(text[position:match.start()]), size=size)
        value = match.group(0)
        if value.startswith("**"):
            style_run(paragraph.add_run(value[2:-2]), bold=True, size=size)
        elif value.startswith("*"):
            style_run(paragraph.add_run(value[1:-1]), italic=True, size=size)
        else:
            style_run(paragraph.add_run(value[1:-1]), size=size)
        position = match.end()
    if position < len(text):
        style_run(paragraph.add_run(text[position:]), size=size)


def configure_document(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.68)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.05
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    title = document.styles["Title"]
    title.font.name = "Times New Roman"
    title._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
    title._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
    title.font.size = Pt(17)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_after = Pt(10)

    for name, size, before, after in (("Heading 1", 12.5, 10, 4), ("Heading 2", 11.0, 7, 3)):
        style = document.styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Times New Roman")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Times New Roman")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(footer.add_run("Double-blind manuscript  |  EHEKATL BWB LQR and DeePC"), size=8)


def add_table(document: Document, rows: list[list[str]]) -> None:
    if not rows:
        return
    width = len(rows[0])
    table = document.add_table(rows=1, cols=width)
    table.autofit = True
    repeat_table_header(table.rows[0])
    for index, value in enumerate(rows[0]):
        cell = table.rows[0].cells[index]
        set_cell_shading(cell, "1F4E78")
        set_cell_border(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_inline_markdown(paragraph, value, 8.5)
        for run in paragraph.runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
    for row_index, values in enumerate(rows[1:], start=1):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            set_cell_border(cell)
            if row_index % 2 == 0:
                set_cell_shading(cell, "EAF2F8")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if index == 0 else WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(1.5)
            add_inline_markdown(paragraph, value, 8.3)
    document.add_paragraph().paragraph_format.space_after = Pt(0)


def add_picture(document: Document, alt: str, relative: str) -> None:
    path = (HERE.parent / relative).resolve()
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_keep_with_next(paragraph)
    paragraph.add_run().add_picture(str(path), width=Inches(6.35))
    caption = document.add_paragraph()
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.space_after = Pt(7)
    style_run(caption.add_run(alt), italic=True, size=9)


def add_equation(document: Document, equation_index: int) -> None:
    image = HERE / "equations" / f"equation_{equation_index}.png"
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.add_run().add_picture(str(image), width=Inches(4.9 if equation_index in (4, 7) else 3.6))


def build() -> None:
    document = Document()
    configure_document(document)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    index = 0
    equation_index = 0
    first_title = True
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line == r"\[":
            while index < len(lines) and lines[index].strip() != r"\]":
                index += 1
            equation_index += 1
            add_equation(document, equation_index)
            index += 1
            continue
        if line.startswith("# "):
            paragraph = document.add_paragraph(style="Title")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline_markdown(paragraph, line[2:], 17)
            first_title = False
            index += 1
            continue
        if line.startswith("## "):
            document.add_paragraph(line[3:], style="Heading 1")
            index += 1
            continue
        if line.startswith("### "):
            document.add_paragraph(line[4:], style="Heading 2")
            index += 1
            continue
        image_match = re.fullmatch(r"!\[(.+)]\((.+)\)", line)
        if image_match:
            add_picture(document, image_match.group(1), image_match.group(2))
            index += 1
            continue
        if line.startswith("|"):
            table_rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                values = [part.strip() for part in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", value) for value in values):
                    table_rows.append(values)
                index += 1
            add_table(document, table_rows)
            continue
        if line.startswith("- "):
            paragraph = document.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.left_indent = Inches(0.22)
            paragraph.paragraph_format.first_line_indent = Inches(-0.14)
            add_inline_markdown(paragraph, line[2:])
            index += 1
            continue

        parts = [line]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith(("#", "|", "- ", "![")) or candidate == r"\[":
                break
            parts.append(candidate)
            index += 1
        paragraph = document.add_paragraph()
        if parts[0] == "**Double-blind manuscript**":
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(12)
        add_inline_markdown(paragraph, " ".join(parts))

    properties = document.core_properties
    properties.title = "From Offline Optimality to Real-Time Simulation Flight"
    properties.subject = "Double-blind IJCOPI manuscript"
    properties.author = "Anonymous"
    properties.last_modified_by = "Anonymous"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
