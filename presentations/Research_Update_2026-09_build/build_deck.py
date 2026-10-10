"""Build the Sept-2026 research-update slides on Gandhi's own NMSU template.

Template = a copy of C:\\Research\\presentations\\062526_biwm_ECE.pptx with every
slide removed (masters, layouts, theme and logo are kept), so the new slides can
be inserted into the live deck with Reuse Slides and look native.

Every number below is copied from a named source file (see the SOURCE comments);
nothing is estimated.
"""
from pathlib import Path
import copy

from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_LABEL_POSITION
from pptx.oxml.ns import qn

SCR = Path(__file__).resolve().parent
FIG = SCR / "figs"
MEDIA = SCR / "ud_media"
TEMPLATE = Path(r"C:\Research\presentations\062526_biwm_ECE.pptx")  # read only; its slides are dropped in memory
OUT = SCR.parent / "Research_Update_Slides_2026-09_rebuilt.pptx"

CRIMSON = "8C0B41"
TEAL = "A7BABE"      # template accent1 (status boxes)
TEAL_D = "5F7F86"
SAND = "CFC7BD"      # template accent2
INK = "1F1F1F"
GRAY = "595959"
LIGHT = "F4F5F6"
RULE = "D5D9DB"
WHITE = "FFFFFF"

TITLE_FONT = "Tahoma"
BODY_FONT = "Calibri"


def rgb(h):
    return RGBColor.from_string(h)


# ---------------------------------------------------------------- template
prs = Presentation(str(TEMPLATE))
sld_ids = prs.slides._sldIdLst
for sld in list(sld_ids):
    prs.part.drop_rel(sld.rId)
    sld_ids.remove(sld)
LAYOUT = next(l for l in prs.slide_layouts if l.name == "Title and Content")


# ---------------------------------------------------------------- helpers
def set_run(run, size=13, bold=False, color=INK, italic=False, font=BODY_FONT):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = font
    f.color.rgb = rgb(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", font)


def add_bullet(p, color=CRIMSON, indent=0.17, char="\u25AA"):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(int(Inches(indent))))
    pPr.set("indent", str(-int(Inches(indent))))
    for tag in ("a:buClr", "a:buFont", "a:buChar", "a:buNone"):
        old = pPr.find(qn(tag))
        if old is not None:
            pPr.remove(old)
    buClr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(buClr, qn("a:srgbClr")).set("val", color)
    buFont = etree.SubElement(pPr, qn("a:buFont"))
    buFont.set("typeface", "Arial")
    etree.SubElement(pPr, qn("a:buChar")).set("char", char)


def text(slide, x, y, w, h, paras, anchor="t", margin=0.04, autosize=False):
    """paras: list of dicts {runs:[(txt, fmt)], align, bullet, after, before, line}"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    first = True
    for para in paras:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = {"l": PP_ALIGN.LEFT, "r": PP_ALIGN.RIGHT, "c": PP_ALIGN.CENTER,
                       "j": PP_ALIGN.JUSTIFY}[para.get("align", "l")]
        if para.get("after") is not None:
            p.space_after = Pt(para["after"])
        if para.get("before") is not None:
            p.space_before = Pt(para["before"])
        if para.get("line") is not None:
            p.line_spacing = para["line"]
        for txt, fmt in para["runs"]:
            r = p.add_run()
            r.text = txt
            set_run(r, **fmt)
        if para.get("bullet"):
            add_bullet(p, **(para["bullet"] if isinstance(para["bullet"], dict) else {}))
    return tb


def P(*runs, **kw):
    """Shorthand paragraph: P(("text", {fmt}), ..., align=, bullet=, after=)"""
    return dict(runs=list(runs), **kw)


def R(t, size=13, bold=False, color=INK, italic=False, font=BODY_FONT):
    return (t, dict(size=size, bold=bold, color=color, italic=italic, font=font))


def box(slide, x, y, w, h, fill=LIGHT, line=None, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
        dash=False, line_w=0.75, shadow=False):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(line_w)
        if dash:
            s.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    if not shadow:
        spPr = s._element.spPr
        eff = spPr.find(qn("a:effectLst"))
        if eff is None:
            etree.SubElement(spPr, qn("a:effectLst"))
    s.text_frame.text = ""
    return s


def shape_text(s, paras, anchor="m", margin=0.06):
    tf = s.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    first = True
    for para in paras:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = {"l": PP_ALIGN.LEFT, "r": PP_ALIGN.RIGHT, "c": PP_ALIGN.CENTER}[para.get("align", "c")]
        if para.get("after") is not None:
            p.space_after = Pt(para["after"])
        for txt, fmt in para["runs"]:
            r = p.add_run()
            r.text = txt
            set_run(r, **fmt)
        if para.get("bullet"):
            add_bullet(p, **(para["bullet"] if isinstance(para["bullet"], dict) else {}))


EVIDENCE = {
    "software": (TEAL, INK, None, "Verified software"),
    "twin": (SAND, INK, None, "Digital twin"),
    "hardware": (CRIMSON, WHITE, None, "Hardware"),
    "proposed": (WHITE, GRAY, "8C8C8C", "Proposed"),
}


def chip(slide, x, y, label, kind="software", w=None, h=0.28, size=10.5):
    fill, fg, line, _ = EVIDENCE[kind]
    if w is None:
        w = 0.24 + 0.074 * len(label) * size / 10.5
    s = box(slide, x, y, w, h, fill=fill, line=line or ("3F5256" if kind == "software" else None),
            radius=0.3, dash=(kind == "proposed"), line_w=0.75)
    shape_text(s, [P(R(label, size=size, bold=(kind == "hardware"), color=fg))], margin=0.04)
    return x + w + 0.10


def status_chip(slide, x, y, label, flag=None, w=3.35):
    """Gray rounded box exactly like the user's paper-status boxes."""
    s = box(slide, x, y, w, 0.36, fill=TEAL, line="1B2A2D", radius=0.25, line_w=1.25)
    shape_text(s, [P(R(label, size=13, color=INK), align="l")], margin=0.12)
    if flag:
        slide.shapes.add_picture(str(MEDIA / flag), Inches(x + w - 0.62), Inches(y + 0.045), height=Inches(0.27))


def number_chip(slide, x, y, n):
    s = box(slide, x, y, 0.5, 0.38, fill=TEAL, line="1B2A2D", radius=0.25, line_w=1.25)
    shape_text(s, [P(R(str(n), size=15, color=WHITE, bold=True))], margin=0.0)


def pic(slide, path, x, y, w=None, h=None):
    kw = {}
    if w is not None:
        kw["width"] = Inches(w)
    if h is not None:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kw)


def set_cell_border(cell, color=RULE, width=0.75, sides=("b",)):
    tcPr = cell._tc.get_or_add_tcPr()
    order = ["lnL", "lnR", "lnT", "lnB"]
    for side in ("l", "r", "t", "b"):
        tag = "a:ln" + side.upper()
        old = tcPr.find(qn(tag))
        if old is not None:
            tcPr.remove(old)
    idx = 0
    for side, name in zip(("l", "r", "t", "b"), order):
        ln = etree.Element(qn("a:" + name))
        if side in sides:
            ln.set("w", str(int(Pt(width))))
            sf = etree.SubElement(ln, qn("a:solidFill"))
            etree.SubElement(sf, qn("a:srgbClr")).set("val", color)
        else:
            ln.set("w", "0")
            etree.SubElement(ln, qn("a:noFill"))
        tcPr.insert(idx, ln)
        idx += 1


def table(slide, x, y, col_w, rows, row_h=0.3, header=True, size=11, header_size=11,
          header_fill=CRIMSON, zebra=True, bold_first_col=False, aligns=None, col_colors=None):
    nrows, ncols = len(rows), len(rows[0])
    gf = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(sum(col_w)),
                                Inches(row_h * nrows))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"   # No Style, No Grid
    tbl.first_row = header
    tbl.horz_banding = False
    for j, w in enumerate(col_w):
        tbl.columns[j].width = Inches(w)
    for i in range(nrows):
        tbl.rows[i].height = Inches(row_h)
        for j in range(ncols):
            c = tbl.cell(i, j)
            val = rows[i][j]
            c.margin_left = c.margin_right = Inches(0.06)
            c.margin_top = c.margin_bottom = Inches(0.025)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            al = (aligns[j] if aligns else ("l" if j == 0 else "c"))
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[al]
            runs = val if isinstance(val, list) else [(str(val), {})]
            for txt, fmt in runs:
                r = p.add_run()
                r.text = txt
                if i == 0 and header:
                    base = dict(size=header_size, bold=True, color=WHITE)
                else:
                    base = dict(size=size, bold=(bold_first_col and j == 0), color=INK)
                    if col_colors and col_colors.get(j):
                        base["color"] = col_colors[j]
                base.update(fmt)
                set_run(r, **base)
            if i == 0 and header:
                c.fill.solid()
                c.fill.fore_color.rgb = rgb(header_fill)
            else:
                c.fill.solid()
                c.fill.fore_color.rgb = rgb(LIGHT if (zebra and i % 2 == 0) else WHITE)
            set_cell_border(c, sides=("b",))
    return gf


