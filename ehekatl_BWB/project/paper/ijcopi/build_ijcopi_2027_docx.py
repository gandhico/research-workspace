"""Build the double-blind paper in the official IJCOPI 2027 Word template."""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "IJCOPI_MANUSCRIPT.md"
TEMPLATE = HERE / "2027-IJCOPI_template_simple_British_English.docx"
OUTPUT = HERE / "EHEKATL_LQR_DeePC_IJCOPI_2027_Double_Blind.docx"

BACK_MATTER = {
    "Data availability and reproducibility statement",
    "Generative AI use disclosure",
    "Conflict of interest statement",
}


def style_run(run, *, bold: bool = False, italic: bool = False, size: float | None = None) -> None:
    run.bold = bold
    run.italic = italic
    run.font.name = "Times New Roman"
    fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    fonts.set(qn("w:ascii"), "Times New Roman")
    fonts.set(qn("w:hAnsi"), "Times New Roman")
    if size is not None:
        run.font.size = Pt(size)


def add_inline_markdown(paragraph, text: str, size: float = 10.0) -> None:
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


def clear_body(document: Document) -> None:
    body = document._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def set_cell_border(cell, colour: str = "D9D9D9", size: str = "5") -> None:
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
        element.set(qn("w:sz"), size)
        element.set(qn("w:color"), colour)


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_margins(cell, value: int = 80) -> None:
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for edge in ("top", "left", "bottom", "right"):
        item = margins.find(qn(f"w:{edge}"))
        if item is None:
            item = OxmlElement(f"w:{edge}")
            margins.append(item)
        item.set(qn("w:w"), str(value))
        item.set(qn("w:type"), "dxa")


def repeat_table_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    marker = OxmlElement("w:tblHeader")
    marker.set(qn("w:val"), "true")
    properties.append(marker)


def replace_paragraph(paragraph, text: str, *, size: float, bold: bool = False,
                      italic: bool = False, alignment=WD_ALIGN_PARAGRAPH.CENTER) -> None:
    paragraph.clear()
    paragraph.alignment = alignment
    style_run(paragraph.add_run(text), size=size, bold=bold, italic=italic)


def configure_template_furniture(document: Document) -> None:
    section = document.sections[0]
    if section.header.paragraphs:
        replace_paragraph(
            section.header.paragraphs[0],
            "Anonymous authors / International Journal of Combinatorial Optimization Problems and Informatics",
            size=8.5,
        )
    if section.first_page_header.tables:
        masthead = section.first_page_header.tables[0]
        target = masthead.cell(0, 1).paragraphs[0]
        replace_paragraph(
            target,
            "International Journal of Combinatorial Optimization Problems and Informatics\nDouble-blind manuscript",
            size=10.0,
            italic=True,
        )


