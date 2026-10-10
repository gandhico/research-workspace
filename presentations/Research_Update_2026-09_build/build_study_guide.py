"""Printable slide-by-slide speech + Q&A study guide for Research_Update_Slides_2026-09."""
from pathlib import Path
import re
import sys
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle, CondPageBreak)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import speech_content as sc  # noqa: E402

SLIDE_IMG = HERE / "render2"
OUT = HERE.parent / "Research_Update_2026-09_Speech_and_QA_Guide_rebuilt.pdf"

CRIMSON = colors.HexColor("#8C0B41")
DARK = colors.HexColor("#5F0027")
TEAL = colors.HexColor("#A7BABE")
SAND = colors.HexColor("#CFC7BD")
INK = colors.HexColor("#1F1F1F")
GRAY = colors.HexColor("#595959")
PALE = colors.HexColor("#F8F1F4")
LIGHT = colors.HexColor("#F4F5F6")
RULE = colors.HexColor("#D5D9DB")
AMBER_BG = colors.HexColor("#FFF6E5")
AMBER = colors.HexColor("#B7791F")

F = r"C:\Windows\Fonts"
pdfmetrics.registerFont(TTFont("Calibri", F + r"\calibri.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-Bold", F + r"\calibrib.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-Italic", F + r"\calibrii.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-BoldItalic", F + r"\calibriz.ttf"))
addMapping("Calibri", 0, 0, "Calibri")
addMapping("Calibri", 1, 0, "Calibri-Bold")
addMapping("Calibri", 0, 1, "Calibri-Italic")
addMapping("Calibri", 1, 1, "Calibri-BoldItalic")
pdfmetrics.registerFont(TTFont("Tahoma-Bold", F + r"\tahomabd.ttf"))


def S(name, **kw):
    base = dict(fontName="Calibri", fontSize=10.5, leading=14, textColor=INK)
    base.update(kw)
    return ParagraphStyle(name, **base)


ST = {
    "cover": S("cover", fontName="Tahoma-Bold", fontSize=25, leading=31, textColor=CRIMSON, alignment=TA_LEFT),
    "coversub": S("coversub", fontSize=14, leading=19, textColor=GRAY),
    "h1": S("h1", fontName="Tahoma-Bold", fontSize=16, leading=20, textColor=CRIMSON, spaceAfter=6),
    "h2": S("h2", fontName="Calibri-Bold", fontSize=12.5, leading=16, textColor=CRIMSON, spaceBefore=8, spaceAfter=4),
    "body": S("body", spaceAfter=4),
    "small": S("small", fontSize=9.5, leading=12.5, textColor=GRAY),
    "bullet": S("bullet", leftIndent=12, bulletIndent=2, spaceAfter=3, bulletFontName="Calibri"),
    "speech": S("speech", fontSize=12, leading=17, spaceAfter=7),
    "lead": S("lead", fontName="Calibri-Italic", fontSize=11, leading=15, textColor=DARK, spaceAfter=6),
    "q": S("q", fontName="Calibri-Bold", fontSize=10.2, leading=13.2),
    "a": S("a", fontSize=10.2, leading=13.2),
    "cell": S("cell", fontSize=9.8, leading=12.4),
    "cellb": S("cellb", fontName="Calibri-Bold", fontSize=9.8, leading=12.4),
    "hdr": S("hdr", fontName="Calibri-Bold", fontSize=10, leading=12.5, textColor=colors.white),
    "barL": S("barL", fontName="Tahoma-Bold", fontSize=13.5, leading=17, textColor=colors.white),
    "barR": S("barR", fontName="Calibri-Bold", fontSize=12, leading=16, textColor=colors.white, alignment=2),
    "avoid": S("avoid", fontSize=10, leading=13.2, textColor=INK, leftIndent=10, bulletIndent=0, bulletFontName="Calibri"),
    "short": S("short", fontName="Calibri-Bold", fontSize=11, leading=14.5, textColor=DARK),
    "foot": S("foot", fontSize=8, leading=10, textColor=GRAY, alignment=TA_CENTER),
}


def md(s):
    """Escape XML, then turn ^{...} into <super>...</super>."""
    s = escape(s)
    return re.sub(r"\^\{([^}]*)\}", r"<super>\1</super>", s)


def para(s, style="body"):
    return Paragraph(md(s), ST[style])


def grid(rows, widths, header=True, zebra=True, styles=("cell", "cell")):
    data = []
    for i, r in enumerate(rows):
        if header and i == 0:
            data.append([Paragraph(md(c), ST["hdr"]) for c in r])
        else:
            data.append([Paragraph(md(c), ST[styles[min(j, len(styles) - 1)]]) for j, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE)]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), CRIMSON))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if (i % 2 == 0) == header:
                cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(cmds))
    return t


def boxed(flowables, bg=PALE, border=CRIMSON, pad=9, width=7.1 * inch):
    t = Table([[flowables]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.8, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                           ("TOPPADDING", (0, 0), (-1, -1), pad - 2), ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 3)]))
    return t


def bar(left, right):
    t = Table([[Paragraph(md(left), ST["barL"]), Paragraph(md(right), ST["barR"])]],
              colWidths=[5.6 * inch, 1.5 * inch])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CRIMSON), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Calibri", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.7 * inch, 0.45 * inch, "Research update, September 2026 · speech and Q&A study guide")
    canvas.drawRightString(letter[0] - 0.7 * inch, 0.45 * inch, f"{doc.page}")
    canvas.restoreState()


story = []
W = 7.1 * inch