def bar_chart(slide, x, y, w, h, cats, series, colors, title=None, fmt='0.0', ymax=None, ymin=None,
              legend=True, label_size=10, axis_size=10.5, gap=70, overlap=-12, title_size=12,
              horizontal=False, label_pos=XL_LABEL_POSITION.OUTSIDE_END, show_val_axis=True, major=None,
              axis_fmt='0'):
    cd = CategoryChartData()
    cd.categories = cats
    for name, vals in series:
        cd.add_series(name, vals)
    ctype = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = slide.shapes.add_chart(ctype, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart
    ch.font.name = BODY_FONT
    ch.font.size = Pt(axis_size)
    ch.font.color.rgb = rgb(GRAY)
    if title:
        ch.has_title = True
        ch.chart_title.text_frame.text = title
        r = ch.chart_title.text_frame.paragraphs[0].runs[0]
        set_run(r, size=title_size, bold=True, color=INK)
    else:
        ch.has_title = False
    ch.has_legend = legend
    if legend:
        ch.legend.position = XL_LEGEND_POSITION.TOP
        ch.legend.include_in_layout = False
        ch.legend.font.size = Pt(axis_size)
        ch.legend.font.color.rgb = rgb(INK)
    plot = ch.plots[0]
    plot.gap_width = gap
    plot.overlap = overlap
    plot.vary_by_categories = False
    for s, col in zip(plot.series, colors):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(col)
        s.format.line.fill.background()
    plot.has_data_labels = True
    dl = plot.data_labels
    dl.number_format = fmt
    dl.number_format_is_linked = False
    dl.position = label_pos
    dl.font.size = Pt(label_size)
    dl.font.color.rgb = rgb(INK)
    va = ch.value_axis
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb("E3E6E8")
    va.major_gridlines.format.line.width = Pt(0.75)
    va.format.line.fill.background()
    va.tick_labels.font.size = Pt(axis_size)
    va.tick_labels.font.color.rgb = rgb(GRAY)
    va.tick_labels.number_format = axis_fmt
    va.tick_labels.number_format_is_linked = False
    if ymax is not None:
        va.maximum_scale = ymax
    if ymin is not None:
        va.minimum_scale = ymin
    if major is not None:
        va.major_unit = major
    if not show_val_axis:
        va.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    ca = ch.category_axis
    ca.format.line.color.rgb = rgb("A6A6A6")
    ca.tick_labels.font.size = Pt(axis_size)
    ca.tick_labels.font.color.rgb = rgb(INK)
    ca.has_major_gridlines = False
    return gf


def new_slide(title, kicker=None, kicker_x=3.2):
    s = prs.slides.add_slide(LAYOUT)
    for ph in list(s.placeholders):
        if ph.placeholder_format.type != 1:   # keep only the title placeholder
            ph._element.getparent().remove(ph._element)
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(3.3), Inches(0.9), Inches(9.55), Inches(0.58)
    tf = t.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    bp = tf._txBody.find(qn("a:bodyPr"))
    for child in list(bp):
        bp.remove(child)
    etree.SubElement(bp, qn("a:noAutofit"))
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    r = p.add_run()
    r.text = title
    tsize = 24 if len(title) <= 46 else (22 if len(title) <= 51 else 20)
    set_run(r, size=tsize, bold=True, color=CRIMSON, font=TITLE_FONT)
    if kicker:
        text(s, kicker_x, 1.47, 12.85 - kicker_x, 0.34, [P(R(kicker, size=12.5, color=GRAY), align="r")])
    return s


def footer(slide, items, source):
    """items: list of (label, kind) evidence chips; source: small provenance text."""
    x = 0.5
    y = 7.0
    if items:
        text(slide, x, y - 0.005, 0.8, 0.28, [P(R("Evidence:", size=10, bold=True, color=GRAY))],
             anchor="m", margin=0.0)
        x += 0.78
        for label, kind in items:
            x = chip(slide, x, y, label, kind, h=0.27, size=10)
    if source:
        text(slide, x + 0.05, y - 0.005, 12.25 - x - 0.05, 0.28,
             [P(R(source, size=9, color="7F7F7F", italic=True))], anchor="m", margin=0.0)


def notes(slide, body):
    slide.notes_slide.notes_text_frame.text = body.strip()


def card(slide, x, y, w, h, head, body_paras, head_size=13, fill=LIGHT, line=None):
    box(slide, x, y, w, h, fill=fill, line=line, radius=0.06)
    paras = [P(R(head, size=head_size, bold=True, color=CRIMSON), after=2)] + body_paras
    text(slide, x + 0.12, y + 0.07, w - 0.24, h - 0.12, paras)


# ============================================================ 1. ACC (1/2)
s = new_slide("ACC 2027 | Neuromorphic Residual Attitude Control",
              "Online PES Decoder Learning in Neuromorphic Residual UAV Attitude Control · "
              "G. Contreras, S. Sandoval, L. R. García Carrillo", kicker_x=4.0)
status_chip(s, 0.5, 1.46, "In Progress | Near Submission", flag="s2_Picture_3.png", w=3.4)
# SOURCE: ACC manuscript PDF (16), Fig. 1
pic(s, FIG / "acc_fig1_arch.png", 0.5, 2.02, w=7.55)
text(s, 0.5, 6.2, 7.55, 0.55, [P(
    R("Fig. 1 of the paper. ", size=10.5, bold=True, color=GRAY),
    R("The CMG–PES path (blue) adds a bounded torque to the saturated quaternion PD before the unchanged "
      "rotor-force allocation; the baseline path is never replaced.", size=10.5, color=GRAY))])
cx, cw = 8.35, 4.5
cards = [
    ("Baseline kept", "Saturated quaternion PD (optional rate feedforward); same allocator, rotor limits and plant."),
    ("Temporal features", "6 continuous coupled membrane–gate (CMG) units driven by paired ± torque currents (3 axes)."),
    ("Online learning", "18 decoder weights adapted by PES with leak + projection; residual bounded |δ| ≤ βℓ."),
    ("Analysis", "Bounded states and weights; β = 0 recovers the baseline exactly; conditional local ISS (Thm. 1)."),
    ("Study", "MuJoCo Skydio X2 + Crazyflie 2 · 5 missions × 45 s at 2 kHz · noise, disturbance, 5 neuron families, ablation."),
]
cy = 2.02
ch_h = 0.93
for head, body in cards:
    card(s, cx, cy, cw, ch_h, head, [P(R(body, size=11.5, color=INK))], head_size=12.5)
    cy += ch_h + 0.07
footer(s, [("Digital twin (MuJoCo)", "twin"), ("Direct ≡ Nengo: 2.0×10⁻⁶ rel.", "software")],
       "Source: ACC 2027 manuscript (Overleaf export v16), Sec. II–III, Fig. 1")
notes(s, """
ACC 2027 — what the paper does (1 min).
- Problem: quadrotor attitude tracking with coupled rotor-force limits, noise and disturbances. We keep the classical quaternion PD (the stabilizing backbone) and add a small learned correction.
- CMG = coupled membrane-gate neuron (NOT a control-moment gyroscope). Six continuous units (+/- pair per torque axis) give a temporal feature basis; the decoder (18 weights) learns online with PES (prescribed error sensitivity).
- Safety-by-construction: the correction is clipped to beta*l per axis and enters BEFORE the same rotor allocator; with beta = 0 the baseline command is recovered exactly.
- Theory is conditional and local: Theorem 1 gives local ISS for small beta. Honest point if asked: the certified beta is ~1e-4 (X2) / 6e-4 (CF2) while experiments use beta = 0.5 -> stability is observed in simulation, not certified.
- Direct (NumPy) and Nengo realizations agree to 2.0e-6 relative mean error (numerical agreement, not formal equivalence).
Status: near submission with Dr. Sandoval and Dr. Garcia Carrillo. Before submitting, replace the placeholder code link (https://github.com/your-repo) in Sec. I.
""")

# ============================================================ 2. ACC (2/2)
s = new_slide("ACC 2027 | Results — Where the Residual Helps",
              "Mean quaternion-angle error over 5 missions (Roll, Full3, Hard45, Hardstep, Yaw360); "
              "geometric mean across missions", kicker_x=3.6)
# SOURCE: ACC manuscript Table II (geo columns)
bar_chart(s, 0.45, 1.95, 6.0, 3.05, ["Fixed PD", "PD + rate ff (ρ = 1)", "Tuned PD + ff (ρ = 3)"],
          [("Skydio X2", (44.5, 57.8, 35.6)), ("Crazyflie 2", (44.2, 57.6, 6.5))],
          [CRIMSON, TEAL_D], title="Error reduction from adding CMG–PES [%]", fmt='0.0"%"', ymax=70, ymin=0,
          major=10, gap=60)
table(s, 0.5, 5.12, [2.1, 1.95, 1.95], [
    ["Geo-mean error [10⁻³ rad]", "X2: base → +CMG", "CF2: base → +CMG"],
    ["Fixed PD", "173.1 → 96.0", "168.7 → 94.1"],
    ["PD + rate ff (ρ = 1)", "26.19 → 11.04", "20.39 → 8.65"],
    ["Tuned PD + ff (ρ = 3)", "4.54 → 2.93", "3.77 → 3.52"],
], row_h=0.36, size=11.5, header_size=11)
kx, kw = 6.85, 6.0
card(s, kx, 1.95, kw, 1.02, "Robust to noise and disturbances", [
    P(R("Realistic sensor noise: every reduction stays positive (18.1–55.8%).", size=11.5), bullet=True, after=1),
    P(R("X2 torque bursts: error 11.50° → 6.65° (−42.2%); CF2 rerun −50.2%.", size=11.5), bullet=True),
], head_size=12.5)
card(s, kx, 3.09, kw, 1.24, "Mechanism: decoder learning is the lever", [
    P(R("Fixed decoder (no PES) recovers at most one-fifth of the gain.", size=11.5), bullet=True, after=1),
    P(R("LIF / ALIF / LIFRate bases are nearly silent (≈0.1% active), so PES cannot learn.", size=11.5),
      bullet=True, after=1),
    P(R("Izhikevich–PES reaches similar error with ~3× residual effort (0.37 vs 0.12).", size=11.5), bullet=True),
], head_size=12.5)
card(s, kx, 4.45, kw, 1.24, "Limits we state in the paper", [
    P(R("Gains shrink as the baseline gets stronger (44% → 58% → 6–36%).", size=11.5), bullet=True, after=1),
    P(R("Hardstep at ρ = 3: error rises 17.0% (X2) / 1.3% (CF2) — 63–111° steps, slew-dominated.",
        size=11.5), bullet=True, after=1),
    P(R("Simulation only; stability at β = 0.5 is observed, not certified.", size=11.5), bullet=True),
], head_size=12.5)
box(s, kx, 5.83, kw, 0.87, fill=CRIMSON, radius=0.08)
text(s, kx + 0.15, 5.85, kw - 0.3, 0.83, [
    P(R("Take-away: ", size=12.5, bold=True, color=WHITE),
      R("the residual improves every rung of the baseline ladder with a bounded, recoverable "
        "interface — a complement to good model-free control, not a replacement for tuning.",
        size=12.5, color=WHITE))], anchor="m")
footer(s, [("Digital twin (MuJoCo)", "twin")],
       "Source: ACC 2027 manuscript v16, Table II and Sec. IV-C–G")
notes(s, """
Results (1.5 min).
- Chart: percentage reduction of the geometric-mean attitude error when CMG-PES is added, for three baselines of increasing strength (fixed PD; PD + desired-rate feedforward; bandwidth-tuned PD + feedforward at rho = 3).
- Against fixed PD: 17.3-60.6% per case (geo 44.5% X2 / 44.2% CF2). With feedforward: 57.8 / 57.6%. Tuned: 35.6% X2 but only 6.5% CF2.
- Noise: two synthetic levels, two seeds; all reductions stay positive (18.08-55.75% at the realistic level). Yaw360 loses most because its error approaches the noise floor.
- Disturbance: 4-burst test on X2: 11.50 -> 6.65 deg burst-phase (42.2%), post-burst 1.21 -> 0.99 deg (18.0%); CF2 rerun 0.1412 -> 0.0707 rad (50.2%).
- Mechanism: with active gates latched (a ~ 1), PES behaves like a lagged proportional correction (corner 9.6 rad/s). Fixed decoder W = W0 gives only small gains; LIF/ALIF/LIFRate are ~silent, so PES has no signal to learn from.
If asked "does a tuned PD+ff alone beat CMG on the fixed PD?" -> yes; that is why we report the whole ladder. The claim is complementary improvement on each baseline.
If asked "why does Hardstep degrade at rho = 3?" -> 97-99% of its mean error is unavoidable slew; the fast loop passes the PES corner so the lagged residual falls out of phase. A saturation-gated residual is proposed as future work (not evaluated).
""")

# ============================================================ 3. ComRob
s = new_slide("ComRob 2026 | Neuromorphic Hexarotor Control",
              "A. Olivares · G. Contreras · V. J. Silva · E. S. Espinoza · J. M. Bustamante · P. Ordaz  "
              "(UAEH · NMSU · UPMH · CINVESTAV)", kicker_x=4.0)
status_chip(s, 0.5, 1.46, "Accepted | Minor Revisions", flag="s2_Picture_8.png", w=3.4)
pic(s, FIG / "comrob_fig1_hexa.png", 0.55, 2.0, w=3.9)
text(s, 0.5, 5.02, 4.1, 0.3, [P(R("Coaxial hexarotor (T6): three arms, counter-rotating rotor pairs.",
                                   size=10.5, color=GRAY))])
text(s, 0.5, 5.4, 4.35, 1.5, [
    P(R("Plant and cascade controller both run as recurrent SNNs in Nengo (NEF).", size=12), bullet=True, after=3),
    P(R("One neural template for 6 subsystems (z, x, y, θ, φ, ψ): outer PID, inner PD.", size=12),
      bullet=True, after=3),
    P(R("200 neurons per ensemble, τ = 0.1 s; 60 s 3-D trajectory vs MATLAB/Simulink.", size=12), bullet=True),
])
# SOURCE: ComRob PDF Table II
table(s, 5.1, 2.0, [1.33, 1.6, 1.6, 1.6, 1.6], [
    ["Variable", "RMSE classical", "RMSE SNN", "ISE classical", "ISE SNN"],
    ["x [m]", "0.008", "0.032", "3.95×10⁻³", "0.0627"],
    ["y [m]", "0.013", "0.033", "0.0101", "0.0660"],
    ["z [m]", "0.019", "0.048", "0.0213", "0.1367"],
    ["θ [rad]", "3.26×10⁻⁴", "0.005", "6.38×10⁻⁶", "1.71×10⁻³"],
    ["φ [rad]", "9.73×10⁻⁴", "0.012", "5.68×10⁻⁵", "8.67×10⁻³"],
    ["ψ [rad]", "6.62×10⁻³", "0.009", "2.63×10⁻³", "4.61×10⁻³"],
], row_h=0.34, size=11.5, header_size=11)
# stat callouts
sx = 5.1
for big, small1, small2 in [("ρ ≥ 0.999", "SNN–classical signal correlation",
                             "x 0.9993 · y 0.9998 · −z 0.9992"),
                            ("< 5 cm", "RMS position error of the SNN",
                             "x 0.032 · y 0.033 · z 0.048 m")]:
    box(s, sx, 4.62, 3.78, 1.2, fill=LIGHT, radius=0.06)
    text(s, sx + 0.1, 4.66, 3.58, 0.55, [P(R(big, size=26, bold=True, color=CRIMSON, font=TITLE_FONT),
                                           align="c")], anchor="m")
    text(s, sx + 0.1, 5.2, 3.58, 0.58, [P(R(small1, size=11.5, color=INK, bold=True), align="c"),
                                         P(R(small2, size=11, color=GRAY), align="c")])
    sx += 3.95
text(s, 5.1, 5.95, 7.73, 0.85, [
    P(R("Honest reading: ", size=11.5, bold=True, color=CRIMSON),
      R("the SNN reproduces the classical closed loop closely but with higher RMSE/ISE (finite ensembles, "
        "LIF saturation). Reduced model — rotor/actuator dynamics, disturbances and neuromorphic hardware "
        "are future work.", size=11.5))])
footer(s, [("Simulation (Nengo vs Simulink)", "twin")],
       "Source: ComRob 2026 manuscript, Table I–II · code: github.com/esteedeq/UAV_Nengo")
notes(s, """
ComRob 2026 — accepted with minor revisions (Mexico).
- Contribution: a fully neuromorphic closed loop — both the reduced hexarotor dynamics and the cascade controller are recurrent spiking networks built with the NEF in Nengo (same template F' = tau F + chi, G' = tau G for all six subsystems).
- Evaluation: 60 s trajectory (climb to 3 m, +1 m in x, +1.5 m lateral step at 15 s), compared with an equivalent MATLAB/Simulink cascade (PID outer, PD inner).
- Result: correlation above 0.999 in the translational axes; sub-decimeter RMS position errors; the SNN has larger RMSE/ISE than the classical baseline (e.g., z 0.019 vs 0.048 m).
- Minor revisions (blue text in the manuscript): Simulink and Nengo implementation details, RMSE/ISE + correlation metrics, NEF limitations discussion, public code link.
My role: co-author (NMSU).
""")

# ============================================================ 4. ToE
s = new_slide("IEEE ToE | Experiential Learning & Digital Twins",
              "H. C. Contreras Aguirre · H. Mirhajianmoghadam · O. A. García Alcántara · G. Contreras · "
              "L. R. García Carrillo", kicker_x=4.0)
status_chip(s, 0.5, 1.46, "In Progress | Near Submission", flag="s2_Picture_3.png", w=3.4)
pic(s, FIG / "toe_platforms.jpg", 0.5, 2.0, w=2.95)
text(s, 0.5, 5.25, 3.05, 1.6, [
    P(R("Qube-Servo 3 and Aero 2: hardware (top) and QLabs twins (bottom).", size=10.5, color=GRAY), after=5),
    P(R("EE 475/551 Control Systems Synthesis, Spring 2026", size=11, bold=True), after=2),
    P(R("21 students · fully asynchronous", size=11), bullet=True, after=1),
    P(R("Kolb experiential-learning cycle", size=11), bullet=True, after=1),
    P(R("MATLAB/Simulink + QUARC + QLabs", size=11), bullet=True),
])
# SOURCE: ToE PDF Table V
bar_chart(s, 3.65, 1.95, 5.3, 3.35, ["M04→05\nCT-ARX ID", "M06→07\nDT-ARX ID", "M10→11\nLQR", "Overall"],
          [("Theory lab", (97.86, 99.05, 99.52, 98.81)), ("Digital-twin lab", (79.95, 80.00, 84.14, 81.37))],
          [TEAL_D, CRIMSON], title="Paired lab scores, same students [%]", fmt='0.0', ymax=110, ymin=0,
          major=20, gap=55, label_size=9.5)
box(s, 3.75, 5.42, 5.1, 1.36, fill=LIGHT, radius=0.06)
text(s, 3.85, 5.45, 1.7, 1.3, [P(R("−17.4 pp", size=24, bold=True, color=CRIMSON, font=TITLE_FONT))],
     anchor="m")
text(s, 5.55, 5.47, 3.25, 1.3, [
    P(R("theory → digital-twin gap", size=11.5, bold=True), after=1),
    P(R("95% CI [11.6, 23.8] · 21/21 students lower", size=11), after=1),
    P(R("p < 0.001 (Wilcoxon, Holm) · sign test p < 0.001", size=11)),
], anchor="m")
# SOURCE: ToE PDF Table IV
text(s, 9.2, 1.97, 3.7, 0.32, [P(R("Aero 2 project: model → twin → hardware", size=12.5, bold=True,
                                    color=CRIMSON))])
table(s, 9.2, 2.33, [1.25, 0.75, 0.78, 0.85], [
    ["RMSE [°]", "Offline", "QLabs", "Hardware"],
    ["PD pitch", "8.97", "8.68", "8.03"],
    ["PD yaw", "19.09", "24.47", "26.07"],
    ["BS pitch", "10.29", "11.03", "9.40"],
    ["BS yaw", "18.08", "25.31", "29.27"],
], row_h=0.34, size=11.5, header_size=11)
text(s, 9.2, 4.12, 3.7, 2.7, [
    P(R("Same controller transfers across stages; pitch stays near the offline value, yaw degrades — "
        "the twin already exposes the hardware difficulty.", size=11.5), bullet=True, after=4),
    P(R("MATLAB ↔ Python (student-built): ≤ 0.65° RMSE difference in QLabs, ≤ 0.19° on hardware.",
        size=11.5), bullet=True, after=4),
    P(R("Reading: the gap reflects the added demands of real-time implementation — not reduced learning.",
        size=11.5, italic=True), bullet=True),
])
footer(s, [("Classroom study (n = 21)", "software"), ("Twin + hardware", "hardware")],
       "Source: ToE manuscript, Tables IV–V, Figs. 8–10 · BS = backstepping")
notes(s, """
IEEE Transactions on Education — near submission.
- Course: EE 475/551 Control Systems Synthesis (NMSU ECE, Spring 2026, 21 students, fully asynchronous). Topics: system identification (time/frequency), robust, optimal (LQR/LQG) and nonlinear control; semester team project.
- Infrastructure: MATLAB/Simulink + QUARC + QLabs digital twins with 1:1 hardware counterparts (Qube-Servo 3, Aero 2, QBot, QCar, QDrone 2).
- Quantitative: three theory -> digital-twin lab pairs; students scored 98.81% on theory vs 81.37% on the matching twin lab (-17.44 pp, bootstrap 95% CI [11.6, 23.8]); all 21 lower on average; Wilcoxon + Holm p < 0.001. We interpret it as a theory-to-practice gap, not reduced learning.
- Aero 2 project: PD and backstepping from offline model -> QLabs twin -> physical Aero 2, in MATLAB and (student initiative) Python. Pitch transfers well; yaw error grows (19 -> 24 -> 26 deg for PD).
- Qualitative: 13/21 survey responses (62%) value hands-on labs and projects.
Limitation (stated in the paper): single-offering, single-institution case study, no control group.
""")

# ============================================================ 5. Research status
s = new_slide("Research Lines | What Is Verified vs. Planned",
              "Each line is labeled by the strongest evidence it has today", kicker_x=4.0)
rows = [
    ["", "Line", "Verified today", "Evidence", "Next milestone"],
    ["1", "HyperLIF (Python / Julia)", "PyTorch 5-seed benchmarks; Julia forward parity; Julia learning package",
     "", "Julia HPC screen → 5-seed runs"],
    ["2", "Quanser + Julia", "Julia closed loops on Qube & Aero 2 twins; Python hardware on Qube, Aero 2, Hover",
     "", "Julia on hardware; matched Python↔Julia runs"],
    ["3", "Omnicopter", "MuJoCo twin; PD vs CMG–PES frozen result; Nengo ≡ direct",
     "", "Parameter ID + shadow-mode test card"],
    ["4", "DILISIC", "Paper replicated (11 metrics at 10⁻⁶) + math audit; QArm ID tool",
     "", "QArm 1-joint ID → shadow replay"],
    ["5", "QCar", "On-car lane following (7 controllers, low speed); ROS 2 EKF lineage",
     "", "Fused-state MPC baseline with Grafton"],
    ["6", "Space systems", "Basilisk–MuJoCo satellite (600 s, verified); gyroscope model derived",
     "", "Gyroscope ID + twin + HIL plan"],
]
colw = [0.5, 2.2, 4.63, 2.4, 2.6]      # sums to 12.33 in (0.5 → 12.83)
HDR_H, ROW_H = 0.42, 0.62
gf = table(s, 0.5, 2.0, colw, rows, row_h=ROW_H, size=11.5, header_size=11.5,
           aligns=["c", "l", "l", "l", "l"])
tbl = gf.table
tbl.rows[0].height = Inches(HDR_H)
for i in range(1, 7):
    c = tbl.cell(i, 1)
    for r in c.text_frame.paragraphs[0].runs:
        r.font.bold = True
        r.font.color.rgb = rgb(CRIMSON)
    c0 = tbl.cell(i, 0)
    for r in c0.text_frame.paragraphs[0].runs:
        r.font.bold = True
        r.font.color.rgb = rgb(GRAY)
evid = {
    1: [("Software", "software")],
    2: [("Twin", "twin"), ("Hardware", "hardware")],
    3: [("Twin", "twin")],
    4: [("Software", "software")],
    5: [("Hardware", "hardware"), ("Plan", "proposed")],
    6: [("Twin", "twin"), ("Plan", "proposed")],
}
ex0 = 0.5 + sum(colw[:3]) + 0.08
for i, items in evid.items():
    y = 2.0 + HDR_H + ROW_H * (i - 1) + (ROW_H - 0.27) / 2
    x = ex0
    for lab, kind in items:
        x = chip(s, x, y, lab, kind, h=0.27, size=10)
# legend
lx = 0.5
ly = 6.35
text(s, lx, ly, 1.0, 0.3, [P(R("Legend:", size=10.5, bold=True, color=GRAY))], anchor="m", margin=0)
lx += 0.75
for lab, kind in [("Verified software", "software"), ("Digital twin", "twin"), ("Hardware run", "hardware"),
                  ("Proposed", "proposed")]:
    lx = chip(s, lx, ly + 0.01, lab, kind, h=0.27, size=10)
text(s, lx + 0.1, ly, 12.83 - lx - 0.1, 0.3, [P(R(
    "“Verified” = reproducible saved result or passing test suite; hardware = logged physical run.",
    size=10, italic=True, color=GRAY))], anchor="m", margin=0)
notes(s, """
Use this slide as the map for the second half.
Rule for the whole talk: every number comes from a saved result file or a passing test, and is labeled as software, digital twin, hardware, or proposed. We never merge these labels.
- Line 2 hardware entries are Python runs (Qube-Servo 3, Aero 2, 3-DOF Hover); the Julia runs so far are on the QLabs twins.
- Line 5 hardware = low-speed lane following on the QCar; the fusion + MPC + neuromorphic benchmark is the plan with Grafton.
- Line 6: the satellite twin runs; the 3-DOF gyroscope has the derived model/controller suite but no code or hardware run yet.
""")

# ============================================================ 6. HyperLIF
s = new_slide("HyperLIF | Python Results Reproduced in Julia",
              "Neuron → architecture → learning · PyTorch / Nengo reference, Julia portable + CUDA path, HPC-ready",
              kicker_x=3.6)
number_chip(s, 0.5, 1.45, 1)
# SOURCE: P1 main.tex Table (tab:ff-temporal)
bar_chart(s, 0.45, 1.95, 6.2, 3.65, ["SHD", "SSC", "DVS-32", "DVS-48", "N-MNIST"],
          [("LIF", (48.4, 12.8, 69.8, 71.9, 89.5)), ("HyperLIF", (63.7, 21.5, 81.8, 78.6, 90.8)),
           ("Adaptive HyperLIF", (58.1, 21.2, 79.0, 75.1, 90.4))],
          [TEAL, CRIMSON, "C98AA3"], title="PyTorch, feed-forward, 5 seeds — test accuracy [%]",
          fmt='0', ymax=100, ymin=0, major=20, gap=45, overlap=-5, label_size=9)
text(s, 0.5, 5.68, 6.1, 1.1, [
    P(R("Largest gains on temporal speech/motion data; smallest on near-static N-MNIST. ", size=11.5),
      R("ALIF stays a strong competitor on SHD shortlists (55.7% vs 54.8% feed-forward) — "
        "HyperLIF is a different mechanism, not a universal winner.", size=11.5, italic=True))])
text(s, 6.95, 1.95, 5.9, 0.35, [P(R("Julia replication ladder", size=14, bold=True, color=CRIMSON))])
steps = [
    ("1", "Neuron parity", "PyTorch ≡ validated NumPy/Nengo reference: max |Δ| < 10⁻⁹, 0 event mismatches."),
    ("2", "Forward parity, shared weights", "Julia (APEX-v2, CUDA) vs PyTorch dense/RSNN/delay: "
                                          "≤ 1.05×10⁻⁵ (HyperLIF), ≤ 5.09×10⁻⁴ (Adaptive)."),
    ("3", "Native Julia training, same SHD cache", "10 epochs × 5 seeds: LIF 24.1 ± 7.8% vs tuned HyperLIF "
                                                   "24.9 ± 6.7% — direction reproduced, within seed spread."),
    ("4", "HyperLIFLearning.jl → HPC", "Continuous, surrogate-event and event-time learning; 100 tests; "
                                      "CPU + CUDA preflight; SLURM bundles ready for NMSU Discovery."),
]
yy = 2.38
for n, head, body in steps:
    circ = box(s, 6.95, yy + 0.05, 0.42, 0.42, fill=CRIMSON, shape=MSO_SHAPE.OVAL)
    shape_text(circ, [P(R(n, size=13, bold=True, color=WHITE))], margin=0)
    text(s, 7.5, yy, 5.35, 0.98, [P(R(head, size=12.5, bold=True, color=INK), after=1),
                                   P(R(body, size=11.5, color=INK))])
    yy += 1.02
footer(s, [("Verified software", "software"), ("Julia tests re-run 18 Sep: 16/16 pass", "software")],
       "Sources: P1 HyperLIF Learning manuscript; code/docs/PARITY.md; THREE_STAGE_DEVELOPMENT_REPORT_2026-09-09")
notes(s, """
Line 1 — HyperLIF: neurons, networks and learning (Python -> Julia).
- Python (PyTorch, 5 seeds): HyperLIF improves over LIF most on temporal data (SHD 48.4 -> 63.7%, SSC 12.8 -> 21.5%, DVS-32 69.8 -> 81.8%); the gap shrinks on N-MNIST (89.5 -> 90.8%). Same pattern in recurrent and delay architectures (e.g., RSNN SHD 53.6 -> 67.4%).
- Honest caveat: ALIF is competitive on SHD shortlists; HyperLIF leads in the recurrent cell. Present it as a different mechanism (decodable gate state), not universal superiority.
- Julia replication (what "replicated" means precisely):
  1) Neuron: the PyTorch HyperLIF equals the validated NumPy/Nengo reference to < 1e-9.
  2) Forward pass: Julia APEX-v2 reproduces PyTorch features/logits with shared weights (dense, recurrent, delay).
  3) Learning result: a native Julia run on the byte-identical SHD cache reproduces the direction of the HyperLIF > LIF result (after gate-feedback calibration); absolute accuracy is lower than PyTorch because it is a different, shallower native pipeline, and the difference is within seed variance.
  4) New HyperLIFLearning.jl package: three learning contracts (continuous, surrogate, event-time), 100 tests passing, CUDA preflight OK, SLURM array scripts packaged. Next: run the screening profile on the NMSU HPC, then the 5-seed/40-epoch profile, and add gradient parity against PyTorch.
- Portable Julia package re-run today (18 Sep): 16/16 tests pass.
""")

# ============================================================ 7. Quanser + Julia
s = new_slide("Quanser Platforms | Julia in the Loop on Digital Twins",
              "Identification → model-based → model-free / neuromorphic residual · offline → QLabs twin → hardware",
              kicker_x=3.6)
number_chip(s, 0.5, 1.45, 2)
# pipeline strip across the full width
px = 0.5
for lab, w, fill, fg in [("System identification", 3.35, TEAL, INK),
                         ("Model-based: PD · LQR · LQG · MPC · backstepping · SMC · NMPC", 5.2, TEAL, INK),
                         ("Model-free / neuromorphic bounded residual", 3.93, CRIMSON, WHITE)]:
    sh = box(s, px, 1.98, w, 0.44, fill=fill, shape=MSO_SHAPE.CHEVRON if px > 0.5 else MSO_SHAPE.PENTAGON)
    shape_text(sh, [P(R(lab, size=11, bold=True, color=fg))], margin=0.22)
    px += w - 0.05
# robot thumbnails
tx = 0.6
for img, lab in [("s5_Imagen_1.png", "Qube-Servo 3"), ("s5_Imagen_2.png", "Aero 2"), ("s5_Imagen_4.png", "3-DOF Hover")]:
    p = pic(s, MEDIA / img, tx, 2.58, h=0.82)
    text(s, tx - 0.25, 3.42, p.width / 914400 + 0.5, 0.25, [P(R(lab, size=10, color=GRAY), align="c")])
    tx += p.width / 914400 + 0.62
pic(s, FIG / "julia_qube_swingup.png", 0.45, 3.75, w=4.45)
# Julia table
RX, RW = 5.2, 7.63
text(s, RX, 2.55, RW, 0.32, [P(R("Julia on Quanser (Julia ccall → hil.dll, no Python in the loop)", size=12.5,
                                  bold=True, color=CRIMSON))])
table(s, RX, 2.9, [1.6, 2.05, 3.98], [
    ["Platform", "Julia controller", "Result"],
    ["Qube-Servo 3 twin", "Energy swing-up + LQR", "499.98 Hz; catch at 4.0 s; held 16 s; final-2 s α RMS 1.24°"],
    ["Aero 2 twin", "PD, pitch square wave", "199.8 Hz realized; pitch RMS 0.048 rad (last 75%)"],
    ["3-DOF Hover", "HIL bridge (Q8 DAQ)", "103/103 tests pass (re-run today); live test pending"],
    ["All Quanser boards", "V0/V1 registry", "hil.dll found; 15 boards resolve, no device opened"],
], row_h=0.37, size=11, header_size=11)
text(s, RX, 4.88, RW, 0.32, [P(R("Hardware highlights (Python stack, same controller contract)", size=12.5,
                                  bold=True, color=CRIMSON))])
table(s, RX, 5.23, [1.6, 2.05, 3.98], [
    ["Platform", "Experiment", "Result"],
    ["Qube-Servo 3", "Gate residual, 12 × 60 s", "0.78° mean |α| error; residual active 4.4% vs 70% always-on"],
    ["Aero 2", "PD tracking, 200 Hz", "pitch RMS 0.084 rad on hardware (twin 0.150)"],
    ["3-DOF Hover", "CMG–PES vs PD (Nengo)", "Roll: +2.7 ± 1.1% (3 pairs); others mixed (Full3 −3.2%)"],
], row_h=0.37, size=11, header_size=11)
footer(s, [("Digital twin (Julia)", "twin"), ("Hardware (Python)", "hardware")],
       "Sources: julia_bridge VALIDATION_STATUS + results; pendulum 2026-06-14 report; hover frozen audit 2026-09-02")
notes(s, """
Line 2 — Quanser + Julia: system identification, model-based and model-free control.
- One pipeline for every robot: identify -> model-based controllers (PD, LQR, LQG, MPC, backstepping, SMC, NMPC) -> model-free / neuromorphic bounded residual; run offline -> QLabs digital twin -> hardware with the same controller contract.
- Julia: the bridge talks directly to Quanser's hil.dll (no Python in the loop). Results so far on the twins: Qube-Servo 3 swing-up + LQR balance at 500 Hz (catch at 4.0 s, 16 s continuous hold, 1.24 deg RMS in the last 2 s); Aero 2 PD at 200 Hz. The Hover Julia bridge passes 103 checks without opening the device; its first live step is sensor-only.
- Honest boundary: Julia has not commanded physical hardware yet (V4 is a lab action). The hardware rows are the Python stack.
- Hardware details if asked: Qube gate residual (June 14, 12 trials, 0 amplifier faults): comparable error to always-on augmentation with ~93% less residual time/energy — it used the legacy gate blend, not the ACC canonical gate. Aero 2 PD hardware pitch tracks tighter than the twin. Hover: CMG-PES beats PD on Roll repeatably (+2.65 +/- 1.08% over 3 pairs); single pairs on other missions are mixed (Full3 -3.2%, Hard45 +0.6%, Hardstep +1.0%).
- Next: matched Python vs Julia runs on the same twin scene, Julia system identification, then Julia on hardware.
""")

# ============================================================ 8. Omnicopter
s = new_slide("Omnicopter | MuJoCo Twin & Neuromorphic Control",
              "Diego–Fabian collaboration · fully actuated 8-rotor vehicle with reversible thrust", kicker_x=4.0)
number_chip(s, 0.5, 1.45, 3)
pic(s, FIG / "omni_model_crop.png", 0.55, 1.98, h=2.35)
text(s, 3.05, 1.98, 3.0, 2.45, [
    P(R("Twin methodology", size=12.5, bold=True, color=CRIMSON), after=3),
    P(R("CAD/STL → body frame", size=11), bullet=True, after=2),
    P(R("8 rotor frames confirmed on the vehicle", size=11), bullet=True, after=2),
    P(R("Wrench map B (6×8), rank 6 → bounded allocation", size=11), bullet=True, after=2),
    P(R("Geometric PD + feedforward", size=11), bullet=True, after=2),
    P(R("CMG–PES residual: 12 units, 6 channels", size=11), bullet=True, after=2),
    P(R("Unknown parameters stay null until measured", size=11), bullet=True),
])
# SOURCE: heldout_500hz_batch_20260910/mission_results.csv (PD+ff vs revised CMG-PES)
bar_chart(s, 0.45, 4.45, 3.0, 2.45, ["Hover\n+ push", "Attitude\n+45°", "Yaw 360°", "Overall"],
          [("PD + ff", (0.219, 0.222, 0.213, 0.218)), ("CMG–PES", (0.090, 0.117, 0.088, 0.098))],
          [TEAL_D, CRIMSON], title="Held-out mismatch · position RMSE [m]", fmt='0.00', ymax=0.3, ymin=0,
          major=0.1, gap=50, label_size=8.5, axis_size=9, title_size=10.5, axis_fmt='0.0')
bar_chart(s, 3.5, 4.45, 3.0, 2.45, ["Hover\n+ push", "Attitude\n+45°", "Yaw 360°", "Overall"],
          [("PD + ff", (4.73, 4.69, 4.59, 4.67)), ("CMG–PES", (3.40, 3.55, 3.33, 3.43))],
          [TEAL_D, CRIMSON], title="Held-out mismatch · attitude RMSE [°]", fmt='0.0', ymax=6, ymin=0,
          major=2, gap=50, label_size=8.5, axis_size=9, title_size=10.5)
# SOURCE: FROZEN_RESULTS_20260910.md
table(s, 6.75, 2.0, [2.2, 1.35, 1.35, 1.18], [
    ["Regime (MuJoCo, 500 Hz)", "PD", "CMG–PES", "Reading"],
    ["Nominal, exact model (25 missions)", "1.03 mm · 0.026°", "11.6 mm · 0.063°", "PD better"],
    ["After impulse: hover push", "18.1 mm · 0.44°", "10.6 mm · 0.29°", "−42% · −34%"],
    ["After impulse: circle + yaw", "12.0 mm · 0.29°", "6.3 mm · 0.20°", "−48% · −33%"],
    ["Held-out mass/inertia/motor/force mismatch (3 seeds × 3)", "0.218 m · 4.67°", "0.098 m · 3.43°",
     "−55% · −27%; 9/9 wins"],
], row_h=0.56, size=10.5, header_size=10.5)
box(s, 6.75, 5.05, 6.08, 0.8, fill=CRIMSON, radius=0.08)
text(s, 6.9, 5.07, 5.8, 0.76, [P(
    R("Frozen conclusion (R1): ", size=12, bold=True, color=WHITE),
    R("PD wins nominal tracking when the plant matches its model; CMG–PES wins disturbance and "
      "uncertainty rejection.", size=12, color=WHITE))], anchor="m")
text(s, 6.75, 6.0, 6.1, 0.85, [
    P(R("Next with Diego & Fabian: ", size=11.5, bold=True, color=CRIMSON),
      R("measure mass/COM/inertia and bidirectional thrust maps; shadow mode → tethered PD → PD + frozen "
        "residual → online PES (test card runs 1–8, common log schema).", size=11.5))])
footer(s, [("Digital twin (ideal model)", "twin"), ("Nengo ≡ direct: ≤ 1.1×10⁻⁷ N", "software")],
       "Source: omnicopter/mujoco — FROZEN_RESULTS_20260910 (NRCTRL-OMNI-2026-09-10-R1), held-out batch 2026-09-10")
notes(s, """
Line 3 — Omnicopter (collaboration with Diego and Fabian).
- Vehicle: fully actuated, 8 reversible rotors on the diagonals of a cube; rank-6 wrench map, so force and torque are decoupled.
- Methodology: STL -> body frame; rotor frames fixed from the physical vehicle and checked by a regression test (orthonormal, rank 6, bounded hover solution); weighted bounded least-squares allocation (+/-10 N); geometric PD + feedforward; CMG-PES residual (12 units, 6 wrench channels) imported from the ACC code; direct and Nengo versions of both controllers.
- Evidence: 25/25 nominal missions for 4 controllers with zero saturation; direct vs Nengo differences <= 1.1e-7 N. Frozen result NRCTRL-OMNI-2026-09-10-R1.
- Reading: on the exact-model plant PD is better nominally (CMG-PES has a startup transient from the gravity-compensating baseline). After impulses and under held-out synthetic mismatch (mass, inertia, motor gain/lag, persistent force/torque), CMG-PES is better: -55% position and -27% attitude RMSE, 9/9 paired wins (revised CMG-PES).
- Honest boundary: ideal thrust, no identified aerodynamics or motor dynamics yet -> not a predictive physical twin. The next step is identification with the collaborators and the staged physical-virtual test card.
""")

# ============================================================ 9. DILISIC
s = new_slide("DILISIC | Replicated; Next: QArm, QArm Mini & Haptic",
              "Limbic-system-inspired performance-guaranteed control (Rubio Scola, García Carrillo, Hespanha — "
              "IEEE TNNLS 2023)", kicker_x=3.3)
number_chip(s, 0.5, 1.45, 4)
pic(s, FIG / "dilisic_replication.png", 0.45, 1.98, w=4.9)
text(s, 0.5, 5.38, 5.0, 1.55, [
    P(R("7-agent flexible-arm experiment, 80 s: all 11 summary metrics reproduce to 10⁻⁶ "
        "(final CoM error 9.5×10⁻⁵ rad).", size=11.5), bullet=True, after=3),
    P(R("Replicated: 4th-order plant, p = 45 RBF, projection-bounded weights, Riccati robust term, "
        "70–75 s disturbance. Gap: exact Appendix flocking/obstacle law.", size=11.5), bullet=True, after=3),
    P(R("Audit: 4 points to confirm with the authors (error-sign convention, a Lyapunov-derivative "
        "term, ĥ* positivity, projection norm).", size=11.5), bullet=True),
])
tx = 6.0
for img, lab in [("s5_Imagen_30.png", "QArm"), ("s5_Imagen_31.png", "QArm Mini"), ("s5_Imagen_29.png", "HD Haptic")]:
    p = pic(s, MEDIA / img, tx, 1.95, h=1.08)
    text(s, tx + p.width / 914400 + 0.05, 2.3, 1.05, 0.35, [P(R(lab, size=11, bold=True, color=GRAY))],
         anchor="m")
    tx += p.width / 914400 + 1.3
text(s, 6.0, 3.1, 6.85, 0.32, [P(R("What must be adapted before the arms move", size=12.5, bold=True,
                                   color=CRIMSON))])
table(s, 6.0, 3.45, [2.1, 2.2, 2.55], [
    ["DILISIC assumes", "QArm / QArm Mini / Haptic", "Adaptation"],
    ["Input enters the highest derivative, known sign (g > 0)", "Smart servos expose position (QArm); "
     "position or PWM (Mini)", "Identify the servo closed loop (ARX) → DILISIC as outer loop / reference shaping"],
    ["Full state up to q⁽³⁾", "Encoders only", "Derivative observer with a noise/bandwidth budget"],
    ["Scalar agents on a graph", "4-DOF arms, different scales", "Joint- or task-space agents (Jacobian); "
     "arm-to-arm graph"],
    ["External leader reference", "Human operator", "Haptic device as leader (passivity, virtual coupling)"],
    ["—", "Shared workspace", "Limits, watchdog, fallback; shadow mode before actuation"],
], row_h=0.55, size=10.5, header_size=10.5)
footer(s, [("Re-run 18 Sep: 11/11 tests, 11/11 metrics", "software"), ("Arms: not actuated yet", "proposed")],
       "Sources: dilisic/verify.py, MATH_AUDIT_2026-09-08, QARM_RUNBOOK_2026-09-09")
notes(s, """
Line 4 — DILISIC (distributed limbic-system-inspired control) and the arms.
- We replicated the TNNLS 2023 paper's seven-agent flexible-arm experiment in Python: same plant parameters, initial spread, 70-75 s disturbance, p = 45 RBF basis, projection-bounded adaptive weights and the Riccati robust term. The 80 s run reproduces all 11 summary metrics at 1e-6 relative tolerance; the test suite passes (re-run today).
- Not replicated yet: the exact Appendix flocking/obstacle law (we use a simplified 1-D formation controller). Engineering additions (initial h_hat near the inverse gain, RBF input clipping, reduced adaptation, filtered u_DI) are disclosed as additions.
- Mathematical audit (useful for the advisors): Sec. III vs Eq. (30) use opposite error signs; the Lyapunov derivative treats the state-dependent 1/h* as constant; positivity of the approximated inverse gain is assumed; Eq. (25) likely uses the wrong norm in the W_f projection.
- Arms: not yet implemented on QArm / QArm Mini. The key mismatch is the interface: the paper needs an affine input at the highest derivative with known sign; the QArm exposes position servos (Mini: position or PWM). Plan: one joint at a time — bounded excitation, ARX identification of the servo loop, non-actuating DILISIC replay (shadow), then a low-authority outer loop with watchdog and fallback. The haptic device enters as the human leader of the multi-arm team.
- An identification tool and bench runbook already exist (they authorize shadow work only).
""")

# ============================================================ 10. QCar
s = new_slide("QCar | Neuromorphic Sensor Fusion & Control",
              "Plan with Grafton: Quanser-native MPC first → HyperLIF / CMG fusion and control → matched benchmark",
              kicker_x=3.6)
number_chip(s, 0.5, 1.45, 5)
pic(s, MEDIA / "s5_Imagen_20.png", 0.6, 2.0, w=2.25)
text(s, 0.5, 3.95, 3.2, 2.9, [
    P(R("Today", size=12.5, bold=True, color=CRIMSON), after=3),
    P(R("On-car (Jetson) runner: PID, SMC, image-state NMPC, Adaptive-HyperLIF gate + 3 gated residual "
        "hybrids.", size=11), bullet=True, after=3),
    P(R("ROS 2 EKF lineage: wheel speed, IMU yaw rate, LiDAR odometry.", size=11), bullet=True, after=3),
    P(R("Earlier benchmark: lane-error RMS 0.126 (PD) → 0.112 (HyperLIF gate), with more steering effort.",
        size=11), bullet=True),
])
# phase diagram
phx, phw = 3.9, 5.3
phases = [
    ("A · Quanser-native baseline", TEAL, INK,
     "Camera · LiDAR · IMU · encoders → time-synchronized EKF (X, Y, ψ, v) → kinematic-bicycle MPC with hard "
     "input / slew / obstacle constraints → safety filter"),
    ("B · Neuromorphic fusion + control", CRIMSON, WHITE,
     "Control: CMG–PES residual on the MPC steering/speed command (ACC + omnicopter architecture; β = 0 "
     "recovers MPC).  Fusion: HyperLIF / CMG populations encode camera, LiDAR, IMU and EKF innovations; PES "
     "learns a bounded correction.  u = Π_safe(u_MPC + α·Δu_SNN)"),
    ("C · Matched benchmark", SAND, INK,
     "Residual: none / ANN / SNN / RL with identical inputs & bounds · nominal, lane loss, obstacle, dropout · "
     "≥ 5 trials per cell"),
]
py_ = 2.0
for head, fill, fg, body in phases:
    hb = box(s, phx, py_, phw, 0.36, fill=fill, radius=0.2)
    shape_text(hb, [P(R(head, size=12, bold=True, color=fg), align="l")], margin=0.12)
    text(s, phx + 0.08, py_ + 0.4, phw - 0.16, 1.05, [P(R(body, size=11, color=INK))])
    if head[0] != "C":
        arr = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(phx + phw / 2 - 0.15), Inches(py_ + 1.43),
                                 Inches(0.3), Inches(0.2))
        arr.fill.solid()
        arr.fill.fore_color.rgb = rgb("BFBFBF")
        arr.line.fill.background()
    py_ += 1.68