def parse_metadata(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {"title": lines[0][2:].strip()}
    for line in lines[:20]:
        if line.startswith("**Spanish title:**"):
            result["spanish_title"] = line.split("**Spanish title:**", 1)[1].strip()

    abstract_start = lines.index("## Abstract") + 1
    keyword_index = next(i for i in range(abstract_start, len(lines)) if lines[i].startswith("**Keywords:**"))
    result["abstract"] = " ".join(line.strip() for line in lines[abstract_start:keyword_index] if line.strip())
    keyword_parts = [lines[keyword_index].split("**Keywords:**", 1)[1].strip()]
    i = keyword_index + 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith("## "):
        keyword_parts.append(lines[i].strip())
        i += 1
    result["keywords"] = " ".join(keyword_parts)

    spanish_start = lines.index("## Spanish metadata") + 1
    resumen_index = next(i for i in range(spanish_start, len(lines)) if lines[i].startswith("**Resumen:**"))
    palabras_index = next(i for i in range(resumen_index + 1, len(lines)) if lines[i].startswith("**Palabras clave:**"))
    resumen = [lines[resumen_index].split("**Resumen:**", 1)[1].strip()]
    resumen.extend(line.strip() for line in lines[resumen_index + 1:palabras_index] if line.strip())
    result["resumen"] = " ".join(resumen)
    palabras = [lines[palabras_index].split("**Palabras clave:**", 1)[1].strip()]
    i = palabras_index + 1
    while i < len(lines) and lines[i].strip() and not lines[i].startswith("## "):
        palabras.append(lines[i].strip())
        i += 1
    result["palabras"] = " ".join(palabras)
    return result


def add_title_block(document: Document, metadata: dict[str, str]) -> None:
    title = document.add_paragraph(style="IJCOPI Title")
    add_inline_markdown(title, metadata["title"], 14)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    spanish = document.add_paragraph()
    spanish.paragraph_format.space_after = Pt(7)
    spanish.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(spanish.add_run(metadata["spanish_title"]), italic=True, size=10)

    authors = document.add_paragraph()
    authors.paragraph_format.space_after = Pt(2)
    authors.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(authors.add_run("Anonymous authors"), bold=True, size=10.5)
    affiliation = document.add_paragraph()
    affiliation.paragraph_format.space_after = Pt(8)
    affiliation.alignment = WD_ALIGN_PARAGRAPH.CENTER
    style_run(
        affiliation.add_run("Author details and affiliations withheld for double-blind review"),
        italic=True,
        size=9.5,
    )


def add_metadata_tables(document: Document, metadata: dict[str, str]) -> None:
    table = document.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(5.55)
    table.columns[1].width = Inches(1.35)
    left, right = table.rows[0].cells
    for cell in (left, right):
        set_cell_border(cell)
        set_cell_margins(cell, 90)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    left_p = left.paragraphs[0]
    left_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(left_p.add_run("Abstract. "), bold=True, size=9)
    style_run(left_p.add_run(metadata["abstract"]), size=9)
    keywords_p = left.add_paragraph()
    keywords_p.paragraph_format.space_before = Pt(0)
    keywords_p.paragraph_format.space_after = Pt(0)
    style_run(keywords_p.add_run("Keywords: "), bold=True, size=9)
    style_run(keywords_p.add_run(metadata["keywords"]), size=9)
    right_p = right.paragraphs[0]
    right_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    style_run(right_p.add_run("Article information\n"), bold=True, size=9)
    style_run(right_p.add_run("Submitted for double-blind peer review"), size=9)

    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)
    spanish_table = document.add_table(rows=1, cols=1)
    cell = spanish_table.cell(0, 0)
    set_cell_border(cell)
    set_cell_margins(cell, 90)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(p.add_run("Resumen. "), bold=True, size=9)
    style_run(p.add_run(metadata["resumen"]), size=9)
    palabras_p = cell.add_paragraph()
    palabras_p.paragraph_format.space_before = Pt(0)
    palabras_p.paragraph_format.space_after = Pt(0)
    style_run(palabras_p.add_run("Palabras clave: "), bold=True, size=9)
    style_run(palabras_p.add_run(metadata["palabras"]), size=9)
    after = document.add_paragraph()
    after.paragraph_format.space_after = Pt(0)


def add_table(document: Document, rows: list[list[str]]) -> None:
    if not rows:
        return
    columns = len(rows[0])
    table = document.add_table(rows=1, cols=columns)
    table.autofit = False
    repeat_table_header(table.rows[0])
    if columns == 3:
        widths = [3.65, 1.35, 1.35]
    elif columns == 4:
        widths = [1.25, 1.85, 2.65, 0.65]
    else:
        widths = [6.8 / columns] * columns
    for index, value in enumerate(rows[0]):
        cell = table.rows[0].cells[index]
        cell.width = Inches(widths[index])
        set_cell_shading(cell, "E7E6E6")
        set_cell_border(cell)
        set_cell_margins(cell, 70)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if index == 0 else WD_ALIGN_PARAGRAPH.CENTER
        add_inline_markdown(paragraph, value, 8.2)
        for run in paragraph.runs:
            run.bold = True
    for row_index, values in enumerate(rows[1:], start=1):
        cells = table.add_row().cells
        for index, value in enumerate(values):
            cell = cells[index]
            cell.width = Inches(widths[index])
            set_cell_border(cell)
            set_cell_margins(cell, 70)
            if row_index % 2 == 0:
                set_cell_shading(cell, "F7F7F7")
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if index in (0, 2) else WD_ALIGN_PARAGRAPH.CENTER
            add_inline_markdown(paragraph, value, 8.0)
    trailing = document.add_paragraph()
    trailing.paragraph_format.space_after = Pt(0)


