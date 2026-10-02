from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(r"C:\Research\papers\ACC2027_Gate_Residual_Control\paper\research_brief_2026-09-23")
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

NAVY = "17365D"
BLUE = "2F75B5"
TEAL = "159A8C"
ORANGE = "D97824"
PALE_BLUE = "EAF2F8"
PALE_GRAY = "F3F5F7"
MID_GRAY = "6B7280"
GRID = "D9D9D9"
BLACK = "000000"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=65, start=75, bottom=65, end=75) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=GRID, size="5") -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        elem = borders.find(tag)
        if elem is None:
            elem = OxmlElement(f"w:{edge}")
            borders.append(elem)
        elem.set(qn("w:val"), "single")
        elem.set(qn("w:sz"), size)
        elem.set(qn("w:space"), "0")
        elem.set(qn("w:color"), color)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_with_next(paragraph, value=True) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    node = p_pr.find(qn("w:keepNext"))
    if node is None:
        node = OxmlElement("w:keepNext")
        p_pr.append(node)
    node.set(qn("w:val"), "1" if value else "0")


def add_hyperlink(paragraph, text: str, url: str, font_size=7.2) -> None:
    part = paragraph.part
    rel_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rel_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), BLUE)
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    size = OxmlElement("w:sz")
    size.set(qn("w:val"), str(int(font_size * 2)))
    r_pr.append(size)
    run.append(r_pr)
    text_node = OxmlElement("w:t")
    text_node.text = text
    run.append(text_node)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def add_field(paragraph, field_code: str) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field_code
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    display = OxmlElement("w:t")
    display.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, display, end])


def style_run(run, size=9.5, bold=False, italic=False, color=BLACK, name="Arial") -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor.from_string(color)


def add_body(doc, text: str, *, after=3.5, before=0, size=9.4, keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.04
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(p.add_run(text), size=size)
    if keep:
        keep_with_next(p)
    return p


def add_heading(doc, text: str, *, level=1, before=6, after=3):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.keep_with_next = True
    p.add_run(text)
    return p


def add_compact_bullets(doc, items, *, size=8.8, after=1.4):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(0.18)
        p.paragraph_format.first_line_indent = Inches(-0.12)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.0
        style_run(p.add_run(item), size=size)


def build_architecture() -> Path:
    path = ASSETS / "brief_architecture.png"
    W, H = 2640, 510
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    regular = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 30)
    bold = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 31)
    small = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 24)
    formula = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 27)

    def centered_multiline(rect, label, font, fill="#16293D", spacing=3):
        box = d.multiline_textbbox((0, 0), label, font=font, align="center", spacing=spacing)
        tw, th = box[2] - box[0], box[3] - box[1]
        x0, y0, x1, y1 = rect
        d.multiline_text(((x0+x1-tw)/2, (y0+y1-th)/2-2), label, font=font,
                         fill=fill, align="center", spacing=spacing)

    def box(rect, label, fill):
        d.rounded_rectangle(rect, radius=18, fill=fill, outline="#41556B", width=3)
        centered_multiline(rect, label, bold, spacing=2)

    def arrow(points, fill="#41556B", width=4):
        for a, b in zip(points[:-1], points[1:]):
            d.line([a, b], fill=fill, width=width)
        x1, y1 = points[-2]
        x2, y2 = points[-1]
        if abs(x2-x1) >= abs(y2-y1):
            s = 1 if x2 > x1 else -1
            tri = [(x2, y2), (x2-15*s, y2-9), (x2-15*s, y2+9)]
        else:
            s = 1 if y2 > y1 else -1
            tri = [(x2, y2), (x2-9, y2-15*s), (x2+9, y2-15*s)]
        d.polygon(tri, fill=fill)

    top_y0, top_y1 = 78, 224
    bot_y0, bot_y1 = 310, 452
    x = [32, 515, 1010, 1505, 2000]
    widths = [365, 395, 375, 375, 445]
    labels = ["Mission and\nstate feedback", "Quaternion\nPD + rate ff",
              "Bounded torque\naddition", "Rotor\nallocation", "MuJoCo or\nhardware plant"]
    for xx, ww, label in zip(x, widths, labels):
        box((xx, top_y0, xx+ww, top_y1), label, "#F3F5F7")
    bx = [515, 1010, 1505, 2000]
    bw = [395, 375, 375, 445]
    blabels = ["Paired-current\nencoding", "Six CMG units\nstate v and gate r",
               "Decoder W\nand PES update", "Saturation-aware\noutput mask m"]
    for xx, ww, label in zip(bx, bw, blabels):
        box((xx, bot_y0, xx+ww, bot_y1), label, "#EAF2F8")

    cy = (top_y0+top_y1)//2
    for i in range(4):
        arrow([(x[i]+widths[i], cy), (x[i+1], cy)])
    arrow([(2445, cy), (2580, cy), (2580, 30), (215, 30), (215, top_y0)])
    d.text((2310, 0), "state q, ω", font=small, fill="#41556B")

    arrow([(712, top_y1), (712, bot_y0)], fill="#2F75B5")
    for i in range(3):
        arrow([(bx[i]+bw[i], 381), (bx[i+1], 381)], fill="#2F75B5")
    arrow([(2220, bot_y0), (2220, 272), (1190, 272), (1190, top_y1)], fill="#2F75B5")
    d.text((1395, 470), "PES adapts the decoder; the mask limits application, not learning",
           font=small, fill="#6B7280")
    im.save(path, optimize=True)
    return path


