# -*- coding: utf-8 -*-
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
import copy

# ---------- palette ----------
NAVY = RGBColor(0x1B, 0x22, 0x30)
NAVY2 = RGBColor(0x24, 0x2E, 0x40)
LIGHT = RGBColor(0xF4, 0xF5, 0xF3)
SURFACE = RGBColor(0xFF, 0xFF, 0xFF)
CLASSICAL = RGBColor(0x3D, 0x5A, 0x80)
CLASSICAL_L = RGBColor(0x7F, 0xA8, 0xD9)
CMG = RGBColor(0xC6, 0x69, 0x0A)
CMG_L = RGBColor(0xF2, 0xA5, 0x4A)
TEXT_LIGHT = RGBColor(0xEC, 0xEE, 0xF0)
TEXT_DARK = RGBColor(0x17, 0x1B, 0x1F)
MUTED_ON_DARK = RGBColor(0x9B, 0xA8, 0xB4)
MUTED_ON_LIGHT = RGBColor(0x5C, 0x66, 0x70)
LINE = RGBColor(0xDC, 0xE0, 0xE1)
NEG = RGBColor(0xB3, 0x41, 0x1F)

HEAD_FONT = "Cambria"
BODY_FONT = "Calibri"

PLOTS = r"C:\Research\papers\ACC2027_Gate_Residual_Control\results\plots"
HOVER_PLOTS = r"C:\Research\hover3dof\results\plots\set_e_final"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide(bg=LIGHT):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg
    return s


def tb(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP, word_wrap=True):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = word_wrap
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return box, tf


def set_run(run, text, font=BODY_FONT, size=14, color=TEXT_DARK, bold=False, italic=False):
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    return run


def para(tf, text, font=BODY_FONT, size=14, color=TEXT_DARK, bold=False, italic=False,
         space_after=6, align=PP_ALIGN.LEFT, first=False, bullet=False, level=0):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after)
    p.level = level
    r = p.add_run()
    set_run(r, text, font, size, color, bold, italic)
    if bullet:
        pPr = p._pPr
        if pPr is None:
            pPr = p._p.get_or_add_pPr()
        buChar = pPr.makeelement(qn('a:buChar'), {'char': '\u2022'})
        buFont = pPr.makeelement(qn('a:buFont'), {'typeface': BODY_FONT})
        pPr.append(buFont)
        pPr.append(buChar)
        pPr.set('indent', str(Emu(Inches(-0.22))))
        pPr.set('marL', str(Emu(Inches(0.22))))
    return p


def eyebrow(slide, x, y, text, color=CMG, on_dark=False):
    _, tf = tb(slide, x, y, 8, 0.35)
    para(tf, text.upper(), font=BODY_FONT, size=11.5, color=color, bold=True, first=True)


def title_text(slide, x, y, w, text, size=32, color=TEXT_DARK, font=HEAD_FONT):
    _, tf = tb(slide, x, y, w, 1.1)
    p = para(tf, text, font=font, size=size, color=color, bold=True, first=True, space_after=0)
    p.line_spacing = 1.02


def footer(slide, text, on_dark=False):
    _, tf = tb(slide, 0.55, 7.08, 10, 0.3)
    para(tf, text, font=BODY_FONT, size=10, color=(MUTED_ON_DARK if on_dark else MUTED_ON_LIGHT), first=True)


def page_num(slide, n, on_dark=False):
    _, tf = tb(slide, 12.6, 7.08, 0.6, 0.3)
    para(tf, str(n), font=BODY_FONT, size=10, color=(MUTED_ON_DARK if on_dark else MUTED_ON_LIGHT),
         first=True, align=PP_ALIGN.RIGHT)


def rounded_box(slide, x, y, w, h, fill, line_color=None, radius=0.08):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = radius
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line_color is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def arrow(slide, x1, y1, x2, y2, color=MUTED_ON_LIGHT, width=1.75):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    ln = conn.line._get_or_add_ln()
    tail = ln.makeelement(qn('a:tailEnd'), {'type': 'triangle', 'w': 'med', 'len': 'med'})
    ln.append(tail)
    return conn


