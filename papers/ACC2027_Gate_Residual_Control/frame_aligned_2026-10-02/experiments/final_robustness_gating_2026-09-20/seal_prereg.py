"""Append SHA-256 hashes of the frozen files to PREREGISTRATION.md (run once, before launch)."""
import datetime
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
files = ["run_final_robustness.py", "run_campaign.py", "run_validation.py", "PREREGISTRATION.md"]
doc = (HERE / "PREREGISTRATION.md").read_text(encoding="utf-8")
assert "## 7. Seal" not in doc, "already sealed"
lines = ["", "## 7. Seal", "", f"Sealed {datetime.datetime.now().isoformat(timespec='seconds')} (local), before launching any campaign.", "",
         "| file | sha256 |", "|---|---|"]
for f in files[:-1]:
    lines.append(f"| `{f}` | `{hashlib.sha256((HERE / f).read_bytes()).hexdigest()}` |")
lines.append(f"| `PREREGISTRATION.md` (above this section) | `{hashlib.sha256(doc.encode('utf-8')).hexdigest()}` |")
(HERE / "PREREGISTRATION.md").write_text(doc + "\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
