"""Single submission message for the Overleaf AI agent (2026-10-02 night).

Combines: Steven's purple edits with our resolutions (main blocks), the footnote fix, Steven's unmarked style edits,
the Eq. (23) split (corrected to the paper's notation), and a one-line switch that prints all review marks black.
Applied to ACC2027 (10).tex with assert-checked single matches -> ACC2027_v35_final.tex; writes OVERLEAF_FINAL_MESSAGE.md.
"""
from pathlib import Path

import build_blocks_for_own_paper as B

HERE = Path(__file__).resolve().parent
main = {t: (d, o, n) for t, d, o, n in B.MAIN}
opt = {t: (d, o, n) for t, d, o, n in B.OPTIONAL}

STEPS = [
    ("1", "Preamble: load xcolor and print the review marks in black for submission",
     "\\usepackage{graphicx}\n",
     "\\usepackage{graphicx}\n\\usepackage{xcolor} % track changes (Sandoval review)\n"
     "\\definecolor{purple}{rgb}{0,0,0} % submission: review marks print black; delete this line to show them\n"),
    ("2", "Sec. II-C, Eq. (15): frame-aligned rate error, plus a disclosure of what the reported runs used", *main["2"][1:]),
    ("3", "Sec. III-B, before Eq. (24): the rate weight is zero in every run (Steven's colon removal included)",
     "weighting attitude and rate error, respectively:\n\\begin{align}",
     "weighting attitude and rate error, respectively \\textcolor{purple}{(all reported runs use $k_\\omega^*=0$, so "
     "$\\bm y_k^*$ depends on $\\bm e_{q,k}$ only)}\n\\begin{align}"),
    ("4", "Eq. (24): frame-aligned rate error in the PES target", *main["3b"][1:]),
    ("5", "Sec. III-B, after Eq. (28): anti-windup sentence", *main["4"][1:]),
    ("6", "Sec. VI-C, Gate/activity regime: contraction condition", *main["5"][1:]),
    ("6b", "Sec. III-B, Eq. (23) (Steven): split into (23a)-(23c) in the paper's notation; no text refers to Eq. (23)",
     "\\begin{equation}\n \\begin{aligned}\n \\bm a_k&=\\sat_{[0,1]}(G\\bm r_k^+),\\qquad W_0=[I_m,-I_m],\\\\\n"
     " \\bm s_k&=\\sat_{[-1,1]}(W_k\\bm a_k).\n \\end{aligned}\n \\label{eq:readout}\n\\end{equation}\n",
     "\\begin{subequations}\\label{eq:readout}\n\\begin{align}\n \\bm a_k&=\\sat_{[0,1]}(G\\bm r_k^+),\\label{eq:activity}\\\\\n"
     " W_0&=[I_m,-I_m],\\label{eq:decoder_init}\\\\\n \\bm s_k&=\\sat_{[-1,1]}(W_k\\bm a_k).\\label{eq:decoder_output}\n"
     "\\end{align}\n\\end{subequations}\n"),
    ("7", "Sec. VI-A, reproducibility sentence: the repository is private until acceptance", *opt["6"][1:]),
    ("8", "Sec. II-A: citation placement (Steven)", *opt["7a"][1:]),
    ("9", "Sec. II-B: no colon before the collective-thrust display (Steven)", *opt["7b"][1:]),
    ("10", "Sec. III-A: no colon before the current-pair display (Steven)", *opt["7c"][1:]),
    ("11", "Sec. III-A: no colon before the CMG display (Steven)", *opt["7d"][1:]),
    ("12", "Sec. V, proof: wording (Steven)", *opt["7e"][1:]),
]


def main_():
    src = B.SRC.read_text(encoding="utf-8")
    s = src
    for tag, _, old, new in STEPS:
        s = B.sub(s, tag, old, new)
    (HERE / "ACC2027_v35_final.tex").write_text(s, encoding="utf-8", newline="")
    L = ["Apply these 13 replacements to the main .tex file exactly as written. Each FIND text occurs once. Change",
         "nothing else: no rewording, no reformatting, and no other edits to equations, tables or numbers. If a FIND",
         "differs only in spaces or line breaks, match it by content. Afterwards, recompile and confirm the PDF is",
         "still 8 pages.", ""]
    for tag, desc, old, new in STEPS:
        L += [f"### {tag}. {desc}", "FIND:", B.fence(old), "REPLACE WITH:", B.fence(new)]
    (HERE / "OVERLEAF_FINAL_MESSAGE.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote ACC2027_v35_final.tex and OVERLEAF_FINAL_MESSAGE.md")


if __name__ == "__main__":
    main_()