def stat_card(slide, x, y, w, h, num, label, num_color=CMG, bg=SURFACE, line_color=LINE, label_color=MUTED_ON_LIGHT):
    box = rounded_box(slide, x, y, w, h, bg, line_color=line_color, radius=0.06)
    _, tf = tb(slide, x + 0.18, y + 0.14, w - 0.36, h - 0.28)
    para(tf, num, font=HEAD_FONT, size=27, color=num_color, bold=True, first=True, space_after=3)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.LEFT
    p2.line_spacing = 1.12
    r = p2.add_run()
    set_run(r, label, font=BODY_FONT, size=10.5, color=label_color)
    return box


def img_fit(slide, path, x, y, max_w, max_h, align='left'):
    from PIL import Image
    im = Image.open(path)
    ar = im.size[0] / im.size[1]
    h = max_h
    w = h * ar
    if w > max_w:
        w = max_w
        h = w / ar
    if align == 'center':
        x = x + (max_w - w) / 2
    elif align == 'right':
        x = x + (max_w - w)
    slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    return w, h


def native_table(slide, x, y, w, h, headers, rows, header_bg=NAVY, header_fg=TEXT_LIGHT,
                  col_widths=None, delta_col=None, font_size=11.5):
    nrows, ncols = len(rows) + 1, len(headers)
    gtable = slide.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(h)).table
    if col_widths:
        for i, cw in enumerate(col_widths):
            gtable.columns[i].width = Inches(cw)
    for i, htext in enumerate(headers):
        cell = gtable.cell(0, i)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_bg
        cell.margin_left = cell.margin_right = Inches(0.08)
        cell.margin_top = cell.margin_bottom = Inches(0.03)
        tf = cell.text_frame
        tf.paragraphs[0].alignment = PP_ALIGN.LEFT if i == 0 else PP_ALIGN.RIGHT
        r = tf.paragraphs[0].add_run()
        set_run(r, htext, font=BODY_FONT, size=10.5, color=header_fg, bold=True)
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            cell = gtable.cell(ri + 1, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = SURFACE if ri % 2 == 0 else LIGHT
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            tf = cell.text_frame
            tf.paragraphs[0].alignment = PP_ALIGN.LEFT if ci == 0 else PP_ALIGN.RIGHT
            r = tf.paragraphs[0].add_run()
            bold = ci == 0
            color = TEXT_DARK
            if delta_col is not None and ci == delta_col:
                color = CMG if not str(val).startswith('-') else NEG
                bold = True
            set_run(r, str(val), font=BODY_FONT, size=font_size, color=color, bold=bold)
    # strip default banding style -> keep our own fills
    tbl = gtable._tbl
    tblPr = tbl.find(qn('a:tblPr'))
    if tblPr is not None:
        tblPr.set('firstRow', '0')
        tblPr.set('bandRow', '0')
    return gtable


# =====================================================================
# Slide 1 - Title
# =====================================================================
s = add_slide(bg=NAVY)
rounded_box(s, 0.0, 0.0, 13.333, 7.5, NAVY, radius=0.0)
eyebrow(s, 0.9, 1.55, "CMG-PES Residual Control", color=CMG_L)
_, tf = tb(s, 0.85, 1.95, 11.5, 2.1)
para(tf, "Coupled Membrane\u2013Gate Residual Control", font=HEAD_FONT, size=44,
     color=TEXT_LIGHT, bold=True, first=True, space_after=6)
p2 = tf.add_paragraph()
p2.line_spacing = 1.05
r = p2.add_run()
set_run(r, "Online-adaptive neuromorphic augmentation for attitude tracking",
        font=HEAD_FONT, size=22, color=CLASSICAL_L, italic=True)
_, tf2 = tb(s, 0.9, 4.35, 10, 0.6)
para(tf2, "From MuJoCo simulation to first physical hardware validation",
     font=BODY_FONT, size=15, color=MUTED_ON_DARK, first=True)

# divider dots motif (three small circles = the 3 result tiers: sim / hardware / paper)
for i, (lbl, col) in enumerate([("Simulation", CLASSICAL_L), ("Hardware", CMG_L), ("Manuscript", TEXT_LIGHT)]):
    xx = 0.9 + i * 2.3
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(xx), Inches(5.55), Inches(0.14), Inches(0.14))
    dot.fill.solid(); dot.fill.fore_color.rgb = col; dot.line.fill.background(); dot.shadow.inherit = False
    _, tfl = tb(s, xx + 0.24, 5.48, 2.0, 0.3)
    para(tfl, lbl, font=BODY_FONT, size=12, color=MUTED_ON_DARK, first=True)

