import re
from pathlib import Path

D = Path(__file__).resolve().parents[1]
tex = (D / "ACC2027.tex").read_text(encoding="utf-8") + "\n" + (D / "tables" / "table_all_restructured.tex").read_text(encoding="utf-8")
body = "\n".join(l for l in tex.split("\n") if not l.lstrip().startswith("%"))
# strip \iffalse ... \fi blocks
body = re.sub(r"\\iffalse.*?\\fi", "", body, flags=re.S)
labels = re.findall(r"\\label\{([^}]+)\}", body)
refs = re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", body)
print("labels:", len(labels), "| refs:", len(refs))
dups = {l for l in labels if labels.count(l) > 1}
print("duplicate labels:", dups or "none")
unref = [l for l in labels if l not in refs and not l.startswith(("eq:", "sec:")) or (l.startswith("sec:") and l not in refs)]
print("labels never referenced:", unref or "none")
print("refs without label:", sorted({r for r in refs if r not in labels}) or "none")
for kind in ("fig:", "tab:", "prop:"):
    print(kind, sorted({l for l in labels if l.startswith(kind)}))
