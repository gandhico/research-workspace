"""Execute the preregistered strict matrix or threshold-aware development sweep."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER = HERE / "run_neuron_basis.py"
PLATFORMS = ("x2", "cf2-rotor")
MISSIONS = ("roll", "full3", "hard45", "hardstep", "yaw360")
CONTROLLERS = (
    "classical",
    "cmg",
    "lif",
    "alif",
    "lifrate",
    "izhikevich",
    "constant-one",
    "paired-current",
)


def platform_args(platform: str) -> list[str]:
    if platform == "x2":
        return ["--beta", "0.5", "--actuator-scale", "1.0"]
    return ["--beta", "0.2", "--actuator-scale", "1.5"]


def strict_cases(root: Path):
    for platform in PLATFORMS:
        for mission in MISSIONS:
            for controller in CONTROLLERS:
                output = root / platform / mission / controller
                command = [
                    sys.executable,
                    str(RUNNER),
                    "--platform",
                    platform,
                    "--controller",
                    controller,
                    "--mission",
                    mission,
                    "--duration",
                    "45",
                    "--learning-rate",
                    "0.0008",
                    "--k-error",
                    "8",
                    "--k-rate",
                    "0",
                    "--output",
                    str(output),
                    *platform_args(platform),
                ]
                if controller != "classical":
                    command += ["--output-gate", "torque-saturation-opposition"]
                yield f"{platform}/{mission}/{controller}", command, output


def development_cases(root: Path):
    # Bias + gain = 2.0 in every candidate. Therefore the maximum canonical
    # current and archived maximum-response feature calibration do not change.
    conventional_biases = (0.75, 0.90, 0.97, 1.03)
    izh_biases = (0.00, 0.25, 0.50, 0.75)
    feature_taus = (0.005, 0.020)
    for family in ("lif", "alif", "lifrate", "izhikevich"):
        biases = izh_biases if family == "izhikevich" else conventional_biases
        for bias in biases:
            gain = 2.0 - bias
            for tau in feature_taus:
                tag = f"b{bias:.2f}_g{gain:.2f}_tau{tau:.3f}".replace(".", "p")
                for mission in ("roll", "hard45"):
                    output = root / family / tag / mission
                    command = [
                        sys.executable,
                        str(RUNNER),
                        "--platform",
                        "x2",
                        "--controller",
                        family,
                        "--mission",
                        mission,
                        "--duration",
                        "15",
                        "--beta",
                        "0.5",
                        "--learning-rate",
                        "0.0008",
                        "--k-error",
                        "8",
                        "--k-rate",
                        "0",
                        "--output-gate",
                        "torque-saturation-opposition",
                        "--family-current-bias",
                        str(bias),
                        "--family-current-gain",
                        str(gain),
                        "--family-feature-tau",
                        str(tau),
                        "--output",
                        str(output),
                    ]
                    yield f"{family}/{tag}/{mission}", command, output


def execute(case, force: bool):
    label, command, output = case
    summary = output / "summary.json"
    if summary.exists() and not force:
        return label, "cached", 0
    output.mkdir(parents=True, exist_ok=True)
    log_path = output / "console.log"
    completed = subprocess.run(command, text=True, capture_output=True)
    log_path.write_text(
        completed.stdout + "\n--- STDERR ---\n" + completed.stderr,
        encoding="utf-8",
    )
    return label, ("ok" if completed.returncode == 0 else "failed"), completed.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("strict", "development"), required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")
    root = HERE / "results" / ("strict_exact" if args.mode == "strict" else args.mode)
    cases = list(strict_cases(root) if args.mode == "strict" else development_cases(root))
    failures = []
    counts = {"ok": 0, "cached": 0, "failed": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_map = {pool.submit(execute, case, args.force): case[0] for case in cases}
        for index, future in enumerate(as_completed(future_map), 1):
            label, status, code = future.result()
            counts[status] += 1
            print(f"[{index:03d}/{len(cases):03d}] {status:6s} {label}", flush=True)
            if code:
                failures.append(label)
    record = {
        "mode": args.mode,
        "python": sys.executable,
        "workers": args.workers,
        "n_cases": len(cases),
        "counts": counts,
        "failures": failures,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "campaign_status.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    if failures:
        raise SystemExit(f"{len(failures)} cases failed; inspect console.log files")


if __name__ == "__main__":
    main()