_, tf3 = tb(s, 0.9, 6.7, 10, 0.4)
para(tf3, "Gandhi A. Contreras Torres \u00b7 ACC 2027 working draft \u00b7 August 2026",
     font=BODY_FONT, size=12, color=MUTED_ON_DARK, first=True)

print("slide 1 done")

# =====================================================================
# Slide 2 - The idea / workflow
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "The Architecture")
title_text(s, 0.55, 0.78, 11, "A small residual on top of a trusted baseline")
_, tf = tb(s, 0.55, 1.75, 7.3, 0.9)
para(tf, "The classical baseline is never attenuated or replaced. A bounded residual, "
         "learned online during the mission itself, is added on top \u2014 closing gaps the "
         "fixed gain cannot, without touching its authority.", font=BODY_FONT, size=13.5,
     color=MUTED_ON_LIGHT, first=True)
p2 = tf.paragraphs[0]; p2.line_spacing = 1.15

# workflow diagram: Reference -> Error -> Baseline -> (+) -> Command -> Plant -> feedback
y0 = 3.05
boxes = [
    ("Reference", 0.55, CLASSICAL, TEXT_LIGHT),
    ("Error", 2.55, NAVY2, TEXT_LIGHT),
]
def flow_box(slide, x, y, w, h, text, fill, fg, size=12.5):
    b = rounded_box(slide, x, y, w, h, fill, radius=0.14)
    tf_ = b.text_frame
    tf_.word_wrap = True
    tf_.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_.margin_left = tf_.margin_right = Inches(0.05)
    p = tf_.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    set_run(r, text, font=BODY_FONT, size=size, color=fg, bold=True)
    return b

flow_box(s, 0.55, y0, 1.55, 0.85, "Reference\nr(t)", CLASSICAL, TEXT_LIGHT)
flow_box(s, 2.55, y0, 1.55, 0.85, "Error\ne = r \u2212 x", NAVY2, TEXT_LIGHT)
flow_box(s, 4.55, y0 - 0.55, 2.0, 0.85, "Classical\nbaseline u\u2080", CLASSICAL, TEXT_LIGHT)
flow_box(s, 4.55, y0 + 0.55, 2.0, 0.85, "CMG\u2013PES\nresidual \u03b2\u00b7neural", CMG, TEXT_LIGHT)
sum_circle = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.05), Inches(y0 + 0.13), Inches(0.6), Inches(0.6))
sum_circle.fill.solid(); sum_circle.fill.fore_color.rgb = NAVY; sum_circle.line.fill.background(); sum_circle.shadow.inherit = False
tf_s = sum_circle.text_frame; tf_s.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf_s.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
set_run(p.add_run(), "+", font=HEAD_FONT, size=22, color=TEXT_LIGHT, bold=True)
flow_box(s, 8.15, y0, 1.7, 0.85, "Command\nu = sat(u\u2080+\u0394u)", NAVY2, TEXT_LIGHT, size=11.5)
flow_box(s, 10.35, y0, 1.55, 0.85, "Plant", CLASSICAL, TEXT_LIGHT)

arrow(s, 2.1, y0 + 0.425, 2.55, y0 + 0.425)
arrow(s, 4.1, y0 + 0.425, 4.4, y0 - 0.125)
arrow(s, 4.1, y0 + 0.425, 4.4, y0 + 0.975)
arrow(s, 6.55, y0 - 0.125, 7.03, y0 + 0.3)
arrow(s, 6.55, y0 + 0.975, 7.03, y0 + 0.5)
arrow(s, 7.67, y0 + 0.425, 8.13, y0 + 0.425)
arrow(s, 9.87, y0 + 0.425, 10.33, y0 + 0.425)
# feedback loop
arrow(s, 11.13, y0 + 0.87, 11.13, y0 + 1.55, color=MUTED_ON_LIGHT)
arrow(s, 11.13, y0 + 1.55, 1.3, y0 + 1.55, color=MUTED_ON_LIGHT)
arrow(s, 1.3, y0 + 1.55, 1.3, y0 + 0.87, color=MUTED_ON_LIGHT)
_, tff = tb(s, 3.0, y0 + 1.65, 6, 0.3)
para(tff, "state x(t) feeds back into the error", font=BODY_FONT, size=10.5, color=MUTED_ON_LIGHT,
     first=True, align=PP_ALIGN.CENTER)

