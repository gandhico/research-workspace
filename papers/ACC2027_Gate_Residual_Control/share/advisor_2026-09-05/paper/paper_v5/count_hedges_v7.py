"""How much of the body text is disclaimer rather than claim?"""
import io
import re

s = io.open("ACC2027_v7.tex", encoding="utf-8").read()
body = s[s.index(r"\section{Introduction}"):s.index(r"\section{Discussion")]
body = re.sub(r"\\begin\{(table|figure)\*?\}.*?\\end\{(table|figure)\*?\}", "",
              body, flags=re.S)
body = re.sub(r"%.*", "", body)

sents = [x.strip() for x in re.split(r"(?<=[.])\s+", body) if len(x.strip()) > 25]
pat = re.compile(
    r"\b(not a |does not|do not|cannot|is not|are not|no claim|not claim|"
    r"without an?\b|rather than|not evidence|not proof|not establish|"
    r"would be incorrect|limitation|not imply|not additional|must not|"
    r"not supported|not universal|no unique|invalidate|does the|not the)\b",
    re.I)
hedge = [x for x in sents if pat.search(x)]

print(f"body sentences        : {len(sents)}")
print(f"carrying a disclaimer : {len(hedge)}  ({100 * len(hedge) / len(sents):.0f}%)")
print()
for h in hedge[:12]:
    print("  -", " ".join(h.split())[:112])
