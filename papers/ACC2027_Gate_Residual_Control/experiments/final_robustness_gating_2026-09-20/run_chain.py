"""Run the remaining pre-registered campaigns back to back (max 4 parallel workers each)."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for name, log in (("hardstep-development", "campaign_dev.log"),
                  ("disturbance", "campaign_dist.log"),
                  ("noise", "campaign_noise.log")):
    with (HERE / log).open("w", encoding="utf-8") as fh:
        rc = subprocess.run([sys.executable, str(HERE / "run_campaign.py"), "--campaign", name, "--workers", "4"],
                            stdout=fh, stderr=subprocess.STDOUT, cwd=HERE).returncode
    print(name, "rc", rc, flush=True)