_, tf = tb(s, 0.55, 5.9, 12.2, 0.9)
para(tf, "The residual is bounded (\u2264 \u03b2\u00b7limits) and disarmable to zero \u2014 the baseline alone "
         "always remains a safe fallback.", font=BODY_FONT, size=12, color=MUTED_ON_LIGHT, first=True, italic=True)
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 2)

print("slide 2 done")

# =====================================================================
# Slide 3 - Why a fixed gain isn't enough
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "The Gap It Closes")
title_text(s, 0.55, 0.78, 11.5, "A fixed gain has no feedforward for a moving target")
_, tf = tb(s, 0.55, 1.9, 6.0, 4.6)
para(tf, "The classical law", font=BODY_FONT, size=14, color=MUTED_ON_LIGHT, first=True, space_after=4)
p = tf.add_paragraph(); p.space_after = Pt(14)
r = p.add_run(); set_run(r, "\u03c4\u2080 = \u2212k_q\u00b7e_q \u2212 k_w\u00b7\u03c9", font="Consolas", size=19, color=CLASSICAL, bold=True)
para(tf, "is computed once, offline, around a nominal model. It has no way to notice, "
         "in flight, unmodeled coupling, actuator nonlinearity \u2014 or that the reference "
         "itself is moving.", font=BODY_FONT, size=13.5, color=TEXT_DARK, space_after=14)
para(tf, "A fixed-gain regulator chasing a moving target carries structural phase lag. "
         "That is linear control theory, not a limitation better tuning removes.",
     font=BODY_FONT, size=13.5, color=TEXT_DARK, space_after=14)
para(tf, "The residual doesn't need a better model \u2014 only a cheap supervisory signal "
         "and a little authority to learn, online, whatever correction the fixed gain "
         "structurally cannot express.", font=BODY_FONT, size=13.5, color=CMG, bold=True)
for p in tf.paragraphs:
    p.line_spacing = 1.18

# right: mini result callout echoing the biggest win
rounded_box(s, 7.0, 1.9, 5.75, 4.6, NAVY, radius=0.05)
_, tf2 = tb(s, 7.35, 2.2, 5.05, 0.4)
para(tf2, "WHERE THIS SHOWS UP MOST", font=BODY_FONT, size=11, color=CMG_L, bold=True, first=True)
_, tf3 = tb(s, 7.35, 2.7, 5.05, 3.6)
para(tf3, "+60.6%", font=HEAD_FONT, size=40, color=CMG_L, bold=True, first=True, space_after=2)
para(tf3, "yaw360 \u2014 smooth continuous ramp, X2 & CF2", font=BODY_FONT, size=13, color=TEXT_LIGHT, space_after=18)
para(tf3, "+56.3%", font=HEAD_FONT, size=40, color=CMG_L, bold=True, space_after=2)
para(tf3, "full3 \u2014 3-axis continuous sinusoid", font=BODY_FONT, size=13, color=TEXT_LIGHT, space_after=18)
para(tf3, "Both are continuously-moving references \u2014 exactly where a fixed gain's "
          "missing feedforward term costs the most.", font=BODY_FONT, size=12, color=MUTED_ON_DARK, italic=True)
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 3)

print("slide 3 done")

# =====================================================================
# Slide 4 - The CMG neuron: equations
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "The CMG Unit")
title_text(s, 0.55, 0.78, 11.5, "Two coupled states, not a filter")

def eq_line(slide, x, y, w, text, size=15, color=NAVY):
    _, tf_ = tb(slide, x, y, w, 0.5)
    p = tf_.paragraphs[0]
    r = p.add_run(); set_run(r, text, font="Consolas", size=size, color=color, bold=True)
    return tf_

rounded_box(s, 0.55, 1.85, 6.1, 2.55, NAVY, radius=0.06)
_, tfx = tb(s, 0.85, 2.05, 5.5, 2.2)
para(tfx, "gate:", font=BODY_FONT, size=11, color=CMG_L, first=True, space_after=1)
para(tfx, "\u03c4_r\u00b7dr/dt = \u03c3(\u03b1(v \u2212 (v_th \u2212 \u03b3\u00b7r))) \u2212 r", font="Consolas", size=14, color=TEXT_LIGHT, space_after=14)
para(tfx, "membrane (exact exponential update):", font=BODY_FONT, size=11, color=CMG_L, space_after=1)
para(tfx, "\u03c4\u00b7dv/dt = \u2212(v\u2212v_rest) \u2212 \u03c4\u00b7g(r)\u00b7(v\u2212v_reset) + I", font="Consolas", size=14, color=TEXT_LIGHT, space_after=6)
para(tfx, "g(r) = (g\u2080 + g\u2081|I|)\u00b7r\u00b2   \u2190 gate-dependent conductance", font="Consolas", size=12.5, color=MUTED_ON_DARK)