text(s, phx, 6.55, phw, 0.4, [P(R("Metrics: collisions, interventions, lane departures, tracking RMS, "
                                   "p95 latency, measured energy (J/route).", size=10.5, italic=True, color=GRAY))])
# Grafton plan
gx, gw = 9.45, 3.4
box(s, gx, 2.0, gw, 3.4, fill=LIGHT, radius=0.05)
text(s, gx + 0.12, 2.06, gw - 0.24, 3.3, [
    P(R("Grafton — first 4 weeks", size=12.5, bold=True, color=CRIMSON), after=5),
    P(R("W1 ", size=11, bold=True), R("perception-only logging; signal dictionary; timestamp/units audit "
                                        "(no motion)", size=11), after=5),
    P(R("W2 ", size=11, bold=True), R("reproduce PID and image-NMPC offline; unit tests for signs, clamps, "
                                        "slew", size=11), after=5),
    P(R("W3 ", size=11, bold=True), R("rosbag fusion evaluator: innovations, NIS, dropout", size=11), after=5),
    P(R("W4 ", size=11, bold=True), R("low-speed matrix with an E-stop operator; one result card per run",
                                        size=11), after=8),
    P(R("Deliverables: ", size=11, bold=True, color=CRIMSON),
      R("log validators, fusion evaluator, result cards — as small reviewed pull requests.", size=11), after=5),
    P(R("Senior team keeps safety gates and claim sign-off.", size=10.5, italic=True, color=GRAY)),
])
box(s, gx, 5.55, gw, 1.3, fill=CRIMSON, radius=0.08)
text(s, gx + 0.14, 5.58, gw - 0.28, 1.24, [
    P(R("Research question", size=11, bold=True, color="F2D5E1"), after=3),
    P(R("Do HyperLIF/CMG temporal states improve fusion and control beyond a memoryless residual with "
        "the same inputs and bounds?", size=12, bold=True, color=WHITE))], anchor="m")