def build_results_plot() -> Path:
    path = ASSETS / "brief_results.png"
    W, H = 2640, 850
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    reg = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 27)
    small = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 23)
    tiny = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 20)
    bold = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 31)
    axis_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 24)

    def txt(xy, text, font=reg, fill="#1F2937", anchor="la"):
        d.text(xy, text, font=font, fill=fill, anchor=anchor)

    def hline(x0, x1, y, fill="#E5E7EB", width=2):
        d.line((x0, y, x1, y), fill=fill, width=width)

    # Panel A
    x0, y0, pw, ph = 125, 105, 1060, 590
    txt((x0, 45), "A  Nominal missions", bold)
    missions = ["Roll", "Full3", "Hard45", "Hardstep", "Yaw360"]
    vals1 = [78.4, 12.4, 13.8, -2.0, 41.8]
    vals2 = [59.9, 5.4, 7.3, -0.2, 20.3]
    xmin, xmax = -8, 84
    zero = x0 + int((0-xmin)/(xmax-xmin)*pw)
    for tick in [0, 20, 40, 60, 80]:
        xx = x0 + int((tick-xmin)/(xmax-xmin)*pw)
        d.line((xx, y0, xx, y0+ph), fill="#E5E7EB", width=2)
        txt((xx, y0+ph+24), str(tick), small, anchor="ma")
    d.line((zero, y0, zero, y0+ph), fill="#4B5563", width=3)
    rowh = ph/5
    for i, mission in enumerate(missions):
        cy = int(y0 + (i+0.5)*rowh)
        txt((x0-10, cy), mission, reg, anchor="rm")
        for j, (val, color) in enumerate(((vals1[i], "#2F75B5"), (vals2[i], "#159A8C"))):
            yy = cy - 27 + j*34
            xv = x0 + int((val-xmin)/(xmax-xmin)*pw)
            left, right = sorted((zero, xv))
            d.rounded_rectangle((left, yy-13, max(left+2, right), yy+13), radius=5, fill=color)
            anchor = "lm" if val >= 0 else "rm"
            tx = xv + 10 if val >= 0 else xv - 10
            txt((tx, yy), f"{val:.1f}", tiny, anchor=anchor)
    txt((x0+pw/2, 785), "Reduction in mean quaternion error (%)", axis_font, anchor="ma")
    d.rectangle((925, 73, 952, 100), fill="#2F75B5")
    txt((965, 86), "X2", small, anchor="lm")
    d.rectangle((1035, 73, 1062, 100), fill="#159A8C")
    txt((1075, 86), "CF2", small, anchor="lm")

    # Panel B
    x0, y0, pw, ph = 1280, 105, 700, 590
    txt((x0, 45), "B  Robustness", bold)
    labs = ["Noise\nFull3", "Noise\nHard45", "Torque\nbursts"]
    x2r, cf2r = [11.3, 10.8, 14.4], [3.9, 4.0, 5.9]
    for tick in [0, 4, 8, 12, 16]:
        yy = int(y0+ph-(tick/16)*ph)
        hline(x0, x0+pw, yy)
        txt((x0-12, yy), str(tick), small, anchor="rm")
    groupw = pw/3
    for i, label in enumerate(labs):
        cx = x0 + (i+0.5)*groupw
        for j, (v, color) in enumerate(((x2r[i], "#2F75B5"), (cf2r[i], "#159A8C"))):
            xx0 = int(cx-58+j*60)
            yy = int(y0+ph-(v/16)*ph)
            d.rounded_rectangle((xx0, yy, xx0+54, y0+ph), radius=5, fill=color)
            txt((xx0+27, yy-10), f"{v:.1f}", tiny, anchor="ms")
        tw = d.multiline_textbbox((0, 0), label, font=small, align="center", spacing=2)
        d.multiline_text((cx-(tw[2]-tw[0])/2, y0+ph+16), label, font=small,
                         fill="#1F2937", align="center", spacing=2)
    txt((x0, 88), "Error reduction (%)", tiny, fill="#6B7280")
    txt((x0+pw/2, 805), "Noise: specified synthetic level; bursts: active phase",
        tiny, fill="#6B7280", anchor="ma")

    # Panel C
    x0, y0, pw, ph = 2080, 105, 510, 590
    txt((x0, 45), "C  3DOF Hover Roll", bold)
    labels, vals = ["PD", "CMG\nβ=0.10", "CMG\nβ=0.20"], [5.4630, 5.3869, 5.3449]
    ymin, ymax = 5.15, 5.56
    for tick in [5.2, 5.3, 5.4, 5.5]:
        yy = int(y0+ph-(tick-ymin)/(ymax-ymin)*ph)
        hline(x0, x0+pw, yy)
        txt((x0-12, yy), f"{tick:.1f}", tiny, anchor="rm")
    colors = ["#7B8794", "#77AADD", "#2F75B5"]
    gw = pw/3
    for i, (label, v, color) in enumerate(zip(labels, vals, colors)):
        cx = x0+(i+0.5)*gw
        yy = int(y0+ph-(v-ymin)/(ymax-ymin)*ph)
        d.rounded_rectangle((int(cx-48), yy, int(cx+48), y0+ph), radius=5, fill=color)
        txt((cx, yy-10), f"{v:.3f}", tiny, anchor="ms")
        box = d.multiline_textbbox((0, 0), label, font=small, align="center", spacing=2)
        d.multiline_text((cx-(box[2]-box[0])/2, y0+ph+16), label, font=small,
                         fill="#1F2937", align="center", spacing=2)
    txt((x0, 88), "Mean error (deg)", tiny, fill="#6B7280")
    txt((x0+pw/2, 805), "One matched 8 s run per arm; feasibility only",
        tiny, fill="#6B7280", anchor="ma")

    im.save(path, optimize=True)
    return path