_, tf = tb(s, 0.55, 4.65, 6.1, 2.5)
para(tf, "v = membrane potential.  r = gate state, 0\u20131.  Each modulates the "
         "other's equation \u2014 that mutual dependence is the \u201ccoupling.\u201d",
     font=BODY_FONT, size=13, color=TEXT_DARK, first=True, space_after=10)
para(tf, "As r grows it raises its own threshold (\u2212\u03b3r) AND the membrane's decay "
         "rate (g(r)~r\u00b2) \u2014 both negative feedback on v. This is spike-frequency "
         "adaptation: a strong response, then rapid self-damping, even while the "
         "input persists.", font=BODY_FONT, size=13, color=TEXT_DARK)
for p in tf.paragraphs: p.line_spacing = 1.16

img_fit(s, PLOTS + r"\x2_hard45_neuron_activity.png", 6.95, 1.85, 5.85, 5.3, align='center')
_, tfc = tb(s, 6.95, 7.14, 5.85, 0.3)
para(tfc, "Real logged trace, X2 hard45 \u2014 not illustrative", font=BODY_FONT, size=9.5,
     color=MUTED_ON_LIGHT, first=True, align=PP_ALIGN.CENTER, italic=True)
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 4)

print("slide 4 done")

# =====================================================================
# Slide 5 - Decoding + PES learning
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "Population Code \u2192 Command")
title_text(s, 0.55, 0.78, 11.7, "Six near-binary units, one graded correction \u2014 learned online")

_, tf = tb(s, 0.55, 1.85, 6.1, 5.1)
para(tf, "PAIRED CURRENTS (push\u2013pull encoding)", font=BODY_FONT, size=11, color=CMG, bold=True, first=True, space_after=3)
para(tf, "I\u207a = bias + gain\u00b7max(e, 0)      I\u207b = bias + gain\u00b7max(\u2212e, 0)", font="Consolas", size=13, color=NAVY, space_after=14)
para(tf, "DECODE (population code)", font=BODY_FONT, size=11, color=CMG, bold=True, space_after=3)
para(tf, "activity = clip(10\u2075\u00b7r, 0, 1)   \u2192 nearly binary per unit", font="Consolas", size=13, color=NAVY, space_after=2)
para(tf, "signed = clip(W\u00b7activity, \u22121, 1)   \u2192 graded, from the population", font="Consolas", size=13, color=NAVY, space_after=14)
para(tf, "ONLINE-PES LEARNING (delta rule)", font=BODY_FONT, size=11, color=CMG, bold=True, space_after=3)
para(tf, "W += \u03b7\u00b7(target \u2212 signed) \u2297 activity \u2212 \u03bb\u00b7W", font="Consolas", size=14, color=CMG, bold=True, space_after=14)
para(tf, "target is computed independently of the baseline \u2014 the single detail that "
         "makes this a real learning signal instead of a tautology.",
     font=BODY_FONT, size=12.5, color=TEXT_DARK, italic=True)
for p in tf.paragraphs: p.line_spacing = 1.15

rounded_box(s, 7.0, 1.85, 5.75, 5.15, LIGHT, line_color=LINE, radius=0.05)
_, tf2 = tb(s, 7.3, 2.05, 5.15, 0.35)
para(tf2, "WHY THIS BEATS A FIXED GAIN", font=BODY_FONT, size=11, color=MUTED_ON_LIGHT, bold=True, first=True)
items = [
    ("Individually near-binary", "gate_gain=10\u2075 makes one unit's activity almost a hard step."),
    ("Graded by population", "W combines 6 units \u2014 the same trick real cortex uses to encode continuous quantities from saturating cells."),
    ("Residual learning", "Same idea as ResNets / boosting: don't relearn the controller \u2014 learn only the gap the fixed gain leaves."),
]
yy = 2.55
for hd, body in items:
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(7.3), Inches(yy + 0.05), Inches(0.13), Inches(0.13))
    dot.fill.solid(); dot.fill.fore_color.rgb = CMG; dot.line.fill.background(); dot.shadow.inherit = False
    _, tfi = tb(s, 7.58, yy - 0.05, 4.9, 0.9)
    para(tfi, hd, font=BODY_FONT, size=13.5, color=TEXT_DARK, bold=True, first=True, space_after=2)
    p = para(tfi, body, font=BODY_FONT, size=12, color=MUTED_ON_LIGHT)
    p.line_spacing = 1.12
    yy += 1.15
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 5)