footer(s, [("Hardware (low speed)", "hardware"), ("Fusion + MPC plan", "proposed")],
       "Source: qcar/docs/CAPABILITY_AUDIT_AND_GRAFTON_PLAN_2026-09-08 · earlier benchmark from the legacy code base")
notes(s, """
Line 5 — QCar: neuromorphic sensor fusion and control (with Grafton).
- What exists: a hardware-safe lane-following runner on the car's Jetson with 7 controllers (PID, SMC, image-state beam-search NMPC, Adaptive-HyperLIF gate, and PID/SMC/NMPC + gated HyperLIF residual), tested at low speed with perception-only checks first. A ROS 2 EKF lineage fuses wheel speed, IMU yaw rate and RF2O LiDAR odometry.
- Honest notes: the current "NMPC" is a two-state image model, so we call it image-state NMPC; the earlier RMS numbers (0.126 -> 0.112) come from the legacy code base and traded tracking for steering effort (5.9% saturation). The EKF audit found items to fix before calling it validated fusion (LiDAR odometry labeled GPS, correlated heading reuse, no timestamp alignment, fixed Q, non-Joseph update).
- Plan: Phase A uses everything Quanser provides (sensors, ROS 2, estimation) for a fused-state kinematic-bicycle MPC with hard constraints. Phase B adds our neuromorphic layer — HyperLIF or CMG populations as temporal encoders of the sensor streams and innovations, and a PES-learned bounded residual on the MPC command projected into a safe set. Phase C benchmarks it against ANN/RL residuals with identical inputs and bounds, so any gain can be attributed to the temporal neuron states.
- Grafton owns reproducibility (signal dictionary, log validators, offline tests, fusion evaluator, result cards) through small reviewed pull requests; safety authority stays with the senior team.
""")

