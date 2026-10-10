"""Confirm and validate the frozen threshold-aware family settings."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_neuron_basis.py"
SETTINGS = HERE / "analysis" / "development" / "selected_settings.json"


def cases(phase, root, selected):
    if phase == "confirm":
        cells = [("x2", mission) for mission in ("roll", "hard45")]
    else:
        cells = [("x2", mission) for mission in ("full3", "hardstep", "yaw360")]
        cells += [("cf2-rotor", mission) for mission in ("roll", "full3", "hard45", "hardstep", "yaw360")]
    for family, setting in selected.items():
        for platform, mission in cells:
            output = root / platform / mission / family
            command = [
                sys.executable,
                str(RUNNER),
                "--platform", platform,
                "--controller", family,
                "--mission", mission,
                "--duration", "45",
                "--beta", "0.5" if platform == "x2" else "0.2",
                "--actuator-scale", "1.0" if platform == "x2" else "1.5",
                "--learning-rate", "0.0008",
                "--k-error", "8",
                "--k-rate", "0",
                "--output-gate", "torque-saturation-opposition",
                "--family-current-bias", str(setting["current_bias"]),
                "--family-current-gain", str(setting["current_gain"]),
                "--family-feature-tau", str(setting["feature_tau_s"]),
                "--output", str(output),
            ]
            yield f"{platform}/{mission}/{family}", command, output


def execute(item, force):
    label, command, output = item
    if (output / "summary.json").exists() and not force:
        return label, "cached", 0
    output.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command, text=True, capture_output=True)
    (output / "console.log").write_text(
        completed.stdout + "\n--- STDERR ---\n" + completed.stderr,
        encoding="utf-8",
    )
    return label, "ok" if completed.returncode == 0 else "failed", completed.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("confirm", "validate"), required=True)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    selected = json.loads(SETTINGS.read_text(encoding="utf-8"))
    root = HERE / "results" / f"selected_{args.phase}"
    items = list(cases(args.phase, root, selected))
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(execute, item, args.force): item[0] for item in items}
        for index, future in enumerate(as_completed(futures), 1):
            label, status, code = future.result()
            print(f"[{index:02d}/{len(items):02d}] {status:6s} {label}", flush=True)
            if code:
                failures.append(label)
    (root / "campaign_status.json").write_text(
        json.dumps({"phase": args.phase, "n_cases": len(items), "failures": failures}, indent=2) + "\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit(f"{len(failures)} cases failed")


if __name__ == "__main__":
    main()