def add_picture(document: Document, alt: str, relative: str, figure_number: int) -> None:
    path = (HERE.parent / relative).resolve()
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    paragraph.add_run().add_picture(str(path), width=Inches(6.25))
    caption = document.add_paragraph(style="IJCOPI Caption")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_inline_markdown(caption, f"Fig. {figure_number}. {alt}", 9)


def add_equation(document: Document, equation_index: int) -> None:
    image = HERE / "equations" / f"equation_{equation_index}.png"
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.space_after = Pt(4)
    width = 4.9 if equation_index in (4, 7) else 3.6
    paragraph.add_run().add_picture(str(image), width=Inches(width))


def collect_paragraph(lines: list[str], index: int) -> tuple[str, int]:
    parts = [lines[index].strip()]
    index += 1
    while index < len(lines):
        candidate = lines[index].strip()
        if not candidate or candidate.startswith(("#", "|", "- ", "![")) or candidate == r"\[":
            break
        parts.append(candidate)
        index += 1
    return " ".join(parts), index


def add_body(document: Document, lines: list[str]) -> None:
    index = lines.index("## 1. Introduction")
    equation_index = 0
    figure_number = 0
    in_references = False
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
        if line.startswith("## "):
            heading = line[3:]
            if heading in BACK_MATTER:
                index += 1
                while index < len(lines) and not lines[index].strip():
                    index += 1
                text, index = collect_paragraph(lines, index)
                paragraph = document.add_paragraph()
                paragraph.paragraph_format.space_before = Pt(5)
                style_run(paragraph.add_run(heading.capitalize() + ": "), bold=True, size=9)
                add_inline_markdown(paragraph, text, 9)
                continue
            paragraph = document.add_paragraph(heading, style="Heading 1")
            paragraph.paragraph_format.keep_with_next = True
            in_references = heading == "References"
            index += 1
            continue
        if line.startswith("### "):
            paragraph = document.add_paragraph(line[4:], style="Heading 2")
            paragraph.paragraph_format.space_before = Pt(5)
            paragraph.paragraph_format.space_after = Pt(2)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.keep_with_next = True
            index += 1
            continue
        image_match = re.fullmatch(r"!\[(.+)]\((.+)\)", line)
        if image_match:
            figure_number += 1
            add_picture(document, image_match.group(1), image_match.group(2), figure_number)
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
        if re.fullmatch(r"\*\*Table \d+\..+\*\*", line):
            paragraph = document.add_paragraph(style="IJCOPI Caption")
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
            add_inline_markdown(paragraph, line[2:-2], 10)
            index += 1
            continue

        text, index = collect_paragraph(lines, index)
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if in_references:
            paragraph.paragraph_format.left_indent = Inches(0.22)
            paragraph.paragraph_format.first_line_indent = Inches(-0.22)
            paragraph.paragraph_format.space_after = Pt(4)
        add_inline_markdown(paragraph, text)


def build() -> None:
    document = Document(TEMPLATE)
    configure_template_furniture(document)
    clear_body(document)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    metadata = parse_metadata(lines)
    add_title_block(document, metadata)
    add_metadata_tables(document, metadata)
    add_body(document, lines)

    properties = document.core_properties
    properties.title = "From Offline Optimality to Real-Time Simulation Flight"
    properties.subject = "Double-blind IJCOPI 2027 manuscript"
    properties.author = "Anonymous"
    properties.last_modified_by = "Anonymous"
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
