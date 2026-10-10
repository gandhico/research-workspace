"""Coverage check: does every symbol that appears inside a displayed
equation also appear somewhere in the nomenclature table?

Approximate by design -- it reports candidates to eyeball, not errors.
"""
from __future__ import annotations

import io
import re

s = io.open("ACC2027_v6.tex", encoding="utf-8").read()

# the nomenclature table body
i = s.index("label{tab:nomen}")
nomen = s[i:s.index("end{table*}", i)]

# every displayed-equation body
eqs = []
for env in ("equation", "align", "gather", "equation*", "align*"):
    eqs += re.findall(r"\\begin\{%s\}(.*?)\\end\{%s\}" % (re.escape(env),
                                                          re.escape(env)),
                      s, re.S)
blob = "\n".join(eqs)

# candidate symbol tokens
toks = set()
toks |= set(re.findall(r"\\bm\\[A-Za-z]+", blob))        # \bm\omega
toks |= set(re.findall(r"\\bm\{?[A-Za-z]\}?", blob))     # \bm u
toks |= set(re.findall(r"\\[A-Za-z]{2,}", blob))         # \sigma, \clip ...
toks |= set(re.findall(r"(?<![A-Za-z\\])[A-Za-z](?=[_^\s\\,)\]}])", blob))

IGNORE = {
    r"\begin", r"\end", r"\left", r"\right", r"\quad", r"\qquad", r"\label",
    r"\text", r"\rm", r"\mathsf", r"\bm", r"\aligned", r"\endaligned",
    r"\frac", r"\max", r"\min", r"\sum", r"\cdot", r"\times", r"\to",
    r"\in", r"\le", r"\ge", r"\ne", r"\approx", r"\qquad", r"\ldots",
    r"\dots", r"\big", r"\Big", r"\bigl", r"\bigr", r"\mathbb", r"\hat",
    r"\bar", r"\dot", r"\ddot", r"\vec", r"\operatorname", r"\mathcal",
    r"\displaystyle", r"\notag", r"\nonumber", r"\;", r"\,", r"\!",
}

missing = []
for t in sorted(toks):
    if t in IGNORE or len(t) == 0:
        continue
    key = t.replace(r"\bm", "").replace("{", "").replace("}", "")
    if key and key not in nomen and t not in nomen:
        missing.append(t)

print("symbols in equations but not found verbatim in Table I:")
for m in missing:
    print("   ", m)
print(f"\n({len(missing)} to eyeball; many will be operators or already "
      "covered by a grouped entry)")