print("slide 5 done")

# =====================================================================
# Slide 6 - MuJoCo mission-suite results table
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "Simulation Results")
title_text(s, 0.55, 0.78, 11.7, "Every mission improves \u2014 none regresses")
_, tf = tb(s, 0.55, 1.55, 11, 0.5)
para(tf, "Matched configuration: dt=0.0005s, \u03b2=0.5, learning rate=8\u00d710\u207b\u2074, k_error=8, 45s duration.",
     font=BODY_FONT, size=12, color=MUTED_ON_LIGHT, first=True)

headers = ["Platform / mission", "Classical (rad)", "CMG\u2013PES (rad)", "Improvement"]
rows = [
    ["X2 \u2014 yaw360", "0.0759", "0.0299", "+60.6%"],
    ["X2 \u2014 full3", "0.3033", "0.1317", "+56.6%"],
    ["X2 \u2014 hard45", "0.2941", "0.1380", "+53.1%"],
    ["X2 \u2014 hardstep", "0.4545", "0.3594", "+20.9%"],
    ["X2 \u2014 roll", "0.0506", "0.0418", "+17.4%"],
    ["CF2 \u2014 yaw360", "0.0758", "0.0299", "+60.6%"],
    ["CF2 \u2014 full3", "0.2884", "0.1265", "+56.1%"],
    ["CF2 \u2014 hard45", "0.2854", "0.1323", "+53.7%"],
    ["CF2 \u2014 hardstep", "0.4262", "0.3479", "+18.4%"],
    ["CF2 \u2014 roll", "0.0513", "0.0424", "+17.3%"],
]
native_table(s, 0.55, 2.15, 8.1, 4.6, headers, rows, col_widths=[3.0, 1.7, 1.7, 1.7],
             delta_col=3, font_size=12.5)

rounded_box(s, 8.95, 2.15, 3.85, 4.6, NAVY, radius=0.06)
_, tf2 = tb(s, 9.25, 2.4, 3.3, 4.1)
para(tf2, "READING THE PATTERN", font=BODY_FONT, size=11, color=CMG_L, bold=True, first=True, space_after=10)
para(tf2, "Biggest gains \u2014 yaw360, full3", font=BODY_FONT, size=13, color=TEXT_LIGHT, bold=True, space_after=2)
p=para(tf2, "continuously-moving references, structural baseline lag.", font=BODY_FONT, size=11.5, color=MUTED_ON_DARK, space_after=12)
para(tf2, "Smallest gain \u2014 roll", font=BODY_FONT, size=13, color=TEXT_LIGHT, bold=True, space_after=2)
p=para(tf2, "baseline already near its floor \u2014 little gap left to close.", font=BODY_FONT, size=11.5, color=MUTED_ON_DARK, space_after=12)
para(tf2, "Mean \u2260 peak \u2014 hardstep", font=BODY_FONT, size=13, color=TEXT_LIGHT, bold=True, space_after=2)
p=para(tf2, "an instantaneous step's peak error is actuator-rate-limited for any controller.", font=BODY_FONT, size=11.5, color=MUTED_ON_DARK)
for p in tf2.paragraphs: p.line_spacing = 1.15
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 6)

print("slide 6 done")

# =====================================================================
# Slide 7 - tracking plot example
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "Simulation \u2014 In Detail")
title_text(s, 0.55, 0.78, 11.7, "yaw360, Skydio X2: tracking, error, and control effort")
img_fit(s, PLOTS + r"\x2_yaw360_classical_vs_cmg.png", 0.55, 1.65, 6.4, 5.55, align='left')
_, tf = tb(s, 7.25, 1.85, 5.5, 5.2)
para(tf, "OUTPUTS", font=BODY_FONT, size=11, color=CMG, bold=True, first=True, space_after=3)
para(tf, "True per-axis roll/pitch/yaw tracked against reference \u2014 the "
         "amber (CMG\u2013PES) line hugs the dashed reference visibly tighter "
         "than blue (classical).", font=BODY_FONT, size=12.5, color=TEXT_DARK, space_after=14)