# ============================================================ 11. Space
s = new_slide("Space Systems | Basilisk Twin & 3-DOF Gyroscope",
              "Neuromorphic perception and control for spacecraft attitude; the gyroscope is our physical "
              "momentum-exchange testbed", kicker_x=3.3)
number_chip(s, 0.5, 1.45, 6)
pic(s, FIG / "basilisk_satellite.png", 0.45, 1.98, w=5.0)
text(s, 0.5, 5.3, 5.0, 1.55, [
    P(R("Basilisk 2.11.1 with native MuJoCo dynamics (MJScene): bus + 3 reaction wheels; standard navigation, "
        "guidance, MRP feedback and wheel allocation.", size=11.5), bullet=True, after=3),
    P(R("600 s: ‖σ‖ 0.374 → 6.4×10⁻⁴; rate error 5.5×10⁻⁵ rad/s; wheel torque saturates at the 0.2 N·m "
        "limit, then recovers.", size=11.5), bullet=True),
])
pic(s, MEDIA / "s5_Imagen_19.png", 5.75, 1.98, h=1.9)
text(s, 7.2, 2.0, 5.65, 1.9, [
    P(R("3-DOF gyroscope (Quanser)", size=12.5, bold=True, color=CRIMSON), after=3),
    P(R("Spinning rotor h = J_r·Ω inside two gimbals: torque on one gimbal moves the other through "
        "gyroscopic coupling — the control-moment-gyroscope principle used on spacecraft.", size=11),
      after=3),
    P(R("Model, identification plan and PID/LQR/LQG/backstepping/SMC/NMPC derived (theory paper); "
        "Julia/QUARC Q8 channel map ready. No hardware run yet.", size=11, italic=True, color=GRAY)),
])
# methodology loop
mx, my = 5.75, 4.05
BW, GAP = 2.12, 0.36
boxes = [
    (mx, my, BW, 0.8, "Basilisk mission", "orbit, environment, flight software", TEAL, INK),
    (mx + BW + GAP, my, BW, 0.8, "Twin (MuJoCo)", "gimbal model inside MJScene", SAND, INK),
    (mx + 2 * (BW + GAP), my, BW, 0.8, "Gyroscope hardware", "QUARC / Julia HIL (Q8)", CRIMSON, WHITE),
]
for bx, by, bw, bh, head, sub, fill, fg in boxes:
    b = box(s, bx, by, bw, bh, fill=fill, radius=0.1)
    shape_text(b, [P(R(head, size=11.5, bold=True, color=fg)), P(R(sub, size=10, color=fg))], margin=0.06)