# ------------------------------------------------------------------ cover
story += [Spacer(1, 0.3 * inch), Paragraph("Research Update", ST["cover"]),
          Paragraph("Speech & Q&amp;A Study Guide", ST["cover"]), Spacer(1, 6),
          Paragraph(f"12 slides · about {sc.TOTAL_MINUTES} minutes · September 2026 · Gandhi Contreras, NMSU", ST["coversub"]),
          Spacer(1, 16)]
story.append(para("How to use this guide", "h2"))
for b in [
    "Read each speech aloud twice with a timer. The target time is on every slide header.",
    "Learn the one-line “short version” of each slide; if time runs out, say only that line.",
    "Know the key numbers in the small table; they are the ones people ask about.",
    "Practice the first three answers under “If they ask” for each slide; the rest are backup.",
    "The same script and short answers are in the speaker notes of the deck (Presenter View).",
    "Lines in [brackets] are for you to fill in (your role, a collaborator’s role, an IRB detail).",
]:
    story.append(Paragraph(md(b), ST["bullet"], bulletText="•"))
story.append(para("Run of show (your deck + the new slides)", "h2"))
story.append(grid([["Slide", "Time", "What to say"]] + [list(r) for r in sc.RUN_OF_SHOW],
                  [2.3 * inch, 0.6 * inch, 4.2 * inch], styles=("cellb", "cell", "cell")))
story.append(Spacer(1, 8))
story.append(boxed([para("Three sentences to remember", "h2"),
                    para("1. We keep the classical controller as the anchor and add a small, bounded, learned neuromorphic correction.", "body"),
                    para("2. It helps most under disturbances and model mismatch; a well-tuned baseline narrows the gain, and we say so.", "body"),
                    para("3. Every result is labeled: software, digital twin, hardware, or proposed. We never mix them.", "body")],
                   bg=LIGHT, border=TEAL))
story.append(PageBreak())

# ------------------------------------------------------------------ slides
for sl in sc.SLIDES:
    story.append(bar(f"Slide {sl['n']} · {sl['title']}", f"≈ {sl['time']} min"))
    story.append(Spacer(1, 7))
    img = Image(str(SLIDE_IMG / f"slide-{sl['n']:02d}.jpg"), width=3.55 * inch, height=3.55 * inch * 9 / 16)
    right = [para("Purpose", "h2"), para(sl["purpose"], "body"), para("Key numbers", "h2"),
             grid([[k, v] for k, v in sl["numbers"]], [1.45 * inch, 1.95 * inch], header=False,
                  styles=("cellb", "cell"))]
    top = Table([[img, right]], colWidths=[3.7 * inch, 3.4 * inch])
    top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(top)
    story.append(Spacer(1, 6))
    sp = [para("Say this", "h2")]
    if sl.get("before"):
        sp.append(para(sl["before"], "lead"))
    sp += [para(p, "speech") for p in sl["speech"]]
    sp.append(para("Short version: " + sl["short"], "short"))
    story.append(boxed(sp))
    story.append(Spacer(1, 6))
    story.append(CondPageBreak(3.3 * inch))
    story.append(para("If they ask", "h2"))
    story.append(grid([["Question", "Answer"]] + [[q, a] for q, a in sl["qa"]], [2.35 * inch, 4.75 * inch],
                      styles=("q", "a")))
    story.append(Spacer(1, 6))
    story.append(KeepTogether([boxed([para("Don’t say", "h2")] +
                                     [Paragraph(md(x), ST["avoid"], bulletText="•") for x in sl["avoid"]],
                                     bg=AMBER_BG, border=AMBER, pad=7)]))
    story.append(PageBreak())

# ------------------------------------------------------------------ appendices
story.append(bar("Appendix A · Cross-cutting questions", "backup"))
story.append(Spacer(1, 7))
story.append(grid([["Topic", "Question", "Answer"]] + [list(r) for r in sc.CROSS_QA],
                  [0.9 * inch, 2.0 * inch, 4.2 * inch], styles=("cellb", "q", "a")))
story.append(Spacer(1, 10))
story.append(para("If a question goes badly", "h2"))
story.append(grid([["Situation", "What to say"]] + [list(r) for r in sc.RECOVERY], [1.9 * inch, 5.2 * inch],
                  styles=("cellb", "a")))
story.append(PageBreak())

story.append(bar("Appendix B · Numbers cheat sheet", "one page"))
story.append(Spacer(1, 7))
rows = [["Slide", "Item", "Value"]]
for sl in sc.SLIDES:
    for i, (k, v) in enumerate(sl["numbers"]):
        rows.append([f"{sl['n']}" if i == 0 else "", k, v])
story.append(grid(rows, [0.5 * inch, 2.6 * inch, 4.0 * inch], styles=("cellb", "cell", "cell")))
story.append(PageBreak())

story.append(bar("Appendix C · Glossary and the 8-minute version", "reference"))
story.append(Spacer(1, 7))
story.append(grid([["Term", "Meaning"]] + [list(r) for r in sc.GLOSSARY], [1.7 * inch, 5.4 * inch],
                  styles=("cellb", "cell")))
story.append(Spacer(1, 10))
story.append(para("If you only have 8 minutes: say the short version of each slide", "h2"))
story.append(grid([["Slide", "Short version"]] + [[f"{sl['n']}. {sl['title'].split('|')[0].strip()}", sl["short"]]
                                                  for sl in sc.SLIDES], [1.7 * inch, 5.4 * inch],
                  styles=("cellb", "cell")))

doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                        topMargin=0.6 * inch, bottomMargin=0.7 * inch,
                        title="Research Update — Speech and Q&A Study Guide", author="Gandhi Contreras")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("saved", OUT.name)