para(tf, "ERROR", font=BODY_FONT, size=11, color=CMG, bold=True, space_after=3)
para(tf, "Combined tracking-error magnitude, both controllers overlaid. "
         "Dotted lines mark each run's mean \u2014 the residual's line sits "
         "well below classical's for nearly the entire 45 s.",
     font=BODY_FONT, size=12.5, color=TEXT_DARK, space_after=14)
para(tf, "INPUTS", font=BODY_FONT, size=11, color=CMG, bold=True, space_after=3)
para(tf, "All three torque channels for both controllers \u2014 the residual "
         "stays within its declared bound throughout.",
     font=BODY_FONT, size=12.5, color=TEXT_DARK)
for p in tf.paragraphs: p.line_spacing = 1.16
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 7)

print("slide 7 done")

# =====================================================================
# Slide 8 - Hardware intro
# =====================================================================
s = add_slide(bg=NAVY)
eyebrow(s, 0.55, 0.45, "First Physical Hardware Run", color=CMG_L)
title_text(s, 0.55, 0.78, 11.7, "Quanser 3DOF Hover: same controller, real motors", color=TEXT_LIGHT)
_, tf = tb(s, 0.55, 1.75, 6.3, 5.2)
para(tf, "The vendor's own LQR baseline", font=BODY_FONT, size=13.5, color=CMG_L, bold=True, first=True, space_after=3)
para(tf, "K reproduced via MATLAB lqr(A,B,Q,R) from the vendor Laboratory "
         "Guide, matched to published precision \u2014 not a controller chosen "
         "for this paper.", font=BODY_FONT, size=12.5, color=MUTED_ON_DARK, space_after=14)
para(tf, "Positive-voltage-only actuation", font=BODY_FONT, size=13.5, color=CMG_L, bold=True, space_after=3)
para(tf, "u \u2265 0 always \u2014 the vendor warns negative excursions can damage "
         "the amplifier. A real physical constraint the simulated drones "
         "don't have.", font=BODY_FONT, size=12.5, color=MUTED_ON_DARK, space_after=14)
para(tf, "Residual authority: ~13% of total", font=BODY_FONT, size=13.5, color=CMG_L, bold=True, space_after=3)
para(tf, "3V of 24V, capped outside the baseline by a disarmed-by-default "
         "safety bridge \u2014 deliberate, not a tuning limitation.",
     font=BODY_FONT, size=12.5, color=MUTED_ON_DARK)
for p in tf.paragraphs: p.line_spacing = 1.18

rounded_box(s, 7.2, 1.75, 5.55, 5.2, NAVY2, radius=0.06)
_, tf2 = tb(s, 7.5, 2.0, 4.95, 4.7)
para(tf2, "FOUR BUGS, FOUND ONLY BY RUNNING REAL HARDWARE", font=BODY_FONT, size=11,
     color=CMG_L, bold=True, first=True, space_after=10)
bugs = [
    "Channel swap \u2014 vendor's own figure disagreed with its own table; silently inverted roll correction sign.",
    "No encoder tare, raw-difference velocity \u2014 spurious 60\u00b0 error + amplified quantization noise.",
    "Full baseline fed into the safety bridge's bounded argument \u2014 silently discarded nearly all authority.",
    "Gate drive == learning target \u2014 decoder had nothing to learn beyond a saturated copy of one signal.",
]
for i, b in enumerate(bugs):
    para(tf2, f"{i+1}.", font=BODY_FONT, size=13, color=CMG_L, bold=True, space_after=1)
    p = tf2.paragraphs[-1]
    r2 = p.add_run(); set_run(r2, "  " + b, font=BODY_FONT, size=12, color=TEXT_LIGHT)
    p.space_after = Pt(11)
    p.line_spacing = 1.14
footer(s, "Coupled Membrane\u2013Gate Residual Control", on_dark=True); page_num(s, 8, on_dark=True)

print("slide 8 done")