for k in (1, 2):
    ax_ = mx + k * BW + (k - 1) * GAP
    a = s.shapes.add_shape(MSO_SHAPE.LEFT_RIGHT_ARROW, Inches(ax_ + 0.04), Inches(my + 0.27), Inches(GAP - 0.08),
                           Inches(0.26))
    a.fill.solid()
    a.fill.fore_color.rgb = rgb("8C8C8C")
    a.line.fill.background()
b = box(s, mx, my + 0.92, 7.08, 0.5, fill=LIGHT, radius=0.1)
shape_text(b, [P(R("Perception: ", size=11, bold=True, color=CRIMSON),
                 R("encoders / IMU / camera → event-driven SNN estimator    ", size=11),
                 R("Control: ", size=11, bold=True, color=CRIMSON),
                 R("classical baseline + bounded CMG–PES / HyperLIF residual", size=11), align="l")], margin=0.12)
table(s, mx, my + 1.55, [0.62, 6.46], [
    ["Step", "Experimental ladder"],
    ["E0 ✓", "Single-satellite MRP baseline reproduced (600 s)"],
    ["G1–G2", "Identify J_r, J_t, friction, h; gimbal twin validated against held-out hardware logs"],
    ["G3", "Hardware in the loop: Basilisk mission profiles executed on the gyroscope"],
    ["E2–E4", "ANN vs SNN estimators on identical data → bounded residual → multi-spacecraft graph"],
], row_h=0.28, size=10, header_size=10, aligns=["c", "l"])
footer(s, [("Digital twin: satellite", "twin"), ("Gyroscope: proposed", "proposed")],
       "Sources: spacecraft_twin/results/verified_single_satellite_600s_20260908 · PROPOSAL.md · gyroscope theory paper")
