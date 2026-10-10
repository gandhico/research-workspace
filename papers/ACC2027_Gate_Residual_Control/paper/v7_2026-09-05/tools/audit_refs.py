"""Audit: is every figure/table label actually cross-referenced in the text,
and is every \ref target defined?"""
import io
import re

s = io.open("ACC2027.tex", encoding="utf-8").read()

labels = re.findall(r"\\label\{((?:fig|tab):[^}]+)\}", s)
refs = set(re.findall(r"\\ref\{((?:fig|tab):[^}]+)\}", s))

print(f"{'LABEL':<30}{'REFERENCED?'}")
print("-" * 46)
unref = []
for lab in labels:
    ok = lab in refs
    if not ok:
        unref.append(lab)
    print(f"{lab:<30}{'yes' if ok else '*** NOT REFERENCED ***'}")

dangling = sorted(r for r in refs if r not in labels)
print()
print(f"unreferenced labels : {unref if unref else 'none'}")
print(f"dangling \\ref targets: {dangling if dangling else 'none'}")
