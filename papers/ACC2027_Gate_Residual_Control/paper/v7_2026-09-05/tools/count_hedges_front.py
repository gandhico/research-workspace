"""Disclaimer density in the parts reviewers weigh most: abstract,
introduction, and conclusion."""
import io
import re
import sys

PAT = re.compile(
    r"\b(not a |does not|do not|cannot|is not|are not|no claim|not claim|"
    r"without an?\b|rather than|not evidence|not proof|not establish|"
    r"would be incorrect|limitation|not imply|not additional|must not|"
    r"not supported|not universal|no unique|invalidate|does the|not the)\b",
    re.I)


def front(path):
    s = io.open(path, encoding="utf-8").read()
    parts = []
    parts.append(s[s.index(r"\begin{abstract}"):s.index(r"\end{abstract}")])
    parts.append(s[s.index(r"\section{Introduction}"):
                   s.index(r"\section{Simulation Models")])
    i = s.index(r"\section{Discussion and Conclusion}")
    parts.append(s[i:s.index(r"\bibliographystyle", i)])
    body = "\n".join(parts)
    body = re.sub(r"\\begin\{(table|figure)\*?\}.*?\\end\{(table|figure)\*?\}",
                  "", body, flags=re.S)
    body = re.sub(r"%.*", "", body)
    sents = [x.strip() for x in re.split(r"(?<=[.])\s+", body)
             if len(x.strip()) > 25]
    hedge = [x for x in sents if PAT.search(x)]
    return len(sents), len(hedge)


for p in sys.argv[1:]:
    n, h = front(p)
    print(f"{p:20s} abstract+intro+conclusion: {h:3d}/{n:3d} sentences "
          f"carry a disclaimer  ({100 * h / n:.0f}%)")
