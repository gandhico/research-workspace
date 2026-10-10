import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
for args, log in ((["confirm", "gated_b02"], "campaign_a2_confirm.log"),
                  (["disturbance", "gated_b02"], "campaign_a2_dist.log"),
                  (["noise_rest", "gated_b02"], "campaign_a2_noise.log")):
    with (HERE / log).open("w", encoding="utf-8") as fh:
        rc = subprocess.run([sys.executable, str(HERE / "run_campaign_a2.py"), *args], stdout=fh, stderr=subprocess.STDOUT, cwd=HERE).returncode
    print(args, "rc", rc, flush=True)
