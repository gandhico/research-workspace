from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PLATFORM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUANSER_PYTHON = Path(r"C:\Quanser\0_libraries\python")

EXAMPLES = {
    "balance": PLATFORM_ROOT / "vendor" / "quanser_examples" / "qube_servo_python" / "balance_control_qube.py",
    "pd_task": PLATFORM_ROOT / "vendor" / "quanser_examples" / "qube_servo_python" / "pd_control_qube_task.py",
    "pd_immediate": PLATFORM_ROOT / "vendor" / "quanser_examples" / "qube_servo_python" / "pd_control_qube_immediate.py",
    "read_write3": PLATFORM_ROOT / "vendor" / "quanser_examples" / "qube_servo_python" / "read_write_qube3.py",
    "quickstart_pd": PLATFORM_ROOT / "vendor" / "quanser_examples" / "qube_servo3_quick_start_software" / "pdcontroller.py",
    "test_quarc": PLATFORM_ROOT / "vendor" / "quanser_examples" / "qube_servo3_quick_start_software" / "testQuarc.py",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch copied, unmodified Quanser-provided Qube examples.")
    parser.add_argument("--list", action="store_true", help="List available copied examples and exit.")
    parser.add_argument("--example", choices=sorted(EXAMPLES), help="Example to launch.")
    parser.add_argument("--quanser-python", type=Path, default=DEFAULT_QUANSER_PYTHON)
    parser.add_argument(
        "--i-understand",
        action="store_true",
        help="Required to run examples because they may command hardware using their hard-coded defaults.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list:
        for name, path in EXAMPLES.items():
            print(f"{name:14s} {path}")
        return
    if not args.example:
        raise SystemExit("Choose --example or use --list.")
    if not args.i_understand:
        raise SystemExit("Refusing to run a vendor example without --i-understand.")

    script = EXAMPLES[args.example]
    if not script.exists():
        raise FileNotFoundError(script)
    if not args.quanser_python.exists():
        raise FileNotFoundError(args.quanser_python)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(args.quanser_python) + os.pathsep + env.get("PYTHONPATH", "")
    try:
        __import__("quanser.hardware")
    except ModuleNotFoundError as exc:
        if exc.name == "quanser":
            raise SystemExit(
                "Quanser API bindings are not installed in this interpreter. "
                "Run .\\scripts\\setup_env.ps1 and launch this command from the activated .venv."
            ) from exc
        raise
    subprocess.run([sys.executable, str(script)], cwd=str(script.parent), env=env, check=True)


if __name__ == "__main__":
    main()