notes(s, """
Line 6 — Neuromorphic perception and control for space systems.
- What runs today: Basilisk 2.11.1 with its native MuJoCo dynamics (MJScene). A single satellite with three reaction wheels, standard Basilisk navigation/guidance/MRP feedback and wheel allocation, converges from an MRP error of 0.374 to 6.4e-4 in 600 s (rate error 5.5e-5 rad/s). The wheel torque hits the 0.2 N m limit early and recovers.
- Gyroscope: not started in code. The theory paper derives the physics (h = J_r Omega, gyroscopic coupling between gimbals), identification of inertias/friction, and the classical controller suite. It is the laboratory version of a control-moment gyroscope.
- Terminology: our neuron "CMG" means coupled membrane-gate — do not confuse it with a control-moment gyroscope.
- Methodology to integrate perception, control and hardware:
  1) identify the gyroscope (rotor inertia, transverse inertia, friction, momentum) from bounded hardware logs;
  2) build its gimbal twin in MuJoCo inside Basilisk and validate it on held-out logs;
  3) hardware in the loop: Basilisk generates mission profiles (slews, disturbance torques) and the physical gyroscope executes them through QUARC / the Julia HIL bridge;
  4) perception: event-driven SNN estimator vs an ANN estimator on the same encoder/IMU/camera data;
  5) control: classical baseline plus the bounded CMG-PES / HyperLIF residual, same safety structure as the UAVs;
  6) then multi-spacecraft with an explicit communication graph (delay, loss).
- Energy claims only with measured power, not operation counts.
""")

