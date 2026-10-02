"""Execute the preregistered development check or confirmatory matrix (cached by summary.json)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_cmg_controls.py"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
# arm label -> runner arguments
ARMS = {
    "lpf-logistic": ["--controller", "lpf-logistic"],
    "constant-rest": ["--controller", "constant-rest"],
    "latch-replay": ["--controller", "latch-replay"],
    "cmg_chi0": ["--controller", "cmg", "--cmg-adaptive", "0"],
    "constant-one-nengo-order": ["--controller", "constant-one-nengo-order"],
    # Added 2026-10-01 per preregistered development rule (G differed from 1e5 by > 3 pp):
    "cmg_G1e3": ["--controller", "cmg", "--cmg-readout-gain", "1000"],
    "cmg_G1": ["--controller", "cmg", "--cmg-readout-gain", "1"],
}
COMMON = ["--learning-rate", "0.0008", "--k-error", "8", "--k-rate", "0",
          "--output-gate", "torque-saturation-opposition"]


def platform_args(platform: str) -> list[str]:
    return ["--beta", "0.5", "--actuator-scale", "1.0"] if platform == "x2" else ["--beta", "0.2", "--actuator-scale", "1.5"]


def confirm_cases(root: Path):
    for platform in PLATFORMS:
        for mission in MISSIONS:
            for arm, extra in ARMS.items():
                out = root / platform / mission / arm
                cmd = [sys.executable, str(RUNNER), "--platform", platform, "--mission", mission,
                       "--duration", "45", *COMMON, *platform_args(platform), *extra, "--output", str(out)]
                yield f"{platform}/{mission}/{arm}", cmd, out


def development_cases(root: Path):
    for gain in (1.0, 1.0e3, 1.0e5):
        for chi in (0, 1):
            tag = f"G{gain:.0e}_chi{chi}".replace("+", "")
            for mission in ("roll", "hard45"):
                out = root / tag / mission
                cmd = [sys.executable, str(RUNNER), "--platform", "x2", "--mission", mission, "--duration", "15",
                       *COMMON, *platform_args("x2"), "--controller", "cmg",
                       "--cmg-readout-gain", str(gain), "--cmg-adaptive", str(chi), "--output", str(out)]
                yield f"{tag}/{mission}", cmd, out


def execute(case, force: bool):
    label, cmd, out = case
    if (out / "summary.json").exists() and not force:
        return label, "cached", 0.0
    out.mkdir(parents=True, exist_ok=True)
    start = time.time()
    done = subprocess.run(cmd, text=True, capture_output=True)
    (out / "console.log").write_text(done.stdout + "\n--- STDERR ---\n" + done.stderr, encoding="utf-8")
    return label, ("ok" if done.returncode == 0 else "failed"), time.time() - start


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("development", "confirm"), required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = HERE / "results" / args.mode
    cases = list(development_cases(root) if args.mode == "development" else confirm_cases(root))
    counts, failures = {"ok": 0, "cached": 0, "failed": 0}, []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(execute, c, args.force) for c in cases]
        for fut in as_completed(futures):
            label, status, secs = fut.result()
            counts[status] += 1
            if status == "failed":
                failures.append(label)
            print(f"[{sum(counts.values())}/{len(cases)}] {status:6s} {secs:6.0f}s {label}", flush=True)
    status = {"mode": args.mode, "python": sys.executable, "workers": args.workers,
              "n_cases": len(cases), "counts": counts, "failures": failures}
    (root / "campaign_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