# =====================================================================
# Slide 9 - hardware results
# =====================================================================
s = add_slide()
eyebrow(s, 0.55, 0.45, "Hardware Results")
title_text(s, 0.55, 0.78, 11.7, "Every hardware mission improves, zero regressions")
_, tf = tb(s, 0.55, 1.55, 11, 0.5)
para(tf, "\u03b2=0.4, max-residual=3V, learning rate=3\u00d710\u207b\u2074, k_error=4, 25s, n=1 per condition.",
     font=BODY_FONT, size=12, color=MUTED_ON_LIGHT, first=True)

headers = ["Mission", "Classical (deg)", "CMG\u2013PES (deg)", "Improvement"]
rows = [
    ["yaw360", "9.696", "9.013", "+7.05%"],
    ["full3", "12.367", "12.061", "+2.47%"],
    ["hard45", "12.954", "12.795", "+1.23%"],
]
native_table(s, 0.55, 2.15, 5.7, 1.85, headers, rows, col_widths=[1.7, 1.35, 1.35, 1.3],
             delta_col=3, font_size=13)

_, tf3 = tb(s, 0.55, 4.3, 5.7, 2.5)
para(tf3, "Smaller than simulation \u2014 and that's expected:", font=BODY_FONT, size=13, color=TEXT_DARK, bold=True, first=True, space_after=6)
para(tf3, "~13% residual authority vs. full-range in MuJoCo, a positive-voltage-only "
          "actuator constraint the drones don't have, real sensor/actuation noise, "
          "and an already near-optimal LQR baseline with less structural gap to close.",
     font=BODY_FONT, size=12.5, color=MUTED_ON_LIGHT)
tf3.paragraphs[-1].line_spacing = 1.2

img_fit(s, HOVER_PLOTS + r"\yaw360_classical_vs_cmg.png", 6.7, 1.85, 6.1, 5.35, align='center')
footer(s, "Coupled Membrane\u2013Gate Residual Control"); page_num(s, 9)

print("slide 9 done")

# =====================================================================
# Slide 10 - closing / takeaways
# =====================================================================
s = add_slide(bg=NAVY)
eyebrow(s, 0.55, 0.5, "Where This Stands", color=CMG_L)
title_text(s, 0.55, 0.85, 11.5, "Simulation-proven, hardware-started", color=TEXT_LIGHT, size=34)

cards = [
    ("+41.5%", "mean improvement, all 10 simulated mission\u00d7airframe pairs"),
    ("+53.4%", "hard45 headline result, both airframes \u2014 the paper's primary case"),
    ("+3.6%", "3DOF Hover hardware mean, first physical validation, n=1"),
    ("0 / 13", "mission\u00d7platform pairs (sim + hardware) that regressed"),
]
xw = 2.95
for i, (num, label) in enumerate(cards):
    xx = 0.55 + i * (xw + 0.15)
    stat_card(s, xx, 2.0, xw, 1.65, num, label, num_color=CMG_L, bg=NAVY2, line_color=NAVY2, label_color=MUTED_ON_DARK)

_, tf = tb(s, 0.55, 4.05, 12.2, 2.7)
para(tf, "What's next", font=BODY_FONT, size=13, color=CMG_L, bold=True, first=True, space_after=8)
nexts = [
    "Repeated-trial statistics on every hardware number \u2014 today's runs are n=1, directional.",
    "roll and hardstep on the physical Hover; a defensible authority-vs-safety trade-off study.",
    "QDrone2 (full 6-DOF freedom), then physical Crazyflie / Skydio X2 \u2014 closing the sim/hardware authority gap this deck reports.",
    "Frozen-weight hold-out evaluation, to separate learned reusable structure from online trajectory adaptation.",
]
for n in nexts:
    p = para(tf, "\u2192  " + n, font=BODY_FONT, size=13.5, color=TEXT_LIGHT, space_after=9)
    p.line_spacing = 1.15

_, tf2 = tb(s, 0.55, 6.85, 11, 0.4)
para(tf2, "C:\\Research\\papers\\ACC2027_Gate_Residual_Control  \u00b7  docs\\SESSION_INDEX_2026-08-27.md",
     font="Consolas", size=10.5, color=MUTED_ON_DARK, first=True)

print("slide 10 done")
prs.save(r"C:\Users\gandhico\AppData\Local\Temp\claude\C--\9a9072ab-f2b6-4828-b6d1-0ea8887f5819\scratchpad\pptx\deck.pptx")