# ============================================================ 12. Summary
s = new_slide("Summary | Next Steps", "One architecture — classical baseline + bounded neuromorphic residual — "
              "from simulation to twins to hardware", kicker_x=3.3)
box(s, 0.5, 2.0, 3.6, 4.8, fill=CRIMSON, radius=0.04)
text(s, 0.68, 2.12, 3.25, 4.62, [
    P(R("Where we stand", size=16, bold=True, color=WHITE, font=TITLE_FONT), after=9),
    P(R("Papers: ", size=12.5, bold=True, color=WHITE), R("1 accepted (ComRob), 2 near submission "
                                                           "(ACC, ToE).", size=12.5, color=WHITE), after=7),
    P(R("Simulation: ", size=12.5, bold=True, color=WHITE),
      R("CMG–PES improves every PD baseline on X2/CF2 and rejects disturbances; on the omnicopter it wins "
        "under impulses and model mismatch (PD wins nominal).", size=12.5, color=WHITE), after=7),
    P(R("Hardware: ", size=12.5, bold=True, color=WHITE),
      R("Qube gate residual is sparse (4.4% active); Hover Roll +2.7% (3 pairs).", size=12.5, color=WHITE),
      after=7),
    P(R("Julia: ", size=12.5, bold=True, color=WHITE), R("reproduces the Python neuron and forward results and "
                                                          "drives Quanser twins; HPC runs next.", size=12.5,
                                                          color=WHITE), after=7),
    P(R("Rule: ", size=12.5, bold=True, color=WHITE), R("software, twin, hardware and proposed claims are "
                                                         "never merged.", size=12.5, color=WHITE)),
])
table(s, 4.4, 2.0, [2.2, 3.35, 2.88], [
    ["Track", "Next 2–4 weeks", "This semester"],
    ["Papers", "ACC 2027 submission (advisor sign-off); ComRob minor revisions", "ToE submission"],
    ["1 HyperLIF", "Launch Julia screen on NMSU HPC", "5-seed runs; gradient parity"],
    ["2 Quanser + Julia", "Matched Python ↔ Julia twin runs; Hover sensor-only test", "Julia on hardware; Julia SysID"],
    ["3 Omnicopter", "Mass / inertia / thrust-map identification", "Shadow mode → tethered hover"],
    ["4 DILISIC", "Exact flocking law; QArm 1-joint ID", "Shadow replay → low-authority loop"],
    ["5 QCar", "Grafton W1–W4; fused-state MPC", "Neuromorphic fusion + residual benchmark"],
    ["6 Space", "Gyroscope identification + twin", "HIL with Basilisk; ANN vs SNN estimator"],
], row_h=0.6, size=11, header_size=11.5, bold_first_col=True, aligns=["l", "l", "l"])
footer(s, None, "All numbers in this deck trace to saved result files or passing tests (list in speaker notes).")
notes(s, """
Close (30 s): one idea across all platforms — keep the classical controller as the stability anchor, add a small bounded neuromorphic correction, and move it from simulation to digital twins to hardware with the evidence labeled at each step.

Provenance of the numbers in this deck:
- ACC: Overleaf export "Online_PES_Decoder_HyperLIF_Residual_Control___Quaternion_Tracking (16).pdf", Table II, Sec. IV.
- ComRob: 2026_Comrob_Hexa_Neural.pdf, Tables I-II.
- ToE: 2026___IEEE_ToE (7).pdf, Tables IV-V.
- HyperLIF: C:\\Research\\papers\\P1_HyperLIF_Learning\\main.tex; code\\docs\\PARITY.md; THREE_STAGE_DEVELOPMENT_REPORT_2026-09-09.md; Julia portable tests re-run 2026-09-18 (16/16).
- Quanser/Julia: C:\\Research\\julia_bridge\\VALIDATION_STATUS.md and results\\twin_swingup_julia_twin_sign1_20260723_025715.json; hover3dof\\julia smoke re-run 2026-09-18 (103/103); pendulum\\docs\\qube_residual_results_and_next_steps_20260614.md; WORKFLOW.md sec. 5.7; hover3dof ... FROZEN_AUDIT_2026-09-02.
- Omnicopter: C:\\Research\\omnicopter\\mujoco\\control\\research\\FROZEN_RESULTS_20260910.md and heldout_500hz_batch_20260910.
- DILISIC: C:\\Research\\dilisic\\verify.py, reference\\dilisic_80s_contract_fixed_20260908, docs\\MATH_AUDIT_2026-09-08.md, docs\\QARM_RUNBOOK_2026-09-09.md.
- QCar: C:\\Research\\qcar\\docs\\CAPABILITY_AUDIT_AND_GRAFTON_PLAN_2026-09-08.md, docs\\source_inventory.md.
- Space: C:\\Research\\spacecraft_twin\\results\\verified_single_satellite_600s_20260908\\summary.json; gyro3dof theory paper.
""")

prs.save(str(OUT))
print("saved", OUT, len(prs.slides), "slides")
