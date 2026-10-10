"""A2 selection input (noise-free CF2 five-mission runs of the two safe variants) and the A1 limit case."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCR = HERE / "run_a1_limit.py"   # (originally executed from a scratch copy of this script; now shipped in this folder)
jobs = [("run_campaign_a2.py", ["nominal", "gated_b02"], "campaign_a2_nominal_b02.log"),
        ("run_campaign_a2.py", ["nominal", "gated_b01"], "campaign_a2_nominal_b01.log"),
        (str(SCR), [], "campaign_a1_limit.log")]
for script, args, log in jobs:
    path = script if Path(script).is_absolute() else str(HERE / script)
    with (HERE / log).open("w", encoding="utf-8") as fh:
        rc = subprocess.run([sys.executable, path, *args], stdout=fh, stderr=subprocess.STDOUT, cwd=HERE).returncode
    print(script, args, "rc", rc, flush=True)
