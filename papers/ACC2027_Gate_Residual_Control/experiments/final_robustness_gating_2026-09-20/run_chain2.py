"""After the noise campaign: amendment A1 (4 runs), then amendment A2 development stage (8 runs)."""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
while not (HERE / "results" / "status_noise.json").exists():
    time.sleep(15)
for script, args, log in (("run_campaign_a1.py", [], "campaign_a1.log"),
                          ("run_campaign_a2.py", ["dev"], "campaign_a2_dev.log")):
    with (HERE / log).open("w", encoding="utf-8") as fh:
        rc = subprocess.run([sys.executable, str(HERE / script), *args], stdout=fh, stderr=subprocess.STDOUT, cwd=HERE).returncode
    print(script, args, "rc", rc, flush=True)
