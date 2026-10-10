"""Verify that the files sealed in PREREGISTRATION.md section 7 still hash to the recorded values.

PREREGISTRATION.md itself is compared on the text that preceded the seal (everything before '## 7. Seal'); later sections
(amendments A1, A2, addenda) are appended by design and are not part of that hash.
"""
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
doc = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
seal = doc[doc.index("## 7. Seal"):]
end = seal.find("\n## 8.")
seal_block = seal if end < 0 else seal[:end]
ok = True
for name, h in re.findall(r"\| `([^`]+)` \| `([0-9a-f]{64})` \|", seal_block):
    if name.startswith("PREREGISTRATION.md"):
        body = doc[:doc.index("## 7. Seal")].rstrip("\n") + "\n"
        # the sealed text ended exactly before the seal heading, plus one blank line handled by the sealing script
        got = hashlib.sha256((doc[:doc.index("\n## 7. Seal")]).encode("utf-8")).hexdigest()
    else:
        got = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
    match = got == h
    ok &= match
    print(f"{'ok  ' if match else 'DIFF'} {name}")
print("\nSEAL INTACT" if ok else "\nSEAL MISMATCH (see above)")
sys.exit(0 if ok else 1)