def format_table(table, widths, font_size=7.7, header_fill=NAVY):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    set_repeat_table_header(table.rows[0])
    for r_idx, row in enumerate(table.rows):
        for c_idx, cell in enumerate(row.cells):
            cell.width = Inches(widths[c_idx])
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell)
            if r_idx == 0:
                set_cell_shading(cell, header_fill)
            elif r_idx % 2 == 0:
                set_cell_shading(cell, PALE_BLUE)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx else WD_ALIGN_PARAGRAPH.LEFT
                for run in p.runs:
                    style_run(run, size=font_size, bold=(r_idx == 0), color="FFFFFF" if r_idx == 0 else BLACK)


def build_docx() -> Path:
    arch_path = build_architecture()
    results_path = build_results_plot()
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    sec.top_margin = Inches(0.48)
    sec.bottom_margin = Inches(0.46)
    sec.left_margin = Inches(0.58)
    sec.right_margin = Inches(0.58)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(9.4)
    for name, size in (("Title", 19), ("Subtitle", 10.5), ("Heading 1", 12.5), ("Heading 2", 10.5)):
        style = styles[name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), style.font.name)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), style.font.name)
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.bold = name in ("Title", "Heading 1", "Heading 2")
    title_style_ppr = styles["Title"]._element.find(qn("w:pPr"))
    if title_style_ppr is not None:
        title_style_border = title_style_ppr.find(qn("w:pBdr"))
        if title_style_border is not None:
            title_style_ppr.remove(title_style_border)

    title = doc.add_paragraph(style="Title")
    title.paragraph_format.space_after = Pt(1)
    style_run(title.add_run("CMG PES Neuromorphic Residual Control Research Brief"), size=17.2, bold=True, name="Arial")
    title_ppr = title._p.get_or_add_pPr()
    borders = title_ppr.find(qn("w:pBdr"))
    if borders is not None:
        title_ppr.remove(borders)
    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(6)
    style_run(subtitle.add_run("Current evidence hardware hypothesis and publication strategy"), size=10.2, bold=True, color=NAVY)
    style_run(subtitle.add_run("  |  23 September 2026"), size=9.2, color=MID_GRAY)

    add_heading(doc, "Current conclusion", before=0, after=2)
    add_body(
        doc,
        "The project now supports a credible control result: a bounded online CMG-PES residual improves a strong quaternion PD controller with desired-rate feedforward on four smooth attitude missions across two MuJoCo multirotor models. The saturation-aware output mask prevents the learned correction from opposing a baseline axis already at its torque limit. It reduces, but does not reverse, the remaining Hardstep loss. The evidence therefore supports an ACC 2027 submission while preserving a clear hardware-validation path.",
        after=4.0,
    )

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(arch_path), width=Inches(7.15))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(4)
    style_run(cap.add_run("Figure 1  Control flow. The learned term is bounded before the unchanged allocation and plant interfaces; PES updates the decoder online."), size=7.5, italic=True, color=MID_GRAY)

    add_heading(doc, "What is being tested", before=2, after=2)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.02
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    style_run(p.add_run("Baseline. "), size=9.2, bold=True)
    style_run(p.add_run("The tuned controller produces the saturated request "), size=9.2)
    style_run(p.add_run("u0"), size=9.2, italic=True)
    style_run(p.add_run(". Residual path. Paired currents drive six continuous membrane-gate units with states "), size=9.2)
    style_run(p.add_run("v"), size=9.2, italic=True)
    style_run(p.add_run(" and "), size=9.2)
    style_run(p.add_run("r"), size=9.2, italic=True)
    style_run(p.add_run("; the activity feeds an 18-weight decoder. PES adapts those weights from quaternion and rate error. The applied correction is δ = βℓ ⊙ m ⊙ s, where β sets authority, ℓ is the torque bound, s is the clipped decoder output, and m is the saturation-aware mask. Thus |δi| ≤ βℓi and β = 0 recovers the baseline exactly."), size=9.2)

    add_heading(doc, "Current numerical evidence", before=3, after=2)
    headers = ["Evidence", "X2", "CF2", "Interpretation"]
    rows = [
        ["Five-mission geometric mean", "37.3%", "22.4%", "Gated CMG-PES vs tuned PD+ff at ρ = 3"],
        ["Four smooth missions", "12.4–78.4%", "5.4–59.9%", "Roll, Full3, Hard45, and Yaw360 all improve"],
        ["Hardstep", "−2.0%", "−0.2%", "Near parity; the residual does not beat the baseline"],
        ["Repeated torque bursts", "14.4%", "5.9%", "Reduction in burst-phase error during Hover"],
        ["Specified sensor noise", "11.3 / 10.8%", "3.9 / 4.0%", "Full3 / Hard45 at the higher tested noise level"],
    ]
    table = doc.add_table(rows=1, cols=4)
    for i, text in enumerate(headers):
        table.rows[0].cells[i].text = text
    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = text
    format_table(table, [1.55, 0.85, 0.9, 3.55], font_size=7.55)

    foot = doc.add_paragraph()
    foot.paragraph_format.space_before = Pt(2)
    foot.paragraph_format.space_after = Pt(0)
    style_run(foot.add_run("Metric: mean shortest-path quaternion-angle error over 45 s. CF2 denotes the proposed 1.5× rotor-authority simulation model, not stock-hardware performance."), size=7.3, italic=True, color=MID_GRAY)

    add_heading(doc, "Why the research is promising", before=4, after=2)
    add_compact_bullets(doc, [
        "The architecture augments a conventional controller rather than replacing it. The baseline, allocator, force limits, and sensing interface remain explicit, while the learned authority is bounded.",
        "The main mechanism is identifiable. Online PES decoder adaptation and persistent activity account for most of the improvement; conductance modulation is nearly inactive in the present saturated-activity regime. This narrows the scientific claim and creates a precise next experiment.",
        "The same residual interface runs in direct Python and Nengo. Ten matched cases agreed to 2.013 × 10⁻⁶ relative mean error, which supports implementation consistency but is not a proof of mathematical equivalence.",
        "Hardstep exposes decoder lag during actuator-limited slews. The output mask prevents catastrophic opposition and restores near parity without hiding the remaining settling-tail limitation.",
    ], size=8.4, after=1.0)

    doc.add_page_break()

    add_heading(doc, "Results and their limits", before=0, after=2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(results_path), width=Inches(7.15))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(4)
    style_run(cap.add_run("Figure 2  Current evidence. Positive values denote lower error than the matched baseline. Panel C is a single matched physical run per controller and is not a statistical hardware claim."), size=7.45, italic=True, color=MID_GRAY)

    add_heading(doc, "Hardware hypothesis and decisive validation", before=3, after=2)
    add_body(
        doc,
        "The first matched Nengo 3DOF Hover Roll trial reduced mean attitude error from 5.463° with PD to 5.345° with CMG-PES at β = 0.20, a 2.16% improvement, and the signed Roll pair carried the neural activity. This supports real-time feasibility. It does not yet establish repeatable performance because each arm has one matched eight-second run.",
        size=8.8,
        after=2.2,
    )
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.0
    style_run(p.add_run("The hypothesis is confirmed only if "), size=8.8, bold=True)
    style_run(p.add_run("interleaved baseline and CMG trials show a consistent paired improvement across repeated Roll trials, then Full3 and disturbance-recovery tests, without increased aborts, saturation, peak error, or deadline misses. An initial minimum is five paired trials per condition with frozen parameters and reported confidence intervals, followed by a power-based sample-size decision."), size=8.8)

    add_heading(doc, "Publication path", before=3, after=2)
    headers = ["Venue", "Best version of the work", "Evidence needed"]
    rows = [
        ["ACC 2027 [1]", "Current control architecture, bounds, ablations, and two-model study", "Ready for advisor review; retain the honest Hardstep and hardware limits"],
        ["IEEE CCTA 2027 [2]", "Implementation-focused extension", "Repeated 3DOF Hover and preferably QDrone results"],
        ["IEEE L-CSS [3]", "Concise control contribution with rapid journal review", "Sharper theorem or stability result and a self-contained six-page treatment"],
        ["IEEE TCST [4]", "Full archival control-technology paper", "Multi-mission hardware, repeatability, timing, safety, and matched adaptive baselines"],
        ["NCE [5] or RA-L [6]", "Neuromorphic mechanism or robotics implementation", "Broader neuron study plus neuromorphic hardware/energy data, or stronger robot experiments"],
    ]
    table = doc.add_table(rows=1, cols=3)
    for i, text in enumerate(headers):
        table.rows[0].cells[i].text = text
    for row in rows:
        cells = table.add_row().cells
        for i, text in enumerate(row):
            cells[i].text = text
    format_table(table, [1.25, 2.55, 3.50], font_size=7.25)

    sources = [
        ("[1] American Control Conference overview", "https://a2c2.org/events/acc"),
        ("[2] IEEE CCTA 2027 scope", "https://ccta2027.ieeecss.org/"),
        ("[3] IEEE Control Systems Letters scope", "https://ieeecss.org/publication/ieee-control-systems-letters"),
        ("[4] IEEE Transactions on Control Systems Technology scope", "https://ieeecss.org/publication/transactions-control-systems-technology"),
        ("[5] Neuromorphic Computing and Engineering scope", "https://publishingsupport.iopscience.iop.org/journals/neuromorphic-computing-engineering/about-neuromorphic-computing-engineering/"),
        ("[6] IEEE Robotics and Automation Letters scope", "https://www.ieee-ras.org/publications/ieee-robotics-and-automation-letters/"),
    ]
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 0.9
    style_run(p.add_run("Venue sources  "), size=7.0, bold=True, color=MID_GRAY)
    for idx, (label, url) in enumerate(sources):
        if idx:
            style_run(p.add_run("  |  "), size=7.0, color=MID_GRAY)
        add_hyperlink(p, label, url, font_size=7.0)

    for section in doc.sections:
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        style_run(fp.add_run("CMG-PES research brief  |  "), size=7.5, color=MID_GRAY)
        add_field(fp, "PAGE")

    out = OUTPUT / "CMG_PES_Research_Brief_2026-09-23.docx"
    doc.save(out)
    return out


if __name__ == "__main__":
    print(build_docx())
